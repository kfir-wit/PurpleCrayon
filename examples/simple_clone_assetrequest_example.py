#!/usr/bin/env python3
"""
Simple Clone Example using AssetRequest approach

This demonstrates the clone functionality as you described:
1. Analyze an existing image to generate a detailed description
2. Create an AssetRequest from that description  
3. Use the standard generation pipeline (like generate_example.py)
"""

import asyncio
from pathlib import Path

from purplecrayon.tools.simple_clone_tools import clone_image_simple, analyze_image_for_description, create_asset_request_from_image
from purplecrayon import PurpleCrayon


async def example_analyze_and_create_request():
    """Example: Analyze image and create AssetRequest manually."""
    print("=== Example 1: Analyze Image and Create AssetRequest ===")
    
    source_image = "./example_assets/stock/stock_pixabay_6_1280x853.jpg"
    
    if not Path(source_image).exists():
        print(f"❌ Source image not found: {source_image}")
        return
    
    print(f"🔍 Analyzing: {source_image}")
    
    # Step 1: Analyze the image
    analysis = await analyze_image_for_description(source_image)
    
    if analysis["success"]:
        print(f"✅ Analysis successful:")
        print(f"   Description: {analysis['description'][:200]}...")
        print(f"   Dimensions: {analysis['original_dimensions']}")
        print(f"   Format: {analysis['original_format']}")
        
        # Step 2: Create AssetRequest
        request = create_asset_request_from_image(
            source_image,
            style="watercolor",
            guidance="soft, artistic interpretation",
            width=1024,
            height=1024
        )
        
        print(f"\n📝 AssetRequest created:")
        print(f"   Description: {request.description[:200]}...")
        print(f"   Dimensions: {request.width}x{request.height}")
        print(f"   Format: {request.format}")
        print(f"   Style: {request.style}")
        print(f"   Sources: {request.preferred_sources}")
        
        # Step 3: Generate using standard pipeline
        print(f"\n🤖 Generating with standard pipeline...")
        crayon = PurpleCrayon(assets_dir="./example_assets")
        result = await crayon.generate_async(request)
        
        if result.success:
            print(f"✅ Generated {len(result.images)} images:")
            for i, img in enumerate(result.images, 1):
                print(f"  {i}. {img.path}")
                print(f"     Size: {img.width}x{img.height}")
                print(f"     Source: {img.source}/{img.provider}")
        else:
            print(f"❌ Generation failed: {result.message}")
    else:
        print(f"❌ Analysis failed: {analysis['error']}")


async def example_simple_clone():
    """Example: Use the simple clone function."""
    print("\n=== Example 2: Simple Clone Function ===")
    
    source_image = "./example_assets/stock/stock_pixabay_6_1280x853.jpg"
    
    if not Path(source_image).exists():
        print(f"❌ Source image not found: {source_image}")
        return
    
    print(f"🎨 Cloning: {source_image}")
    
    result = await clone_image_simple(
        source_image,
        style="oil painting",
        guidance="classical art style, rich colors",
        width=512,
        height=512,
        output_dir=Path("./example_assets/cloned")
    )
    
    if result["success"]:
        print(f"✅ Clone successful:")
        print(f"   Original: {result['original_filename']}")
        print(f"   Clone: {result['clone_filename']}")
        print(f"   Path: {result['clone_path']}")
        print(f"   Dimensions: {result['clone_dimensions']}")
        print(f"   Format: {result['format']}")
        print(f"   Prompt: {result['generation_prompt'][:100]}...")
    else:
        print(f"❌ Clone failed: {result['error']}")


async def example_compare_approaches():
    """Example: Compare the old approach vs new approach."""
    print("\n=== Example 3: Compare Approaches ===")
    
    source_image = "./example_assets/stock/stock_pixabay_6_1280x853.jpg"
    
    if not Path(source_image).exists():
        print(f"❌ Source image not found: {source_image}")
        return
    
    print(f"🔄 Comparing approaches for: {source_image}")
    
    # New approach: AssetRequest-based
    print(f"\n📝 New Approach (AssetRequest-based):")
    print(f"   1. Analyze image → Generate description")
    print(f"   2. Create AssetRequest from description")
    print(f"   3. Use standard generation pipeline")
    print(f"   4. No file uploads needed!")
    
    # Show what the AssetRequest would look like
    analysis = await analyze_image_for_description(source_image)
    if analysis["success"]:
        request = create_asset_request_from_image(
            source_image,
            style="watercolor",
            width=512,
            height=512
        )
        
        print(f"\n   Generated AssetRequest:")
        print(f"   Description: {request.description[:150]}...")
        print(f"   This is exactly like generate_example.py!")
    
    print(f"\n🔄 Old Approach (Image Upload-based):")
    print(f"   1. Upload source image to AI service")
    print(f"   2. Use image-to-image generation")
    print(f"   3. More complex, requires file uploads")
    print(f"   4. Bookmarked for later implementation")


async def main():
    """Run all examples."""
    print("🎨 Simple Clone Examples (AssetRequest Approach)")
    print("=" * 60)
    
    await example_analyze_and_create_request()
    await example_simple_clone()
    await example_compare_approaches()
    
    print(f"\n✅ All examples completed!")
    print(f"\n💡 Key Benefits of this approach:")
    print(f"   - No file uploads required")
    print(f"   - Uses standard generation pipeline")
    print(f"   - Leverages existing AssetRequest system")
    print(f"   - Same as generate_example.py but with image analysis")
    print(f"   - Much simpler implementation")


if __name__ == "__main__":
    asyncio.run(main())
