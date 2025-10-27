from __future__ import annotations

import uuid
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image
import re


class AssetCatalog:
    """Manages the YAML-based asset catalog for curated assets."""
    
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Load the YAML catalog file."""
        if not self.catalog_path.exists():
            return {
                "stats": {
                    "total_assets": 0,
                    "by_source": {"ai": 0, "stock": 0, "proprietary": 0, "downloaded": 0},
                    "by_format": {"jpg": 0, "jpeg": 0, "png": 0, "webp": 0, "gif": 0, "ico": 0, "svg": 0, "bmp": 0, "tiff": 0},
                    "by_aspect_ratio": {"square": 0, "landscape": 0, "portrait": 0}
                },
                "assets": []
            }
        
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                # Ensure stats come first
                if "stats" not in data:
                    data["stats"] = {
                        "total_assets": 0,
                        "by_source": {"ai": 0, "stock": 0, "proprietary": 0, "downloaded": 0},
                        "by_format": {"jpg": 0, "jpeg": 0, "png": 0, "webp": 0, "gif": 0, "ico": 0, "svg": 0, "bmp": 0, "tiff": 0},
                        "by_aspect_ratio": {"square": 0, "landscape": 0, "portrait": 0}
                    }
                if "assets" not in data:
                    data["assets"] = []
                return data
        except Exception as e:
            print(f"Error loading catalog: {e}")
            return {
                "stats": {
                    "total_assets": 0,
                    "by_source": {"ai": 0, "stock": 0, "proprietary": 0, "downloaded": 0},
                    "by_format": {"jpg": 0, "jpeg": 0, "png": 0, "webp": 0, "gif": 0, "ico": 0, "svg": 0, "bmp": 0, "tiff": 0},
                    "by_aspect_ratio": {"square": 0, "landscape": 0, "portrait": 0}
                },
                "assets": []
            }
    
    def _save_catalog(self):
        """Save the catalog to YAML file with stats first."""
        try:
            # Ensure stats come first in the YAML
            ordered_catalog = {
                "stats": self.catalog.get("stats", {}),
                "assets": self.catalog.get("assets", [])
            }
            
            with open(self.catalog_path, 'w', encoding='utf-8') as f:
                yaml.dump(ordered_catalog, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Error saving catalog: {e}")
    
    def save_json_catalog(self, json_path: Path = None):
        """Save the catalog to JSON file."""
        if json_path is None:
            json_path = self.catalog_path.with_suffix('.json')
        
        try:
            # Ensure stats come first in the JSON
            ordered_catalog = {
                "stats": self.catalog.get("stats", {}),
                "assets": self.catalog.get("assets", [])
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(ordered_catalog, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving JSON catalog: {e}")
            return False
    
    def _get_image_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract image metadata."""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                aspect_ratio = round(width / height, 2)
                
                # Determine aspect ratio category
                if abs(aspect_ratio - 1.0) < 0.1:
                    aspect_category = "square"
                elif aspect_ratio > 1.0:
                    aspect_category = "landscape"
                else:
                    aspect_category = "portrait"
                
                return {
                    "width": width,
                    "height": height,
                    "format": img.format.lower() if img.format else "unknown",
                    "aspect_ratio": aspect_ratio,
                    "aspect_category": aspect_category,
                    "mode": img.mode,
                    "has_alpha": img.mode in ('RGBA', 'LA')
                }
        except Exception as e:
            print(f"Error reading image {file_path}: {e}")
            return {}
    
    def _determine_source_category(self, file_path: Path) -> str:
        """Determine which assets/ subfolder this belongs to."""
        path_str = str(file_path).lower()
        
        # Check directory structure first
        if "/ai/" in path_str or "\\ai\\" in path_str:
            return "ai"
        elif "/cloned/" in path_str or "\\cloned\\" in path_str:
            return "ai"  # Cloned files are AI-generated alternatives
        elif "/stock/" in path_str or "\\stock\\" in path_str:
            return "stock"
        elif "/proprietary/" in path_str or "\\proprietary\\" in path_str:
            return "proprietary"
        elif "/downloaded/" in path_str or "\\downloaded\\" in path_str:
            return "downloaded"
        
        # Fallback to filename patterns
        if "ai_gemini" in path_str or "ai_" in path_str or "cloned_" in path_str:
            return "ai"
        elif "stock_" in path_str or "unsplash" in path_str or "pexels" in path_str or "pixabay" in path_str:
            return "stock"
        elif "proprietary" in path_str:
            return "proprietary"
        else:
            return "downloaded"
    
    def _generate_description(self, filename: str, image_info: Dict[str, Any]) -> str:
        """Generate a description based on filename and image content."""
        # Remove extension and common prefixes
        name = Path(filename).stem
        name = re.sub(r'^(stock_|ai_|proprietary_|downloaded_)', '', name)
        
        # Extract meaningful words
        words = re.findall(r'[a-zA-Z]+', name)
        
        if len(words) >= 2:
            return ' '.join(words[:3]).replace('_', ' ')
        else:
            return f"Image asset ({image_info.get('format', 'unknown')} format)"
    
    def _generate_tags(self, filename: str, description: str) -> List[str]:
        """Generate tags based on filename and description."""
        tags = []
        
        # Extract from filename
        name = Path(filename).stem.lower()
        if "panda" in name:
            tags.extend(["panda", "wildlife", "nature"])
        if "bamboo" in name:
            tags.extend(["bamboo", "forest"])
        if "wallpaper" in name:
            tags.append("wallpaper")
        if "artistic" in name:
            tags.append("artistic")
        
        # Extract from description
        desc_lower = description.lower()
        if "panda" in desc_lower:
            tags.extend(["panda", "wildlife"])
        if "bamboo" in desc_lower:
            tags.extend(["bamboo", "forest"])
        
        # Add format tag
        if filename.lower().endswith('.png'):
            tags.append("png")
        elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            tags.append("jpg")
        
        return list(set(tags))  # Remove duplicates
    
    def add_asset(self, file_path: Path, source: str = None, license: str = None, quality_score: float = None, match_score: float = None) -> str:
        """Add a new asset to the catalog or update existing one."""
        if not file_path.exists():
            raise FileNotFoundError(f"Asset file not found: {file_path}")
        
        relative_path = str(file_path.relative_to(self.catalog_path.parent))
        
        # Check if asset already exists by path
        existing_asset = None
        for asset in self.catalog["assets"]:
            if asset["path"] == relative_path:
                existing_asset = asset
                break
        
        if existing_asset:
            print(f"  🔄 Updating existing asset: {relative_path}")
            # Update existing asset
            image_info = self._get_image_info(file_path)
            if not image_info:
                raise ValueError(f"Could not read image: {file_path}")
            
            # Re-determine source category if not provided
            if source is None:
                source = self._determine_source_category(file_path)
            
            # Update the existing asset
            existing_asset.update({
                "filename": file_path.name,
                "width": image_info["width"],
                "height": image_info["height"],
                "format": image_info["format"],
                "source": source,
                "aspect_ratio": image_info["aspect_ratio"],
                "aspect_category": image_info["aspect_category"],
                "has_alpha": image_info.get("has_alpha", False),
                "date_modified": datetime.now().isoformat() + "Z"
            })
            
            if quality_score is not None:
                existing_asset["quality_score"] = quality_score
            if match_score is not None:
                existing_asset["match_score"] = match_score
            
            self._update_stats()
            self._save_catalog()
            return "existing"
        
        # Create new asset
        print(f"  ➕ Creating new asset: {relative_path}")
        image_info = self._get_image_info(file_path)
        if not image_info:
            raise ValueError(f"Could not read image: {file_path}")
        
        # Determine source category
        if source is None:
            source = self._determine_source_category(file_path)
        
        # Generate description and tags
        description = self._generate_description(file_path.name, image_info)
        tags = self._generate_tags(file_path.name, description)
        
        # Create asset entry (no ID field, path is unique identifier)
        asset = {
            "filename": file_path.name,
            "path": relative_path,
            "description": description,
            "tags": tags,
            "width": image_info["width"],
            "height": image_info["height"],
            "format": image_info["format"],
            "source": source,
            "aspect_ratio": image_info["aspect_ratio"],
            "aspect_category": image_info["aspect_category"],
            "has_alpha": image_info.get("has_alpha", False),
            "date_created": datetime.now().isoformat() + "Z",
            "date_modified": datetime.now().isoformat() + "Z",
            "license": license or "unknown",
            "quality_score": quality_score,
            "match_score": match_score
        }
        
        # Add to catalog
        self.catalog["assets"].append(asset)
        self._update_stats()
        self._save_catalog()
        
        return "new"
    
    def update_asset_by_path(self, asset_path: str, updates: Dict[str, Any]) -> bool:
        """Update an existing asset by path."""
        for asset in self.catalog["assets"]:
            if asset["path"] == asset_path:
                asset.update(updates)
                asset["date_modified"] = datetime.now().isoformat() + "Z"
                self._update_stats()
                self._save_catalog()
                return True
        return False
    
    def remove_asset_by_path(self, asset_path: str) -> bool:
        """Remove an asset from the catalog by path."""
        for i, asset in enumerate(self.catalog["assets"]):
            if asset["path"] == asset_path:
                del self.catalog["assets"][i]
                self._update_stats()
                self._save_catalog()
                return True
        return False
    
    def get_asset_by_path(self, asset_path: str) -> Optional[Dict[str, Any]]:
        """Get asset by path."""
        for asset in self.catalog["assets"]:
            if asset["path"] == asset_path:
                return asset
        return None
    
    def search_assets(self, query: str = None, tags: List[str] = None, source: str = None, format: str = None) -> List[Dict[str, Any]]:
        """Search assets by query, tags, source, or format."""
        results = []
        
        for asset in self.catalog["assets"]:
            match = True
            
            if query:
                query_lower = query.lower()
                if not (query_lower in asset["description"].lower() or 
                       query_lower in asset["filename"].lower()):
                    match = False
            
            if tags:
                if not any(tag.lower() in [t.lower() for t in asset["tags"]] for tag in tags):
                    match = False
            
            if source and asset["source"] != source:
                match = False
            
            if format and asset["format"] != format.lower():
                match = False
            
            if match:
                results.append(asset)
        
        return results
    
    def _update_stats(self):
        """Update catalog statistics."""
        assets = self.catalog["assets"]
        
        # Reset stats
        stats = {
            "total_assets": len(assets),
            "by_source": {"ai": 0, "stock": 0, "proprietary": 0, "downloaded": 0},
            "by_format": {"jpg": 0, "jpeg": 0, "png": 0, "webp": 0, "gif": 0, "ico": 0, "svg": 0, "bmp": 0, "tiff": 0},
            "by_aspect_ratio": {"square": 0, "landscape": 0, "portrait": 0}
        }
        
        for asset in assets:
            # Count by source
            source = asset.get("source", "downloaded")
            if source in stats["by_source"]:
                stats["by_source"][source] += 1
            
            # Count by format
            format_type = asset.get("format", "unknown")
            if format_type in stats["by_format"]:
                stats["by_format"][format_type] += 1
            
            # Count by aspect ratio
            aspect_category = asset.get("aspect_category", "unknown")
            if aspect_category in stats["by_aspect_ratio"]:
                stats["by_aspect_ratio"][aspect_category] += 1
        
        self.catalog["stats"] = stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get catalog statistics."""
        return self.catalog.get("stats", {})
    
    def scan_and_update_assets(self, assets_dir: Path) -> Dict[str, int]:
        """Scan assets directory and update catalog with new/renamed files."""
        if not assets_dir.exists():
            return {"added": 0, "updated": 0, "errors": 0}
        
        added = 0
        updated = 0
        errors = 0
        
        # Get existing assets by path
        existing_paths = {asset["path"]: asset for asset in self.catalog["assets"]}
        
        # Scan all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg'}
        
        for file_path in assets_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                try:
                    rel_path = str(file_path.relative_to(assets_dir))
                    
                    if rel_path in existing_paths:
                        # Check if file was renamed
                        existing_asset = existing_paths[rel_path]
                        if existing_asset["filename"] != file_path.name:
                            # Update filename
                            self.update_asset_by_path(rel_path, {"filename": file_path.name})
                            updated += 1
                    else:
                        # New asset
                        result = self.add_asset(file_path)
                        if result == "new":
                            added += 1
                        else:
                            updated += 1
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    errors += 1
        
        return {"added": added, "updated": updated, "errors": errors}
    
    def update_catalog_from_assets(self, assets_dir: Path) -> Dict[str, int]:
        """Update catalog by completely rescanning the assets directory."""
        if not assets_dir.exists():
            return {"added": 0, "updated": 0, "errors": 0, "removed": 0}
        
        print("📊 Rescanning assets directory and rebuilding catalog...")
        
        # Get all current assets by path for comparison
        current_assets = {asset["path"]: asset for asset in self.catalog["assets"]}
        
        # Scan all image files in assets directory
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg'}
        found_files = {}
        
        added = 0
        updated = 0
        errors = 0
        
        # First pass: collect all current files
        for file_path in assets_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                try:
                    rel_path = str(file_path.relative_to(assets_dir))
                    found_files[rel_path] = file_path
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    errors += 1
        
        # Second pass: update or add assets
        for rel_path, file_path in found_files.items():
            try:
                if rel_path in current_assets:
                    # File exists in catalog, check if it needs updating
                    existing_asset = current_assets[rel_path]
                    if existing_asset["filename"] != file_path.name:
                        # Update the existing asset with new filename
                        self.update_asset_by_path(rel_path, {"filename": file_path.name})
                        updated += 1
                else:
                    # New file, add to catalog
                    print(f"  📝 Adding new asset: {rel_path}")
                    result = self.add_asset(file_path)
                    if result == "new":
                        added += 1
                    else:
                        updated += 1
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                errors += 1
        
        # Third pass: remove assets that no longer exist
        removed = 0
        for asset_path, asset in current_assets.items():
            if asset_path not in found_files:
                self.remove_asset_by_path(asset_path)
                removed += 1
        
        print(f"📊 Catalog rescan complete: {added} added, {updated} updated, {removed} removed, {errors} errors")
        return {"added": added, "updated": updated, "removed": removed, "errors": errors}
    
    def rebuild_catalog_from_scratch(self, assets_dir: Path) -> Dict[str, int]:
        """Completely rebuild the catalog from scratch by scanning all files."""
        if not assets_dir.exists():
            return {"added": 0, "errors": 0}
        
        print("🔄 Completely rebuilding catalog from scratch...")
        
        # Clear existing catalog
        self.catalog["assets"] = []
        self._update_stats()
        
        # Scan all image files and add them
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg'}
        added = 0
        errors = 0
        
        for file_path in assets_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                try:
                    result = self.add_asset(file_path)
                    if result == "new":
                        added += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    errors += 1
        
        print(f"📊 Catalog rebuild complete: {added} assets added, {errors} errors")
        return {"added": added, "errors": errors}
    
    def cleanup_and_update_catalog(self, assets_dir: Path, remove_junk: bool = True, format: str = "both") -> Dict[str, int]:
        """Clean up corrupted/junk images and update catalog."""
        from .image_validation_tools import cleanup_corrupted_images
        
        print("🧹 Cleaning up corrupted and junk images...")
        print("=" * 50)
        
        # Clean up the assets directory
        cleanup_stats = cleanup_corrupted_images(str(assets_dir), remove_junk)
        
        print("=" * 50)
        print("📊 Cleanup Results:")
        print(f"  ✅ Valid images: {cleanup_stats['valid']}")
        print(f"  ❌ Corrupted images removed: {cleanup_stats['corrupted']}")
        if remove_junk:
            print(f"  🗑️ Junk files removed: {cleanup_stats['junk']}")
        print(f"  ⚠️ Errors: {cleanup_stats['errors']}")
        
        # Now update the catalog
        print("\n📊 Updating catalog after cleanup...")
        catalog_stats = self.update_catalog_from_assets(assets_dir)
        
        # Export in requested format(s)
        if format.lower() in ["yaml", "both"]:
            self._save_catalog()
        
        if format.lower() in ["json", "both"]:
            json_path = assets_dir / "catalog.json"
            self.save_json_catalog(json_path)
        
        # Combine stats
        total_removed = cleanup_stats['corrupted'] + cleanup_stats.get('junk', 0)
        return {
            "valid": cleanup_stats['valid'],
            "corrupted": cleanup_stats['corrupted'],
            "junk": cleanup_stats.get('junk', 0),
            "cleanup_errors": cleanup_stats['errors'],
            "catalog_added": catalog_stats['added'],
            "catalog_updated": catalog_stats['updated'],
            "catalog_removed": catalog_stats['removed'],
            "catalog_errors": catalog_stats['errors'],
            "total_removed": total_removed
        }


def scan_assets_directory(assets_dir: Path = None) -> Dict[str, int]:
    """Scan the assets directory and update the catalog."""
    if assets_dir is None:
        assets_dir = Path("assets")
    
    catalog_path = assets_dir / "catalog.yaml"
    catalog = AssetCatalog(catalog_path)
    
    return catalog.scan_and_update_assets(assets_dir)
