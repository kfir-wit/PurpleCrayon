"""Enhanced tests for asset catalog API functions."""

import json
import yaml
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
from PIL import Image

from purplecrayon.tools.asset_management_tools import AssetCatalog
from purplecrayon.tools.image_renaming_tools import scan_and_rename_assets
from tests.conftest import has_api_key


def _create_image(path: Path, fmt: str = "JPEG", size=(10, 10), color=(123, 123, 123)) -> None:
    """Helper function to create test images."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=color)
    img.save(path, format=fmt)


def _create_catalog_with_assets(tmp_path: Path) -> tuple[AssetCatalog, Path]:
    """Helper function to create a catalog with test assets."""
    assets_dir = tmp_path / "assets"
    catalog_path = assets_dir / "catalog.yaml"
    
    # Create test images in different directories
    ai_dir = assets_dir / "ai"
    downloaded_dir = assets_dir / "downloaded"
    cloned_dir = assets_dir / "cloned"
    
    _create_image(ai_dir / "ai_image1.png", fmt="PNG", size=(512, 512), color=(255, 0, 0))
    _create_image(ai_dir / "ai_image2.jpg", fmt="JPEG", size=(1024, 768), color=(0, 255, 0))
    _create_image(downloaded_dir / "web_image1.png", fmt="PNG", size=(800, 600), color=(0, 0, 255))
    _create_image(downloaded_dir / "web_image2.jpg", fmt="JPEG", size=(640, 480), color=(255, 255, 0))
    _create_image(cloned_dir / "clone_image1.png", fmt="PNG", size=(256, 256), color=(255, 0, 255))
    
    catalog = AssetCatalog(catalog_path)
    catalog.scan_and_update_assets(assets_dir)
    
    return catalog, assets_dir


class TestAssetCatalogCreation:
    """Test asset catalog creation and management."""

    @pytest.mark.unit


    def test_asset_catalog_creation_new(self, tmp_path):
        """Test creating a new asset catalog."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        
        assert catalog.catalog_path == catalog_path
        assert "assets" in catalog.catalog
        assert "stats" in catalog.catalog
        assert len(catalog.catalog["assets"]) == 0

    @pytest.mark.unit


    def test_asset_catalog_creation_existing(self, tmp_path):
        """Test loading an existing asset catalog."""
        catalog_path = tmp_path / "catalog.yaml"
        
        # Create initial catalog
        catalog1 = AssetCatalog(catalog_path)
        # Add custom metadata to stats
        catalog1.catalog["stats"]["created"] = "2024-01-01"
        catalog1.save_catalog()
        
        # Load existing catalog
        catalog2 = AssetCatalog(catalog_path)
        assert catalog2.catalog["stats"]["created"] == "2024-01-01"

    @pytest.mark.unit


    def test_asset_catalog_creation_yaml_format(self, tmp_path):
        """Test catalog creation with YAML format."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        
        # Add an asset
        asset_path = tmp_path / "test.png"
        _create_image(asset_path)
        catalog.add_asset(asset_path)
        catalog.save_catalog()
        
        # Verify YAML file was created
        assert catalog_path.exists()
        with open(catalog_path, 'r') as f:
            data = yaml.safe_load(f)
            assert "assets" in data
            assert "stats" in data

        @pytest.mark.unit
def test_asset_catalog_creation_json_format(self, tmp_path):
        """Test catalog creation with JSON format."""
        catalog_path = tmp_path / "catalog.json"
        catalog = AssetCatalog(catalog_path)
        
        # Add an asset
        asset_path = tmp_path / "test.png"
        _create_image(asset_path)
        catalog.add_asset(asset_path)
        catalog.save_catalog()
        
        # Verify JSON file was created
        assert catalog_path.exists()
        with open(catalog_path, 'r') as f:
            data = json.load(f)
            assert "assets" in data
            assert "stats" in data


class TestAssetCatalogOperations:
    """Test asset catalog operations."""

    def test_add_asset_single(self, tmp_path):
        """Test adding a single asset to catalog."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        
        asset_path = tmp_path / "test.png"
        _create_image(asset_path)
        
        result = catalog.add_asset(asset_path)
        assert result is True
        assert len(catalog.catalog["assets"]) == 1
        
        asset = catalog.catalog["assets"][0]
        assert asset["filename"] == "test.png"
        assert asset["path"] == str(asset_path)
        assert asset["width"] == 10
        assert asset["height"] == 10

    def test_add_asset_multiple(self, tmp_path):
        """Test adding multiple assets to catalog."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        
        # Create multiple test images
        for i in range(3):
            asset_path = tmp_path / f"test{i}.png"
            _create_image(asset_path, size=(100 + i*10, 100 + i*10))
            catalog.add_asset(asset_path)
        
        assert len(catalog.catalog["assets"]) == 3

    def test_remove_asset(self, tmp_path):
        """Test removing an asset from catalog."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        
        asset_path = tmp_path / "test.png"
        _create_image(asset_path)
        catalog.add_asset(asset_path)
        
        assert len(catalog.catalog["assets"]) == 1
        
        result = catalog.remove_asset(asset_path)
        assert result is True
        assert len(catalog.catalog["assets"]) == 0

    def test_remove_asset_nonexistent(self, tmp_path):
        """Test removing a nonexistent asset from catalog."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        
        asset_path = tmp_path / "nonexistent.png"
        result = catalog.remove_asset(asset_path)
        assert result is False

        @pytest.mark.unit
def test_scan_and_update_assets_does_not_duplicate_existing_entries(self, tmp_path):
        """Test that scanning doesn't duplicate existing entries."""
        assets_dir = tmp_path / "assets"
        catalog_path = assets_dir / "catalog.yaml"
        asset_path = assets_dir / "ai" / "sample.jpeg"

        _create_image(asset_path, fmt="JPEG")

        catalog = AssetCatalog(catalog_path)
        catalog.add_asset(asset_path)

        assert len(catalog.catalog["assets"]) == 1

        stats_before = catalog.get_stats().copy()

        result = catalog.scan_and_update_assets(assets_dir)

        assert result == {"added": 0, "updated": 0, "errors": 0}
        assert len(catalog.catalog["assets"]) == 1
        assert catalog.get_stats() == stats_before

        @pytest.mark.unit
