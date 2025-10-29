from pathlib import Path

import pytest
from PIL import Image

from purplecrayon.core.types import AssetRequest
from purplecrayon.services.image_service import ImageService


def _create_image(path: Path, fmt: str = "JPEG", size=(10, 10)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=(10, 20, 30))
    img.save(path, format=fmt)


@pytest.mark.asyncio
async def test_search_local_assets_matches_jpg_and_jpeg(tmp_path):
    assets_dir = tmp_path / "assets"
    image_path = assets_dir / "ai" / "sample_image.jpeg"
    _create_image(image_path, fmt="JPEG")

    service = ImageService(assets_dir)
    service.catalog.add_asset(image_path)

    request = AssetRequest(
            query="sample", format="jpg")
    results = await service.search_local_assets(request)

    assert len(results) == 1
    assert results[0].path.endswith("sample_image.jpeg")


@pytest.mark.asyncio
async def test_fetch_stock_images_respects_preferred_sources(monkeypatch, tmp_path):
    service = ImageService(tmp_path)
    calls = {"unsplash": 0, "pexels": 0, "pixabay": 0}

    async def fake_unsplash(*args, **kwargs):
        calls["unsplash"] += 1
        return []

    async def fake_pexels(*args, **kwargs):
        calls["pexels"] += 1
        return []

    async def fake_pixabay(*args, **kwargs):
        calls["pixabay"] += 1
        return []

    monkeypatch.setattr("purplecrayon.services.image_service.search_unsplash", fake_unsplash)
    monkeypatch.setattr("purplecrayon.services.image_service.search_pexels", fake_pexels)
    monkeypatch.setattr("purplecrayon.services.image_service.search_pixabay", fake_pixabay)

    request = AssetRequest(
            query="test", preferred_sources=["pexels"])
    await service.fetch_stock_images(request)

    assert calls == {"unsplash": 0, "pexels": 1, "pixabay": 0}


@pytest.mark.asyncio
async def test_generate_ai_images_respects_preferred_sources(monkeypatch, tmp_path):
    service = ImageService(tmp_path)

    async def fake_gemini(*args, **kwargs):
        return {"status": "succeeded", "url": "http://example.com/gemini.jpg"}

    async def fake_imagen(*args, **kwargs):
        raise AssertionError("Imagen should not be invoked when not preferred")

    monkeypatch.setattr("purplecrayon.services.image_service.generate_with_gemini_async", fake_gemini)
    monkeypatch.setattr("purplecrayon.services.image_service.generate_with_replicate", fake_imagen)

    request = AssetRequest(
            query="test", preferred_sources=["gemini"])
    results = await service.generate_ai_images(request)

    assert len(results) == 1
    assert results[0].provider == "gemini"


def test_dict_to_image_result_handles_inline_data(monkeypatch, tmp_path):
    service = ImageService(tmp_path)
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir(parents=True, exist_ok=True)

    # Create simple PNG bytes
    import io

    buffer = io.BytesIO()
    Image.new("RGB", (16, 8), color="red").save(buffer, format="PNG")
    png_bytes = buffer.getvalue()

    saved_path = str(ai_dir / "gemini_123.png")
    monkeypatch.setattr("purplecrayon.tools.file_tools.save_file", lambda content, path: saved_path)
    monkeypatch.setattr("time.time", lambda: 123)

    result = service._dict_to_image_result(
        {
            "image_data": png_bytes,
            "format": "png",
            "description": "generated",
        },
        source="ai",
        provider="gemini",
    )

    assert result.path == saved_path
    assert result.width == 16
    assert result.height == 8
    assert result.format == "png"
    assert result.description == "generated"
