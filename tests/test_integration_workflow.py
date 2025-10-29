import pytest

from purplecrayon.core.runner import PurpleCrayon
from purplecrayon.core.types import AssetRequest, ImageResult


@pytest.mark.asyncio
async def test_source_async_combines_results(monkeypatch, tmp_path):
    crayon = PurpleCrayon(assets_dir=tmp_path)

    async def fake_local(request):
        return [
            ImageResult(
                path=str(tmp_path / "assets" / "ai" / "local.png"),
                source="local",
                provider="catalog",
                width=100,
                height=100,
                format="png",
                description=None,
                match_score=0.9,
            )
        ]

    async def fake_stock(request):
        return [
            ImageResult(
                path="http://example.com/stock.jpg",
                source="stock",
                provider="unsplash",
                width=100,
                height=80,
                format="jpg",
                description=None,
                match_score=0.7,
            )
        ]

    async def fake_ai(request):
        return [
            ImageResult(
                path=str(tmp_path / "assets" / "ai" / "gemini.png"),
                source="ai",
                provider="gemini",
                width=512,
                height=512,
                format="png",
                description=None,
                match_score=None,
            )
        ]

    monkeypatch.setattr(crayon.service, "search_local_assets", fake_local)
    monkeypatch.setattr(crayon.service, "fetch_stock_images", fake_stock)
    monkeypatch.setattr(crayon.service, "generate_ai_images", fake_ai)

    request = AssetRequest(
            description="test image")
    results = await crayon._source_async(request)

    assert len(results) == 3
    assert {img.source for img in results} == {"local", "stock", "ai"}


@pytest.mark.asyncio
async def test_fetch_async_returns_operation(monkeypatch, tmp_path):
    crayon = PurpleCrayon(assets_dir=tmp_path)

    async def fake_fetch(request):
        return [
            ImageResult(
                path="http://example.com/stock.jpg",
                source="stock",
                provider="pexels",
                width=400,
                height=300,
                format="jpg",
                description=None,
                match_score=None,
            )
        ]

    monkeypatch.setattr(crayon.service, "fetch_stock_images", fake_fetch)

    request = AssetRequest(
            description="stock image")
    operation = await crayon.fetch_async(request)

    assert operation.success is True
    assert operation.images[0].provider == "pexels"
