#!/usr/bin/env python3
"""
API Key Checker and Clone Test

This script helps you check your API keys and test the clone functionality
with fallback to multiple generation engines.
"""

import os
import asyncio
from pathlib import Path
from purplecrayon.utils.config import get_env

def check_api_keys():
    """Check which API keys are available."""
    print("🔑 API Key Status Check")
    print("=" * 40)
    
    # Check Gemini API key
    gemini_key = get_env('GEMINI_API_KEY') or get_env('GOOGLE_API_KEY')
    if gemini_key:
        print(f"✅ Gemini API Key: {gemini_key[:10]}...")
    else:
        print("❌ Gemini API Key: Not set")
        print("   Set with: export GEMINI_API_KEY=your_key_here")
    
    # Check Replicate API key
    replicate_key = get_env('REPLICATE_API_TOKEN')
    if replicate_key:
        print(f"✅ Replicate API Key: {replicate_key[:10]}...")
    else:
        print("❌ Replicate API Key: Not set")
        print("   Set with: export REPLICATE_API_TOKEN=your_key_here")
    
    # Check OpenAI API key
    openai_key = get_env('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OpenAI API Key: {openai_key[:10]}...")
    else:
        print("❌ OpenAI API Key: Not set")
        print("   Set with: export OPENAI_API_KEY=your_key_here")
    
    return {
        'gemini': bool(gemini_key),
        'replicate': bool(replicate_key),
        'openai': bool(openai_key)
    }


async def test_generation_engines():
    """Test each generation engine individually."""
    print("\n🎨 Testing Generation Engines")
    print("=" * 40)
    
    test_prompt = "A simple test image of a red apple on a white background"
    
    # Test Gemini
    print("\n1. Testing Gemini...")
    try:
        from purplecrayon.tools.clone_image_tools import _try_gemini_generation
        result = await _try_gemini_generation(test_prompt, 512, 512)
        if result["success"]:
            print("✅ Gemini: Working")
        else:
            print(f"❌ Gemini: {result['error']}")
    except Exception as e:
        print(f"❌ Gemini: Error - {e}")
    
    # Test Imagen/Replicate
    print("\n2. Testing Imagen/Replicate...")
    try:
        from purplecrayon.tools.clone_image_tools import _try_imagen_generation
        result = await _try_imagen_generation(test_prompt, 512, 512)
        if result["success"]:
            print("✅ Imagen: Working")
        else:
            print(f"❌ Imagen: {result['error']}")
    except Exception as e:
        print(f"❌ Imagen: Error - {e}")


async def test_clone_with_fallback():
    """Test clone functionality with fallback."""
    print("\n🎨 Testing Clone with Fallback")
    print("=" * 40)
    
    from purplecrayon import PurpleCrayon
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Test with the stock image
    source_image = "./example_assets/stock/stock_pixabay_6_1280x853.jpg"
    
    if not Path(source_image).exists():
        print(f"❌ Source image not found: {source_image}")
        return
    
    print(f"📸 Testing clone with: {source_image}")
    
    try:
        result = await crayon.clone_async(
            source=source_image,
            style="photorealistic",
            guidance="high quality, professional lighting",
            width=512,
            height=512
        )
        
        if result.success:
            print(f"✅ Clone successful: {result.message}")
            for img in result.images:
                print(f"  📸 {img.path}")
                print(f"     Engine: {img.provider}")
                print(f"     Size: {img.width}x{img.height}")
        else:
            print(f"❌ Clone failed: {result.message}")
            
    except Exception as e:
        print(f"❌ Clone error: {e}")


def show_api_setup_instructions():
    """Show instructions for setting up API keys."""
    print("\n📋 API Key Setup Instructions")
    print("=" * 40)
    
    print("\n1. Gemini API Key:")
    print("   - Go to: https://makersuite.google.com/app/apikey")
    print("   - Create a new API key")
    print("   - Set: export GEMINI_API_KEY=your_key_here")
    
    print("\n2. Replicate API Key:")
    print("   - Go to: https://replicate.com/account/api-tokens")
    print("   - Create a new API token")
    print("   - Set: export REPLICATE_API_TOKEN=your_key_here")
    
    print("\n3. OpenAI API Key:")
    print("   - Go to: https://platform.openai.com/api-keys")
    print("   - Create a new API key")
    print("   - Set: export OPENAI_API_KEY=your_key_here")
    
    print("\n💡 You only need ONE of these for the clone functionality to work!")
    print("   The system will automatically fallback to available engines.")


async def main():
    """Main function."""
    print("🚀 PurpleCrayon API Key Checker & Clone Test")
    print("=" * 50)
    
    # Check API keys
    api_status = check_api_keys()
    
    # Show setup instructions if no keys found
    if not any(api_status.values()):
        show_api_setup_instructions()
        return
    
    # Test generation engines
    await test_generation_engines()
    
    # Test clone with fallback
    await test_clone_with_fallback()
    
    print("\n✅ Testing completed!")
    print("\n💡 If you see errors above, check your API keys and try again.")


if __name__ == "__main__":
    asyncio.run(main())
