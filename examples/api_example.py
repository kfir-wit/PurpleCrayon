#!/usr/bin/env python3
"""
PurpleCrayon API Usage Examples

This script demonstrates how to use PurpleCrayon as a library in other projects.
Shows different ways to import and use the various components with async/await patterns.
"""

import argparse
import asyncio
from pathlib import Path

# Example 1: Using the main PurpleCrayon client
async def example_main_client():
    """Example using the main PurpleCrayon client with async patterns."""
    print("=== Example 1: Main PurpleCrayon Client (Async) ===")
    
    from purplecrayon import PurpleCrayon, AssetRequest
    
    # Initialize the main client
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Generate AI images
    print("Generating AI images...")
    request = AssetRequest(
        description="a modern logo design with geometric shapes",
        width=512,
        height=512,
        format="png",
        max_results=1
    )
    
    result = await crayon.generate_async(request)
    
    if result.success:
        print(f"✅ Generated {len(result.images)} images")
        
        # Clean up the generated images
        print("Cleaning up images...")
        cleanup_result = crayon.cleanup_assets(remove_junk=True, format="both")
        
        if cleanup_result["success"]:
            print("✅ Cleanup completed")
            
            # Search for specific images
            print("Searching for AI images...")
            ai_images = crayon.catalog.search_assets(query="logo", source="ai")
            print(f"Found {len(ai_images)} AI images")
    else:
        print(f"❌ Generation failed: {result.message}")


# Example 2: Using individual tools directly
async def example_individual_tools():
    """Example using individual tools directly with async patterns."""
    print("\n=== Example 2: Individual Tools (Async) ===")
    
    from purplecrayon.tools import (
        validate_image_file,
        cleanup_corrupted_images,
        AssetCatalog,
        generate_with_gemini,
        generate_with_replicate
    )
    
    # Generate images using individual tools
    print("Generating images with individual tools...")
    
    # Test Gemini generation
    gemini_result = generate_with_gemini(
        "a simple geometric logo design",
        aspect_ratio="1:1"
    )
    print(f"Gemini result: {gemini_result.get('status')}")
    
    # Test Replicate generation
    replicate_result = generate_with_replicate(
        "a watercolor painting of a mountain",
        aspect_ratio="1:1"
    )
    print(f"Replicate result: {replicate_result.get('status')}")
    
    # Validate generated images
    print("Validating images...")
    ai_dir = Path("./example_assets/ai")
    if ai_dir.exists():
        for image_file in ai_dir.glob("*.png"):
            validation = validate_image_file(str(image_file))
            print(f"  {image_file.name}: {validation['valid']}")
            if validation['valid']:
                print(f"    Dimensions: {validation['width']}x{validation['height']}")
                print(f"    Format: {validation['format']}")
    
    # Clean up a directory
    print("Cleaning up directory...")
    cleanup_stats = cleanup_corrupted_images("./example_assets", remove_junk=True)
    print(f"Cleanup results: {cleanup_stats}")
    
    # Work with catalog directly
    print("Working with catalog...")
    catalog_path = Path("./example_assets/catalog.yaml")
    catalog = AssetCatalog(catalog_path)
    
    # Search for specific assets
    ai_images = catalog.search_assets(query="logo", source="ai")
    print(f"Found {len(ai_images)} AI images")
    
    # Get catalog statistics
    stats = catalog.get_stats()
    print(f"Catalog stats: {stats}")


# Example 3: Using services layer
async def example_services():
    """Example using the services layer with async patterns."""
    print("\n=== Example 3: Services Layer (Async) ===")
    
    from purplecrayon.services import ImageService
    from purplecrayon import AssetRequest
    
    # Initialize service
    service = ImageService(assets_dir="./example_assets")
    
    # Get service statistics
    stats = service.get_stats()
    print(f"Service stats: {stats}")
    
    # Test async generation through service
    print("Testing async generation through service...")
    request = AssetRequest(
        description="a professional business card design",
        width=400,
        height=250,
        format="png",
        max_results=1
    )
    
    # Note: Service layer would need async methods implemented
    print("Service layer provides high-level operations that orchestrate multiple tools")


