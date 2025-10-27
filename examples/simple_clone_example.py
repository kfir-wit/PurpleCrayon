#!/usr/bin/env python3
"""
Example: Simple clone using text-to-image generation
This is a simplified approach that generates a new image based on the filename
without complex vision analysis.
"""

from purplecrayon import PurpleCrayon, AssetRequest
from pathlib import Path


def main():
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Source image to clone
    source_image = "./example_assets/stock/stock_pixabay_6_1280x853.jpg"
    
    if not Path(source_image).exists():
        print(f"❌ Source image not found: {source_image}")
        return
    
    print(f"🎨 Simple cloning: {source_image}")
    print("=" * 50)
    
    # Create a simple description based on filename
    filename = Path(source_image).stem
    # Convert filename to a readable description
    description = filename.replace('_', ' ').replace('stock', 'stock photo').replace('pixabay', 'Pixabay')
    
    # Create a request for AI generation (similar to generate_example.py)
    request = AssetRequest(
        description=f"high quality {description}, professional photography style, detailed and clear",
        width=512,
        height=512,
        format="png",
        style="photorealistic",
        preferred_sources=["gemini"],  # Use only Gemini for now
        max_results=1
    )
    
    print(f"📝 Prompt: {request.description}")
    print("🤖 Generating cloned image...")
    
    result = crayon.generate(request)
    
    if result.success:
        print(f"✅ {result.message}")
        print(f"🎨 Generated {len(result.images)} cloned images:")
        
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
