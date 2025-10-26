#!/usr/bin/env python3
"""
Standalone script to update the asset catalog.
Usage: python -m src.utils.update_catalog
"""

from pathlib import Path
from ..tools.asset_management_tools import AssetCatalog


def main():
    assets_dir = Path("assets")
    catalog_path = assets_dir / "catalog.yaml"
    
    if not assets_dir.exists():
        print("❌ Assets directory does not exist: assets/")
        print("💡 Create the assets directory first")
        return
    
    print("📊 Updating asset catalog...")
    print("=" * 50)
    
    catalog = AssetCatalog(catalog_path)
    stats = catalog.update_catalog_from_assets(assets_dir)
    
    print("=" * 50)
    print(f"📊 Catalog Update Results:")
    print(f"  ✅ Added: {stats['added']}")
    print(f"  🔄 Updated: {stats['updated']}")
    print(f"  🗑️ Removed: {stats['removed']}")
    print(f"  ❌ Errors: {stats['errors']}")
    
    # Show current stats
    current_stats = catalog.get_stats()
    print(f"\n📈 Current Catalog Stats:")
    print(f"  Total assets: {current_stats.get('total_assets', 0)}")
    print(f"  By source: {current_stats.get('by_source', {})}")
    print(f"  By format: {current_stats.get('by_format', {})}")
    print(f"  By aspect ratio: {current_stats.get('by_aspect_ratio', {})}")


if __name__ == "__main__":
    main()
