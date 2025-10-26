from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from PIL import Image

from ..utils.config import ORIGINALS_DIR, ensure_parent_dir


ResizeMode = Literal["crop", "center", "fill"]


def _duplicate_original(input_path: Path) -> Path:
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    backup = ORIGINALS_DIR / input_path.name
    if input_path.resolve() != backup.resolve():
        if not backup.exists():
            backup.write_bytes(input_path.read_bytes())
    return backup


def convert_image(input_path: str, output_format: str, output_path: str | None = None) -> str:
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {input_path}")
    _duplicate_original(src)

    output_format = output_format.upper()
    dst = Path(output_path) if output_path else src.with_suffix(f".{output_format.lower()}")
    ensure_parent_dir(dst)

    with Image.open(src) as img:
        # Convert mode for JPEG/WebP if needed
        if output_format in {"JPEG", "JPG"} and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(dst, format="JPEG" if output_format == "JPG" else output_format)
    return str(dst)


def resize_image(
    input_path: str,
    width: int,
    height: int,
    mode: ResizeMode = "center",
    keep_aspect: bool = True,
    output_path: str | None = None,
) -> str:
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {input_path}")
    _duplicate_original(src)

    dst = Path(output_path) if output_path else src
    ensure_parent_dir(dst)

    with Image.open(src) as img:
        if keep_aspect:
            img = img.copy()
            img.thumbnail((width, height), Image.LANCZOS)
            if mode == "fill":
                canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                ox = (width - img.width) // 2
                oy = (height - img.height) // 2
                canvas.paste(img, (ox, oy))
                img = canvas
            elif mode == "center":
                # center within canvas of requested size without fill; keep resulting size
                pass
            elif mode == "crop":
                # upscale to cover then crop center
                ratio = max(width / img.width, height / img.height)
                cov = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
                left = (cov.width - width) // 2
                top = (cov.height - height) // 2
                img = cov.crop((left, top, left + width, top + height))
        else:
            img = img.resize((width, height), Image.LANCZOS)

        # Determine output path/format consistency
        fmt = (img.format or dst.suffix.lstrip(".") or "png").upper()
        save_kwargs = {}
        if fmt in {"JPG", "JPEG"} and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            fmt = "JPEG"
        img.save(dst, format="JPEG" if fmt == "JPG" else fmt, **save_kwargs)
    return str(dst)
