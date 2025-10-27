from pathlib import Path

from PIL import Image

from purplecrayon.tools.asset_management_tools import AssetCatalog


def _create_image(path: Path, fmt: str = "JPEG", size=(10, 10)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=(123, 123, 123))
    img.save(path, format=fmt)


def test_scan_and_update_assets_does_not_duplicate_existing_entries(tmp_path):
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
