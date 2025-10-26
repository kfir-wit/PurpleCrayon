from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


# Resolve base directory:
# - In local dev (repo), use repo root (pyproject.toml present)
# - In installed package, default to current working directory
_repo_root = Path(__file__).resolve().parents[2]
BASE_DIR = _repo_root if (_repo_root / "pyproject.toml").exists() else Path.cwd()
CONFIG_PATH = BASE_DIR / "config" / "graphics_sources.yaml"
CATALOG_PATH = BASE_DIR / "data" / "asset_catalog.json"
INPUT_PROMPT_PATH = BASE_DIR / "input" / "prompt.md"
DOWNLOADS_DIR = BASE_DIR / "downloads"
ORIGINALS_DIR = BASE_DIR / "originals"
PROCESSED_DIR = BASE_DIR / "processed"


def init_environment() -> None:
    """Load .env and ensure required directories exist."""
    load_dotenv()
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def get_env(name: str, default: str | None = None) -> str | None:
    """Get environment variable with optional default."""
    return os.getenv(name, default)


def load_graphics_sources() -> Dict[str, Any]:
    """Load YAML config for sources; returns empty dict if missing."""
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
