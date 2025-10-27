"""PurpleCrayon - AI graphics sourcing and generation toolkit.

This package provides comprehensive tools for:
- Web scraping images from websites
- AI-powered image generation and modification
- Image cloning for royalty-free alternatives
- Asset catalog management and organization
- Image validation and cleanup
- Stock photo integration
- Content-based file renaming

Main Classes:
    PurpleCrayon: Main client for all operations
    AssetRequest: Request object for asset operations
    ImageResult: Result object containing image data
    OperationResult: Generic operation result wrapper

Key Functions:
    scrape_website_comprehensive: Comprehensive web scraping
    cleanup_corrupted_images: Image validation and cleanup
    validate_image_file: Single image validation
    AssetCatalog: Catalog management system
    clone_image: Clone images for royalty-free alternatives
    clone_images_from_directory: Batch image cloning

Example Usage:
    from purplecrayon import PurpleCrayon, AssetRequest
    
    # Initialize client
    crayon = PurpleCrayon(assets_dir="./my_assets")
    
    # Scrape images from a website
    result = crayon.scrape("https://example.com", verbose=True)
    
    # Clone an image for royalty-free alternative
    clone_result = await crayon.clone_async(
        source="./assets/downloaded/image.jpg",
        width=1024,
        height=1024,
        style="photorealistic"
    )
    
    # Clean up and organize assets
    cleanup_result = crayon.cleanup_assets(remove_junk=True)
    
    # Search for specific images
    images = crayon.catalog.search_assets(query="logo", source="downloaded")
"""

from __future__ import annotations

import sys as _sys

# Core classes and types
from .core import (
    AssetRequest,
    ImageResult,
    OperationResult,
    PurpleCrayon,
    markdownRequest,
)

# Key tools and utilities
from .tools.asset_management_tools import AssetCatalog
from .tools.image_validation_tools import (
    cleanup_corrupted_images,
    validate_image_file,
    validate_image_with_llm,
)
from .tools.scraping_tools import (
    scrape_website_comprehensive,
    scrape_with_engine,
    scrape_with_fallback,
)
from .tools.image_renaming_tools import scan_and_rename_assets
from .tools.clone_image_tools import (
    clone_image,
    clone_images_from_directory,
    describe_image_for_regeneration,
    check_similarity,
    is_sufficiently_different,
)
from .services.image_service import ImageService

__version__ = "0.1.0"
__author__ = "PurpleCrayon Team"
__description__ = "AI graphics sourcing and generation toolkit"

__all__ = [
    # Core classes
    "PurpleCrayon",
    "AssetRequest", 
    "ImageResult",
    "OperationResult",
    "markdownRequest",
    
    # Catalog management
    "AssetCatalog",
    
    # Image validation and cleanup
    "cleanup_corrupted_images",
    "validate_image_file", 
    "validate_image_with_llm",
    
    # Web scraping
    "scrape_website_comprehensive",
    "scrape_with_engine",
    "scrape_with_fallback",
    
    # File management
    "scan_and_rename_assets",
    
    # Image cloning
    "clone_image",
    "clone_images_from_directory",
    "describe_image_for_regeneration",
    "check_similarity",
    "is_sufficiently_different",
    
    # Services
    "ImageService",
]

# Backwards compatibility shim for earlier module name.
_sys.modules.setdefault("purple_crayon", _sys.modules[__name__])
