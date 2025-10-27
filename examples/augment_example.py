#!/usr/bin/env python3
"""
Image Augmentation Example

This script demonstrates how to use PurpleCrayon's image augmentation functionality
to modify existing images using AI image-to-image generation.

The augmentation process:
1. Uploads the source image to AI engines (Gemini or Replicate)
2. Applies modifications based on natural language prompts
3. Generates new images that maintain the original style while incorporating changes
4. Saves augmented images to the assets/ai/ directory

Usage:
    uv run python examples/augment_example.py
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import purplecrayon
sys.path.insert(0, str(Path(__file__).parent.parent))

from purplecrayon import PurpleCrayon, augment_image


async def demonstrate_augmentation():
    """Demonstrate various image augmentation techniques."""
    
    print("🎨 PurpleCrayon Image Augmentation Demo")
    print("=" * 50)
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Create example assets directory
    example_dir = Path("./example_assets")
    example_dir.mkdir(exist_ok=True)
    (example_dir / "ai").mkdir(exist_ok=True)
    
    # Check if we have any images to work with
    image_files = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        image_files.extend(Path("assets").glob(f"**/{ext}"))
    
    if not image_files:
        print("❌ No images found in assets/ directory")
        print("💡 Please add some images to assets/ first, or run other examples to generate some")
        return
    
    # Use the first available image
    source_image = image_files[0]
    print(f"📸 Using source image: {source_image}")
    
    # Example 1: Add elements to an image
    print("\n🎨 Example 1: Adding elements")
    print("-" * 30)
    
    try:
        result1 = await crayon.augment_async(
            image_path=source_image,
            prompt="add a beautiful sunset background with warm orange and pink colors",
            width=1920,
            height=1080,
            format="png"
        )
        
        if result1.success:
            print(f"✅ Successfully augmented image: {result1.images[0].path}")
            print(f"   Provider: {result1.images[0].provider}")
            print(f"   Dimensions: {result1.images[0].width}x{result1.images[0].height}")
        else:
            print(f"❌ Augmentation failed: {result1.message}")
            
    except Exception as e:
        print(f"❌ Error during augmentation: {e}")
    
    # Example 2: Change style or mood
    print("\n🎨 Example 2: Changing style")
    print("-" * 30)
    
    try:
        result2 = await crayon.augment_async(
            image_path=source_image,
            prompt="convert to a watercolor painting style with soft, artistic brushstrokes",
            width=1024,
            height=1024,
            format="png"
        )
        
        if result2.success:
            print(f"✅ Successfully augmented image: {result2.images[0].path}")
            print(f"   Provider: {result2.images[0].provider}")
            print(f"   Dimensions: {result2.images[0].width}x{result2.images[0].height}")
        else:
            print(f"❌ Augmentation failed: {result2.message}")
            
    except Exception as e:
        print(f"❌ Error during augmentation: {e}")
    
    # Example 3: Modify specific elements
    print("\n🎨 Example 3: Modifying specific elements")
    print("-" * 30)
    
    try:
        result3 = await crayon.augment_async(
            image_path=source_image,
            prompt="change the lighting to dramatic evening lighting with deep shadows",
            width=1280,
            height=720,
            format="jpg"
        )
        
        if result3.success:
            print(f"✅ Successfully augmented image: {result3.images[0].path}")
            print(f"   Provider: {result3.images[0].provider}")
            print(f"   Dimensions: {result3.images[0].width}x{result3.images[0].height}")
        else:
            print(f"❌ Augmentation failed: {result3.message}")
            
    except Exception as e:
        print(f"❌ Error during augmentation: {e}")
    
    # Example 4: Direct tool usage
    print("\n🎨 Example 4: Direct tool usage")
    print("-" * 30)
    
    try:
        result4 = await augment_image(
            image_path=source_image,
            prompt="add a professional studio lighting setup with soft key light and rim lighting",
            width=1920,
            height=1080,
            output_format="png",
            output_dir="./example_assets/ai"
        )
        
        if result4.success:
            print(f"✅ Successfully augmented image: {result4.data['output_path']}")
            print(f"   Provider: {result4.data['provider']}")
            print(f"   Dimensions: {result4.data['width']}x{result4.data['height']}")
        else:
            print(f"❌ Augmentation failed: {result4.message}")
            
    except Exception as e:
        print(f"❌ Error during direct tool usage: {e}")
    
    # Show final results
    print("\n📊 Augmentation Results Summary")
    print("=" * 50)
    
    ai_dir = Path("./example_assets/ai")
    if ai_dir.exists():
        augmented_files = list(ai_dir.glob("augmented_*"))
        print(f"📁 Augmented images saved to: {ai_dir}")
        print(f"📸 Total augmented images: {len(augmented_files)}")
        
        for i, file in enumerate(augmented_files, 1):
            print(f"  {i}. {file.name}")
    else:
        print("❌ No augmented images were created")
    
    print("\n💡 Tips for better augmentation:")
    print("  • Be specific about what you want to change")
    print("  • Mention the style or mood you're looking for")
    print("  • Include details about lighting, colors, or composition")
    print("  • Try different prompts to get varied results")
    print("  • Use high-quality source images for better results")


async def demonstrate_sync_augmentation():
    """Demonstrate synchronous augmentation (for comparison)."""
    
    print("\n🔄 Synchronous Augmentation Demo")
    print("=" * 50)
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Find an image to work with
    image_files = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        image_files.extend(Path("assets").glob(f"**/{ext}"))
    
    if not image_files:
        print("❌ No images found in assets/ directory")
        return
    
    source_image = image_files[0]
    print(f"📸 Using source image: {source_image}")
    
    try:
        result = await crayon.augment_async(
            image_path=source_image,
            prompt="add a magical forest background with glowing mushrooms and fireflies",
            width=1024,
            height=1024,
            format="png"
        )
        
        if result.success:
            print(f"✅ Successfully augmented image: {result.images[0].path}")
            print(f"   Provider: {result.images[0].provider}")
            print(f"   Dimensions: {result.images[0].width}x{result.images[0].height}")
        else:
            print(f"❌ Augmentation failed: {result.message}")
            
    except Exception as e:
        print(f"❌ Error during synchronous augmentation: {e}")


async def main():
    """Main function to run all demonstrations."""
    
    # Check API keys
    import os
    from purplecrayon.utils.config import get_env
    
    gemini_key = get_env("GEMINI_API_KEY")
    replicate_key = get_env("REPLICATE_API_TOKEN")
    
    if not gemini_key and not replicate_key:
        print("❌ No API keys found!")
        print("💡 Please set GEMINI_API_KEY or REPLICATE_API_TOKEN in your .env file")
        print("   Example: GEMINI_API_KEY=your_key_here")
        return
    
    print(f"🔑 API Keys: Gemini={'✅' if gemini_key else '❌'}, Replicate={'✅' if replicate_key else '❌'}")
    
    # Run async demonstrations
    await demonstrate_augmentation()
    
    # Run sync demonstration
    await demonstrate_sync_augmentation()
    
    print("\n🎉 Augmentation demo completed!")
    print("💡 Check the example_assets/ai/ directory for your augmented images")


if __name__ == "__main__":
    asyncio.run(main())
