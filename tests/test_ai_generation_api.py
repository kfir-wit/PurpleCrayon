"""Unit tests for the AI generation tools without hitting live providers."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from purplecrayon.models.generation_models import ModelConfig, ModelProvider
from purplecrayon.tools.ai_generation_tools import (
    check_model_updates,
    generate_with_gemini,
    generate_with_models,
    generate_with_models_async,
    generate_with_replicate,
    list_available_models,
)
from tests.conftest import has_api_key


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 120


@pytest.fixture
def set_test_env(monkeypatch):
    """Ensure API keys are present for unit tests."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("REPLICATE_API_TOKEN", "test-replicate-key")
    return monkeypatch


def make_gemini_response(image_bytes: bytes | None) -> SimpleNamespace:
    """Build a minimal Gemini-like response object."""
    if image_bytes is None:
        parts = [SimpleNamespace(inline_data=None)]
    else:
        parts = [SimpleNamespace(inline_data=SimpleNamespace(data=image_bytes))]
    candidate = SimpleNamespace(content=SimpleNamespace(parts=parts))
    return SimpleNamespace(candidates=[candidate])


class TestGeminiGeneration:
    @patch("purplecrayon.tools.ai_generation_tools.genai.Client")
    def test_generate_with_gemini_success(self, mock_client, set_test_env):
        image_bytes = PNG_BYTES
        mock_client.return_value.models.generate_content.return_value = make_gemini_response(image_bytes)

        result = generate_with_gemini(prompt="red apple")

        assert result["status"] == "succeeded"
        assert result["image_data"] == image_bytes
        assert result["model"] == "gemini-2.5-flash-image"

    @patch("purplecrayon.tools.ai_generation_tools.genai.Client")
    def test_generate_with_gemini_handles_missing_image(self, mock_client, set_test_env):
        mock_client.return_value.models.generate_content.return_value = make_gemini_response(None)

        result = generate_with_gemini(prompt="empty result")

        assert result["status"] == "failed"
        assert "no image data" in result["reason"].lower()

    def test_generate_with_gemini_missing_key(self, set_test_env):
        set_test_env.delenv("GEMINI_API_KEY", raising=False)

        result = generate_with_gemini(prompt="should skip")

        assert result["status"] == "skipped"
        assert "missing" in result["reason"].lower()


class TestReplicateGeneration:
    @patch("purplecrayon.tools.ai_generation_tools.requests.get")
    @patch("purplecrayon.tools.ai_generation_tools._generate_with_replicate_sync")
    def test_generate_with_replicate_success(self, mock_sync, mock_get, set_test_env):
        mock_sync.return_value = {"status": "succeeded", "url": "https://example.com/img.png", "model": "flux"}
        response = MagicMock()
        response.content = PNG_BYTES
        mock_get.return_value = response

        result = generate_with_replicate(prompt="city skyline")

        assert result["status"] == "succeeded"
        assert result["image_data"] == PNG_BYTES
        assert result["model"] == "flux"

    @patch("purplecrayon.tools.ai_generation_tools._generate_with_replicate_sync")
    def test_generate_with_replicate_failure_passthrough(self, mock_sync, set_test_env):
        mock_sync.return_value = {"status": "failed", "reason": "All Replicate models failed"}

        result = generate_with_replicate(prompt="fails quickly")

        assert result["status"] == "failed"
        assert "replicate" in result["reason"].lower()

    @patch("purplecrayon.tools.ai_generation_tools.requests.get")
    @patch("purplecrayon.tools.ai_generation_tools._generate_with_replicate_sync")
    def test_generate_with_replicate_invalid_image_data(self, mock_sync, mock_get, set_test_env):
        mock_sync.return_value = {"status": "succeeded", "url": "https://example.com/img.png"}
        response = MagicMock()
        response.content = b"hi"
        mock_get.return_value = response

        result = generate_with_replicate(prompt="invalid bytes")

        assert result["status"] == "failed"
        assert "too small" in result["reason"].lower()

    def test_generate_with_replicate_missing_key(self, set_test_env):
        set_test_env.delenv("REPLICATE_API_TOKEN", raising=False)

        result = generate_with_replicate(prompt="should skip")

        assert result["status"] == "skipped"
        assert "missing" in result["reason"].lower()