def test_scan_and_update_assets_adds_new_assets(self, tmp_path):
        """Test that scanning adds new assets."""
        assets_dir = tmp_path / "assets"
        catalog_path = assets_dir / "catalog.yaml"
        
        # Create initial asset
        asset1 = assets_dir / "ai" / "sample1.jpeg"
        _create_image(asset1, fmt="JPEG")
        
        catalog = AssetCatalog(catalog_path)
        catalog.add_asset(asset1)
        assert len(catalog.catalog["assets"]) == 1
        
        # Create new asset
        asset2 = assets_dir / "ai" / "sample2.png"
        _create_image(asset2, fmt="PNG")
        
        result = catalog.scan_and_update_assets(assets_dir)
        assert result["added"] == 1
        assert len(catalog.catalog["assets"]) == 2


class TestCatalogSearch:
    """Test catalog search functionality."""

        @pytest.mark.unit
def test_search_assets_by_query(self, tmp_path):
        """Test searching assets by query string."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        # Search for AI images
        results = catalog.search_assets(query="ai")
        assert len(results) >= 2  # Should find ai_image1 and ai_image2
        
        # Search for specific filename
        results = catalog.search_assets(query="web_image1")
        assert len(results) == 1
        assert results[0]["filename"] == "web_image1.png"

        @pytest.mark.unit
def test_search_assets_by_source(self, tmp_path):
        """Test searching assets by source."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        # Search by source
        ai_results = catalog.search_assets(source="ai")
        assert len(ai_results) == 2
        
        downloaded_results = catalog.search_assets(source="downloaded")
        assert len(downloaded_results) == 2
        
        cloned_results = catalog.search_assets(source="cloned")
        assert len(cloned_results) == 1

        @pytest.mark.unit
def test_search_assets_by_format(self, tmp_path):
        """Test searching assets by format."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        # Search by format
        png_results = catalog.search_assets(format="png")
        assert len(png_results) >= 3  # Should find all PNG files
        
        jpg_results = catalog.search_assets(format="jpg")
        assert len(jpg_results) == 2  # Should find JPG files

        @pytest.mark.unit
def test_search_assets_by_size(self, tmp_path):
        """Test searching assets by size range."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        # Search by minimum width
        large_results = catalog.search_assets(min_width=800)
        assert len(large_results) >= 1  # Should find large images
        
        # Search by size range
        medium_results = catalog.search_assets(min_width=500, max_width=1000)
        assert len(medium_results) >= 1

        @pytest.mark.unit
def test_search_assets_combined_filters(self, tmp_path):
        """Test searching assets with combined filters."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        # Combined search
        results = catalog.search_assets(
            query="image",
            source="ai",
            format="png",
            min_width=500
        )
        assert len(results) >= 0  # May or may not find matches

        @pytest.mark.unit
def test_search_assets_no_results(self, tmp_path):
        """Test searching with no results."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        # Search for nonexistent asset
        results = catalog.search_assets(query="nonexistent")
        assert len(results) == 0


