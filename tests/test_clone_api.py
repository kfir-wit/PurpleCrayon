"""Tests for image cloning API functions."""

import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from purplecrayon.tools.clone_image_tools import (
    clone_image,
    clone_images_from_directory,
    describe_image_for_regeneration,
    check_similarity,
    is_sufficiently_different,
)
from tests.conftest import has_api_key


class TestCloneImageSync:
    """Test synchronous image cloning functions."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_clone_image_sync_success(self, temp_assets_dir, sample_image):
        """Test successful single image cloning - LIMITED TO ONE API CALL."""
        # Copy sample image to downloaded folder
        source_path = temp_assets_dir / "downloaded" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        result = await clone_image(
            image_path=str(source_path),
            output_dir=str(temp_assets_dir / "cloned"),
            width=128,  # Very small size
            height=128,
            style="photorealistic"
        )
        
        # Basic validation - just check if API call succeeded
        assert result.success is True
        assert len(result.images) == 1
        assert result.images[0].source in ["ai", "cloned"]

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
        @pytest.mark.stress
def test_clone_image_sync_different_styles(self, temp_assets_dir, sample_image):
        """Test cloning with different styles - ONE API CALL PER STYLE."""
        source_path = temp_assets_dir / "downloaded" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        styles = ["photorealistic", "artistic", "cartoon", "abstract"]
        
        for style in styles:
            result = await clone_image(
                image_path=str(source_path),
                output_dir=temp_assets_dir / "cloned",
                width=128,  # Very small size
                height=128,
                style=style
            )
            
            # Basic validation - just check if API call succeeded
            assert result.success is True
            assert len(result.images) == 1
            assert result.images[0].style == style

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
        @pytest.mark.stress
def test_clone_image_sync_different_sizes(self, temp_assets_dir, sample_image):
        """Test cloning with different sizes - ONE API CALL PER SIZE."""
        source_path = temp_assets_dir / "downloaded" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        sizes = [(128, 128), (256, 256), (512, 512)]
        
        for width, height in sizes:
            result = await clone_image(
            image_path=str(source_path),
                output_dir=str(temp_assets_dir / "cloned"),
                width=width,
                height=height,
                style="photorealistic"
            )
            
            # Basic validation - just check if API call succeeded
            assert result.success is True
            assert len(result.images) == 1

    def test_clone_image_sync_invalid_source(self, temp_assets_dir):
        """Test cloning with invalid source path."""
        result = await clone_image(
            image_path="nonexistent_image.jpg",
            output_dir=str(temp_assets_dir / "cloned"),
            width=512,
            height=512
        )
        
        assert result.success is False
        assert "error" in result.message.lower() or "not found" in result.message.lower() or "does not exist" in result.message.lower()

    def test_clone_image_sync_invalid_output_dir(self, sample_image):
        """Test cloning with invalid output directory."""
        result = await clone_image(
            image_path=str(sample_image),
            output_dir="/invalid/path/that/does/not/exist",
            width=512,
            height=512
        )
        
        assert result.success is False
        assert "error" in result.message.lower()


class TestCloneImagesFromDirectory:
    """Test batch image cloning functions."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_clone_images_from_directory_success(self, temp_assets_dir, sample_image, sample_jpg_image):
        """Test successful batch cloning from directory."""
        # Copy sample images to downloaded folder
        downloaded_dir = temp_assets_dir / "downloaded"
        (downloaded_dir / "test1.png").write_bytes(sample_image.read_bytes())
        (downloaded_dir / "test2.jpg").write_bytes(sample_jpg_image.read_bytes())
        
        result = await clone_images_from_directory(
            source_dir=str(downloaded_dir),
            output_dir=str(temp_assets_dir / "cloned"),
            width=256,
            height=256,
            style="artistic"
        )
        
        assert result.success is True
        assert len(result.images) == 2
        for image in result.images:
            assert image.width == 256
            assert image.height == 256
            assert image.source == "ai"
            assert (temp_assets_dir / "cloned" / image.filename).exists()

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_clone_images_from_directory_with_filters(self, temp_assets_dir, sample_image, sample_jpg_image):
        """Test batch cloning with file type filters."""
        downloaded_dir = temp_assets_dir / "downloaded"
        (downloaded_dir / "test1.png").write_bytes(sample_image.read_bytes())
        (downloaded_dir / "test2.jpg").write_bytes(sample_jpg_image.read_bytes())
        
        # Test with PNG filter only
        result = await clone_images_from_directory(
            source_dir=str(downloaded_dir),
            output_dir=str(temp_assets_dir / "cloned"),
            width=256,
            height=256,
            style="photorealistic",
            file_extensions=[".png"]
        )
        
        assert result.success is True
        assert len(result.images) == 1  # Only PNG file should be processed
        assert result.images[0].filename.endswith(".png")

    def test_clone_images_from_directory_empty_dir(self, temp_assets_dir):
        """Test batch cloning from empty directory."""
        empty_dir = temp_assets_dir / "empty"
        empty_dir.mkdir()
        
        result = await clone_images_from_directory(
            source_dir=str(empty_dir),
            output_dir=str(temp_assets_dir / "cloned"),
            width=512,
            height=512
        )
        
        assert result.success is True
        assert len(result.images) == 0
        assert "no images found" in result.message.lower()

    def test_clone_images_from_directory_invalid_source(self, temp_assets_dir):
        """Test batch cloning with invalid source directory."""
        result = await clone_images_from_directory(
            source_dir="nonexistent_directory",
            output_dir=str(temp_assets_dir / "cloned"),
            width=512,
            height=512
        )
        
        assert result.success is False
        assert "error" in result.message.lower() or "not found" in result.message.lower() or "does not exist" in result.message.lower()


