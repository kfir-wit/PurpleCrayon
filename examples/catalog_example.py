#!/usr/bin/env python3
"""
Example: Create and manage asset catalog using PurpleCrayon package
Demonstrates catalog creation, cleanup, and management features.
"""

import argparse
import json
from pathlib import Path
from purplecrayon import PurpleCrayon


def create_catalog_example(crayon, assets_dir, cleanup=True, rename=True, format="yaml"):
    """Create a comprehensive catalog example."""
    print(f"📚 PurpleCrayon Catalog Management Example")
    print("=" * 50)
    print(f"📁 Assets directory: {assets_dir}")
    print(f"🧹 Cleanup enabled: {cleanup}")
    print(f"🏷️ Rename enabled: {rename}")
    print(f"📄 Catalog format: {format.upper()}")
    print()
    
    # Step 1: Clean up assets if requested
    if cleanup:
        print("🧹 Step 1: Cleaning up assets...")
        print("-" * 30)
        cleanup_result = crayon.cleanup_assets(remove_junk=True)
        
        if cleanup_result["success"]:
            cleanup_stats = cleanup_result["cleanup_stats"]
            print(f"✅ Cleanup completed:")
            print(f"  📸 Valid images: {cleanup_stats['valid']}")
            if cleanup_stats['corrupted'] > 0:
                print(f"  ❌ Corrupted files removed: {cleanup_stats['corrupted']}")
            if cleanup_stats['junk'] > 0:
                print(f"  🗑️ Junk files removed: {cleanup_stats['junk']}")
            if cleanup_stats['corrupted'] > 0 or cleanup_stats['junk'] > 0:
                print(f"  📝 Total files processed: {cleanup_stats.get('total_removed', 0)}")
        else:
            print(f"⚠️ Cleanup failed: {cleanup_result['error']}")
            return False
        print()
    
    # Step 2: Rename and organize assets if requested
    if rename:
        print("🏷️ Step 2: Renaming and organizing assets...")
        print("-" * 30)
        rename_result = crayon.sort_catalog()
        
        if rename_result["success"]:
            rename_stats = rename_result["rename_stats"]
            catalog_stats = rename_result["catalog_stats"]
            print(f"✅ Renaming completed:")
            print(f"  📝 Files renamed: {rename_stats['renamed']}")
            print(f"  ⏭️ Files skipped: {rename_stats['skipped']}")
            print(f"  ⚠️ Errors: {rename_stats['errors']}")
            print(f"  📊 Catalog updated: {catalog_stats['added']} added, {catalog_stats['updated']} updated, {catalog_stats['removed']} removed")
        else:
            print(f"⚠️ Renaming failed: {rename_result['error']}")
            return False
        print()
    
    # Step 3: Show final catalog statistics
    print("📊 Step 3: Final catalog statistics...")
    print("-" * 30)
    final_stats = crayon.catalog.get_stats()
    
    print(f"📈 Catalog Statistics:")
    print(f"  📸 Total assets: {final_stats.get('total_assets', 0)}")
    print(f"  📂 By source: {final_stats.get('by_source', {})}")
    print(f"  🎨 By format: {final_stats.get('by_format', {})}")
    print(f"  📐 By aspect ratio: {final_stats.get('by_aspect_ratio', {})}")
    print()
    
    # Step 4: Export catalog in requested format(s)
    print("📄 Step 4: Exporting catalog...")
    print("-" * 30)
    
    if format.lower() in ["yaml", "both"]:
        yaml_path = Path(assets_dir) / "catalog.yaml"
        if yaml_path.exists():
            print(f"✅ YAML catalog: {yaml_path}")
            print(f"📏 Size: {yaml_path.stat().st_size:,} bytes")
        else:
            print("⚠️ No YAML catalog found")
    
    if format.lower() in ["json", "both"]:
        export_json_catalog(crayon, assets_dir)
    
    if format.lower() == "both":
        print()
        print("📊 Format comparison:")
        yaml_path = Path(assets_dir) / "catalog.yaml"
        json_path = Path(assets_dir) / "catalog.json"
        
        if yaml_path.exists() and json_path.exists():
            yaml_size = yaml_path.stat().st_size
            json_size = json_path.stat().st_size
            savings = ((yaml_size - json_size) / yaml_size) * 100
            print(f"  YAML: {yaml_size:,} bytes")
            print(f"  JSON: {json_size:,} bytes")
            print(f"  💾 JSON is {savings:.1f}% smaller")
    
    return True


