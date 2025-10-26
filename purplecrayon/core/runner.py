from pathlib import Path
from typing import Optional, Dict, Any, List
import asyncio

from .types import AssetRequest, OperationResult, ImageResult
from .parsers import markdownRequest
from ..services.image_service import ImageService
from ..tools.asset_management_tools import AssetCatalog
from ..tools.image_renaming_tools import scan_and_rename_assets


class PurpleCrayon:
    def __init__(self, assets_dir: str = "./assets", config: Optional[dict] = None):
        """Initialize with assets directory and optional config."""
        self.assets_dir = Path(assets_dir)
        self.config = config or {}
        self._ensure_asset_structure()
        self.catalog = AssetCatalog(self.assets_dir / "catalog.yaml")
        self.service = ImageService(self.assets_dir)
    
    def _ensure_asset_structure(self):
        """Create standard asset structure if not exists."""
        # Create standard directories
        for subdir in ["ai", "stock", "proprietary", "downloaded"]:
            (self.assets_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    async def source_async(self, request: AssetRequest) -> OperationResult:
        """Async entry point for sourcing assets across all providers."""
        try:
            results = await self._source_async(request)
            return OperationResult(
                success=True,
                message=f"Found {len(results)} images from all sources",
                images=results
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Source operation failed: {str(e)}",
                images=[],
                error_code="SOURCE_ERROR"
            )

    def source(self, request: AssetRequest) -> OperationResult:
        """Check local assets, fetch from stock sites, and generate with AI."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.source_async(request))
        raise RuntimeError("PurpleCrayon.source() cannot be used inside an active event loop. Use await PurpleCrayon.source_async(...) instead.")

    async def fetch_async(self, request: AssetRequest) -> OperationResult:
        """Async entry point to fetch images only from stock photo websites."""
        try:
            results = await self.service.fetch_stock_images(request)
            return OperationResult(
                success=True,
                message=f"Fetched {len(results)} stock images",
                images=results
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Fetch operation failed: {str(e)}",
                images=[],
                error_code="FETCH_ERROR"
            )

    def fetch(self, request: AssetRequest) -> OperationResult:
        """Fetch images only from stock photo websites."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.fetch_async(request))
        raise RuntimeError("PurpleCrayon.fetch() cannot be used inside an active event loop. Use await PurpleCrayon.fetch_async(...) instead.")

    async def generate_async(self, request: AssetRequest) -> OperationResult:
        """Async entry point to generate images using AI providers."""
        try:
            results = await self.service.generate_ai_images(request)
            return OperationResult(
                success=True,
                message=f"Generated {len(results)} AI images",
                images=results
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Generate operation failed: {str(e)}",
                images=[],
                error_code="GENERATE_ERROR"
            )

    def generate(self, request: AssetRequest) -> OperationResult:
        """Generate images only using AI providers."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.generate_async(request))
        raise RuntimeError("PurpleCrayon.generate() cannot be used inside an active event loop. Use await PurpleCrayon.generate_async(...) instead.")

    async def scrape_async(self, url: str, engine: Optional[str] = None) -> OperationResult:
        """Async entry point to scrape all images from a URL.
        
        Args:
            url: URL to scrape
            engine: Scraping engine to use ('firecrawl', 'playwright', 'beautifulsoup', or None for auto-fallback)
        """
        try:
            results = await self.service.scrape_website(url, engine)
            return OperationResult(
                success=True,
                message=f"Scraped {len(results)} images from {url}",
                images=results
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Scrape operation failed: {str(e)}",
                images=[],
                error_code="SCRAPE_ERROR"
            )

    def scrape(self, url: str, engine: Optional[str] = None) -> OperationResult:
        """Scrape all images from a URL.
        
        Args:
            url: URL to scrape
            engine: Scraping engine to use ('firecrawl', 'playwright', 'beautifulsoup', or None for auto-fallback)
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.scrape_async(url, engine))
        raise RuntimeError("PurpleCrayon.scrape() cannot be used inside an active event loop. Use await PurpleCrayon.scrape_async(...) instead.")

    def modify(self, image_path: str, prompt: str, **kwargs) -> OperationResult:
        """Modify existing image with AI (future implementation)."""
        return OperationResult(
            success=False,
            message="Modify functionality not yet implemented",
            images=[],
            error_code="NOT_IMPLEMENTED"
        )
    
    def sort_catalog(self) -> Dict[str, Any]:
        """Sort and update asset catalog."""
        try:
            # Rename images with proper naming convention
            rename_stats = scan_and_rename_assets(self.assets_dir)
            
            # Update catalog
            catalog_stats = self.catalog.update_catalog_from_assets(self.assets_dir)
            
            return {
                "success": True,
                "rename_stats": rename_stats,
                "catalog_stats": catalog_stats,
                "final_stats": self.catalog.get_stats()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _source_async(self, request: AssetRequest) -> List[ImageResult]:
        """Async implementation of source method."""
        results = []
        
        # Search local assets
        local_results = await self.service.search_local_assets(request)
        results.extend(local_results)
        
        # Fetch stock images
        stock_results = await self.service.fetch_stock_images(request)
        results.extend(stock_results)
        
        # Generate AI images
        ai_results = await self.service.generate_ai_images(request)
        results.extend(ai_results)
        
        return results
