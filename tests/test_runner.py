import pytest

from purplecrayon.core.runner import PurpleCrayon
from purplecrayon.core.types import AssetRequest, ImageResult


@pytest.mark.asyncio
async def test_source_async_returns_success(monkeypatch, tmp_path):
    crayon = PurpleCrayon(assets_dir=tmp_path)
    sample_result = [
        ImageResult(
            path="mock.jpg",
            source="stock",
            provider="unsplash",
            width=100,
            height=100,
            format="jpg",
            description=None,
            match_score=None,
        )
    ]

    async def fake_source_async(self, request):
        return sample_result

    monkeypatch.setattr(PurpleCrayon, "_source_async", fake_source_async, raising=False)

    request = AssetRequest(
            query="test image")
    result = await crayon.source_async(request)

    assert result.success is True
    assert result.images == sample_result


@pytest.mark.asyncio
async def test_source_sync_raises_inside_event_loop(tmp_path):
    crayon = PurpleCrayon(assets_dir=tmp_path)
    request = AssetRequest(
            query="test image")

    with pytest.raises(RuntimeError, match="Use await PurpleCrayon.source_async"):
        crayon.source(request)
