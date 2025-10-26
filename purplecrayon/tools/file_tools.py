from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import httpx

from ..utils.config import ensure_parent_dir


def copy_file(source: str, destination: str) -> str:
    src = Path(source)
    dst = Path(destination)
    if not src.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    ensure_parent_dir(dst)
    shutil.copy2(src, dst)
    return str(dst)


async def download_file(url: str, save_path: str, timeout: float = 60.0) -> str:
    dst = Path(save_path)
    ensure_parent_dir(dst)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        dst.write_bytes(resp.content)
    return str(dst)


def save_file(content: bytes, path: str) -> str:
    dst = Path(path)
    ensure_parent_dir(dst)
    dst.write_bytes(content)
    return str(dst)
