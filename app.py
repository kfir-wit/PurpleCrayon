from __future__ import annotations

import mimetypes
import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional
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


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "gui_templates"
STATIC_DIR = BASE_DIR / "gui_static"
OUTPUT_ROOT = BASE_DIR / "gui_output"

app = Flask(__name__, template_folder=str(TEMPLATE_DIR), static_folder=str(STATIC_DIR))

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
            append_error(job_id, f"Failed to store image: {exc}")
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
    source_path = Path(image_result.path)
    ext = source_path.suffix.lower()
    if not ext:
        fmt_value = (getattr(image_result, "format", "") or "").lower()
        if fmt_value:
            if "/" in fmt_value:
                guessed = mimetypes.guess_extension(fmt_value)
                ext = guessed or ".png"
            else:
                ext = fmt_value if fmt_value.startswith(".") else f".{fmt_value}"
        else:
            guessed = mimetypes.guess_extension(fmt_value or "")
            ext = guessed or ".png"

    file_id = uuid4().hex
    filename = f"{operation}_{file_id}{ext}"
    destination = images_dir / filename

    if source_path.exists():
        shutil.copy2(source_path, destination)
    else:
        download_remote_image(image_result.path, destination)

    thumbnail_path = thumbnails_dir / filename
    create_thumbnail(destination, thumbnail_path)

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


def download_remote_image(url: str, destination: Path) -> None:
    """Download image from remote URL."""
    if not url:
        raise ValueError("Empty image URL.")

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        response = client.get(url)
        response.raise_for_status()
        destination.write_bytes(response.content)


def create_thumbnail(source: Path, destination: Path, size: int = 256) -> None:
    """Create a square thumbnail while preserving aspect ratio."""
    with Image.open(source) as img:
        img.thumbnail((size, size))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        destination.parent.mkdir(parents=True, exist_ok=True)
        img.save(destination)


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
    # Flask's reloader would duplicate the executor. Disable it by default.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
