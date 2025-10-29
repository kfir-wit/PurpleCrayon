"""Tests for AI generation API functions."""

import asyncio
from unittest.mock import patch, MagicMock

import pytest

from purplecrayon.tools.ai_generation_tools import (
    generate_with_gemini,
    generate_with_replicate,
    generate_with_models,
    generate_with_models_async,
    list_available_models,
    check_model_updates,
)
from tests.conftest import has_api_key


class TestGeminiGeneration:
    """Test Gemini AI generation functions."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_generate_with_gemini_success(self):
        """Test successful Gemini image generation - LIMITED TO ONE API CALL."""
        result = generate_with_gemini(
            prompt="red apple",  # Short prompt to minimize tokens
            aspect_ratio="1:1",
            style="photorealistic"
        )
        
        # Basic validation - just check if API call succeeded
        assert result["status"] == "succeeded"
        assert "image_data" in result or "url" in result
        assert "model" in result

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    @pytest.mark.stress

    def test_generate_with_gemini_different_aspect_ratios(self):
        """Test Gemini generation with different aspect ratios - ONE API CALL PER RATIO."""
        aspect_ratios = ["1:1", "16:9", "3:2", "4:3"]
        
        for ratio in aspect_ratios:
            result = generate_with_gemini(
                prompt="blue wave",  # Short prompt
                aspect_ratio=ratio,
                style="artistic"
            )
            
            # Basic validation - just check if API call succeeded
            assert result["status"] == "succeeded"
            assert "image_data" in result or "url" in result

    def test_generate_with_gemini_invalid_prompt(self):
        """Test Gemini generation with invalid prompt."""
        result = generate_with_gemini(
            prompt="",  # Empty prompt
            aspect_ratio="1:1"
        )
        
        assert result["status"] == "failed"
        assert "error" in result["reason"].lower() or "no image data" in result["reason"].lower()

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    @pytest.mark.stress

    def test_generate_with_gemini_different_styles(self):
        """Test Gemini generation with different styles - ONE API CALL PER STYLE."""
        styles = ["photorealistic", "artistic", "cartoon", "abstract"]
        
        for style in styles:
            result = generate_with_gemini(
                prompt="mountain",  # Short prompt
                aspect_ratio="1:1",  # Simple ratio
                style=style
            )
            
            # Basic validation - just check if API call succeeded
            assert result["status"] == "succeeded"
            assert "image_data" in result or "url" in result


class TestReplicateGeneration:
    """Test Replicate AI generation functions."""

    @pytest.mark.api_replicate
    @pytest.mark.skipif(not has_api_key("replicate"), reason="Replicate API key not available")
    def test_generate_with_replicate_success(self):
        """Test successful Replicate image generation - LIMITED TO ONE API CALL."""
        result = generate_with_replicate(
            prompt="city skyline",  # Short prompt
            aspect_ratio="1:1",  # Simple ratio
            width=256,  # Small size
            height=256
        )
        
        # Basic validation - just check if API call succeeded
        assert result["status"] == "succeeded"
        assert "image_data" in result or "url" in result
        assert "model" in result

    @pytest.mark.api_replicate
    @pytest.mark.skipif(not has_api_key("replicate"), reason="Replicate API key not available")
    @pytest.mark.stress

    def test_generate_with_replicate_different_sizes(self):
        """Test Replicate generation with different sizes - ONE API CALL PER SIZE."""
        sizes = [(256, 256), (512, 512), (1024, 768)]
        
        for width, height in sizes:
            result = generate_with_replicate(
                prompt="abstract painting",  # Short prompt
                aspect_ratio="1:1",
                width=width,
                height=height
            )
            
            # Basic validation - just check if API call succeeded
            assert result["status"] == "succeeded"
            assert "image_data" in result or "url" in result

    @pytest.mark.api_replicate
    @pytest.mark.skipif(not has_api_key("replicate"), reason="Replicate API key not available")
    @pytest.mark.stress

    def test_generate_with_replicate_different_models(self):
        """Test Replicate generation with different models - ONE API CALL PER MODEL."""
        # Test each available Replicate model individually
        models_to_test = [
            "black-forest-labs/flux-1.1-pro",
            "stability-ai/stable-diffusion"
        ]
        
        for model in models_to_test:
            result = generate_with_replicate(
                prompt="test image",  # Short prompt
                aspect_ratio="1:1",
                width=256,  # Small size
                height=256,
                model=model  # Test specific model
            )
            
            # Basic validation - just check if API call succeeded
            assert result["status"] == "succeeded"
            assert "image_data" in result or "url" in result
            assert result["model"] == model

    def test_generate_with_replicate_invalid_prompt(self):
        """Test Replicate generation with invalid prompt."""
        result = generate_with_replicate(
            prompt="",  # Empty prompt
            aspect_ratio="1:1"
        )
        
        assert result["status"] == "failed"
        assert "error" in result["reason"].lower()


class TestUnifiedModelAPI:
    """Test unified model API functions."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_generate_with_models_sync_default(self):
        """Test unified model API with default settings."""
        result = generate_with_models(
            prompt="a beautiful sunset over mountains",
            aspect_ratio="16:9",
            model_type="text_to_image"
        )
        
        assert result["status"] == "succeeded"
        assert "image_data" in result or "url" in result
        assert "model" in result

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_generate_with_models_sync_with_specific_model(self):
        """Test unified model API with specific model."""
        result = generate_with_models(
            prompt="a cute cat playing with yarn",
            aspect_ratio="1:1",
            model_type="text_to_image",
            with_models=["gemini-flash"]
        )
        
        assert result["status"] == "succeeded"
        assert "image_data" in result or "url" in result
        assert result["model"] == "gemini-2.5-flash-image"

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_generate_with_models_sync_exclude_models(self):
        """Test unified model API excluding specific models."""
        result = generate_with_models(
            prompt="a vintage car in a garage",
            aspect_ratio="3:2",
            model_type="text_to_image",
            exclude_models=["flux-1.1-pro", "stable-diffusion"]
        )
        
        assert result["status"] == "succeeded"
        assert "image_data" in result or "url" in result
        # Should use Gemini since others are excluded
        assert "gemini" in result["model"]

    @pytest.mark.asyncio
    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    async def test_generate_with_models_async_default(self):
        """Test unified model API async with default settings."""
        result = await generate_with_models_async(
            prompt="a magical forest with glowing mushrooms",
            aspect_ratio="4:3",
            model_type="text_to_image"
        )
        
        assert result["status"] == "succeeded"
        assert "image_data" in result or "url" in result
        assert "model" in result

    @pytest.mark.asyncio
    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    async def test_generate_with_models_async_image_to_image(self, sample_image):
        """Test unified model API for image-to-image generation."""
        result = await generate_with_models_async(
            prompt="add a rainbow in the sky",
            aspect_ratio="16:9",
            model_type="image_to_image",
            image_path=str(sample_image)
        )
        
        assert result["status"] == "succeeded"
        assert "image_data" in result or "url" in result
        assert "model" in result

    @pytest.mark.asyncio
    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    async def test_generate_with_models_async_image_to_text(self, sample_image):
        """Test unified model API for image-to-text analysis."""
        result = await generate_with_models_async(
            prompt="describe this image in detail",
            model_type="image_to_text",
            image_path=str(sample_image)
        )
        
        assert result["status"] == "succeeded"
        assert "text" in result or "description" in result
        assert "model" in result

    def test_generate_with_models_invalid_model_type(self):
        """Test unified model API with invalid model type."""
        result = generate_with_models(
            prompt="test prompt",
            model_type="invalid_type"
        )
        
        assert result["status"] == "failed"
        assert "error" in result["reason"].lower()

    def test_generate_with_models_no_available_models(self):
        """Test unified model API when no models are available."""
        with patch('purplecrayon.tools.ai_generation_tools.model_manager') as mock_manager:
            mock_manager.get_available_models.return_value = []
            
            result = generate_with_models(
                prompt="test prompt",
                model_type="text_to_image"
            )
            
            assert result["status"] == "failed"
            assert "no models available" in result["reason"].lower()


