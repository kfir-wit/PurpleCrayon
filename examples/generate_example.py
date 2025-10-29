#!/usr/bin/env python3
"""
Example: Generate AI images using PurpleCrayon package

This example demonstrates both sync and async usage patterns.
"""

import asyncio
import sys
from pathlib import Path

# If running from source without installing, uncomment next 2 lines:
# sys.path.insert(0, str(Path(__file__).parent.parent))
from purplecrayon import PurpleCrayon, AssetRequest


async def async_generation_example():
    """Example using async/await pattern (recommended)."""
    print("🚀 Async Generation Example")
    print("=" * 40)
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Create a request for AI generation
    request = AssetRequest(
        description="artistic panda illustration in watercolor style",
        width=1024,
        height=1024,
        format="png",
        style="watercolor",
        preferred_sources=["gemini", "replicate"],
        max_results=2
    )
    
    print("🤖 Generating AI images (async)...")
    result = await crayon.generate_async(request)
    
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


def sync_generation_example():
    """Example using sync pattern (for comparison)."""
    print("\n🔄 Sync Generation Example")
    print("=" * 40)
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Create a request for AI generation
    request = AssetRequest(
        description="photorealistic red panda in a forest",
        width=512,
        height=512,
        format="png",
        style="photorealistic",
        preferred_sources=["gemini"],
        max_results=1
    )
    
    print("🤖 Generating AI images (sync)...")
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


async def concurrent_generation_example():
    """Example of concurrent generation using async."""
    print("\n⚡ Concurrent Generation Example")
    print("=" * 40)
    
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Create multiple requests
    requests = [
        AssetRequest(
            description="abstract geometric art with blue triangles",
            width=256,
            height=256,
            format="png",
            max_results=1
        ),
        AssetRequest(
            description="watercolor landscape with mountains",
            width=256,
            height=256,
            format="png",
            max_results=1
        ),
        AssetRequest(
            description="minimalist black and white design",
            width=256,
            height=256,
            format="png",
            max_results=1
        )
    ]
    
    print("🤖 Generating multiple images concurrently...")
    
    # Run all generations concurrently
    tasks = [crayon.generate_async(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = 0
    total_images = 0
    
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"  {i}. ❌ Request {i} failed: {result}")
        elif result.success:
            successful += 1
            total_images += len(result.images)
            print(f"  {i}. ✅ Generated {len(result.images)} image(s)")
        else:
            print(f"  {i}. ❌ Request {i} failed: {result.message}")
    
    print(f"\n📊 Concurrent Results:")
    print(f"  Successful requests: {successful}/{len(requests)}")
    print(f"  Total images generated: {total_images}")


async def main():
    """Main function demonstrating all patterns."""
    print("🎨 PurpleCrayon Generation Examples")
    print("=" * 50)
    
    # Check API keys
    from purplecrayon.utils.config import get_env
    gemini_key = get_env("GEMINI_API_KEY")
    replicate_key = get_env("REPLICATE_API_TOKEN")
    
    if not gemini_key and not replicate_key:
        print("❌ No API keys found!")
        print("💡 Please set GEMINI_API_KEY or REPLICATE_API_TOKEN in your .env file")
        return
    
    print(f"🔑 API Keys: Gemini={'✅' if gemini_key else '❌'}, Replicate={'✅' if replicate_key else '❌'}")
    
    # Run examples
    await async_generation_example()
    sync_generation_example()
    await concurrent_generation_example()
    
    print("\n✅ All generation examples completed!")
    print("💡 Check the example_assets/ai/ directory for generated images")


if __name__ == "__main__":
    asyncio.run(main())
