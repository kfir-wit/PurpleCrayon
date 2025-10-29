"""Tests for image augmentation API functions."""

import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from purplecrayon.tools.image_augmentation_tools import (
    augment_image,
    augment_images_from_directory,
)
from tests.conftest import has_api_key


class TestAugmentImageSync:
    """Test synchronous image augmentation functions."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_image_success(self, temp_assets_dir, sample_image):
        """Test successful single image augmentation - LIMITED TO ONE API CALL."""
        # Copy sample image to ai folder
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        result = augment_image(
            image_path=str(source_path),
            prompt="add sunset",  # Short prompt
            output_dir=str(temp_assets_dir / "ai"),
            width=128,  # Very small size
            height=128
        )
        
        # Basic validation - just check if API call succeeded
        assert result.success is True
        assert len(result.images) == 1
        assert result.images[0].source == "ai"

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_image_different_prompts(self, temp_assets_dir, sample_image):
        """Test augmentation with different prompts - LIMITED TO ONE API CALL."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        # Test only one prompt to minimize API usage
        result = augment_image(
            image_path=str(source_path),
            prompt="add rainbow",  # Short prompt
            output_dir=str(temp_assets_dir / "ai"),
            width=128,  # Very small size
            height=128
        )
        
        # Basic validation - just check if API call succeeded
        assert result.success is True
        assert len(result.images) == 1

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_image_different_sizes(self, temp_assets_dir, sample_image):
        """Test augmentation with different sizes - LIMITED TO ONE API CALL."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        # Test only one size to minimize API usage
        result = augment_image(
            image_path=str(source_path),
            prompt="add border",  # Short prompt
            output_dir=str(temp_assets_dir / "ai"),
            width=128,  # Very small size
            height=128
        )
        
        # Basic validation - just check if API call succeeded
        assert result.success is True
        assert len(result.images) == 1

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_image_different_styles(self, temp_assets_dir, sample_image):
        """Test augmentation with different styles - ONE API CALL PER STYLE."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        styles = ["photorealistic", "artistic", "cartoon", "abstract"]
        
        for style in styles:
            result = augment_image(
                image_path=str(source_path),
                prompt="enhance",  # Short prompt
                output_dir=str(temp_assets_dir / "ai"),
                width=128,  # Very small size
                height=128,
                style=style
            )
            
            # Basic validation - just check if API call succeeded
            assert result.success is True
            assert len(result.images) == 1
            assert result.images[0].style == style

    def test_augment_image_invalid_source(self, temp_assets_dir):
        """Test augmentation with invalid source path."""
        result = augment_image(
            image_path="nonexistent_image.jpg",
            prompt="add something",
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512
        )
        
        assert result.success is False
        assert "error" in result.message.lower() or "not found" in result.message.lower()

    def test_augment_image_invalid_output_dir(self, sample_image):
        """Test augmentation with invalid output directory."""
        result = augment_image(
            image_path=str(sample_image),
            prompt="add something",
            output_dir="/invalid/path/that/does/not/exist",
            width=512,
            height=512
        )
        
        assert result.success is False
        assert "error" in result.message.lower()

    def test_augment_image_empty_prompt(self, temp_assets_dir, sample_image):
        """Test augmentation with empty prompt."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        result = augment_image(
            image_path=str(source_path),
            prompt="",  # Empty prompt
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512
        )
        
        assert result.success is False
        assert "error" in result.message.lower() or "invalid" in result.message.lower()


class TestAugmentImagesFromDirectory:
    """Test batch image augmentation functions."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_images_from_directory_success(self, temp_assets_dir, sample_image, sample_jpg_image):
        """Test successful batch augmentation from directory."""
        # Copy sample images to ai folder
        ai_dir = temp_assets_dir / "ai"
        (ai_dir / "test1.png").write_bytes(sample_image.read_bytes())
        (ai_dir / "test2.jpg").write_bytes(sample_jpg_image.read_bytes())
        
        result = augment_images_from_directory(
            image_dir=str(ai_dir),
            prompt="add a magical glow effect",
            output_dir=str(ai_dir),
            width=256,
            height=256
        )
        
        assert result.success is True
        assert len(result.images) == 2
        for image in result.images:
            assert image.width == 256
            assert image.height == 256
            assert image.source == "ai"
            assert (ai_dir / image.filename).exists()

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_images_from_directory_with_filters(self, temp_assets_dir, sample_image, sample_jpg_image):
        """Test batch augmentation with file type filters."""
        ai_dir = temp_assets_dir / "ai"
        (ai_dir / "test1.png").write_bytes(sample_image.read_bytes())
        (ai_dir / "test2.jpg").write_bytes(sample_jpg_image.read_bytes())
        
        # Test with PNG filter only
        result = augment_images_from_directory(
            image_dir=str(ai_dir),
            prompt="add a vintage filter",
            output_dir=str(ai_dir),
            width=256,
            height=256,
            file_extensions=[".png"]
        )
        
        assert result.success is True
        assert len(result.images) == 1  # Only PNG file should be processed
        assert result.images[0].filename.endswith(".png")

    def test_augment_images_from_directory_empty_dir(self, temp_assets_dir):
        """Test batch augmentation from empty directory."""
        empty_dir = temp_assets_dir / "empty"
        empty_dir.mkdir()
        
        result = augment_images_from_directory(
            image_dir=str(empty_dir),
            prompt="add something",
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512
        )
        
        assert result.success is True
        assert len(result.images) == 0
        assert "no images found" in result.message.lower()

    def test_augment_images_from_directory_invalid_source(self, temp_assets_dir):
        """Test batch augmentation with invalid source directory."""
        result = augment_images_from_directory(
            image_dir="nonexistent_directory",
            prompt="add something",
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512
        )
        
        assert result.success is False
        assert "error" in result.message.lower() or "not found" in result.message.lower()


