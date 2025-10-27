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
    # Web Scraping
    scrape_website_comprehensive: Comprehensive web scraping with multiple engines
    scrape_with_engine: Scrape using specific engine (firecrawl, playwright, beautifulsoup)
    scrape_with_fallback: Scrape with automatic engine fallback
    
    # AI Generation
    generate_with_gemini: Generate images using Google Gemini
    
    # Stock Photo Fetching
    search_unsplash: Search Unsplash for stock photos
    search_pexels: Search Pexels for stock photos
    search_pixabay: Search Pixabay for stock photos
    
    # Image Validation & Cleanup
    cleanup_corrupted_images: Clean up corrupted and junk images
    validate_image_file: Validate single image file
    validate_image_with_llm: Use AI to validate image content
    
    # Asset Management
    AssetCatalog: Complete catalog management system
    scan_and_rename_assets: Rename files based on content analysis
    
    # Image Cloning
    clone_image: Clone single image for royalty-free alternative
    clone_images_from_directory: Batch clone images from directory
    describe_image_for_regeneration: Analyze image for AI regeneration
    check_similarity: Check similarity between images
    is_sufficiently_different: Verify clone is sufficiently different

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
    
    # Augment existing images with AI modifications
    augment_result = await crayon.augment_async(
        image_path="./assets/ai/image.jpg",
        prompt="add a sunset background",
        width=1920,
        height=1080
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
from .tools.ai_generation_tools import generate_with_gemini
from .tools.clone_image_tools import (
    clone_image,
    clone_images_from_directory,
    describe_image_for_regeneration,
    check_similarity,
    is_sufficiently_different,
)
from .tools.image_augmentation_tools import (
    augment_image,
    augment_images_from_directory,
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
    
    # AI generation
    "generate_with_gemini",
    
    # File management
    "scan_and_rename_assets",
    
    # Image cloning
    "clone_image",
    "clone_images_from_directory",
    "describe_image_for_regeneration",
    "check_similarity",
    "is_sufficiently_different",
    
    # Image augmentation
    "augment_image",
    "augment_images_from_directory",
    
    # Services
    "ImageService",
]

# Backwards compatibility shim for earlier module name.
_sys.modules.setdefault("purple_crayon", _sys.modules[__name__])
