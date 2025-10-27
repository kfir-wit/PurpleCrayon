from pathlib import Path

from purplecrayon.utils.file_utils import get_unique_filename, safe_save_file, safe_save_text


def test_get_unique_filename_generates_incremental_names(tmp_path):
    base = tmp_path / "output" / "image.png"
    base.parent.mkdir(parents=True, exist_ok=True)
    base.write_bytes(b"first")

    unique = get_unique_filename(base, prefix="augmented", suffix="_v1")
    assert unique.name.startswith("augmented_image_v1")
    assert unique.suffix == ".png"

    unique.touch()
    second = get_unique_filename(base, prefix="augmented", suffix="_v1")
    assert second != unique
    assert second.exists() is False


def test_safe_save_file_creates_directories_and_resolves_conflicts(tmp_path):
    target = tmp_path / "nested" / "image.png"
    first_path = safe_save_file(b"content", target)
    assert first_path.exists()
    assert first_path.read_bytes() == b"content"

    second_path = safe_save_file(b"more", target)
    assert second_path.exists()
    assert second_path != first_path
    assert second_path.read_bytes() == b"more"


def test_safe_save_text(tmp_path):
    target = tmp_path / "logs" / "entry.txt"
    saved = safe_save_text("hello", target, prefix="run")
    assert saved.exists()
    assert saved.read_text() == "hello"