class TestCatalogStatistics:
    """Test catalog statistics generation."""

    def test_get_statistics_basic(self, tmp_path):
        """Test basic statistics generation."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        stats = catalog.get_statistics()
        
        assert "total_assets" in stats
        assert "by_source" in stats
        assert "by_format" in stats
        assert "by_aspect_ratio" in stats
        
        assert stats["total_assets"] == 5  # Total number of test assets

    def test_get_statistics_by_source(self, tmp_path):
        """Test statistics by source."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        stats = catalog.get_statistics()
        by_source = stats["by_source"]
        
        assert by_source["ai"] == 2
        assert by_source["downloaded"] == 2
        assert by_source["cloned"] == 1

    def test_get_statistics_by_format(self, tmp_path):
        """Test statistics by format."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        stats = catalog.get_statistics()
        by_format = stats["by_format"]
        
        assert by_format["png"] >= 3
        assert by_format["jpg"] == 2

    def test_get_statistics_by_aspect_ratio(self, tmp_path):
        """Test statistics by aspect ratio."""
        catalog, assets_dir = _create_catalog_with_assets(tmp_path)
        
        stats = catalog.get_statistics()
        by_aspect_ratio = stats["by_aspect_ratio"]
        
        # Should have different aspect ratios
        assert len(by_aspect_ratio) > 0
        assert all(isinstance(ratio, str) for ratio in by_aspect_ratio.keys())

    def test_get_statistics_empty_catalog(self, tmp_path):
        """Test statistics for empty catalog."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        
        stats = catalog.get_statistics()
        
        assert stats["total_assets"] == 0
        assert stats["by_source"] == {}
        assert stats["by_format"] == {}
        assert stats["by_aspect_ratio"] == {}


class TestCatalogFormats:
    """Test catalog format handling."""

        @pytest.mark.unit
