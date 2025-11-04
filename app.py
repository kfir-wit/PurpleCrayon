from __future__ import annotations

import mimetypes
import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from PIL import Image
from werkzeug.utils import secure_filename

from purplecrayon import AssetRequest, PurpleCrayon

# LangSmith tracing setup
try:
    from langsmith import traceable
    
    # Enable LangSmith tracing if API key is set
    LANGCHAIN_API_KEY = os.environ.get("LANGCHAIN_API_KEY")
    LANGCHAIN_TRACING_V2 = os.environ.get("LANGCHAIN_TRACING_V2", "true").lower() == "true"
    LANGCHAIN_PROJECT = os.environ.get("LANGCHAIN_PROJECT", "purplecrayon-gui")
    
    if LANGCHAIN_API_KEY and LANGCHAIN_TRACING_V2:
        # Set environment variables for LangSmith to pick up
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
        
        LANGSMITH_ENABLED = True
        print(f"[INFO] LangSmith tracing enabled for project: {LANGCHAIN_PROJECT}")
        print(f"[INFO] Set LANGCHAIN_API_KEY to enable tracing. View traces at: https://smith.langchain.com")
    else:
        LANGSMITH_ENABLED = False
        if not LANGCHAIN_API_KEY:
            print("[INFO] LangSmith tracing disabled: LANGCHAIN_API_KEY not set")
        else:
            print("[INFO] LangSmith tracing disabled: LANGCHAIN_TRACING_V2 not enabled")
except ImportError:
    # LangSmith not available, create a no-op decorator
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    LANGSMITH_ENABLED = False
    print("[INFO] LangSmith not available, tracing disabled")


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "gui_templates"
STATIC_DIR = BASE_DIR / "gui_static"
OUTPUT_ROOT = BASE_DIR / "gui_output"

app = Flask(__name__, template_folder=str(TEMPLATE_DIR), static_folder=str(STATIC_DIR))

# Debug: Log all incoming requests to API routes
@app.before_request
def log_request():
    if request.path.startswith("/api/"):
        print(f"[DEBUG] Incoming request: {request.method} {request.path}")

# Ensure output directory exists immediately so the user can inspect it
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# Single PurpleCrayon client reused across jobs
CRAYON = PurpleCrayon(assets_dir="./assets")


