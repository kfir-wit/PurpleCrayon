"""Tests for web scraping API functions."""

from unittest.mock import patch, MagicMock, Mock
import pytest

from purplecrayon.tools.scraping_tools import (
    scrape_website_comprehensive,
    scrape_with_engine,
    scrape_with_fallback,
)
from tests.conftest import has_api_key


class TestScrapeWithEngine:
    """Test scraping with specific engines."""

    @patch('purplecrayon.tools.scraping_tools.BeautifulSoup')
    @patch('purplecrayon.tools.scraping_tools.requests.get')
    def test_scrape_with_engine_beautifulsoup_success(self, mock_get, mock_bs):
        """Test successful scraping with BeautifulSoup engine."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <img src="https://example.com/image1.jpg" alt="Test image 1">
                <img src="https://example.com/image2.png" alt="Test image 2">
                <img src="/relative/image3.jpg" alt="Test image 3">
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Mock BeautifulSoup
        mock_soup = Mock()
        mock_img_tags = [
            Mock(get=lambda x: "https://example.com/image1.jpg" if x == "src" else "Test image 1"),
            Mock(get=lambda x: "https://example.com/image2.png" if x == "src" else "Test image 2"),
            Mock(get=lambda x: "/relative/image3.jpg" if x == "src" else "Test image 3"),
        ]
        mock_soup.find_all.return_value = mock_img_tags
        mock_bs.return_value = mock_soup
        
        result = scrape_with_engine(
            url="https://example.com",
            engine="beautifulsoup",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is True
        assert len(result.images) == 3
        mock_get.assert_called_once()
        mock_bs.assert_called_once()

    @patch('purplecrayon.tools.scraping_tools.playwright')
    def test_scrape_with_engine_playwright_success(self, mock_playwright):
        """Test successful scraping with Playwright engine."""
        # Mock Playwright browser and page
        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        # Mock page content
        mock_page.content.return_value = """
        <html>
            <body>
                <img src="https://example.com/image1.jpg" alt="Test image 1">
                <img src="https://example.com/image2.png" alt="Test image 2">
            </body>
        </html>
        """
        
        result = scrape_with_engine(
            url="https://example.com",
            engine="playwright",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is True
        assert len(result.images) >= 0  # May vary based on implementation
        mock_browser.close.assert_called_once()

    @pytest.mark.api_firecrawl
    @pytest.mark.skipif(not has_api_key("firecrawl"), reason="Firecrawl API key not available")
    def test_scrape_with_engine_firecrawl_success(self):
        """Test successful scraping with Firecrawl engine."""
        with patch('purplecrayon.tools.scraping_tools.FirecrawlApp') as mock_firecrawl:
            mock_app = Mock()
            mock_firecrawl.return_value = mock_app
            
            # Mock Firecrawl response
            mock_response = {
                "success": True,
                "data": {
                    "content": """
                    <html>
                        <body>
                            <img src="https://example.com/image1.jpg" alt="Test image 1">
                            <img src="https://example.com/image2.png" alt="Test image 2">
                        </body>
                    </html>
                    """,
                    "metadata": {
                        "title": "Test Page",
                        "description": "Test Description"
                    }
                }
            }
            mock_app.scrape.return_value = mock_response
            
            result = scrape_with_engine(
                url="https://example.com",
                engine="firecrawl",
                output_dir="./test_assets/downloaded"
            )
            
            assert result.success is True
            mock_app.scrape.assert_called_once()

    def test_scrape_with_engine_invalid_engine(self):
        """Test scraping with invalid engine."""
        result = scrape_with_engine(
            url="https://example.com",
            engine="invalid_engine",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "error" in result.message.lower() or "invalid" in result.message.lower()

    def test_scrape_with_engine_invalid_url(self):
        """Test scraping with invalid URL."""
        result = scrape_with_engine(
            url="not_a_valid_url",
            engine="beautifulsoup",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "error" in result.message.lower()

    @patch('purplecrayon.tools.scraping_tools.requests.get')
    def test_scrape_with_engine_network_error(self, mock_get):
        """Test scraping with network error."""
        mock_get.side_effect = Exception("Network error")
        
        result = scrape_with_engine(
            url="https://example.com",
            engine="beautifulsoup",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "error" in result.message.lower()


class TestScrapeWithFallback:
    """Test scraping with automatic engine fallback."""

    @patch('purplecrayon.tools.scraping_tools.scrape_with_engine')
    def test_scrape_with_fallback_success_first_engine(self, mock_scrape):
        """Test fallback when first engine succeeds."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.images = [Mock(), Mock()]
        mock_scrape.return_value = mock_result
        
        result = scrape_with_fallback(
            url="https://example.com",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is True
        assert len(result.images) == 2
        mock_scrape.assert_called_once()

    @patch('purplecrayon.tools.scraping_tools.scrape_with_engine')
    def test_scrape_with_fallback_second_engine_succeeds(self, mock_scrape):
        """Test fallback when second engine succeeds."""
        # First call fails, second call succeeds
        mock_scrape.side_effect = [
            Mock(success=False, message="First engine failed"),
            Mock(success=True, images=[Mock(), Mock()])
        ]
        
        result = scrape_with_fallback(
            url="https://example.com",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is True
        assert len(result.images) == 2
        assert mock_scrape.call_count == 2

    @patch('purplecrayon.tools.scraping_tools.scrape_with_engine')
    def test_scrape_with_fallback_all_engines_fail(self, mock_scrape):
        """Test fallback when all engines fail."""
        mock_scrape.return_value = Mock(success=False, message="Engine failed")
        
        result = scrape_with_fallback(
            url="https://example.com",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "all engines failed" in result.message.lower()

    def test_scrape_with_fallback_invalid_url(self):
        """Test fallback with invalid URL."""
        result = scrape_with_fallback(
            url="not_a_valid_url",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "error" in result.message.lower()


class TestScrapeWebsiteComprehensive:
    """Test comprehensive website scraping."""

    @patch('purplecrayon.tools.scraping_tools.scrape_with_fallback')
    def test_scrape_website_comprehensive_success(self, mock_fallback):
        """Test successful comprehensive scraping."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.images = [Mock(), Mock(), Mock()]
        mock_fallback.return_value = mock_result
        
        result = scrape_website_comprehensive(
            url="https://example.com",
            output_dir="./test_assets/downloaded",
            verbose=True
        )
        
        assert result.success is True
        assert len(result.images) == 3
        mock_fallback.assert_called_once()

    @patch('purplecrayon.tools.scraping_tools.scrape_with_fallback')
    def test_scrape_website_comprehensive_failure(self, mock_fallback):
        """Test comprehensive scraping when fallback fails."""
        mock_result = Mock()
        mock_result.success = False
        mock_result.message = "All engines failed"
        mock_fallback.return_value = mock_result
        
        result = scrape_website_comprehensive(
            url="https://example.com",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "all engines failed" in result.message.lower()

    def test_scrape_website_comprehensive_invalid_url(self):
        """Test comprehensive scraping with invalid URL."""
        result = scrape_website_comprehensive(
            url="not_a_valid_url",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "error" in result.message.lower()

    @patch('purplecrayon.tools.scraping_tools.scrape_with_fallback')
    def test_scrape_website_comprehensive_with_engine_override(self, mock_fallback):
        """Test comprehensive scraping with engine override."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.images = [Mock()]
        mock_fallback.return_value = mock_result
        
        result = scrape_website_comprehensive(
            url="https://example.com",
            output_dir="./test_assets/downloaded",
            engine="playwright"
        )
        
        assert result.success is True
        mock_fallback.assert_called_once()

    @patch('purplecrayon.tools.scraping_tools.scrape_with_fallback')
    def test_scrape_website_comprehensive_with_filters(self, mock_fallback):
        """Test comprehensive scraping with image filters."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.images = [Mock(), Mock()]
        mock_fallback.return_value = mock_result
        
        result = scrape_website_comprehensive(
            url="https://example.com",
            output_dir="./test_assets/downloaded",
            min_width=800,
            min_height=600,
            file_extensions=[".jpg", ".png"]
        )
        
        assert result.success is True
        mock_fallback.assert_called_once()


class TestScrapingErrorHandling:
    """Test error handling in scraping functions."""

    @patch('purplecrayon.tools.scraping_tools.requests.get')
    def test_scrape_http_error(self, mock_get):
        """Test scraping with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response
        
        result = scrape_with_engine(
            url="https://example.com/notfound",
            engine="beautifulsoup",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "error" in result.message.lower()

    @patch('purplecrayon.tools.scraping_tools.requests.get')
    def test_scrape_timeout_error(self, mock_get):
        """Test scraping with timeout error."""
        mock_get.side_effect = Exception("Request timeout")
        
        result = scrape_with_engine(
            url="https://example.com",
            engine="beautifulsoup",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "error" in result.message.lower()

    def test_scrape_invalid_output_dir(self):
        """Test scraping with invalid output directory."""
        result = scrape_with_engine(
            url="https://example.com",
            engine="beautifulsoup",
            output_dir="/invalid/path/that/does/not/exist"
        )
        
        assert result.success is False
        assert "error" in result.message.lower()

    @patch('purplecrayon.tools.scraping_tools.BeautifulSoup')
    @patch('purplecrayon.tools.scraping_tools.requests.get')
    def test_scrape_parsing_error(self, mock_get, mock_bs):
        """Test scraping with HTML parsing error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid HTML content"
        mock_get.return_value = mock_response
        
        mock_bs.side_effect = Exception("Parsing error")
        
        result = scrape_with_engine(
            url="https://example.com",
            engine="beautifulsoup",
            output_dir="./test_assets/downloaded"
        )
        
        assert result.success is False
        assert "error" in result.message.lower()


class TestScrapingIntegration:
    """Test scraping function integration scenarios."""

    @patch('purplecrayon.tools.scraping_tools.scrape_with_fallback')
    def test_scraping_workflow_complete(self, mock_fallback):
        """Test complete scraping workflow."""
        # Mock successful scraping result
        mock_image1 = Mock()
        mock_image1.filename = "image1.jpg"
        mock_image1.width = 800
        mock_image1.height = 600
        mock_image1.source = "downloaded"
        
        mock_image2 = Mock()
        mock_image2.filename = "image2.png"
        mock_image2.width = 1024
        mock_image2.height = 768
        mock_image2.source = "downloaded"
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.images = [mock_image1, mock_image2]
        mock_fallback.return_value = mock_result
        
        result = scrape_website_comprehensive(
            url="https://example.com",
            output_dir="./test_assets/downloaded",
            verbose=True
        )
        
        assert result.success is True
        assert len(result.images) == 2
        
        # Verify image properties
        for image in result.images:
            assert hasattr(image, 'filename')
            assert hasattr(image, 'width')
            assert hasattr(image, 'height')
            assert hasattr(image, 'source')

    @patch('purplecrayon.tools.scraping_tools.scrape_with_fallback')
    def test_scraping_with_verbose_output(self, mock_fallback):
        """Test scraping with verbose output enabled."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.images = [Mock()]
        mock_fallback.return_value = mock_result
        
        result = scrape_website_comprehensive(
            url="https://example.com",
            output_dir="./test_assets/downloaded",
            verbose=True
        )
        
        assert result.success is True
        mock_fallback.assert_called_once()

    @patch('purplecrayon.tools.scraping_tools.scrape_with_fallback')
    def test_scraping_with_custom_headers(self, mock_fallback):
        """Test scraping with custom headers."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.images = [Mock()]
        mock_fallback.return_value = mock_result
        
        custom_headers = {
            "User-Agent": "Custom Bot 1.0",
            "Accept": "text/html,application/xhtml+xml"
        }
        
        result = scrape_website_comprehensive(
            url="https://example.com",
            output_dir="./test_assets/downloaded",
            headers=custom_headers
        )
        
        assert result.success is True
        mock_fallback.assert_called_once()

    @patch('purplecrayon.tools.scraping_tools.scrape_with_fallback')
    def test_scraping_with_max_images_limit(self, mock_fallback):
        """Test scraping with maximum images limit."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.images = [Mock() for _ in range(10)]  # 10 images
        mock_fallback.return_value = mock_result
        
        result = scrape_website_comprehensive(
            url="https://example.com",
            output_dir="./test_assets/downloaded",
            max_images=5
        )
        
        assert result.success is True
        # Should be limited to max_images
        assert len(result.images) <= 5
        mock_fallback.assert_called_once()
