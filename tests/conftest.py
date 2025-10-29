import os
import sys
from pathlib import Path
from typing import Dict, Any

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def api_keys() -> Dict[str, str]:
    """Load API keys from environment."""
    return {
        "gemini": os.getenv("GEMINI_API_KEY"),
        "replicate": os.getenv("REPLICATE_API_TOKEN"),
        "unsplash": os.getenv("UNSPLASH_ACCESS_KEY"),
        "pexels": os.getenv("PEXELS_API_KEY"),
        "pixabay": os.getenv("PIXABAY_API_KEY"),
        "firecrawl": os.getenv("FIRECRAWL_API_KEY"),
    }


def has_api_key(key_name: str) -> bool:
    """Check if API key is available."""
    keys = {
        "gemini": os.getenv("GEMINI_API_KEY"),
        "replicate": os.getenv("REPLICATE_API_TOKEN"),
        "unsplash": os.getenv("UNSPLASH_ACCESS_KEY"),
        "pexels": os.getenv("PEXELS_API_KEY"),
        "pixabay": os.getenv("PIXABAY_API_KEY"),
        "firecrawl": os.getenv("FIRECRAWL_API_KEY"),
    }
    return bool(keys.get(key_name))


@pytest.fixture
def temp_assets_dir(tmp_path: Path) -> Path:
    """Create temporary assets directory structure."""
    assets = tmp_path / "assets"
    (assets / "ai").mkdir(parents=True)
    (assets / "downloaded").mkdir()
    (assets / "cloned").mkdir()
    (assets / "proprietary").mkdir()
    return assets


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a sample test image."""
    img = Image.new('RGB', (100, 100), color='red')
    path = tmp_path / "test_image.png"
    img.save(path)
    return path


@pytest.fixture
def sample_image_large(tmp_path: Path) -> Path:
    """Create a larger sample test image."""
    img = Image.new('RGB', (512, 512), color='blue')
    path = tmp_path / "test_image_large.png"
    img.save(path)
    return path


@pytest.fixture
def sample_jpg_image(tmp_path: Path) -> Path:
    """Create a sample JPG test image."""
    img = Image.new('RGB', (200, 200), color='green')
    path = tmp_path / "test_image.jpg"
    img.save(path, 'JPEG')
    return path


@pytest.fixture
def mock_website_content():
    """Mock website content for scraping tests."""
    return """
    <html>
        <body>
            <img src="https://example.com/image1.jpg" alt="Test image 1">
            <img src="https://example.com/image2.png" alt="Test image 2">
            <img src="/relative/image3.jpg" alt="Test image 3">
        </body>
    </html>
    """


@pytest.fixture
def mock_image_urls():
    """Mock image URLs for testing."""
    return [
        "https://example.com/image1.jpg",
        "https://example.com/image2.png", 
        "https://example.com/relative/image3.jpg"
    ]


# Pytest markers for different test types
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring API keys"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "api_gemini: Tests requiring Gemini API key"
    )
    config.addinivalue_line(
        "markers", "api_replicate: Tests requiring Replicate API key"
    )
    config.addinivalue_line(
        "markers", "api_unsplash: Tests requiring Unsplash API key"
    )
    config.addinivalue_line(
        "markers", "api_pexels: Tests requiring Pexels API key"
    )
    config.addinivalue_line(
        "markers", "api_pixabay: Tests requiring Pixabay API key"
    )
    config.addinivalue_line(
        "markers", "api_firecrawl: Tests requiring Firecrawl API key"
    )