class TestAugmentWithDifferentModels:
    """Test augmentation with different AI models."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_with_gemini_model(self, temp_assets_dir, sample_image):
        """Test augmentation using Gemini model."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        result = augment_image(
            image_path=str(source_path),
            prompt="add a futuristic cityscape background",
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512,
            model="gemini-flash"
        )
        
        assert result.success is True
        assert len(result.images) == 1
        assert "gemini" in result.images[0].model.lower()

    @pytest.mark.api_replicate
    @pytest.mark.skipif(not has_api_key("replicate"), reason="Replicate API key not available")
    def test_augment_with_replicate_model(self, temp_assets_dir, sample_image):
        """Test augmentation using Replicate model."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        result = augment_image(
            image_path=str(source_path),
            prompt="add a cyberpunk aesthetic",
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512,
            model="flux-kontext-pro"
        )
        
        assert result.success is True
        assert len(result.images) == 1
        assert "flux" in result.images[0].model.lower()

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_with_model_fallback(self, temp_assets_dir, sample_image):
        """Test augmentation with model fallback when primary fails."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        with patch('purplecrayon.tools.image_augmentation_tools.augment_image_with_gemini') as mock_gemini:
            mock_gemini.return_value = {"status": "failed", "reason": "API error"}
            
            result = augment_image(
                image_path=str(source_path),
                prompt="add a dreamy atmosphere",
                output_dir=str(temp_assets_dir / "ai"),
                width=256,
                height=256
            )
            
            # Should fallback to other models if available
            if has_api_key("replicate"):
                assert result.success is True
            else:
                assert result.success is False

    def test_augment_with_invalid_model(self, temp_assets_dir, sample_image):
        """Test augmentation with invalid model name."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        result = augment_image(
            image_path=str(source_path),
            prompt="add something",
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512,
            model="invalid_model"
        )
        
        assert result.success is False
        assert "error" in result.message.lower()


class TestAugmentErrorHandling:
    """Test error handling in augmentation functions."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_with_api_failure(self, temp_assets_dir, sample_image):
        """Test augmentation handling when API fails."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        with patch('purplecrayon.tools.image_augmentation_tools.augment_image_with_gemini') as mock_gemini:
            mock_gemini.return_value = {"status": "failed", "reason": "API error"}
            
            result = augment_image(
                image_path=str(source_path),
                prompt="add something",
                output_dir=str(temp_assets_dir / "ai"),
                width=512,
                height=512
            )
            
            assert result.success is False
            assert "error" in result.message.lower()

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_with_generation_failure(self, temp_assets_dir, sample_image):
        """Test augmentation handling when image generation fails."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        with patch('purplecrayon.tools.image_augmentation_tools.generate_with_models') as mock_generate:
            mock_generate.return_value = {"status": "failed", "reason": "Generation failed"}
            
            result = augment_image(
                image_path=str(source_path),
                prompt="add something",
                output_dir=str(temp_assets_dir / "ai"),
                width=512,
                height=512
            )
            
            assert result.success is False
            assert "error" in result.message.lower()

    @pytest.mark.asyncio
    async def test_augment_async_timeout(self, temp_assets_dir, sample_image):
        """Test augment async timeout handling."""
        source_path = temp_assets_dir / "ai" / "test_source.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        with patch('purplecrayon.tools.image_augmentation_tools.augment_image_with_gemini') as mock_gemini:
            mock_gemini.side_effect = asyncio.TimeoutError("Request timeout")
            
            from purplecrayon.tools.image_augmentation_tools import augment_image_async
            result = await augment_image_async(
                image_path=str(source_path),
                prompt="add something",
                output_dir=str(temp_assets_dir / "ai"),
                width=512,
                height=512
            )
            
            assert result.success is False
            assert "timeout" in result.message.lower()

    def test_augment_with_invalid_image_format(self, temp_assets_dir):
        """Test augmentation with invalid image format."""
        # Create a text file with .png extension
        invalid_image = temp_assets_dir / "ai" / "invalid.png"
        invalid_image.write_text("This is not an image")
        
        result = augment_image(
            image_path=str(invalid_image),
            prompt="add something",
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512
        )
        
        assert result.success is False
        assert "error" in result.message.lower()


