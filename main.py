from __future__ import annotations

import argparse
from pathlib import Path

from purplecrayon import OperationResult, PurpleCrayon, markdownRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="PurpleCrayon AI Graphics Agent")
    parser.add_argument("--mode", default="full", choices=["full", "search", "generate", "process", "benchmark", "scrape", "clone"], help="Run mode")
    parser.add_argument("--url", help="URL to scrape (required for scrape mode)")
    parser.add_argument("--source", help="Source image file or directory to clone (required for clone mode)")
    parser.add_argument("--width", type=int, help="Width for cloned images")
    parser.add_argument("--height", type=int, help="Height for cloned images")
    parser.add_argument("--format", help="Output format for cloned images (png, jpg, webp, etc.)")
    parser.add_argument("--style", help="Style guidance for cloned images (photorealistic, artistic, etc.)")
    parser.add_argument("--guidance", help="Additional guidance for image generation")
    parser.add_argument("--similarity-threshold", type=float, default=0.7, help="Maximum similarity threshold (0.0-1.0)")
    parser.add_argument("--max-images", type=int, help="Maximum number of images to process (for directory input)")
    parser.add_argument("--sort-catalog", action="store_true", help="Sort and update catalog in assets/ directory")
    parser.add_argument("--cleanup", action="store_true", help="Clean up corrupted and junk images")
    parser.add_argument("--keep-junk", action="store_true", help="Keep junk files when cleaning (only remove corrupted)")
    parser.add_argument("--catalog-format", choices=["yaml", "json", "both"], default="both", help="Catalog format (default: both)")
    args = parser.parse_args()
    
    # Initialize package
    crayon = PurpleCrayon(assets_dir="./assets")
    
    # Handle cleanup mode
    if args.cleanup:
        print("🧹 Cleaning up corrupted and junk images...")
        print("=" * 50)
        
        result = crayon.cleanup_assets(remove_junk=not args.keep_junk, format=args.catalog_format)
        
        if result["success"]:
            cleanup_stats = result['cleanup_stats']
            print(f"\n📊 Cleanup Results:")
            print(f"  ✅ Valid images: {cleanup_stats['valid']}")
            print(f"  ❌ Corrupted images removed: {cleanup_stats['corrupted']}")
            if not args.keep_junk:
                print(f"  🗑️ Junk files removed: {cleanup_stats['junk']}")
            print(f"  ⚠️ Cleanup errors: {cleanup_stats['cleanup_errors']}")
            
            print(f"\n📊 Catalog Update Results:")
            print(f"  ➕ Added: {cleanup_stats['catalog_added']}")
            print(f"  🔄 Updated: {cleanup_stats['catalog_updated']}")
            print(f"  🗑️ Removed: {cleanup_stats['catalog_removed']}")
            print(f"  ⚠️ Catalog errors: {cleanup_stats['catalog_errors']}")
            
            # Show final stats
            final_stats = result['final_stats']
            print(f"\n📈 Final Catalog Stats:")
            print(f"  Total assets: {final_stats.get('total_assets', 0)}")
            print(f"  By source: {final_stats.get('by_source', {})}")
            print(f"  By format: {final_stats.get('by_format', {})}")
            print(f"  By aspect ratio: {final_stats.get('by_aspect_ratio', {})}")
        else:
            print(f"❌ Cleanup failed: {result['error']}")
        return
    
    # Handle sort-catalog mode
    if args.sort_catalog:
        print("🏷️ Sorting and updating catalog in assets/ directory...")
        print("=" * 50)
        
        result = crayon.sort_catalog()
        
        if result["success"]:
            print(f"📊 Renaming results: {result['rename_stats']['renamed']} renamed, {result['rename_stats']['skipped']} skipped, {result['rename_stats']['errors']} errors")
            print(f"📊 Catalog results: {result['catalog_stats']['added']} added, {result['catalog_stats']['updated']} updated, {result['catalog_stats']['removed']} removed")
            
            # Show final stats
            final_stats = result['final_stats']
            print(f"\n📈 Final Catalog Stats:")
            print(f"  Total assets: {final_stats.get('total_assets', 0)}")
            print(f"  By source: {final_stats.get('by_source', {})}")
            print(f"  By format: {final_stats.get('by_format', {})}")
            print(f"  By aspect ratio: {final_stats.get('by_aspect_ratio', {})}")
        else:
            print(f"❌ Sort catalog failed: {result['error']}")
        return
    
    # Validate scrape mode
    if args.mode == "scrape" and not args.url:
        print("❌ Error: --url is required for scrape mode")
        print("Example: uv run python -m main --mode scrape --url 'https://example.com/gallery'")
        return
    
    # Validate clone mode
    if args.mode == "clone" and not args.source:
        print("❌ Error: --source is required for clone mode")
        print("Example: uv run python -m main --mode clone --source './assets/downloaded/image.jpg'")
        print("Example: uv run python -m main --mode clone --source './assets/downloaded/' --max-images 5")
        return
    
    # Handle scrape mode
    if args.mode == "scrape":
        result = crayon.scrape(args.url)
        print_operation_result(result, "Scrape")
        return
    
    # Handle clone mode
    if args.mode == "clone":
        print("🎨 Cloning images...")
        print("=" * 50)
        
        result = crayon.clone(
            source=args.source,
            width=args.width,
            height=args.height,
            format=args.format,
            style=args.style,
            guidance=args.guidance,
            similarity_threshold=args.similarity_threshold,
            max_images=args.max_images
        )
        print_operation_result(result, "Clone")
        return
    
    # Handle other modes using prompt file
    prompt_file = Path("input/prompt.md")
    if not prompt_file.exists():
        print("❌ Error: input/prompt.md not found")
        print("💡 Create the prompt file first")
        return
    
    prompt_content = prompt_file.read_text()
    request = markdownRequest(prompt_content)
    
    if args.mode == "full":
        result = crayon.source(request)
        print_operation_result(result, "Source")
    elif args.mode == "search":
        result = crayon.fetch(request)
        print_operation_result(result, "Fetch")
    elif args.mode == "generate":
        result = crayon.generate(request)
        print_operation_result(result, "Generate")
    else:
        print(f"❌ Mode '{args.mode}' not yet implemented in package API")


def print_operation_result(result: OperationResult, operation_name: str) -> None:
    """Print operation results in a formatted way."""
    print(f"\n🎨 {operation_name} Results:")
    print("=" * 50)
    
    if result.success:
        print(f"✅ {result.message}")
        
        if result.images:
            print(f"\n📸 Images ({len(result.images)}):")
            for i, img in enumerate(result.images, 1):
                status = "✅" if not img.error else "❌"
                print(f"  {i}. {status} {img.path} ({img.source}/{img.provider})")
                if img.error:
                    print(f"      Error: {img.error}")
        else:
            print("📭 No images found")
    else:
        print(f"❌ {result.message}")
        if result.error_code:
            print(f"   Error Code: {result.error_code}")


if __name__ == "__main__":
    main()
