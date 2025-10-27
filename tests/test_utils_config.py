from pathlib import Path

import pytest

from purplecrayon.utils import config


def test_init_environment_creates_directories(tmp_path, monkeypatch):
    downloads = tmp_path / "downloads"
    originals = tmp_path / "originals"
    processed = tmp_path / "processed"

    monkeypatch.setattr(config, "DOWNLOADS_DIR", downloads)
    monkeypatch.setattr(config, "ORIGINALS_DIR", originals)
    monkeypatch.setattr(config, "PROCESSED_DIR", processed)

    calls = []
    monkeypatch.setattr(config, "load_dotenv", lambda: calls.append(True))

    config.init_environment()

    assert downloads.is_dir()
    assert originals.is_dir()
    assert processed.is_dir()
    assert calls == [True]


def test_load_graphics_sources_handles_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "missing.yaml")
    assert config.load_graphics_sources() == {}

    data = {"sources": ["one"]}
    config_path = tmp_path / "config.yaml"
    config_path.write_text("sources:\n  - one\n")
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    assert config.load_graphics_sources() == data


def test_ensure_parent_dir_creates_parents(tmp_path):
    target = tmp_path / "nested" / "file.txt"
    config.ensure_parent_dir(target)
    assert target.parent.is_dir()
