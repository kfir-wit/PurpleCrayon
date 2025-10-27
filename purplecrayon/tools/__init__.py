"""PurpleCrayon Tools - Core functionality for image processing and management.

This module provides direct access to key tools and utilities:

Image Validation & Cleanup:
    validate_image_file: Validate a single image file
    validate_image_with_llm: Use AI to validate image content
    cleanup_corrupted_images: Clean up a directory of images

Web Scraping:
    scrape_website_comprehensive: Comprehensive web scraping
    scrape_with_engine: Scrape with specific engine
    scrape_with_fallback: Scrape with automatic fallback

Asset Management:
    AssetCatalog: Complete catalog management system
    scan_and_rename_assets: Rename files based on content

Example Usage:
    from purplecrayon.tools import validate_image_file, cleanup_corrupted_images
    from purplecrayon.tools import AssetCatalog, scrape_website_comprehensive
    
    # Validate a single image
    result = validate_image_file("image.jpg")
    
    # Clean up a directory
    stats = cleanup_corrupted_images("./images", remove_junk=True)
    
    # Create a catalog
    catalog = AssetCatalog(Path("./assets/catalog.yaml"))
    
    # Scrape a website
    images = scrape_website_comprehensive("https://example.com")
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

# Asset management
from .asset_management_tools import AssetCatalog

# Image validation and cleanup
from .image_validation_tools import (
    validate_image_file,
    validate_image_with_llm,
    cleanup_corrupted_images,
    is_junk_image,
)

# Web scraping
from .scraping_tools import (
    scrape_website_comprehensive,
    scrape_with_engine,
    scrape_with_fallback,
    beautifulsoup_scrape,
    playwright_scrape,
    firecrawl_scrape_images,
)

# File management
from .image_renaming_tools import scan_and_rename_assets

# AI generation
from .ai_generation_tools import generate_with_gemini

# Stock photo tools (functions may not be available yet)
# from .stock_photo_tools import (
#     search_stock_photos,
#     search_unsplash,
#     search_pexels,
#     search_pixabay,
# )

__all__ = [
    # Asset management
    "AssetCatalog",
    
    # Image validation
    "validate_image_file",
    "validate_image_with_llm", 
    "cleanup_corrupted_images",
    "is_junk_image",
    
    # Web scraping
    "scrape_website_comprehensive",
    "scrape_with_engine",
    "scrape_with_fallback",
    "beautifulsoup_scrape",
    "playwright_scrape", 
    "firecrawl_scrape_images",
    
    # File management
    "scan_and_rename_assets",
    
    # AI generation
    "generate_with_gemini",
    
    # Stock photos (commented out until functions are implemented)
    # "search_stock_photos",
    # "search_unsplash",
    # "search_pexels", 
    # "search_pixabay",
]
