"""PurpleCrayon Services - High-level service layer for complex operations.

This module provides service classes that orchestrate multiple tools and provide
high-level interfaces for common workflows.

Services:
    ImageService: Comprehensive image operations including scraping, validation, and cataloging

Example Usage:
    from purplecrayon.services import ImageService
    
    # Initialize service
    service = ImageService(assets_dir="./my_assets")
    
    # Scrape and process images
    result = service.scrape_website("https://example.com", verbose=True)
    
    # Get service statistics
    stats = service.get_stats()
"""

from .image_service import ImageService

__all__ = [
    "ImageService",
]