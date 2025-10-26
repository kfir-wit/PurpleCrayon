from __future__ import annotations

import argparse
from pathlib import Path

from purplecrayon import OperationResult, PurpleCrayon, markdownRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="PurpleCrayon AI Graphics Agent")
    parser.add_argument("--mode", default="full", choices=["full", "search", "generate", "process", "benchmark", "scrape"], help="Run mode")
    parser.add_argument("--url", help="URL to scrape (required for scrape mode)")
    parser.add_argument("--sort-catalog", action="store_true", help="Sort and update catalog in assets/ directory")
    args = parser.parse_args()
    
    # Initialize package
    crayon = PurpleCrayon(assets_dir="./assets")
    
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
    
    # Handle scrape mode
    if args.mode == "scrape":
        result = crayon.scrape(args.url)
        print_operation_result(result, "Scrape")
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
