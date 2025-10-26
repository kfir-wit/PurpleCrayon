#!/usr/bin/env python3
"""
Example: Generate AI images using PurpleCrayon package
"""

# If running from source without installing, uncomment next 2 lines:
# import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from purplecrayon import PurpleCrayon, AssetRequest


def main():
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")  # works when installed/packaged
    
    # Create a request for AI generation
    request = AssetRequest(
        description="artistic panda illustration in watercolor style",
        width=1024,
        height=1024,
        format="png",
        style="watercolor",
        preferred_sources=["gemini", "imagen"],
        max_results=2
    )
    
    print("🤖 Generating AI images...")
    result = crayon.generate(request)
    
    if result.success:
        print(f"✅ {result.message}")
        print(f"🎨 Generated {len(result.images)} images:")
        
        for i, img in enumerate(result.images, 1):
            print(f"  {i}. {img.path}")
            print(f"     Source: {img.source}/{img.provider}")
            print(f"     Size: {img.width}x{img.height}")
            if img.description:
                print(f"     Description: {img.description}")
            if img.error:
                print(f"     ❌ Error: {img.error}")
            print()
    else:
        print(f"❌ Generation failed: {result.message}")
        if result.error_code:
            print(f"   Error Code: {result.error_code}")


if __name__ == "__main__":
    main()