class TestUnifiedModelAPI:
    def make_model(self, name: str, provider: ModelProvider, **capabilities) -> ModelConfig:
        return ModelConfig(
            name=name,
            provider=provider,
            model_id=f"{name}-id",
            display_name=name.title(),
            description="",
            priority=1,
            capabilities={"text_to_image": False, "image_to_image": False, "image_to_text": False, **capabilities},
        )

    @patch("purplecrayon.tools.ai_generation_tools.generate_with_gemini")
    @patch("purplecrayon.tools.ai_generation_tools.model_manager.get_fallback_models")
    def test_generate_with_models_uses_fallback(self, mock_fallback, mock_gemini, set_test_env):
        mock_fallback.return_value = [
            self.make_model("gemini-flash", ModelProvider.GEMINI, text_to_image=True)
        ]
        mock_gemini.return_value = {"status": "succeeded", "image_data": PNG_BYTES, "model": "gemini-2.5-flash-image"}

        result = generate_with_models(prompt="mountain", model_type="text_to_image")

        assert result["status"] == "succeeded"
        assert result["successful_generations"] == 1
        mock_gemini.assert_called_once()

    @patch("purplecrayon.tools.ai_generation_tools.generate_with_gemini")
    @patch("purplecrayon.tools.ai_generation_tools.generate_with_replicate")
    @patch("purplecrayon.tools.ai_generation_tools.model_manager.get_fallback_models")
    def test_generate_with_models_fallback_to_replicate(
        self, mock_fallback, mock_replicate, mock_gemini, set_test_env
    ):
        mock_fallback.return_value = [
            self.make_model("gemini-flash", ModelProvider.GEMINI, text_to_image=True),
            self.make_model("flux-1.1-pro", ModelProvider.REPLICATE, text_to_image=True),
        ]
        mock_gemini.return_value = {"status": "failed", "reason": "Gemini outage"}
        mock_replicate.return_value = {"status": "succeeded", "image_data": PNG_BYTES, "model": "flux-1.1-pro"}

        result = generate_with_models(prompt="fallback test", model_type="text_to_image")

        assert result["status"] == "succeeded"
        assert result["successful_generations"] == 1
        assert "flux-1.1-pro" in result["results"]

    @patch("purplecrayon.tools.ai_generation_tools.model_manager.get_fallback_models")
    def test_generate_with_models_no_models(self, mock_fallback):
        mock_fallback.return_value = []

        result = generate_with_models(prompt="nothing available")

        assert result["status"] == "failed"
        assert "no available models" in result["reason"].lower()

    @pytest.mark.asyncio
    @patch("purplecrayon.tools.ai_generation_tools.generate_with_models")
    async def test_generate_with_models_async(self, mock_sync):
        mock_sync.return_value = {"status": "succeeded", "successful_generations": 1}

        result = await generate_with_models_async(prompt="async prompt")

        assert result["status"] == "succeeded"
        mock_sync.assert_called_once()


class TestModelManagement:
    @patch("purplecrayon.tools.ai_generation_tools.model_manager.get_model_info")
    def test_list_available_models(self, mock_info):
        mock_info.return_value = {"total_models": 1}

        result = list_available_models()

        assert result["total_models"] == 1
        mock_info.assert_called_once()

    @patch("purplecrayon.tools.ai_generation_tools.model_manager.check_for_updates")
    def test_check_model_updates_delegates(self, mock_check):
        mock_check.return_value = True

        assert check_model_updates(force=True) is True
        mock_check.assert_called_once_with(force=True)

    @patch("purplecrayon.tools.ai_generation_tools.model_manager.check_for_updates")
    def test_check_model_updates_handles_exception(self, mock_check):
        mock_check.side_effect = RuntimeError("network")

        assert check_model_updates(force=True) is False


class TestAsyncErrorHandling:
    @pytest.mark.asyncio
    @patch("purplecrayon.tools.ai_generation_tools.generate_with_gemini")
    @patch("purplecrayon.tools.ai_generation_tools.model_manager.get_fallback_models")
    async def test_generate_with_models_async_timeout(self, mock_fallback, mock_gemini):
        mock_fallback.return_value = [
            ModelConfig(
                name="gemini-flash",
                provider=ModelProvider.GEMINI,
                model_id="gemini-2.5-flash-image",
                display_name="Gemini Flash",
                description="",
                priority=1,
                capabilities={"text_to_image": True},
            )
        ]
        mock_gemini.side_effect = asyncio.TimeoutError("Request timeout")

        result = await generate_with_models_async(prompt="slow prompt")

        assert result["status"] == "failed"
        gemini_result = result["results"]["gemini-flash"]["result"]
        assert gemini_result["status"] == "failed"
        assert "timeout" in gemini_result["reason"].lower()


@pytest.mark.integration
def test_live_generation_single_model():
    prefer_models = []
    if has_api_key("gemini"):
        prefer_models.append("gemini-flash")
    if has_api_key("replicate"):
        prefer_models.append("flux-1.1-pro")
    if not prefer_models:
        pytest.skip("No live API keys configured")

    model = prefer_models[0]
    result = generate_with_models(
        prompt="a minimal black and white icon of a pencil",
        aspect_ratio="1:1",
        model_type="text_to_image",
        with_models=[model],
    )

    assert result["status"] in {"succeeded", "failed"}
    assert model in result["results"]
