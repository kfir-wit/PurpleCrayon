#!/usr/bin/env python3
"""
PurpleCrayon API Usage Examples

This script demonstrates how to use PurpleCrayon as a library in other projects.
Shows different ways to import and use the various components.
"""

import argparse
from pathlib import Path

# Example 1: Using the main PurpleCrayon client
def example_main_client():
    """Example using the main PurpleCrayon client."""
    print("=== Example 1: Main PurpleCrayon Client ===")
    
    from purplecrayon import PurpleCrayon
    
    # Initialize the main client
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Scrape images from a website
    print("Scraping images...")
    result = crayon.scrape("https://www.jaxxon.tech", engine="playwright", verbose=True)
    
    if result.success:
        print(f"✅ Found {len(result.images)} images")
        
        # Clean up the scraped images
        print("Cleaning up images...")
        cleanup_result = crayon.cleanup_assets(remove_junk=True, format="both")
        
        if cleanup_result["success"]:
            print("✅ Cleanup completed")
            
            # Search for specific images
            print("Searching for logo images...")
            logos = crayon.catalog.search_assets(query="logo", source="downloaded")
            print(f"Found {len(logos)} logo images")
    else:
        print(f"❌ Scraping failed: {result.message}")


# Example 2: Using individual tools directly
def example_individual_tools():
    """Example using individual tools directly."""
    print("\n=== Example 2: Individual Tools ===")
    
    from purplecrayon.tools import (
        validate_image_file,
        cleanup_corrupted_images,
        AssetCatalog,
        scrape_website_comprehensive
    )
    
    # Validate a single image
    print("Validating images...")
    image_path = "./example_assets/ai/panda_watercolor_art_1024x1024.png"
    if Path(image_path).exists():
        validation = validate_image_file(image_path)
        print(f"Image validation: {validation['valid']}")
        if validation['valid']:
            print(f"  Dimensions: {validation['width']}x{validation['height']}")
            print(f"  Format: {validation['format']}")
    
    # Clean up a directory
    print("Cleaning up directory...")
    cleanup_stats = cleanup_corrupted_images("./example_assets", remove_junk=True)
    print(f"Cleanup results: {cleanup_stats}")
    
    # Work with catalog directly
    print("Working with catalog...")
    catalog_path = Path("./example_assets/catalog.yaml")
    catalog = AssetCatalog(catalog_path)
    
    # Search for specific assets
    panda_images = catalog.search_assets(query="panda", source="ai")
    print(f"Found {len(panda_images)} panda images in AI category")
    
    # Get catalog statistics
    stats = catalog.get_stats()
    print(f"Catalog stats: {stats}")


# Example 3: Using services layer
def example_services():
    """Example using the services layer."""
    print("\n=== Example 3: Services Layer ===")
    
    from purplecrayon.services import ImageService
    
    # Initialize service
    service = ImageService(assets_dir="./example_assets")
    
    # Get service statistics
    stats = service.get_stats()
    print(f"Service stats: {stats}")
    
    # The service provides high-level operations
    # that orchestrate multiple tools


# Example 4: Advanced usage with custom parameters
def example_advanced_usage():
    """Example showing advanced usage patterns."""
    print("\n=== Example 4: Advanced Usage ===")
    
    from purplecrayon import PurpleCrayon, AssetRequest
    from purplecrayon.tools import validate_image_with_llm
    
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Create a custom asset request
    request = AssetRequest(
        query="watercolor panda",
        max_results=5,
        quality_threshold=0.8
    )
    
    print(f"Custom request: {request.query}")
    
    # Use LLM validation for specific images
    image_path = "./example_assets/ai/panda_watercolor_art_1024x1024.png"
    if Path(image_path).exists():
        print("Using LLM to validate image content...")
        llm_result = validate_image_with_llm(
            image_path, 
            "A watercolor painting of a panda"
        )
        print(f"LLM validation: {llm_result['valid']}")
        if llm_result['valid']:
            print(f"  Match score: {llm_result['match_score']}")
            print(f"  Description: {llm_result['description']}")


# Example 5: Batch processing
def example_batch_processing():
    """Example showing batch processing capabilities."""
    print("\n=== Example 5: Batch Processing ===")
    
    from purplecrayon.tools import AssetCatalog, cleanup_corrupted_images
    from pathlib import Path
    
    # Process multiple directories
    directories = ["./example_assets/ai", "./example_assets/stock", "./example_assets/downloaded"]
    
    for directory in directories:
        if Path(directory).exists():
            print(f"Processing {directory}...")
            
            # Clean up each directory
            stats = cleanup_corrupted_images(directory, remove_junk=True)
            print(f"  Cleaned: {stats['valid']} valid, {stats['corrupted']} corrupted, {stats['junk']} junk")
    
    # Update master catalog
    catalog = AssetCatalog(Path("./example_assets/catalog.yaml"))
    catalog.update_catalog_from_assets(Path("./example_assets"))
    
    # Export in different formats
    catalog.save_json_catalog(Path("./example_assets/catalog.json"))
    print("Exported catalogs in both YAML and JSON formats")


def main():
    """Run all examples."""
    parser = argparse.ArgumentParser(description="PurpleCrayon API Examples")
    parser.add_argument("--example", choices=["1", "2", "3", "4", "5", "all"], 
                       default="all", help="Which example to run")
    args = parser.parse_args()
    
    print("🚀 PurpleCrayon API Examples")
    print("=" * 40)
    
    if args.example in ["1", "all"]:
        example_main_client()
    
    if args.example in ["2", "all"]:
        example_individual_tools()
    
    if args.example in ["3", "all"]:
        example_services()
    
    if args.example in ["4", "all"]:
        example_advanced_usage()
    
    if args.example in ["5", "all"]:
        example_batch_processing()
    
    print("\n✅ All examples completed!")


if __name__ == "__main__":
    main()
