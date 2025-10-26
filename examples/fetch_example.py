#!/usr/bin/env python3
"""
Example: Fetch stock photos using PurpleCrayon package
"""

from purplecrayon import PurpleCrayon, AssetRequest
from pathlib import Path
import asyncio
from purplecrayon.tools.file_tools import download_file


def main():
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Create a request for stock photos
    # NOTE: max_results applies per provider (Unsplash, Pexels, Pixabay), so total results can exceed this value.
    request = AssetRequest(
        description="panda eating bamboo in forest",
        width=1920,
        height=1080,
        format="jpg",
        preferred_sources=["unsplash", "pexels"],
        max_results=3
    )
    
    print("🔍 Fetching stock photos...")
    result = crayon.fetch(request)
    
    if result.success:
        print(f"✅ {result.message}")
        print(f"📸 Found {len(result.images)} images:")
        
        for i, img in enumerate(result.images, 1):
            print(f"  {i}. {img.path}")
            print(f"     Source: {img.source}/{img.provider}")
            print(f"     Size: {img.width}x{img.height}")
            if img.description:
                print(f"     Description: {img.description}")
            if img.error:
                print(f"     ❌ Error: {img.error}")
            print()
        
        # Save top results to example_assets/stock
        out_dir = Path("./example_assets/stock")
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"💾 Saving images to: {out_dir}")
        
        for i, img in enumerate(result.images, 1):
            if isinstance(img.path, str) and img.path.startswith("http"):
                target = out_dir / f"stock_{img.provider}_{i}.jpg"
                try:
                    asyncio.run(download_file(img.path, str(target)))
                    print(f"   ✅ Saved: {target}")
                except Exception as e:
                    print(f"   ❌ Failed to save {img.path[:60]}... -> {e}")
    else:
        print(f"❌ Fetch failed: {result.message}")
        if result.error_code:
            print(f"   Error Code: {result.error_code}")


if __name__ == "__main__":
    main()
