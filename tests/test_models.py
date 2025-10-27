from datetime import datetime
from pathlib import Path

import pytest

from purplecrayon.models.asset_request import (
    AssetRequest as ModelAssetRequest,
    ImageCloneRequest,
    ImageModificationRequest,
)
from purplecrayon.models.image_result import ImageResult as ModelImageResult, OperationResult as ModelOperationResult, ImageSource, ImageStatus
from purplecrayon.models.agent_state import AgentState, AgentMode


def test_asset_request_normalizes_fields():
    request = ModelAssetRequest(
        query="Panda artwork",
        format="JPG",
        quality="HIGH",
        providers=["Gemini", "Imagen"],
    )

    assert request.format == "jpg"
    assert request.quality == "high"
    assert request.providers == ["gemini", "imagen"]


def test_asset_request_invalid_provider_raises():
    with pytest.raises(ValueError, match="Provider 'invalid' not supported"):
        ModelAssetRequest(query="Test", providers=["invalid"])


def test_image_modification_request_validates_input_image(tmp_path):
    image_path = tmp_path / "example.png"
    image_path.write_bytes(b"fake")

    request = ImageModificationRequest(
        query="Modify image",
        input_image=image_path,
        modification_prompt="Add sparkle",
    )

    assert request.input_image == image_path

    with pytest.raises(ValueError, match="Input image does not exist"):
        ImageModificationRequest(
            query="Missing image",
            input_image=image_path.parent / "missing.png",
            modification_prompt="none",
        )


def test_image_clone_request_requires_source_image(tmp_path):
    source = tmp_path / "source.jpg"
    source.write_bytes(b"data")

    request = ImageCloneRequest(
        query="Clone image",
        source_image=source,
    )

    assert request.source_image == source

    directory = tmp_path / "folder"
    directory.mkdir()
    with pytest.raises(ValueError, match="Source path is not a file"):
        ImageCloneRequest(query="X", source_image=directory)


def test_image_result_validators(tmp_path):
    image_path = tmp_path / "output.png"
    image_path.write_bytes(b"content")

    result = ModelImageResult(
        id="123",
        filename="output.png",
        path=image_path,
        width=10,
        height=20,
        format="PNG",
        size_bytes=4,
        prompt="desc",
        provider="gemini",
        model="gpt",
        source=ImageSource.GENERATED,
    )

    assert result.format == "png"
    assert result.path == image_path

    with pytest.raises(ValueError, match="Path must be absolute"):
        ModelImageResult(
            id="999",
            filename="bad.png",
            path=Path("relative.png"),
            width=1,
            height=1,
            format="png",
            size_bytes=1,
            prompt="desc",
            provider="p",
            model="m",
            source=ImageSource.GENERATED,
        )


def test_operation_result_mark_completed(tmp_path):
    image_path = tmp_path / "img.png"
    image_path.write_bytes(b"data")
    model_image = ModelImageResult(
        id="abc",
        filename="img.png",
        path=image_path,
        width=100,
        height=50,
        format="png",
        size_bytes=10,
        prompt="p",
        provider="prov",
        model="model",
        source=ImageSource.GENERATED,
        quality_score=0.8,
    )

    operation = ModelOperationResult(
        success=False,
        operation_type="Generate",
        total_images=0,
        started_at=datetime.now(),
    )
    operation.add_image(model_image)
    operation.mark_completed()

    assert operation.success is False
    assert operation.total_images == 1
    assert operation.total_size_bytes == 10
    assert operation.average_quality_score == 0.8
    assert operation.duration_seconds is not None


def test_agent_state_lifecycle(tmp_path):
    agent = AgentState(mode=AgentMode.GENERATE, session_id="session-1")

    request = ModelAssetRequest(query="Generate Panda")
    agent.start_operation(request)
    assert agent.is_processing is True
    assert agent.current_operation is not None

    class DummyImage:
        def __init__(self):
            self.status = ImageStatus.COMPLETED
            self.quality_score = 0.9

    agent.current_operation.images.append(DummyImage())
    agent.complete_operation(success=True)

    assert agent.is_processing is False
    assert agent.total_operations == 1
    assert agent.total_images_generated == 1
    assert agent.completed_operations[-1].success is True

    agent.add_error("boom")
    agent.add_warning("careful")
    assert agent.errors == ["boom"]
    assert agent.warnings == ["careful"]