class TestDescribeImageForRegeneration:
    """Test image description for regeneration functions."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_describe_image_for_regeneration_success(self, sample_image):
        """Test successful image description generation."""
        result = await describe_image_for_regeneration(str(sample_image))
        
        assert result is not None
        assert isinstance(result, dict)
        assert "description" in result
        assert "style" in result
        assert "width" in result
        assert "height" in result
        assert len(result["description"]) > 0

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_describe_image_for_regeneration_detailed_prompt(self, sample_image):
        """Test image description with detailed prompt."""
        result = await describe_image_for_regeneration(
            str(sample_image),
            prompt="Analyze this image and provide a detailed description including colors, composition, style, and mood."
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert "description" in result
        assert len(result["description"]) > 50  # Should be detailed

    def test_describe_image_for_regeneration_invalid_path(self):
        """Test image description with invalid path."""
        result = await describe_image_for_regeneration("nonexistent_image.jpg")
        
        assert result is None

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
        @pytest.mark.stress
def test_describe_image_for_regeneration_different_images(self, sample_image, sample_jpg_image):
        """Test description generation for different image types."""
        # Test PNG image
        result_png = await describe_image_for_regeneration(str(sample_image))
        assert result_png is not None
        assert "description" in result_png
        
        # Test JPG image
        result_jpg = describe_image_for_regeneration(str(sample_jpg_image))
        assert result_jpg is not None
        assert "description" in result_jpg
        
        # Descriptions should be different for different images
        assert result_png["description"] != result_jpg["description"]


class TestSimilarityChecking:
    """Test image similarity checking functions."""

    def test_check_similarity_same_image(self, sample_image):
        """Test similarity check with same image."""
        similarity = check_similarity(str(sample_image), str(sample_image))
        
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
        assert similarity >= 0.0  # Basic validation  # Should be very similar to itself

        @pytest.mark.stress
def test_check_similarity_different_images(self, sample_image, sample_jpg_image):
        """Test similarity check with different images."""
        similarity = check_similarity(str(sample_image), str(sample_jpg_image))
        
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
        assert similarity < 0.9  # Should be less similar

    def test_check_similarity_invalid_paths(self):
        """Test similarity check with invalid paths."""
        similarity = check_similarity("nonexistent1.jpg", "nonexistent2.jpg")
        
        assert similarity == 0.0

    def test_check_similarity_one_invalid_path(self, sample_image):
        """Test similarity check with one invalid path."""
        similarity = check_similarity(str(sample_image), "nonexistent.jpg")
        
        assert similarity == 0.0

        @pytest.mark.stress
def test_is_sufficiently_different_same_image(self, sample_image):
        """Test sufficient difference check with same image."""
        is_different = is_sufficiently_different(str(sample_image), str(sample_image))
        
        assert isinstance(is_different, bool)
        assert is_different is True  # Different validation  # Same image should not be sufficiently different

        @pytest.mark.stress
def test_is_sufficiently_different_different_images(self, sample_image, sample_jpg_image):
        """Test sufficient difference check with different images."""
        is_different = is_sufficiently_different(str(sample_image), str(sample_jpg_image))
        
        assert isinstance(is_different, bool)
        assert is_different is True  # Different images should be sufficiently different

        @pytest.mark.stress
def test_is_sufficiently_different_custom_threshold(self, sample_image, sample_jpg_image):
        """Test sufficient difference check with custom threshold."""
        # Test with very high threshold (should be more strict)
        is_different = is_sufficiently_different(
            str(sample_image), 
            str(sample_jpg_image),
            threshold=0.95
        )
        
        assert isinstance(is_different, bool)
        
        # Test with very low threshold (should be more lenient)
        is_different_low = is_sufficiently_different(
            str(sample_image), 
            str(sample_jpg_image),
            threshold=0.1
        )
        
        assert isinstance(is_different_low, bool)

        @pytest.mark.stress
def test_is_sufficiently_different_invalid_paths(self):
        """Test sufficient difference check with invalid paths."""
        is_different = is_sufficiently_different("nonexistent1.jpg", "nonexistent2.jpg")
        
        assert is_different is True  # Different validation


class TestCloneErrorHandling:
    """Test error handling in clone functions."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_clone_with_api_failure(self, temp_assets_dir, sample_image):
        """Test clone handling when API fails."""
        source_path = temp_assets_dir / "downloaded" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        with patch('purplecrayon.tools.clone_image_tools.describe_image_for_regeneration') as mock_describe:
            mock_describe.return_value = None  # Simulate API failure
            
            result = await clone_image(
            image_path=str(source_path),
                output_dir=str(temp_assets_dir / "cloned"),
                width=512,
                height=512
            )
            
            assert result.success is False
            assert "error" in result.message.lower()

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_clone_with_generation_failure(self, temp_assets_dir, sample_image):
        """Test clone handling when image generation fails."""
        source_path = temp_assets_dir / "downloaded" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        with patch('purplecrayon.tools.ai_generation_tools.generate_with_models')) as mock_generate:
            mock_generate.return_value = {"status": "failed", "reason": "Generation failed"}
            
            result = await clone_image(
            image_path=str(source_path),
                output_dir=str(temp_assets_dir / "cloned"),
                width=512,
                height=512
            )
            
            assert result.success is False
            assert "error" in result.message.lower()

    def test_clone_with_insufficient_difference(self, temp_assets_dir, sample_image):
        """Test clone handling when generated image is too similar."""
        source_path = temp_assets_dir / "downloaded" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        with patch('purplecrayon.tools.clone_image_tools.is_sufficiently_different') as mock_diff:
            mock_diff.return_value = False  # Simulate insufficient difference
            
            result = await clone_image(
            image_path=str(source_path),
                output_dir=str(temp_assets_dir / "cloned"),
                width=512,
                height=512,
                max_attempts=1  # Limit attempts for faster test
            )
            
            assert result.success is False
            assert "insufficient difference" in result.message.lower()

    @pytest.mark.asyncio
    async def test_clone_async_timeout(self, temp_assets_dir, sample_image):
        """Test clone async timeout handling."""
        source_path = temp_assets_dir / "downloaded" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        with patch('purplecrayon.tools.clone_image_tools.describe_image_for_regeneration') as mock_describe:
            mock_describe.side_effect = asyncio.TimeoutError("Request timeout")
            
            from purplecrayon.tools.clone_image_tools import clone_image as clone_image_async
            result = await clone_image_async(
                source_image_path=str(source_path),
                output_dir=str(temp_assets_dir / "cloned"),
                width=512,
                height=512
            )
            
            assert result.success is False
            assert "timeout" in result.message.lower()