# Example 4: Advanced usage with custom parameters
async def example_advanced_usage():
    """Example showing advanced usage patterns with async."""
    print("\n=== Example 4: Advanced Usage (Async) ===")
    
    from purplecrayon import PurpleCrayon, AssetRequest
    from purplecrayon.tools import validate_image_with_llm
    
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Create a custom asset request
    request = AssetRequest(
        description="watercolor panda in a bamboo forest",
        width=1024,
        height=1024,
        format="png",
        max_results=2,
        quality_threshold=0.8
    )
    
    print(f"Custom request: {request.description}")
    
    # Generate with custom parameters
    result = await crayon.generate_async(request)
    
    if result.success:
        print(f"✅ Generated {len(result.images)} images")
        
        # Use LLM validation for generated images
        for img in result.images:
            if Path(img.path).exists():
                print(f"Validating {Path(img.path).name}...")
                llm_result = validate_image_with_llm(
                    img.path, 
                    "A watercolor painting of a panda"
                )
                print(f"  LLM validation: {llm_result['valid']}")
                if llm_result['valid']:
                    print(f"    Match score: {llm_result['match_score']}")
                    print(f"    Description: {llm_result['description']}")
    else:
        print(f"❌ Generation failed: {result.message}")


# Example 5: Batch processing with async
async def example_batch_processing():
    """Example showing batch processing capabilities with async."""
    print("\n=== Example 5: Batch Processing (Async) ===")
    
    from purplecrayon.tools import AssetCatalog, cleanup_corrupted_images
    from purplecrayon import AssetRequest
    from pathlib import Path
    
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Create multiple requests for batch processing
    requests = [
        AssetRequest(
            description="logo design for tech startup",
            width=256,
            height=256,
            format="png",
            max_results=1
        ),
        AssetRequest(
            description="icon for mobile app",
            width=128,
            height=128,
            format="png",
            max_results=1
        ),
        AssetRequest(
            description="banner for website",
            width=800,
            height=200,
            format="png",
            max_results=1
        )
    ]
    
    print("Processing multiple requests concurrently...")
    
    # Run all requests concurrently
    tasks = [crayon.generate_async(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = 0
    total_images = 0
    
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"  Request {i}: ❌ Failed with {result}")
        elif result.success:
            successful += 1
            total_images += len(result.images)
            print(f"  Request {i}: ✅ Generated {len(result.images)} image(s)")
        else:
            print(f"  Request {i}: ❌ Failed - {result.message}")
    
    print(f"\nBatch Results: {successful}/{len(requests)} successful, {total_images} total images")
    
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


async def main():
    """Run all examples with async patterns."""
    parser = argparse.ArgumentParser(description="PurpleCrayon API Examples")
    parser.add_argument("--example", choices=["1", "2", "3", "4", "5", "all"], 
                       default="all", help="Which example to run")
    args = parser.parse_args()
    
    print("🚀 PurpleCrayon API Examples (Async)")
    print("=" * 50)
    
    # Check API keys
    from purplecrayon.utils.config import get_env
    gemini_key = get_env("GEMINI_API_KEY")
    replicate_key = get_env("REPLICATE_API_TOKEN")
    
    if not gemini_key and not replicate_key:
        print("❌ No API keys found!")
        print("💡 Please set GEMINI_API_KEY or REPLICATE_API_TOKEN in your .env file")
        return
    
    print(f"🔑 API Keys: Gemini={'✅' if gemini_key else '❌'}, Replicate={'✅' if replicate_key else '❌'}")
    
    if args.example in ["1", "all"]:
        await example_main_client()
    
    if args.example in ["2", "all"]:
        await example_individual_tools()
    
    if args.example in ["3", "all"]:
        await example_services()
    
    if args.example in ["4", "all"]:
        await example_advanced_usage()
    
    if args.example in ["5", "all"]:
        await example_batch_processing()
    
    print("\n✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
