#!/usr/bin/env python3
"""
PurpleCrayon Clone Example

This script demonstrates how to use the clone functionality to create
royalty-free alternatives of existing images.
"""

import argparse
import asyncio
from pathlib import Path

from purplecrayon import PurpleCrayon, clone_image, clone_images_from_directory


def example_single_image_clone():
    """Example of cloning a single image."""
    print("=== Example 1: Single Image Clone ===")
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Clone a single image
    source_image = "./example_assets/downloaded/scraped_fc_a_1456x816.jpg"
    
    if Path(source_image).exists():
        print(f"🎨 Cloning: {source_image}")
        result = crayon.clone(
            source=source_image,
            style="photorealistic",
            guidance="high quality, professional lighting"
        )
        
        if result.success:
            print(f"✅ Success: {result.message}")
            for img in result.images:
                print(f"  📸 Cloned: {img.path}")
                print(f"     Dimensions: {img.width}x{img.height}")
                print(f"     Format: {img.format}")
        else:
            print(f"❌ Failed: {result.message}")
    else:
        print(f"⚠️ Source image not found: {source_image}")


def example_directory_batch_clone():
    """Example of cloning all images from a directory."""
    print("\n=== Example 2: Directory Batch Clone ===")
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Clone all images from downloaded directory
    source_dir = "./example_assets/downloaded"
    
    if Path(source_dir).exists():
        print(f"🎨 Cloning all images from: {source_dir}")
        result = crayon.clone(
            source=source_dir,
            style="artistic",
            guidance="creative interpretation, unique style",
            max_images=3  # Limit to 3 images for demo
        )
        
        if result.success:
            print(f"✅ Success: {result.message}")
            for i, img in enumerate(result.images, 1):
                print(f"  {i}. 📸 {img.path}")
                print(f"     Dimensions: {img.width}x{img.height}")
                print(f"     Format: {img.format}")
        else:
            print(f"❌ Failed: {result.message}")
    else:
        print(f"⚠️ Source directory not found: {source_dir}")


async def example_direct_tools_usage():
    """Example using clone tools directly."""
    print("\n=== Example 3: Direct Tools Usage ===")
    
    # Clone single image using direct tools
    source_image = "./example_assets/stock/stock_unsplash_6000x3777.jpg"
    
    if Path(source_image).exists():
        print(f"🔍 Analyzing image: {source_image}")
        
        # First, analyze the image
        from purplecrayon.tools.clone_image_tools import describe_image_for_regeneration
        analysis = await describe_image_for_regeneration(source_image)
        
        if analysis["success"]:
            print(f"📝 Analysis successful:")
            print(f"  Description: {analysis['description'][:100]}...")
            print(f"  Dimensions: {analysis['original_dimensions']}")
            print(f"  Format: {analysis['original_format']}")
            
            # Now clone the image
            print(f"\n🎨 Cloning image...")
            result = await clone_image(
                source_image,
                style="watercolor",
                guidance="soft, artistic interpretation",
                output_dir=Path("./example_assets/cloned")
            )
            
            if result["success"]:
                print(f"✅ Clone successful:")
                print(f"  Original: {result['original_filename']}")
                print(f"  Clone: {result['clone_filename']}")
                print(f"  Similarity: {result['similarity_score']:.2f}")
            else:
                print(f"❌ Clone failed: {result['error']}")
        else:
            print(f"❌ Analysis failed: {analysis['error']}")
    else:
        print(f"⚠️ Source image not found: {source_image}")


def example_with_custom_parameters():
    """Example with custom parameters."""
    print("\n=== Example 4: Custom Parameters ===")
    
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Clone with specific dimensions and format
    source_image = "./example_assets/ai/panda_watercolor_art_1024x1024.png"
    
    if Path(source_image).exists():
        print(f"🎨 Cloning with custom parameters: {source_image}")
        result = crayon.clone(
            source=source_image,
            width=512,
            height=512,
            format="jpg",
            style="oil painting",
            guidance="classical art style, rich colors",
            similarity_threshold=0.6  # Allow more similarity
        )
        
        if result.success:
            print(f"✅ Success: {result.message}")
            for img in result.images:
                print(f"  📸 {img.path}")
                print(f"     Size: {img.width}x{img.height}")
                print(f"     Format: {img.format}")
        else:
            print(f"❌ Failed: {result.message}")
    else:
        print(f"⚠️ Source image not found: {source_image}")


def example_similarity_checking():
    """Example of similarity checking between original and clone."""
    print("\n=== Example 5: Similarity Checking ===")
    
    from purplecrayon.tools.clone_image_tools import check_similarity, is_sufficiently_different
    
    # Check similarity between two images
    original = Path("./example_assets/ai/panda_watercolor_art_1024x1024.png")
    clone = Path("./example_assets/cloned/panda_watercolor_art_1024x1024.png")
    
    if original.exists() and clone.exists():
        similarity = check_similarity(original, clone)
        is_different = is_sufficiently_different(original, clone, threshold=0.7)
        
        print(f"🔍 Similarity Analysis:")
        print(f"  Original: {original.name}")
        print(f"  Clone: {clone.name}")
        print(f"  Similarity Score: {similarity:.2f} (0.0 = identical, 1.0 = completely different)")
        print(f"  Sufficiently Different: {'Yes' if is_different else 'No'}")
    else:
        print("⚠️ Need both original and clone images for similarity checking")


def main():
    """Run all clone examples."""
    parser = argparse.ArgumentParser(description="PurpleCrayon Clone Examples")
    parser.add_argument("--example", choices=["1", "2", "3", "4", "5", "all"], 
                       default="all", help="Which example to run")
    args = parser.parse_args()
    
    print("🎨 PurpleCrayon Clone Examples")
    print("=" * 40)
    
    if args.example in ["1", "all"]:
        example_single_image_clone()
    
    if args.example in ["2", "all"]:
        example_directory_batch_clone()
    
    if args.example in ["3", "all"]:
        asyncio.run(example_direct_tools_usage())
    
    if args.example in ["4", "all"]:
        example_with_custom_parameters()
    
    if args.example in ["5", "all"]:
        example_similarity_checking()
    
    print("\n✅ All clone examples completed!")
    print("\n💡 Tips:")
    print("  - Use --style to control artistic style (photorealistic, artistic, watercolor, etc.)")
    print("  - Use --guidance for specific instructions")
    print("  - Use --similarity-threshold to control how different the clone should be")
    print("  - Use --max-images to limit batch processing")
    print("  - Cloned images are saved to assets/cloned/ directory")


if __name__ == "__main__":
    main()
