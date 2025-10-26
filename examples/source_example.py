#!/usr/bin/env python3
"""
Example: Full workflow - search local + fetch stock + generate AI
"""

from purplecrayon import PurpleCrayon, AssetRequest


def main():
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Create a comprehensive request
    request = AssetRequest(
        description="panda wallpaper for desktop",
        width=1920,
        height=1080,
        format="jpg",
        style="high quality",
        preferred_sources=["unsplash", "gemini"],
        max_results=5,
        tags=["nature", "wildlife", "cute"]
    )
    
    print("🔍 Running full source workflow...")
    print("  1. Searching local assets")
    print("  2. Fetching from stock photo APIs")
    print("  3. Generating with AI providers")
    print()
    
    result = crayon.source(request)
    
    if result.success:
        print(f"✅ {result.message}")
        print(f"📸 Found {len(result.images)} total images:")
        
        # Group by source
        sources = {}
        for img in result.images:
            if img.source not in sources:
                sources[img.source] = []
            sources[img.source].append(img)
        
        for source, images in sources.items():
            print(f"\n📁 {source.upper()} ({len(images)} images):")
            for i, img in enumerate(images, 1):
                print(f"  {i}. {img.path}")
                print(f"     Provider: {img.provider}")
                print(f"     Size: {img.width}x{img.height}")
                if img.match_score:
                    print(f"     Match Score: {img.match_score:.2f}")
                if img.error:
                    print(f"     ❌ Error: {img.error}")
                print()
    else:
        print(f"❌ Source operation failed: {result.message}")
        if result.error_code:
            print(f"   Error Code: {result.error_code}")


if __name__ == "__main__":
    main()