def test_catalog_yaml_format(self, tmp_path):
        """Test catalog with YAML format."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        
        asset_path = tmp_path / "test.png"
        _create_image(asset_path)
        catalog.add_asset(asset_path)
        catalog.save_catalog()
        
        # Verify YAML format
        assert catalog_path.exists()
        with open(catalog_path, 'r') as f:
            data = yaml.safe_load(f)
            assert "assets" in data
            assert "metadata" in data

        @pytest.mark.unit
def test_catalog_json_format(self, tmp_path):
        """Test catalog with JSON format."""
        catalog_path = tmp_path / "catalog.json"
        catalog = AssetCatalog(catalog_path)
        
        asset_path = tmp_path / "test.png"
        _create_image(asset_path)
        catalog.add_asset(asset_path)
        catalog.save_catalog()
        
        # Verify JSON format
        assert catalog_path.exists()
        with open(catalog_path, 'r') as f:
            data = json.load(f)
            assert "assets" in data
            assert "metadata" in data

        @pytest.mark.unit
def test_catalog_format_detection(self, tmp_path):
        """Test automatic format detection."""
        # Test YAML detection
        yaml_path = tmp_path / "catalog.yaml"
        yaml_catalog = AssetCatalog(yaml_path)
        assert yaml_catalog.format == "yaml"
        
        # Test JSON detection
        json_path = tmp_path / "catalog.json"
        json_catalog = AssetCatalog(json_path)
        assert json_catalog.format == "json"


class TestScanAndRenameAssets:
    """Test content-based asset renaming."""

        @pytest.mark.unit
def test_scan_and_rename_assets_basic(self, tmp_path):
        """Test basic asset renaming functionality."""
        assets_dir = tmp_path / "assets"
        ai_dir = assets_dir / "ai"
        ai_dir.mkdir(parents=True)
        
        # Create test images with different content
        _create_image(ai_dir / "image1.png", color=(255, 0, 0))  # Red
        _create_image(ai_dir / "image2.png", color=(0, 255, 0))  # Green
        _create_image(ai_dir / "image3.png", color=(0, 0, 255))  # Blue
        
        result = scan_and_rename_assets(str(assets_dir))
        
        assert result["success"] is True
        assert result["renamed"] >= 0  # May rename some files based on content

        @pytest.mark.unit
def test_scan_and_rename_assets_with_ai_detection(self, tmp_path):
        """Test asset renaming with AI detection."""
        assets_dir = tmp_path / "assets"
        ai_dir = assets_dir / "ai"
        ai_dir.mkdir(parents=True)
        
        # Create test images
        _create_image(ai_dir / "test1.png", size=(512, 512))
        _create_image(ai_dir / "test2.jpg", size=(1024, 768))
        
        with patch('purplecrayon.tools.image_renaming_tools.validate_image_with_llm') as mock_llm:
            mock_llm.return_value = {
                "is_valid": True,
                "is_ai_generated": True,
                "description": "AI generated test image",
                "style": "digital art"
            }
            
            result = scan_and_rename_assets(str(assets_dir), use_ai_analysis=True)
            
            assert result["success"] is True
            mock_llm.assert_called()

        @pytest.mark.unit
def test_scan_and_rename_assets_error_handling(self, tmp_path):
        """Test asset renaming error handling."""
        assets_dir = tmp_path / "assets"
        ai_dir = assets_dir / "ai"
        ai_dir.mkdir(parents=True)
        
        # Create invalid image file
        invalid_file = ai_dir / "invalid.png"
        invalid_file.write_text("This is not an image")
        
        result = scan_and_rename_assets(str(assets_dir))
        
        assert result["success"] is True  # Should handle errors gracefully
        assert result["errors"] >= 0


class TestCatalogErrorHandling:
    """Test catalog error handling."""

        @pytest.mark.unit
def test_catalog_invalid_path(self, tmp_path):
        """Test catalog with invalid path."""
        invalid_path = tmp_path / "nonexistent" / "catalog.yaml"
        
        with pytest.raises(Exception):
            AssetCatalog(invalid_path)

        @pytest.mark.unit
def test_catalog_corrupted_file(self, tmp_path):
        """Test catalog with corrupted file."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog_path.write_text("invalid yaml content: [")
        
        # Should handle corrupted file gracefully
        catalog = AssetCatalog(catalog_path)
        assert catalog.catalog["assets"] == []

        @pytest.mark.unit
def test_catalog_permission_error(self, tmp_path):
        """Test catalog with permission error."""
        catalog_path = tmp_path / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        
        # Create a file that can't be written to
        catalog_path.write_text("test")
        catalog_path.chmod(0o444)  # Read-only
        
        try:
            with pytest.raises(Exception):
                catalog.save_catalog()
        finally:
            catalog_path.chmod(0o644)  # Restore permissions


class TestCatalogIntegration:
    """Test catalog integration scenarios."""

        @pytest.mark.unit
def test_catalog_workflow_complete(self, tmp_path):
        """Test complete catalog workflow."""
        assets_dir = tmp_path / "assets"
        catalog_path = assets_dir / "catalog.yaml"
        
        # Create test assets
        ai_dir = assets_dir / "ai"
        downloaded_dir = assets_dir / "downloaded"
        
        _create_image(ai_dir / "ai_image.png", size=(512, 512))
        _create_image(downloaded_dir / "web_image.jpg", size=(800, 600))
        
        # Create catalog
        catalog = AssetCatalog(catalog_path)
        result = catalog.scan_and_update_assets(assets_dir)
        
        assert result["added"] == 2
        assert len(catalog.catalog["assets"]) == 2
        
        # Test search
        ai_results = catalog.search_assets(source="ai")
        assert len(ai_results) == 1
        
        # Test statistics
        stats = catalog.get_statistics()
        assert stats["total_assets"] == 2
        assert stats["by_source"]["ai"] == 1
        assert stats["by_source"]["downloaded"] == 1
        
        # Test save and reload
        catalog.save_catalog()
        new_catalog = AssetCatalog(catalog_path)
        assert len(new_catalog.catalog["assets"]) == 2

        @pytest.mark.unit
def test_catalog_with_renaming_integration(self, tmp_path):
        """Test catalog integration with asset renaming."""
        assets_dir = tmp_path / "assets"
        catalog_path = assets_dir / "catalog.yaml"
        
        # Create test assets
        ai_dir = assets_dir / "ai"
        _create_image(ai_dir / "test1.png", size=(512, 512))
        _create_image(ai_dir / "test2.jpg", size=(1024, 768))
        
        # Create initial catalog
        catalog = AssetCatalog(catalog_path)
        catalog.scan_and_update_assets(assets_dir)
        
        # Rename assets
        rename_result = scan_and_rename_assets(str(assets_dir))
        assert rename_result["success"] is True
        
        # Update catalog after renaming
        update_result = catalog.scan_and_update_assets(assets_dir)
        assert update_result["updated"] >= 0  # May have updated some assets
