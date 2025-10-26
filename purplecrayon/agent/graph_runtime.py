from __future__ import annotations

import asyncio
from typing import Any

from .graph import run_agent


def run_sync(mode: str = "full", url: str = None) -> dict[str, Any]:
    return asyncio.run(run_agent(mode, url))