def export_json_catalog(crayon, assets_dir):
    """Export catalog as JSON for comparison."""
    json_path = Path(assets_dir) / "catalog.json"
    
    try:
        # Use the catalog's built-in JSON export method
        success = crayon.catalog.save_json_catalog(json_path)
        
        if success:
            print(f"✅ JSON catalog exported: {json_path}")
            print(f"📏 Size: {json_path.stat().st_size:,} bytes")
        else:
            print(f"❌ JSON export failed")
        
    except Exception as e:
        print(f"❌ JSON export failed: {e}")


def search_catalog_example(crayon, query=None, source=None, format_type=None):
    """Demonstrate catalog search functionality."""
    print(f"🔍 Catalog Search Example")
    print("=" * 30)
    
    # Search assets
    results = crayon.catalog.search_assets(
        query=query,
        source=source,
        format=format_type
    )
    
    print(f"📊 Search Results: {len(results)} assets found")
    if query:
        print(f"🔍 Query: '{query}'")
    if source:
        print(f"📂 Source: {source}")
    if format_type:
        print(f"🎨 Format: {format_type}")
    print()
    
    # Show first few results
    for i, asset in enumerate(results[:5], 1):
        print(f"  {i}. {asset['filename']}")
        print(f"     📁 {asset['path']}")
        print(f"     📏 {asset['width']}x{asset['height']} {asset['format']}")
        print(f"     📂 Source: {asset['source']}")
        if asset.get('description'):
            print(f"     📝 {asset['description']}")
        print()
    
    if len(results) > 5:
        print(f"  ... and {len(results) - 5} more assets")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Create and manage asset catalog")
    parser.add_argument("--assets-dir", default="./example_assets", 
                       help="Assets directory to catalog (default: ./example_assets)")
    parser.add_argument("--no-cleanup", action="store_true",
                       help="Skip cleanup step")
    parser.add_argument("--no-rename", action="store_true",
                       help="Skip rename/organize step")
    parser.add_argument("--format", choices=["yaml", "json", "both"], default="both",
                       help="Catalog format (default: both)")
    parser.add_argument("--search", help="Search query for assets")
    parser.add_argument("--source", choices=["ai", "stock", "proprietary", "downloaded"],
                       help="Filter by source")
    parser.add_argument("--format-type", choices=["jpg", "png", "webp", "gif", "svg", "bmp"],
                       help="Filter by format")
    
    args = parser.parse_args()
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir=args.assets_dir)
    
    # Check if assets directory exists
    assets_path = Path(args.assets_dir)
    if not assets_path.exists():
        print(f"❌ Assets directory does not exist: {args.assets_dir}")
        print("💡 Create the directory and add some images first")
        return
    
    # If search arguments provided, do search instead of full catalog
    if args.search or args.source or args.format_type:
        search_catalog_example(crayon, args.search, args.source, args.format_type)
        return
    
    # Create comprehensive catalog
    success = create_catalog_example(
        crayon, 
        args.assets_dir, 
        cleanup=not args.no_cleanup,
        rename=not args.no_rename,
        format=args.format
    )
    
    if success:
        print("🎉 Catalog management completed successfully!")
    else:
        print("❌ Catalog management failed")


def demo_catalog_features():
    """Demonstrate various catalog features."""
    print("🚀 PurpleCrayon Catalog Features Demo")
    print("=" * 40)
    
    # Initialize with example assets
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Check if we have assets
    assets_path = Path("./example_assets")
    if not assets_path.exists():
        print("❌ No example_assets directory found")
        print("💡 Run some scraping examples first to create assets")
        return
    
    print("📚 Available catalog features:")
    print("  1. Cleanup corrupted and junk files")
    print("  2. Rename files with proper naming convention")
    print("  3. Create comprehensive YAML/JSON catalog")
    print("  4. Search assets by query, source, or format")
    print("  5. Export catalog in multiple formats")
    print()
    
    # Show current stats
    stats = crayon.catalog.get_stats()
    print(f"📊 Current catalog stats:")
    print(f"  Total assets: {stats.get('total_assets', 0)}")
    print(f"  By source: {stats.get('by_source', {})}")
    print(f"  By format: {stats.get('by_format', {})}")
    print()
    
    print("💡 Usage examples:")
    print("  python catalog_example.py")
    print("  python catalog_example.py --no-cleanup --format json")
    print("  python catalog_example.py --search 'logo' --source downloaded")
    print("  python catalog_example.py --format-type png")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # No arguments provided, show demo
        demo_catalog_features()
    else:
        main()
