#!/usr/bin/env python3
"""
Unified Model API Example

This script demonstrates the new unified model management system for text-to-image generation.
It shows how to use the list, all, with, exclude, and default options.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import purplecrayon
sys.path.insert(0, str(Path(__file__).parent.parent))

from purplecrayon.tools.ai_generation_tools import (
    generate_with_models_async,
    list_available_models,
    check_model_updates
)


async def demonstrate_model_listing():
    """Demonstrate model listing and information."""
    print("🔍 Available Models:")
    print("=" * 50)
    
    model_info = list_available_models()
    
    print(f"Total Models: {model_info['total_models']}")
    print(f"Enabled Models: {model_info['enabled_models']}")
    print(f"Providers: {', '.join(model_info['providers'])}")
    print(f"Fallback Order: {' → '.join(model_info['fallback_order'])}")
    print()
    
    print("Model Details:")
    for name, details in model_info['models'].items():
        status = "✅" if details['enabled'] else "❌"
        print(f"  {status} {details['display_name']}")
        print(f"    Provider: {details['provider']}")
        print(f"    Priority: {details['priority']}")
        print(f"    Cost Tier: {details['cost_tier']}")
        print(f"    Max Resolution: {details['max_resolution']}")
        print(f"    Formats: {', '.join(details['supported_formats'])}")
        print()


async def demonstrate_default_generation():
    """Demonstrate default generation (fallback order)."""
    print("🎨 Default Generation (Fallback Order):")
    print("=" * 50)
    
    result = await generate_with_models_async(
        prompt="a futuristic city skyline at sunset",
        aspect_ratio="16:9",
        model_type="text_to_image"
    )
    
    print(f"Status: {result['status']}")
    print(f"Successful: {result['successful_generations']}/{result['total_attempts']}")
    
    for model_name, model_result in result['results'].items():
        status = "✅" if model_result['result']['status'] == 'succeeded' else "❌"
        print(f"  {status} {model_result['model']}: {model_result['result']['status']}")
        if model_result['result']['status'] == 'succeeded':
            image_data = model_result['result'].get('image_data')
            if image_data:
                print(f"    Generated {len(image_data)} bytes of image data")
    print()


async def demonstrate_specific_models():
    """Demonstrate generation with specific models."""
    print("🎯 Specific Model Generation:")
    print("=" * 50)
    
    # Generate with only Gemini
    print("Generating with Gemini only...")
    result = await generate_with_models_async(
        prompt="a watercolor painting of a mountain landscape",
        aspect_ratio="1:1",
        with_models=["gemini-flash"]
    )
    
    print(f"Gemini Result: {result['status']} ({result['successful_generations']}/{result['total_attempts']})")
    
    # Generate with only Replicate models
    print("\nGenerating with Replicate models only...")
    result = await generate_with_models_async(
        prompt="a cyberpunk robot in a neon-lit alley",
        aspect_ratio="1:1",
        with_models=["flux-1.1-pro", "stable-diffusion"]
    )
    
    print(f"Replicate Result: {result['status']} ({result['successful_generations']}/{result['total_attempts']})")
    print()


async def demonstrate_exclude_models():
    """Demonstrate generation excluding specific models."""
    print("🚫 Exclude Model Generation:")
    print("=" * 50)
    
    # Generate excluding Gemini
    print("Generating excluding Gemini...")
    result = await generate_with_models_async(
        prompt="a minimalist logo design",
        aspect_ratio="1:1",
        exclude_models=["gemini-flash"]
    )
    
    print(f"Result: {result['status']} ({result['successful_generations']}/{result['total_attempts']})")
    for model_name, model_result in result['results'].items():
        status = "✅" if model_result['result']['status'] == 'succeeded' else "❌"
        print(f"  {status} {model_result['model']}: {model_result['result']['status']}")
    print()


async def demonstrate_all_models():
    """Demonstrate generation with all available models."""
    print("🌟 All Models Generation:")
    print("=" * 50)
    
    result = await generate_with_models_async(
        prompt="a cute cartoon cat wearing a space helmet",
        aspect_ratio="1:1",
        all_models=True
    )
    
    print(f"Result: {result['status']} ({result['successful_generations']}/{result['total_attempts']})")
    
    for model_name, model_result in result['results'].items():
        status = "✅" if model_result['result']['status'] == 'succeeded' else "❌"
        print(f"  {status} {model_result['model']}: {model_result['result']['status']}")
        if model_result['result']['status'] == 'succeeded':
            image_data = model_result['result'].get('image_data')
            if image_data:
                print(f"    Generated {len(image_data)} bytes of image data")
    print()


async def demonstrate_model_updates():
    """Demonstrate model update checking."""
    print("🔄 Model Update Check:")
    print("=" * 50)
    
    print("Checking for model configuration updates...")
    updated = check_model_updates(force=False)
    
    if updated:
        print("✅ Model configuration updated!")
    else:
        print("ℹ️ No updates available")
    print()


async def demonstrate_model_types():
    """Demonstrate different model types."""
    print("🔄 Model Type Demonstrations:")
    print("=" * 50)
    
    # Text-to-Image
    print("1. Text-to-Image Generation:")
    result = await generate_with_models_async(
        prompt="a serene lake with mountains in the background",
        aspect_ratio="16:9",
        model_type="text_to_image"
    )
    print(f"   Status: {result['status']} ({result['successful_generations']}/{result['total_attempts']})")
    
    # Image-to-Image (if we have a source image)
    print("\n2. Image-to-Image Generation:")
    source_image = "./example_assets/ai/panda_watercolor_art_1024x1024.png"
    if Path(source_image).exists():
        result = await generate_with_models_async(
            prompt="convert to oil painting style with dramatic lighting",
            aspect_ratio="1:1",
            model_type="image_to_image",
            image_path=source_image
        )
        print(f"   Status: {result['status']} ({result['successful_generations']}/{result['total_attempts']})")
    else:
        print("   ⚠️ No source image found for image-to-image demo")
    
    # Image-to-Text (if we have a source image)
    print("\n3. Image-to-Text Analysis:")
    if Path(source_image).exists():
        result = await generate_with_models_async(
            prompt="Analyze this image and describe its artistic style and composition",
            model_type="image_to_text",
            image_path=source_image
        )
        print(f"   Status: {result['status']} ({result['successful_generations']}/{result['total_attempts']})")
        if result['successful_generations'] > 0:
            for model_name, model_result in result['results'].items():
                if model_result['result']['status'] == 'succeeded':
                    description = model_result['result'].get('description', '')
                    print(f"   Description: {description[:100]}...")
    else:
        print("   ⚠️ No source image found for image-to-text demo")
    
    print()


async def main():
    """Run all demonstrations."""
    print("🚀 PurpleCrayon Unified Model API Demo")
    print("=" * 60)
    print()
    
    # Check API keys
    from purplecrayon.utils.config import get_env
    gemini_key = get_env("GEMINI_API_KEY")
    replicate_key = get_env("REPLICATE_API_TOKEN")
    
    if not gemini_key and not replicate_key:
        print("❌ No API keys found!")
        print("💡 Please set GEMINI_API_KEY or REPLICATE_API_TOKEN in your .env file")
        return
    
    print(f"🔑 API Keys: Gemini={'✅' if gemini_key else '❌'}, Replicate={'✅' if replicate_key else '❌'}")
    print()
    
    # Run demonstrations
    await demonstrate_model_listing()
    await demonstrate_model_updates()
    await demonstrate_default_generation()
    await demonstrate_specific_models()
    await demonstrate_exclude_models()
    await demonstrate_all_models()
    await demonstrate_model_types()
    
    print("✅ Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
