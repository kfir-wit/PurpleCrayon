from purplecrayon.tools.smart_selection_tools import select_best_images, extract_size_from_prompt


def test_select_best_images_prioritises_exact_matches():
    images = [
        {"width": 1920, "height": 1080, "aspect_ratio": 16 / 9, "id": "exact"},
        {"width": 1900, "height": 1070, "aspect_ratio": 16 / 9, "id": "close"},
        {"width": 1080, "height": 1920, "aspect_ratio": 0.56, "id": "portrait"},
    ]

    selected = select_best_images(images, 1920, 1080, max_images=2)
    ids = [img["id"] for img in selected]
    assert ids[0] == "exact"
    assert "close" in ids


def test_select_best_images_handles_empty_list():
    assert select_best_images([], 100, 100) == []


def test_extract_size_from_prompt_patterns():
    assert extract_size_from_prompt("Create a 800x600 banner") == (800, 600)
    assert extract_size_from_prompt("Desktop wallpaper scene") == (1920, 1080)
    assert extract_size_from_prompt("portrait poster") == (1080, 1920)
    assert extract_size_from_prompt("square icon") == (1024, 1024)