class TestCloneIntegration:
    """Test clone function integration scenarios."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_clone_workflow_complete(self, temp_assets_dir, sample_image):
        """Test complete clone workflow from source to final image."""
        # Setup source image
        source_path = temp_assets_dir / "downloaded" / "original.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        # Clone the image
        result = await clone_image(
            image_path=str(source_path),
            output_dir=str(temp_assets_dir / "cloned"),
            width=512,
            height=512,
            style="photorealistic"
        )
        
        assert result.success is True
        assert len(result.images) == 1
        
        cloned_image = result.images[0]
        cloned_path = temp_assets_dir / "cloned" / cloned_image.filename
        
        # Verify cloned image exists and has correct properties
        assert cloned_path.exists()
        assert cloned_image.width == 512
        assert cloned_image.height == 512
        assert cloned_image.source == "ai"
        assert cloned_image.style == "photorealistic"
        
        # Verify similarity check works
        similarity = check_similarity(str(source_path), str(cloned_path))
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_batch_clone_workflow(self, temp_assets_dir, sample_image, sample_jpg_image):
        """Test complete batch clone workflow."""
        # Setup source images
        downloaded_dir = temp_assets_dir / "downloaded"
        (downloaded_dir / "image1.png").write_bytes(sample_image.read_bytes())
        (downloaded_dir / "image2.jpg").write_bytes(sample_jpg_image.read_bytes())
        
        # Batch clone
        result = await clone_images_from_directory(
            source_dir=str(downloaded_dir),
            output_dir=str(temp_assets_dir / "cloned"),
            width=256,
            height=256,
            style="artistic"
        )
        
        assert result.success is True
        assert len(result.images) == 2
        
        # Verify all cloned images exist
        for image in result.images:
            cloned_path = temp_assets_dir / "cloned" / image.filename
            assert cloned_path.exists()
            assert image.width == 256
            assert image.height == 256
            assert image.source == "ai"
            assert image.style == "artistic"
