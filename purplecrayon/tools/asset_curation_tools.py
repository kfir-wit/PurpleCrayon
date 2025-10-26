from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .asset_management_tools import AssetCatalog


def curate_downloads_to_assets(downloads_dir: Path, assets_dir: Path, validation_results: List[Dict] = None) -> Dict[str, int]:
    """
    Move curated files from downloads/ to assets/ with proper organization.
    
    Args:
        downloads_dir: Path to downloads directory
        assets_dir: Path to assets directory  
        validation_results: LLM validation results with match scores
        
    Returns:
        Dict with curation statistics
    """
    if not downloads_dir.exists():
        return {"moved": 0, "errors": 0}
    
    # Ensure assets subdirectories exist
    for subdir in ["ai", "stock", "proprietary", "downloaded"]:
        (assets_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Initialize catalog
    catalog_path = assets_dir / "catalog.yaml"
    catalog = AssetCatalog(catalog_path)
    
    moved_count = 0
    error_count = 0
    
    # Create validation lookup
    validation_lookup = {}
    if validation_results:
        for result in validation_results:
            path = result.get("path", "")
            if path:
                validation_lookup[Path(path).name] = result
    
    # Process each downloads subdirectory
    for source_dir in [downloads_dir / "stock", downloads_dir / "ai", downloads_dir / "final", downloads_dir / "downloaded"]:
        if not source_dir.exists():
            continue
            
        print(f"\n📁 Processing {source_dir.name}/ directory...")
        
        for file_path in source_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}:
                try:
                    # Determine target subdirectory
                    if source_dir.name == "ai":
                        target_subdir = "ai"
                    elif source_dir.name == "stock":
                        target_subdir = "stock"
                    elif source_dir.name == "downloaded":
                        target_subdir = "downloaded"
                    else:  # final
                        target_subdir = "downloaded"
                    
                    # Create target path
                    target_path = assets_dir / target_subdir / file_path.name
                    
                    # Handle filename conflicts
                    counter = 1
                    original_target = target_path
                    while target_path.exists():
                        stem = original_target.stem
                        suffix = original_target.suffix
                        target_path = original_target.parent / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    # Move file
                    shutil.move(str(file_path), str(target_path))
                    print(f"  ✅ Moved: {file_path.name} -> assets/{target_subdir}/")
                    
                    # Get validation data if available
                    validation_data = validation_lookup.get(file_path.name, {})
                    quality_score = validation_data.get("match_score")
                    match_score = validation_data.get("match_score")
                    
                    # Add to catalog
                    try:
                        catalog.add_asset(
                            target_path,
                            source=target_subdir,
                            quality_score=quality_score,
                            match_score=match_score
                        )
                        print(f"  📝 Added to catalog")
                    except Exception as e:
                        print(f"  ⚠️ Could not add to catalog: {e}")
                    
                    moved_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Error moving {file_path.name}: {e}")
                    error_count += 1
    
    # Clean up empty directories
    for subdir in [downloads_dir / "stock", downloads_dir / "ai", downloads_dir / "final"]:
        if subdir.exists() and not any(subdir.iterdir()):
            subdir.rmdir()
            print(f"  🗑️ Removed empty directory: {subdir.name}")
    
    return {
        "moved": moved_count,
        "errors": error_count
    }


def organize_assets_by_quality(assets_dir: Path, min_score: float = 0.7) -> Dict[str, int]:
    """
    Organize assets by moving high-quality ones to appropriate folders.
    
    Args:
        assets_dir: Path to assets directory
        min_score: Minimum quality score for organization
        
    Returns:
        Dict with organization statistics
    """
    catalog_path = assets_dir / "catalog.yaml"
    catalog = AssetCatalog(catalog_path)
    
    organized_count = 0
    error_count = 0
    
    # Get high-quality assets
    high_quality_assets = []
    for asset in catalog.catalog["assets"]:
        quality_score = asset.get("quality_score", 0)
        match_score = asset.get("match_score", 0)
        
        if quality_score >= min_score or match_score >= min_score:
            high_quality_assets.append(asset)
    
    print(f"📊 Found {len(high_quality_assets)} high-quality assets (score >= {min_score})")
    
    for asset in high_quality_assets:
        try:
            current_path = assets_dir / asset["path"]
            if not current_path.exists():
                continue
            
            # Determine if it should be moved to a better category
            current_source = asset["source"]
            quality_score = asset.get("quality_score", 0)
            match_score = asset.get("match_score", 0)
            
            # Move high-quality AI images to ai/
            if current_source == "downloaded" and "ai_" in asset["filename"] and quality_score >= 0.8:
                target_path = assets_dir / "ai" / current_path.name
                if not target_path.exists():
                    shutil.move(str(current_path), str(target_path))
                    catalog.update_asset(asset["id"], {"source": "ai", "path": str(target_path.relative_to(assets_dir))})
                    print(f"  ✅ Moved AI image to ai/: {current_path.name}")
                    organized_count += 1
            
            # Move high-quality stock images to stock/
            elif current_source == "downloaded" and "stock_" in asset["filename"] and quality_score >= 0.8:
                target_path = assets_dir / "stock" / current_path.name
                if not target_path.exists():
                    shutil.move(str(current_path), str(target_path))
                    catalog.update_asset(asset["id"], {"source": "stock", "path": str(target_path.relative_to(assets_dir))})
                    print(f"  ✅ Moved stock image to stock/: {current_path.name}")
                    organized_count += 1
                    
        except Exception as e:
            print(f"  ❌ Error organizing {asset.get('filename', 'unknown')}: {e}")
            error_count += 1
    
    return {
        "organized": organized_count,
        "errors": error_count
    }


def get_asset_recommendations(assets_dir: Path, query: str = None) -> List[Dict]:
    """
    Get asset recommendations based on query and quality scores.
    
    Args:
        assets_dir: Path to assets directory
        query: Search query
        
    Returns:
        List of recommended assets sorted by quality
    """
    catalog_path = assets_dir / "catalog.yaml"
    catalog = AssetCatalog(catalog_path)
    
    # Search assets
    if query:
        assets = catalog.search_assets(query=query)
    else:
        assets = catalog.catalog["assets"]
    
    # Sort by quality score
    assets.sort(key=lambda x: (x.get("quality_score", 0) + x.get("match_score", 0)) / 2, reverse=True)
    
    return assets[:10]  # Return top 10