class TestAugmentIntegration:
    """Test augmentation function integration scenarios."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_workflow_complete(self, temp_assets_dir, sample_image):
        """Test complete augmentation workflow from source to final image."""
        # Setup source image
        source_path = temp_assets_dir / "ai" / "original.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        # Augment the image
        result = augment_image(
            image_path=str(source_path),
            prompt="add a beautiful sunset background with warm colors",
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512,
            style="photorealistic"
        )
        
        assert result.success is True
        assert len(result.images) == 1
        
        augmented_image = result.images[0]
        augmented_path = temp_assets_dir / "ai" / augmented_image.filename
        
        # Verify augmented image exists and has correct properties
        assert augmented_path.exists()
        assert augmented_image.width == 512
        assert augmented_image.height == 512
        assert augmented_image.source == "ai"
        assert augmented_image.style == "photorealistic"

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_batch_augment_workflow(self, temp_assets_dir, sample_image, sample_jpg_image):
        """Test complete batch augmentation workflow."""
        # Setup source images
        ai_dir = temp_assets_dir / "ai"
        (ai_dir / "image1.png").write_bytes(sample_image.read_bytes())
        (ai_dir / "image2.jpg").write_bytes(sample_jpg_image.read_bytes())
        
        # Batch augment
        result = augment_images_from_directory(
            image_dir=str(ai_dir),
            prompt="add a vintage film grain effect",
            output_dir=str(ai_dir),
            width=256,
            height=256,
            style="artistic"
        )
        
        assert result.success is True
        assert len(result.images) == 2
        
        # Verify all augmented images exist
        for image in result.images:
            augmented_path = ai_dir / image.filename
            assert augmented_path.exists()
            assert image.width == 256
            assert image.height == 256
            assert image.source == "ai"
            assert image.style == "artistic"

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_augment_preserve_original(self, temp_assets_dir, sample_image):
        """Test that augmentation preserves the original image."""
        source_path = temp_assets_dir / "ai" / "original.png"
        source_path.write_bytes(sample_image.read_bytes())
        
        original_size = source_path.stat().st_size
        
        # Augment the image
        result = augment_image(
            image_path=str(source_path),
            prompt="add a subtle glow effect",
            output_dir=str(temp_assets_dir / "ai"),
            width=512,
            height=512
        )
        
        assert result.success is True
        
        # Verify original image is unchanged
        assert source_path.exists()
        assert source_path.stat().st_size == original_size
        
        # Verify new augmented image was created
        assert len(result.images) == 1
        augmented_path = temp_assets_dir / "ai" / result.images[0].filename
        assert augmented_path.exists()
        assert augmented_path != source_path  # Should be different file
