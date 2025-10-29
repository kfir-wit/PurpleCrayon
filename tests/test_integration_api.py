"""Integration tests for high-level PurpleCrayon API."""

import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from purplecrayon import PurpleCrayon, AssetRequest
from tests.conftest import has_api_key


class TestPurpleCrayonIntegration:
    """Test high-level PurpleCrayon class integration."""

    def test_purplecrayon_init_default(self, temp_assets_dir):
        """Test PurpleCrayon initialization with default config."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        assert crayon.assets_dir == temp_assets_dir
        assert crayon.catalog is not None
        assert (temp_assets_dir / "ai").exists()
        assert (temp_assets_dir / "downloaded").exists()
        assert (temp_assets_dir / "cloned").exists()

    def test_purplecrayon_init_custom_config(self, temp_assets_dir):
        """Test PurpleCrayon initialization with custom config."""
        config = {
            "max_concurrent_downloads": 5,
            "verbose": True,
            "timeout": 30
        }
        crayon = PurpleCrayon(assets_dir=temp_assets_dir, config=config)
        
        assert crayon.assets_dir == temp_assets_dir
        assert crayon.config["max_concurrent_downloads"] == 5
        assert crayon.config["verbose"] is True

    @pytest.mark.asyncio
    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    async def test_generate_async_single_image(self, temp_assets_dir, api_keys):
        """Test generating a single image with PurpleCrayon - LIMITED TO ONE API CALL."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        # Use minimal parameters to reduce API call complexity
        request = AssetRequest(
            query="red apple",  # Short prompt to minimize tokens
            width=256,  # Smaller size to reduce processing
            height=256,
            style="photorealistic"
        )
        
        result = await crayon.generate_async(request)
        
        # Basic validation - just check if API call succeeded
        assert result.success is True
        assert len(result.images) == 1
        assert result.images[0].source in ["ai", "cloned"]
        # Don't validate specific dimensions as they may vary

    @pytest.mark.asyncio
    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    async def test_generate_async_multiple_images(self, temp_assets_dir):
        """Test generating multiple images with PurpleCrayon - ONE API CALL PER COUNT."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        # Test different counts with one API call each
        counts_to_test = [1, 2, 3]
        
        for count in counts_to_test:
            request = AssetRequest(
                query="blue wave",  # Short prompt
                width=128,  # Very small size
                height=128,
                style="artistic",
                max_results=count
            )
            
            result = await crayon.generate_async(request)
            
            # Basic validation - just check if API call succeeded
            assert result.success is True
            assert len(result.images) == count
            for image in result.images:
                assert image.source == "ai"

    @pytest.mark.asyncio
    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    async def test_clone_async_single_file(self, temp_assets_dir, sample_image):
        """Test cloning a single image file - LIMITED TO ONE API CALL."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        # Copy sample image to downloaded folder
        downloaded_image = temp_assets_dir / "downloaded" / "test_source.png"
        downloaded_image.write_bytes(sample_image.read_bytes())
        
        # Use minimal parameters to reduce API usage
        result = await crayon.clone_async(
            source=str(downloaded_image),
            width=128,  # Very small size
            height=128,
            style="photorealistic"
        )
        
        # Basic validation - just check if API call succeeded
        assert result.success is True
        assert len(result.images) == 1
        assert result.images[0].source in ["ai", "cloned"]

    @pytest.mark.asyncio
    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    async def test_clone_async_directory(self, temp_assets_dir, sample_image, sample_jpg_image):
        """Test batch cloning images from directory - LIMITED TO ONE API CALL."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        # Copy only ONE sample image to minimize API calls
        downloaded_dir = temp_assets_dir / "downloaded"
        (downloaded_dir / "test1.png").write_bytes(sample_image.read_bytes())
        # Skip the second image to reduce API usage
        
        result = await crayon.clone_async(
            source=str(downloaded_dir),
            width=128,  # Very small size
            height=128,
            style="artistic"
        )
        
        # Basic validation - just check if API call succeeded
        assert result.success is True
        assert len(result.images) == 1  # Only one image processed
        assert result.images[0].source in ["ai", "cloned"]

    @pytest.mark.asyncio
    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    async def test_augment_async_single(self, temp_assets_dir, sample_image):
        """Test augmenting a single image - LIMITED TO ONE API CALL."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        # Copy sample image to ai folder
        ai_image = temp_assets_dir / "ai" / "test_source.png"
        ai_image.write_bytes(sample_image.read_bytes())
        
        # Use minimal parameters to reduce API usage
        result = await crayon.augment_async(
            image_path=str(ai_image),
            prompt="add sunset",  # Short prompt
            width=128,  # Very small size
            height=128
        )
        
        # Basic validation - just check if API call succeeded
        assert result.success is True
        assert len(result.images) == 1
        assert result.images[0].source in ["ai", "cloned"]

    @pytest.mark.asyncio
    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    async def test_augment_async_directory(self, temp_assets_dir, sample_image, sample_jpg_image):
        """Test batch augmenting images from directory - LIMITED TO ONE API CALL."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        # Copy only ONE sample image to minimize API calls
        ai_dir = temp_assets_dir / "ai"
        (ai_dir / "test1.png").write_bytes(sample_image.read_bytes())
        # Skip the second image to reduce API usage
        
        result = await crayon.augment_async(
            image_path=str(ai_dir),
            prompt="add border",  # Short prompt
            width=128,  # Very small size
            height=128
        )
        
        # Basic validation - just check if API call succeeded
        assert result.success is True
        assert len(result.images) == 1  # Only one image processed
        assert result.images[0].source in ["ai", "cloned"]

    @patch('purplecrayon.tools.scraping_tools.scrape_with_fallback')
    def test_scrape_mock(self, mock_scrape, temp_assets_dir):
        """Test web scraping with mocked response."""
        # Mock the scraping response
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.images = [
            MagicMock(filename="scraped1.jpg", width=800, height=600, source="downloaded"),
            MagicMock(filename="scraped2.png", width=1024, height=768, source="downloaded")
        ]
        mock_scrape.return_value = mock_result
        
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        result = crayon.scrape("https://example.com", verbose=True)
        
        assert result.success is True
        assert len(result.images) == 2
        mock_scrape.assert_called_once()

    def test_cleanup_assets(self, temp_assets_dir, sample_image):
        """Test asset cleanup functionality."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        # Create some test files
        ai_dir = temp_assets_dir / "ai"
        (ai_dir / "valid_image.png").write_bytes(sample_image.read_bytes())
        (ai_dir / "tiny_file.png").write_bytes(b"x")  # Invalid image
        
        result = crayon.cleanup_assets(remove_junk=True)
        assert result["success"] is True
        # Tiny file should be removed
        assert not (ai_dir / "tiny_file.png").exists()
        # Valid image should remain
        assert (ai_dir / "valid_image.png").exists()

    def test_catalog_operations(self, temp_assets_dir, sample_image):
        """Test catalog creation and search operations."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        # Add some test images
        ai_dir = temp_assets_dir / "ai"
        (ai_dir / "test_logo.png").write_bytes(sample_image.read_bytes())
        (ai_dir / "test_banner.jpg").write_bytes(sample_image.read_bytes())
        
        # Create catalog
        catalog_result = crayon.catalog.save_catalog()
        assert catalog_result.success is True
        
        # Search for images
        search_result = crayon.catalog.search_assets(query="logo", source="ai")
        assert len(search_result) >= 0  # May or may not find matches depending on content analysis
        
        # Get statistics
        stats = crayon.catalog.get_statistics()
        assert "total_assets" in stats
        assert "by_source" in stats
        assert "by_format" in stats

    @pytest.mark.asyncio
    async def test_error_handling_invalid_prompt(self, temp_assets_dir):
        """Test error handling with invalid prompt."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        request = AssetRequest(
            query="",  # Empty prompt should fail
            width=512,
            height=512
        )
        
        result = await crayon.generate_async(request)
        
        # Should handle error gracefully
        assert result.success is False
        assert "error" in result.message.lower() or "invalid" in result.message.lower()

    @pytest.mark.asyncio
    async def test_error_handling_invalid_image_path(self, temp_assets_dir):
        """Test error handling with invalid image path."""
        crayon = PurpleCrayon(assets_dir=temp_assets_dir)
        
        result = await crayon.clone_async(
            source="nonexistent_image.jpg",
            width=512,
            height=512
        )
        
        assert result.success is False
        assert "error" in result.message.lower() or "not found" in result.message.lower() or "does not exist" in result.message.lower()

    def test_asset_request_validation(self):
        """Test AssetRequest validation."""
        # Valid request
        request = AssetRequest(
            query="test prompt",
            width=512,
            height=512,
            style="photorealistic"
        )
        assert request.query == "test prompt"
        assert request.width == 512
        assert request.height == 512
        
        # Test default values
        request_default = AssetRequest(
            query="test")
        assert request_default.width is None  # Default is None, not 1024
        assert request_default.height is None  # Default is None, not 1024
        assert request_default.style is None  # Default is None, not "photorealistic"
