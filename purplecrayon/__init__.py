"""PurpleCrayon - AI graphics sourcing and generation toolkit."""

from __future__ import annotations

import sys as _sys

from .core import (
    AssetRequest,
    ImageResult,
    OperationResult,
    PurpleCrayon,
    markdownRequest,
)

__version__ = "0.1.0"
__author__ = "PurpleCrayon Team"

__all__ = [
    "AssetRequest",
    "ImageResult",
    "OperationResult",
    "PurpleCrayon",
    "markdownRequest",
]

# Backwards compatibility shim for earlier module name.
_sys.modules.setdefault("purple_crayon", _sys.modules[__name__])
