from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from ..utils.config import CATALOG_PATH, ensure_parent_dir


@dataclass
class Asset:
    id: str
    filepath: str
    filename: str
    source: str
    description: str
    tags: List[str]
    format: str
    width: int
    height: int
    created_at: str
    license: str


def _read_catalog() -> Dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {"assets": []}
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_catalog(data: Dict[str, Any]) -> None:
    ensure_parent_dir(CATALOG_PATH)
    with CATALOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def index_asset(
    filepath: str,
    source: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    license: str = "",
) -> Asset:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Asset not found: {filepath}")

    try:
        with Image.open(path) as img:
            width, height = img.size
            fmt = (img.format or path.suffix.lstrip(".")).lower()
    except Exception:
        # Non-image or unreadable – still index basic info
        width, height = 0, 0
        fmt = path.suffix.lstrip(".").lower()

    asset = Asset(
        id=str(uuid.uuid4()),
        filepath=str(path.as_posix()),
        filename=path.name,
        source=source,
        description=description,
        tags=sorted(set([t.strip().lower() for t in (tags or []) if t.strip()])),
        format=fmt,
        width=width,
        height=height,
        created_at=datetime.now(timezone.utc).isoformat(),
        license=license,
    )
    catalog = _read_catalog()
    catalog.setdefault("assets", []).append(asdict(asset))
    _write_catalog(catalog)
    return asset


def search_local_assets(query: str | None = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    catalog = _read_catalog()
    assets = catalog.get("assets", [])

    if not query and not tags:
        return assets

    q = (query or "").strip().lower()
    tagset = {t.strip().lower() for t in (tags or []) if t.strip()}

    def matches(a: Dict[str, Any]) -> bool:
        text = " ".join([
            a.get("filename", ""),
            a.get("description", ""),
            " ".join(a.get("tags", [])),
            a.get("source", ""),
        ]).lower()
        ok_text = (q in text) if q else True
        ok_tags = tagset.issubset(set(map(str.lower, a.get("tags", [])))) if tagset else True
        return ok_text and ok_tags

    return [a for a in assets if matches(a)]


def get_asset_info(asset_id: str) -> Optional[Dict[str, Any]]:
    catalog = _read_catalog()
    for a in catalog.get("assets", []):
        if a.get("id") == asset_id:
            return a
    return None
