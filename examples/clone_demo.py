#!/usr/bin/env python3
"""
PurpleCrayon Clone Demo - Mock Version

This script demonstrates the clone functionality without requiring API keys.
It shows the file structure and workflow that would be used.
"""

import argparse
from pathlib import Path
from purplecrayon import PurpleCrayon


def mock_clone_demo():
    """Demonstrate clone functionality with mock implementation."""
    print("🎨 PurpleCrayon Clone Demo (Mock Version)")
    print("=" * 50)
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Show the source image
    source_image = "./example_assets/stock/stock_pixabay_6_1280x853.jpg"
    
    if not Path(source_image).exists():
        print(f"❌ Source image not found: {source_image}")
        return
    
    print(f"📸 Source Image: {source_image}")
    
    # Get image info
    from PIL import Image
    with Image.open(source_image) as img:
        width, height = img.size
        format_type = img.format
        file_size = Path(source_image).stat().st_size
    
    print(f"   Dimensions: {width}x{height}")
    print(f"   Format: {format_type}")
    print(f"   Size: {file_size:,} bytes")
    
    # Show what would happen in a real clone
    print(f"\n🔍 What would happen in a real clone:")
    print(f"   1. Analyze image with Gemini Vision API")
    print(f"   2. Generate detailed description prompt")
    print(f"   3. Create AI-generated alternative")
    print(f"   4. Save to: ./example_assets/cloned/stock_pixabay_6_1280x853.jpg")
    print(f"   5. Categorize as 'ai' source in catalog")
    
    # Create the cloned directory structure
    cloned_dir = Path("./example_assets/cloned")
    cloned_dir.mkdir(exist_ok=True)
    
    # Create a placeholder file to show the structure
    cloned_file = cloned_dir / "stock_pixabay_6_1280x853.jpg"
    
    if not cloned_file.exists():
        # Copy the original as a placeholder
        import shutil
        shutil.copy2(source_image, cloned_file)
        print(f"\n📁 Created placeholder clone: {cloned_file}")
    
    # Update catalog to show the cloned file
    print(f"\n📊 Updating catalog...")
    catalog_stats = crayon.catalog.update_catalog_from_assets(crayon.assets_dir)
    
    print(f"   Added: {catalog_stats['added']}")
    print(f"   Updated: {catalog_stats['updated']}")
    print(f"   Removed: {catalog_stats['removed']}")
    
    # Show final stats
    final_stats = crayon.catalog.get_stats()
    print(f"\n📈 Final Catalog Stats:")
    print(f"   Total assets: {final_stats.get('total_assets', 0)}")
    print(f"   By source: {final_stats.get('by_source', {})}")
    
    # Show the cloned file would be categorized as 'ai'
    print(f"\n✅ Clone workflow completed!")
    print(f"   The cloned file would be categorized as 'ai' source")
    print(f"   This ensures proper counting in 'by source' statistics")


def show_clone_api_usage():
    """Show how to use the clone API."""
    print("\n" + "=" * 50)
    print("🚀 Clone API Usage Examples")
    print("=" * 50)
    
    print("\n1. CLI Usage:")
    print("   # Clone single image")
    print("   uv run python -m main --mode clone --source './assets/stock/image.jpg'")
    print("")
    print("   # Clone directory with custom parameters")
    print("   uv run python -m main --mode clone --source './assets/stock/' --style 'watercolor' --max-images 5")
    print("")
    print("   # Clone with specific dimensions")
    print("   uv run python -m main --mode clone --source './assets/proprietary/logo.png' --width 512 --height 512")
    
    print("\n2. Python API Usage:")
    print("   from purplecrayon import PurpleCrayon")
    print("   ")
    print("   crayon = PurpleCrayon(assets_dir='./assets')")
    print("   ")
    print("   # Clone single image")
    print("   result = crayon.clone(")
    print("       source='./assets/stock/image.jpg',")
    print("       style='photorealistic',")
    print("       guidance='high quality, professional lighting'")
    print("   )")
    print("   ")
    print("   # Clone directory")
    print("   result = crayon.clone(")
    print("       source='./assets/stock/',")
    print("       style='artistic',")
    print("       max_images=10")
    print("   )")
    
    print("\n3. Direct Tools Usage:")
    print("   from purplecrayon.tools.clone_image_tools import clone_image")
    print("   ")
    print("   result = await clone_image(")
    print("       'image.jpg',")
    print("       style='watercolor',")
    print("       guidance='soft, artistic interpretation'")
    print("   )")


def main():
    """Run the clone demo."""
    parser = argparse.ArgumentParser(description="PurpleCrayon Clone Demo")
    parser.add_argument("--api-examples", action="store_true", help="Show API usage examples")
    args = parser.parse_args()
    
    if args.api_examples:
        show_clone_api_usage()
    else:
        mock_clone_demo()
        show_clone_api_usage()


if __name__ == "__main__":
    main()