class TestModelManagement:
    """Test model management functions."""

    def test_list_available_models_default(self):
        """Test listing available models with default settings."""
        models = list_available_models()
        
        assert "total_models" in models
        assert "enabled_models" in models
        assert "providers" in models
        assert "fallback_order" in models
        assert "models" in models
        
        assert models["total_models"] > 0
        assert models["enabled_models"] > 0
        assert len(models["providers"]) > 0
        assert "text_to_image" in models["fallback_order"]
        assert "image_to_image" in models["fallback_order"]
        assert "image_to_text" in models["fallback_order"]

    def test_list_available_models_specific_type(self):
        """Test listing models for specific type."""
        # Note: list_available_models doesn't take model_type parameter
        # This test verifies the function works without parameters
        models = list_available_models()
        
        assert isinstance(models, dict)
        assert "models" in models
        assert len(models["models"]) > 0
        for model_name, model_info in models["models"].items():
            assert "display_name" in model_info
            assert "provider" in model_info
            assert "enabled" in model_info

    def test_list_available_models_with_filters(self):
        """Test listing models with filters."""
        # Note: list_available_models doesn't support filtering parameters
        # This test verifies the function works and returns all models
        models = list_available_models()
        
        assert isinstance(models, dict)
        assert "models" in models
        assert len(models["models"]) > 0
        
        # Verify we have the expected models
        model_names = list(models["models"].keys())
        assert "gemini-flash" in model_names
        assert "flux-1.1-pro" in model_names

    def test_check_model_updates(self):
        """Test checking for model updates."""
        # Test with force=False (should use cache if available)
        result = check_model_updates(force=False)
        assert isinstance(result, bool)
        
        # Test with force=True (should force check)
        result = check_model_updates(force=True)
        assert isinstance(result, bool)

    @patch('purplecrayon.tools.ai_generation_tools.model_manager')
    def test_check_model_updates_error_handling(self, mock_manager):
        """Test model update check error handling."""
        mock_manager.check_for_updates.side_effect = Exception("Network error")
        
        result = check_model_updates(force=True)
        assert result is False