class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class JobStore:
    """Thread-safe in-memory store for job metadata."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def create_job(self) -> Dict:
        job_id = uuid4().hex
        job_record = {
            "id": job_id,
            "status": JobStatus.PENDING,
            "progress": 0,
            "message": "Waiting to start",
            "prompt": "",
            "operations": [],
            "results": [],
            "errors": [],
        }
        with self._lock:
            self._jobs[job_id] = job_record
        return job_record

    def update_job(self, job_id: str, **fields) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.update(fields)

    def get_job(self, job_id: str) -> Optional[Dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def mutate_job(self, job_id: str, fn) -> Optional[Dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            fn(job)
            return dict(job)


JOBS = JobStore()
EXECUTOR = ThreadPoolExecutor(max_workers=2)


def allowed_operations() -> Dict[str, str]:
    return {
        "fetch": "Fetch stock images",
        "generate": "Generate AI images",
        "clone": "Clone an uploaded image",
        "augment": "Augment an uploaded image",
    }


@traceable(name="start_background_job", run_type="chain")
def start_background_job(
    job_id: str,
    prompt: str,
    operations: List[str],
    uploaded_path: Optional[Path],
) -> None:
    """Kick off a job in the background executor."""

    def runner() -> None:
        job_dir = OUTPUT_ROOT / job_id
        images_dir = job_dir / "images"
        thumbnails_dir = job_dir / "thumbnails"
        uploads_dir = job_dir / "uploads"

        for directory in (images_dir, thumbnails_dir, uploads_dir):
            directory.mkdir(parents=True, exist_ok=True)

        job_upload_path = uploaded_path

        JOBS.update_job(
            job_id,
            status=JobStatus.RUNNING,
            progress=1 if operations else 0,
            message="Starting job",
            prompt=prompt,
            operations=operations,
        )

        if not operations:
            JOBS.update_job(
                job_id,
                status=JobStatus.FAILED,
                progress=0,
                message="Select at least one operation to run.",
            )
            return

        total_steps = len(operations)
        try:
            for index, operation in enumerate(operations, start=1):
                JOBS.update_job(
                    job_id,
                    progress=int(((index - 1) / total_steps) * 100),
                    message=f"Running {operation.title()}...",
                )

                if operation in {"clone", "augment"} and not job_upload_path:
                    JOBS.update_job(
                        job_id,
                        status=JobStatus.FAILED,
                        progress=int(((index - 1) / total_steps) * 100),
                        message=f"{operation.title()} requires an uploaded image.",
                    )
                    return

                result = execute_operation(operation, prompt, job_upload_path, job_dir)

                if not result["success"]:
                    JOBS.update_job(
                        job_id,
                        status=JobStatus.FAILED,
                        progress=int(((index - 1) / total_steps) * 100),
                        message=result["message"],
                        errors=append_error(job_id, result["message"]),
                    )
                    return

                record_outputs(
                    job_id,
                    operation,
                    result["images"],
                    images_dir,
                    thumbnails_dir,
                )

                JOBS.update_job(
                    job_id,
                    progress=int((index / total_steps) * 100),
                    message=f"{operation.title()} completed.",
                )

            JOBS.update_job(
                job_id,
                status=JobStatus.SUCCESS,
                progress=100,
                message="All operations completed.",
            )
        except Exception as exc:  # pragma: no cover - defensive
            JOBS.update_job(
                job_id,
                status=JobStatus.FAILED,
                message=f"Job failed: {exc}",
                errors=append_error(job_id, str(exc)),
            )

    EXECUTOR.submit(runner)


@traceable(name="execute_operation", run_type="chain")
def execute_operation(
    operation: str,
    prompt: str,
    uploaded_path: Optional[Path],
    job_dir: Path,
) -> Dict:
    """Run a single PurpleCrayon operation."""
    if operation == "fetch":
        request = AssetRequest(description=prompt or "Image", max_results=3)
        outcome = CRAYON.fetch(request)
        return {"success": outcome.success, "message": outcome.message, "images": outcome.images}

    if operation == "generate":
        request = AssetRequest(
            description=prompt or "Image",
            max_results=3,
            output_dir=job_dir / "generate",
        )
        outcome = CRAYON.generate(request)
        return {"success": outcome.success, "message": outcome.message, "images": outcome.images}

    if operation == "clone":
        outcome = CRAYON.clone(
            source=str(uploaded_path),
            guidance=prompt or None,
        )
        return {"success": outcome.success, "message": outcome.message, "images": outcome.images}

    if operation == "augment":
        outcome = CRAYON.augment(
            image_path=str(uploaded_path),
            prompt=prompt or "Apply subtle enhancements",
            output_dir=job_dir / "augment",
        )
        return {"success": outcome.success, "message": outcome.message, "images": outcome.images}

    return {"success": False, "message": f"Unsupported operation: {operation}", "images": []}


def record_outputs(
    job_id: str,
    operation: str,
    images: List,
    images_dir: Path,
    thumbnails_dir: Path,
) -> None:
    """Persist operation outputs and thumbnails."""
    for image_result in images:
        try:
            stored = prepare_image_files(
                image_result,
                operation,
                images_dir,
                thumbnails_dir,
            )
        except Exception as exc:  # pragma: no cover - defensive
            # Log to console but don't show in GUI - these are non-critical errors
            # where some images fail to process but the operation continues
            image_path = getattr(image_result, "path", "unknown")
            print(f"[WARNING] Failed to store image from {image_path}: {exc}")
            print(f"[WARNING] This image will be skipped, but the operation will continue.")
            continue

        def mutator(job):
            job["results"].append(stored)

        JOBS.mutate_job(job_id, mutator)


def prepare_image_files(
    image_result,
    operation: str,
    images_dir: Path,
    thumbnails_dir: Path,
) -> Dict:
    """Copy or download an image, generate thumbnail, and return metadata."""
    source_path_str = image_result.path
    is_url = source_path_str.startswith(("http://", "https://"))
    
    print(f"[DEBUG] ===== prepare_image_files START =====")
    print(f"[DEBUG] source_path_str={source_path_str}")
    print(f"[DEBUG] is_url={is_url}")
    print(f"[DEBUG] image_result attributes: {dir(image_result)}")
    print(f"[DEBUG] image_result.path={getattr(image_result, 'path', 'N/A')}")
    print(f"[DEBUG] image_result.format={getattr(image_result, 'format', 'N/A')}")
    print(f"[DEBUG] image_result.provider={getattr(image_result, 'provider', 'N/A')}")
    print(f"[DEBUG] image_result.source={getattr(image_result, 'source', 'N/A')}")
    
    # Initial extension extraction
    ext = None
    if is_url:
        # Parse URL to remove query parameters
        parsed_url = urlparse(source_path_str)
        path_without_query = parsed_url.path
        print(f"[DEBUG] URL parsing: path_without_query={path_without_query}")
        # Extract extension from path (before any query params)
        if path_without_query:
            source_path = Path(path_without_query)
            ext = source_path.suffix.lower()
            print(f"[DEBUG] Extracted extension from URL path: {ext}")
            # Clean up: remove query strings that might have leaked into suffix
            if "?" in ext:
                ext = ext.split("?")[0]
                print(f"[DEBUG] Cleaned extension (removed query): {ext}")
    else:
        source_path = Path(source_path_str)
        ext = source_path.suffix.lower()
        print(f"[DEBUG] Local file extension: {ext}")

    # Validate extension - must be a valid image extension
    valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}
    # Reject numeric-only extensions and invalid ones
    if not ext or ext not in valid_extensions:
        print(f"[DEBUG] Extension '{ext}' is invalid, setting to None")
        ext = None
    else:
        print(f"[DEBUG] Extension '{ext}' is valid")

    # If no valid extension found, try to get it from image_result.format
    if not ext:
        fmt_value = (getattr(image_result, "format", "") or "").lower()
        print(f"[DEBUG] Trying image_result.format: '{fmt_value}'")
        if fmt_value:
            # Handle MIME types like "image/jpeg"
            if "/" in fmt_value:
                guessed = mimetypes.guess_extension(fmt_value)
                print(f"[DEBUG] MIME type detected, guessed extension: {guessed}")
                if guessed and guessed in valid_extensions:
                    ext = guessed
                else:
                    # Try to infer from MIME type
                    if "jpeg" in fmt_value or "jpg" in fmt_value:
                        ext = ".jpg"
                    elif "png" in fmt_value:
                        ext = ".png"
                    elif "gif" in fmt_value:
                        ext = ".gif"
                    elif "webp" in fmt_value:
                        ext = ".webp"
                    print(f"[DEBUG] Inferred extension from MIME: {ext}")
            else:
                # Handle format strings like "jpeg", "png", ".png"
                fmt_clean = fmt_value.lstrip(".")
                print(f"[DEBUG] Format string detected: '{fmt_clean}'")
                if fmt_clean in {"jpg", "jpeg"}:
                    ext = ".jpg"
                elif fmt_clean in {"png", "gif", "webp", "bmp", "tiff", "tif"}:
                    ext = f".{fmt_clean}"
                else:
                    ext = None
                print(f"[DEBUG] Extension from format string: {ext}")
        else:
            print(f"[DEBUG] No format value in image_result")

    file_id = uuid4().hex
    # Use temporary extension if we still don't have one (will detect after download)
    temp_ext = ext or ".tmp"
    filename = f"{operation}_{file_id}{temp_ext}"
    destination = images_dir / filename
    print(f"[DEBUG] Using temp extension: {temp_ext}, filename: {filename}")

    # Download or copy the image
    content_type = None
    if is_url:
        print(f"[DEBUG] Downloading from URL: {source_path_str}")
        content_type = download_remote_image(source_path_str, destination)
        print(f"[DEBUG] Download complete, Content-Type: {content_type}")
    else:
        if source_path.exists():
            print(f"[DEBUG] Copying local file: {source_path}")
            shutil.copy2(source_path, destination)
        else:
            raise FileNotFoundError(f"Local image not found: {source_path}")

    # If we downloaded a file and don't have a valid extension yet, detect format
    if is_url and (not ext or temp_ext == ".tmp"):
        print(f"[DEBUG] Need to detect format after download (ext={ext}, temp_ext={temp_ext})")
        # Try to detect from downloaded file using PIL
        detected_ext = None
        try:
            with Image.open(destination) as img:
                detected_format = img.format
                print(f"[DEBUG] PIL detected format: {detected_format}")
                if detected_format:
                    fmt_lower = detected_format.lower()
                    if fmt_lower in {"jpeg", "jpg"}:
                        detected_ext = ".jpg"
                    elif fmt_lower in {"png", "gif", "webp", "bmp", "tiff", "tif"}:
                        detected_ext = f".{fmt_lower}"
                    print(f"[DEBUG] PIL detected extension: {detected_ext}")
        except Exception as e:
            print(f"[DEBUG] PIL detection failed: {e}")
        
        # If PIL detection failed, try Content-Type header
        if not detected_ext and content_type:
            print(f"[DEBUG] Trying Content-Type header: {content_type}")
            guessed = mimetypes.guess_extension(content_type)
            print(f"[DEBUG] mimetypes.guess_extension result: {guessed}")
            if guessed and guessed in valid_extensions:
                detected_ext = guessed
            elif "jpeg" in content_type.lower() or "jpg" in content_type.lower():
                detected_ext = ".jpg"
            elif "png" in content_type.lower():
                detected_ext = ".png"
            elif "gif" in content_type.lower():
                detected_ext = ".gif"
            elif "webp" in content_type.lower():
                detected_ext = ".webp"
            print(f"[DEBUG] Content-Type inferred extension: {detected_ext}")
        
        # Use detected extension or default to .png
        if detected_ext:
            ext = detected_ext
        else:
            ext = ".png"
            print(f"[DEBUG] Using default extension: {ext}")
        
        print(f"[DEBUG] Final extension: {ext}, temp_ext was: {temp_ext}")
        # Rename file if we changed the extension
        if ext != temp_ext:
            new_filename = f"{operation}_{file_id}{ext}"
            new_destination = images_dir / new_filename
            print(f"[DEBUG] Renaming file from {filename} to {new_filename}")
            destination.rename(new_destination)
            destination = new_destination
            filename = new_filename
    else:
        print(f"[DEBUG] Using existing extension: {ext}")

    # Ensure filename has valid extension (should already be fixed, but double-check)
    if not filename.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        # If filename still has invalid extension, use PNG
        filename = f"{operation}_{file_id}.png"
        new_destination = images_dir / filename
        if destination.exists() and destination != new_destination:
            destination.rename(new_destination)
            destination = new_destination
        print(f"[DEBUG] Final filename fix: {filename}")
    
    thumbnail_path = thumbnails_dir / filename
    print(f"[DEBUG] Creating thumbnail: {thumbnail_path}")
    try:
        create_thumbnail(destination, thumbnail_path)
        print(f"[DEBUG] Thumbnail created successfully")
    except Exception as e:
        print(f"[DEBUG] Thumbnail creation failed: {e}")
        raise

    print(f"[DEBUG] ===== prepare_image_files END (filename={filename}) =====\n")
    return {
        "id": file_id,
        "operation": operation,
        "provider": image_result.provider,
        "source": image_result.source,
        "width": getattr(image_result, "width", None),
        "height": getattr(image_result, "height", None),
        "filename": filename,
        "image_path": str(destination),
        "thumbnail_path": str(thumbnail_path),
    }


def download_remote_image(url: str, destination: Path) -> Optional[str]:
    """Download image from remote URL and return Content-Type header."""
    if not url:
        raise ValueError("Empty image URL.")

    print(f"[DEBUG] download_remote_image: Starting download from {url}")
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        response = client.get(url)
        response.raise_for_status()
        print(f"[DEBUG] download_remote_image: Response status={response.status_code}")
        print(f"[DEBUG] download_remote_image: Response headers={dict(response.headers)}")
        content_type = response.headers.get("Content-Type")
        print(f"[DEBUG] download_remote_image: Content-Type={content_type}")
        print(f"[DEBUG] download_remote_image: Content length={len(response.content)} bytes")
        destination.write_bytes(response.content)
        print(f"[DEBUG] download_remote_image: File saved to {destination}")
        # Return Content-Type header for format detection
        return content_type


def create_thumbnail(source: Path, destination: Path, size: int = 256) -> None:
    """Create a square thumbnail while preserving aspect ratio."""
    print(f"[DEBUG] create_thumbnail: source={source}, destination={destination}")
    print(f"[DEBUG] create_thumbnail: source exists={source.exists()}")
    if source.exists():
        print(f"[DEBUG] create_thumbnail: source size={source.stat().st_size} bytes")
    try:
        with Image.open(source) as img:
            print(f"[DEBUG] create_thumbnail: Image opened, format={img.format}, mode={img.mode}, size={img.size}")
            img.thumbnail((size, size))
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
                print(f"[DEBUG] create_thumbnail: Converted to RGB")
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine format from destination extension or use PNG as default
            dest_ext = destination.suffix.lower()
            format_map = {
                ".jpg": "JPEG", ".jpeg": "JPEG",
                ".png": "PNG",
                ".gif": "GIF",
                ".webp": "WEBP",
            }
            save_format = format_map.get(dest_ext, "PNG")
            
            # If destination has invalid extension, ensure it has .png
            if save_format == "PNG" and dest_ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                # Rename to have .png extension
                destination = destination.with_suffix(".png")
                print(f"[DEBUG] create_thumbnail: Fixed invalid extension, using .png")
            
            print(f"[DEBUG] create_thumbnail: Saving thumbnail with format={save_format}")
            img.save(destination, format=save_format)
            print(f"[DEBUG] create_thumbnail: Thumbnail saved successfully")
    except Exception as e:
        print(f"[DEBUG] create_thumbnail: ERROR - {type(e).__name__}: {e}")
        raise


def append_error(job_id: str, message: str) -> List[str]:
    """Append an error to job state and return the updated list."""
    def mutator(job):
        job.setdefault("errors", []).append(message)
        return job["errors"]

    updated = JOBS.mutate_job(job_id, mutator)
    return updated.get("errors", []) if updated else []


@app.route("/")
def index():
    return render_template("index.html", operations=allowed_operations())


@app.route("/api/jobs", methods=["POST"])
def create_job():
    prompt = request.form.get("prompt", "").strip()
    operations = request.form.getlist("operations")
    operations = [op for op in operations if op in allowed_operations()]

    job_record = JOBS.create_job()
    upload = request.files.get("inputImage")
    uploaded_path: Optional[Path] = None

    if any(op in {"clone", "augment"} for op in operations):
        if not upload or not upload.filename:
            return jsonify({"error": "Clone and augment operations require an image upload."}), 400

    if upload and upload.filename:
        job_upload_dir = OUTPUT_ROOT / job_record["id"] / "uploads"
        job_upload_dir.mkdir(parents=True, exist_ok=True)
        filename = secure_filename(upload.filename)
        uploaded_path = job_upload_dir / filename
        upload.save(uploaded_path)

    start_background_job(job_record["id"], prompt, operations, uploaded_path)

    return jsonify({"job_id": job_record["id"]})


@app.route("/api/jobs/<job_id>", methods=["GET"])
def job_status(job_id: str):
    job = JOBS.get_job(job_id)
    if not job:
        abort(404, description="Job not found.")

    results_payload = []
    for result in job.get("results", []):
        results_payload.append(
            {
                "id": result["id"],
                "operation": result["operation"],
                "provider": result.get("provider"),
                "source": result.get("source"),
                "width": result.get("width"),
                "height": result.get("height"),
                "image_url": url_for(
                    "serve_image",
                    job_id=job_id,
                    filename=result["filename"],
                ),
                "thumbnail_url": url_for(
                    "serve_thumbnail",
                    job_id=job_id,
                    filename=result["filename"],
                ),
                "download_url": url_for(
                    "download_image",
                    job_id=job_id,
                    filename=result["filename"],
                ),
            }
        )

    payload = {
        "id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job.get("message", ""),
        "results": results_payload,
        "errors": job.get("errors", []),
    }
    return jsonify(payload)


@app.route("/api/jobs/<job_id>/results/<result_id>", methods=["DELETE"])
def delete_result(job_id: str, result_id: str):
    job = JOBS.get_job(job_id)
    if not job:
        abort(404, description="Job not found.")

    def mutator(job_record):
        remaining = []
        removed_entry = None
        for entry in job_record.get("results", []):
            if entry["id"] == result_id:
                removed_entry = entry
            else:
                remaining.append(entry)
        job_record["results"] = remaining
        return removed_entry

    removed = JOBS.mutate_job(job_id, mutator)
    if not removed:
        abort(404, description="Result not found.")

    for path_key in ("image_path", "thumbnail_path"):
        path = Path(removed[path_key])
        try:
            if path.exists():
                path.unlink()
        except OSError:
            continue

    return jsonify({"status": "deleted"})


@app.route("/api/jobs/<job_id>/results/<result_id>/revise", methods=["POST"])
@traceable(name="revise_result", run_type="chain")
def revise_result(job_id: str, result_id: str):
    """Create a new job that augments the specified result image with a revision prompt."""
    print(f"[DEBUG] ===== revise_result CALLED =====")
    print(f"[DEBUG] revise_result: Request method: {request.method}")
    print(f"[DEBUG] revise_result: Request path: {request.path}")
    print(f"[DEBUG] revise_result: job_id={job_id}, result_id={result_id}")
    job = JOBS.get_job(job_id)
    if not job:
        print(f"[DEBUG] revise_result: Job {job_id} not found")
        abort(404, description="Job not found.")

    # Find the result in the job
    result = None
    for entry in job.get("results", []):
        if entry["id"] == result_id:
            result = entry
            break

    if not result:
        print(f"[DEBUG] revise_result: Result {result_id} not found in job {job_id}")
        abort(404, description="Result not found.")

    print(f"[DEBUG] revise_result: Found result: {result}")

    # Get the revision prompt from request
    data = request.get_json()
    if not data or "prompt" not in data:
        return jsonify({"error": "Revision prompt is required."}), 400

    revision_prompt = data.get("prompt", "").strip()
    if not revision_prompt:
        return jsonify({"error": "Revision prompt cannot be empty."}), 400

    print(f"[DEBUG] revise_result: Revision prompt: {revision_prompt}")

    # Get the image path from the result
    image_path_str = result.get("image_path", "")
    print(f"[DEBUG] revise_result: image_path from result: {image_path_str}")
    
    if not image_path_str:
        return jsonify({"error": "Image path not found in result."}), 404
    
    image_path = Path(image_path_str)
    print(f"[DEBUG] revise_result: Converted to Path: {image_path}")
    print(f"[DEBUG] revise_result: Path exists: {image_path.exists()}")
    print(f"[DEBUG] revise_result: Path is absolute: {image_path.is_absolute()}")
    
    if not image_path.exists():
        # Try to resolve as absolute path
        if not image_path.is_absolute():
            # Try relative to OUTPUT_ROOT
            possible_path = OUTPUT_ROOT / job_id / "images" / result.get("filename", "")
            print(f"[DEBUG] revise_result: Trying alternative path: {possible_path}")
            if possible_path.exists():
                image_path = possible_path
                print(f"[DEBUG] revise_result: Using alternative path")
            else:
                return jsonify({"error": f"Source image file not found at {image_path} or {possible_path}."}), 404
        else:
            return jsonify({"error": f"Source image file not found at {image_path}."}), 404

    print(f"[DEBUG] revise_result: Using image path: {image_path}")

    # Create a new job for the revision
    new_job_record = JOBS.create_job()
    print(f"[DEBUG] revise_result: Created new job: {new_job_record['id']}")

    # Start the augment operation in the background
    start_background_job(
        new_job_record["id"],
        revision_prompt,
        ["augment"],
        image_path,
    )

    return jsonify({"job_id": new_job_record["id"]})


@app.route("/gui_output/<job_id>/images/<path:filename>")
def serve_image(job_id: str, filename: str):
    directory = OUTPUT_ROOT / job_id / "images"
    if not directory.exists():
        abort(404)
    return send_from_directory(directory, filename)


@app.route("/gui_output/<job_id>/thumbnails/<path:filename>")
def serve_thumbnail(job_id: str, filename: str):
    directory = OUTPUT_ROOT / job_id / "thumbnails"
    if not directory.exists():
        abort(404)
    return send_from_directory(directory, filename)


@app.route("/gui_output/<job_id>/download/<path:filename>")
def download_image(job_id: str, filename: str):
    directory = OUTPUT_ROOT / job_id / "images"
    if not directory.exists():
        abort(404)
    return send_from_directory(directory, filename, as_attachment=True)


@app.errorhandler(404)
def handle_not_found(err):
    if request.path.startswith("/api/"):
        return jsonify({"error": str(err)}), 404
    return render_template("404.html", message=str(err)), 404


@app.errorhandler(500)
def handle_server_error(err):  # pragma: no cover - defensive
    if request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("500.html", message=str(err)), 500


if __name__ == "__main__":
    # Debug: Print all registered routes
    print("[DEBUG] Registered routes:")
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/api/"):
            print(f"  {rule.methods} {rule.rule}")
    
    # Flask's reloader would duplicate the executor. Disable it by default.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
