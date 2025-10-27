#!/usr/bin/env python3
"""
Test: Image-to-image generation with proper API calls
This tests the fixed image-to-image functionality.
"""

from pathlib import Path
from purplecrayon.tools.ai_generation_tools import generate_with_gemini_image_to_image_async


import asyncio
import pytest


@pytest.mark.asyncio
async def test_image_to_image():
    """Test image-to-image generation with a simple image."""
    source_image = "./example_assets/stock/stock_pixabay_6_1280x853.jpg"
    
    if not Path(source_image).exists():
        print(f"❌ Source image not found: {source_image}")
        return
    
    print(f"🎨 Testing image-to-image generation with: {source_image}")
    print("=" * 60)
    
    # Simple prompt for image modification
    prompt = "Transform this image into a watercolor painting style while keeping the same composition and subject matter"
    
    print(f"📝 Prompt: {prompt}")
    print("🤖 Generating image-to-image...")
    
    try:
        result = await generate_with_gemini_image_to_image_async(
            prompt=prompt,
            source_image_path=source_image,
            aspect_ratio="1:1"
        )
        
        if result.get("status") == "succeeded":
            print(f"✅ Image-to-image generation successful!")
            print(f"   Model: {result.get('model')}")
            print(f"   Format: {result.get('format')}")
            print(f"   Source: {result.get('source_image')}")
            print(f"   Image data size: {len(result.get('image_data', b''))} bytes")
            
            # Save the result
            output_path = Path("./example_assets/ai/test_image_to_image.png")
            with open(output_path, "wb") as f:
                f.write(result["image_data"])
            print(f"💾 Saved to: {output_path}")
            
        else:
            print(f"❌ Generation failed: {result.get('reason', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during generation: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_image_to_image())