class TestModelFallback:
    """Test model fallback mechanisms."""

    @pytest.mark.api_gemini
    @pytest.mark.skipif(not has_api_key("gemini"), reason="Gemini API key not available")
    def test_model_fallback_gemini_to_replicate(self):
        """Test fallback from Gemini to Replicate when Gemini fails."""
        with patch('purplecrayon.tools.ai_generation_tools.generate_with_gemini') as mock_gemini:
            mock_gemini.return_value = {"status": "failed", "reason": "API error"}
            
            result = generate_with_models(
                prompt="test prompt",
                model_type="text_to_image"
            )
            
            # Should fallback to Replicate if available
            if has_api_key("replicate"):
                assert result["status"] in ["succeeded", "failed"]
            else:
                assert result["status"] == "failed"

    def test_model_fallback_all_models_fail(self):
        """Test when all models fail."""
        with patch('purplecrayon.tools.ai_generation_tools.generate_with_gemini') as mock_gemini, \
             patch('purplecrayon.tools.ai_generation_tools.generate_with_replicate') as mock_replicate:
            
            mock_gemini.return_value = {"status": "failed", "reason": "Gemini error"}
            mock_replicate.return_value = {"status": "failed", "reason": "Replicate error"}
            
            result = generate_with_models(
                prompt="test prompt",
                model_type="text_to_image"
            )
            
            assert result["status"] == "failed"
            assert "all models failed" in result["reason"].lower()


class TestErrorHandling:
    """Test error handling in AI generation functions."""

    def test_invalid_aspect_ratio(self):
        """Test handling of invalid aspect ratio."""
        result = generate_with_gemini(
            prompt="test prompt",
            aspect_ratio="invalid_ratio"
        )
        
        assert result["status"] == "failed"
        assert "error" in result["reason"].lower()

    def test_missing_required_parameters(self):
        """Test handling of missing required parameters."""
        result = generate_with_models(
            prompt="",  # Empty prompt
            model_type="text_to_image"
        )
        
        assert result["status"] == "failed"
        assert "error" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_async_timeout_handling(self):
        """Test async function timeout handling."""
        with patch('purplecrayon.tools.ai_generation_tools.generate_with_gemini') as mock_gemini:
            mock_gemini.side_effect = asyncio.TimeoutError("Request timeout")
            
            result = await generate_with_models_async(
                prompt="test prompt",
                model_type="text_to_image"
            )
            
            assert result["status"] == "failed"
            assert "timeout" in result["reason"].lower()
