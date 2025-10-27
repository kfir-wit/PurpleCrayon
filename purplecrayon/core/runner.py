from pathlib import Path
from typing import Optional, Dict, Any, List
import asyncio

from .types import AssetRequest, OperationResult, ImageResult
from .parsers import markdownRequest
from ..services.image_service import ImageService
from ..tools.asset_management_tools import AssetCatalog
from ..tools.image_renaming_tools import scan_and_rename_assets
from ..tools.clone_image_tools import clone_image, clone_images_from_directory
from ..tools.image_augmentation_tools import augment_image, augment_images_from_directory


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
        for subdir in ["ai", "stock", "proprietary", "downloaded", "cloned"]:
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

    async def scrape_async(self, url: str, engine: Optional[str] = None, verbose: bool = False) -> OperationResult:
        """Async entry point to scrape all images from a URL.
        
        Args:
            url: URL to scrape
            engine: Scraping engine to use ('firecrawl', 'playwright', 'beautifulsoup', or None for auto-fallback)
            verbose: Enable verbose debugging output
        """
        try:
            results = await self.service.scrape_website(url, engine, verbose)
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

    def scrape(self, url: str, engine: Optional[str] = None, verbose: bool = False) -> OperationResult:
        """Scrape all images from a URL.
        
        Args:
            url: URL to scrape
            engine: Scraping engine to use ('firecrawl', 'playwright', 'beautifulsoup', or None for auto-fallback)
            verbose: Enable verbose debugging output
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.scrape_async(url, engine, verbose))
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
    
    def cleanup_assets(self, remove_junk: bool = True, format: str = "both") -> Dict[str, Any]:
        """Clean up corrupted and junk images, then update catalog."""
        try:
            # Clean up and update catalog
            cleanup_stats = self.catalog.cleanup_and_update_catalog(self.assets_dir, remove_junk, format)
            
            return {
                "success": True,
                "cleanup_stats": cleanup_stats,
                "final_stats": self.catalog.get_stats()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def clone_async(
        self,
        source: str | Path,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        format: Optional[str] = None,
        style: Optional[str] = None,
        guidance: Optional[str] = None,
        similarity_threshold: float = 0.7,
        max_images: Optional[int] = None
    ) -> OperationResult:
        """
        Clone images from downloaded/ or proprietary/ folders using AI.
        
        Args:
            source: Path to source image file or directory
            width: Desired width for cloned images
            height: Desired height for cloned images
            format: Output format (if None, uses original format)
            style: Style guidance (photorealistic, artistic, etc.)
            guidance: Additional guidance for generation
            similarity_threshold: Maximum allowed similarity to original
            max_images: Maximum number of images to process (for directory input)
            
        Returns:
            OperationResult containing clone results
        """
        try:
            source_path = Path(source)
            output_dir = self.assets_dir / "cloned"
            
            # Determine if source is file or directory
            if source_path.is_file():
                # Single file cloning
                print(f"🎨 Cloning single image: {source_path.name}")
                result = await clone_image(
                    source_path,
                    width=width,
                    height=height,
                    format=format,
                    style=style,
                    guidance=guidance,
                    similarity_threshold=similarity_threshold,
                    output_dir=output_dir
                )
                
                if result["success"]:
                    # Create ImageResult for the cloned image
                    cloned_image = ImageResult(
                        path=result["clone_path"],
                        source="cloned",
                        provider="ai_clone",
                        width=result["clone_dimensions"][0],
                        height=result["clone_dimensions"][1],
                        format=result["format"],
                        description=f"Cloned from {result['original_filename']}",
                        match_score=None
                    )
                    
                    return OperationResult(
                        success=True,
                        message=f"Successfully cloned {result['original_filename']} -> {result['clone_filename']}",
                        images=[cloned_image]
                    )
                else:
                    return OperationResult(
                        success=False,
                        message=f"Failed to clone image: {result['error']}",
                        images=[]
                    )
            
            elif source_path.is_dir():
                # Directory batch cloning
                print(f"🎨 Cloning all images from directory: {source_path}")
                result = await clone_images_from_directory(
                    source_path,
                    output_dir=output_dir,
                    width=width,
                    height=height,
                    format=format,
                    style=style,
                    guidance=guidance,
                    similarity_threshold=similarity_threshold,
                    max_images=max_images
                )
                
                if result["success"]:
                    # Create ImageResult objects for successful clones
                    cloned_images = []
                    for clone_result in result["results"]:
                        if clone_result["success"]:
                            cloned_image = ImageResult(
                                path=clone_result["clone_path"],
                                source="cloned",
                                provider="ai_clone",
                                width=clone_result["clone_dimensions"][0],
                                height=clone_result["clone_dimensions"][1],
                                format=clone_result["format"],
                                description=f"Cloned from {clone_result['original_filename']}",
                                match_score=None
                            )
                            cloned_images.append(cloned_image)
                    
                    return OperationResult(
                        success=True,
                        message=f"Successfully cloned {result['successful']}/{result['total_images']} images",
                        images=cloned_images
                    )
                else:
                    return OperationResult(
                        success=False,
                        message=f"Failed to clone images from directory: {result['error']}",
                        images=[]
                    )
            else:
                return OperationResult(
                    success=False,
                    message=f"Source path does not exist: {source_path}",
                    images=[]
                )
                
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Clone operation failed: {str(e)}",
                images=[]
            )
    
    def clone(
        self,
        source: str | Path,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        format: Optional[str] = None,
        style: Optional[str] = None,
        guidance: Optional[str] = None,
        similarity_threshold: float = 0.7,
        max_images: Optional[int] = None
    ) -> OperationResult:
        """
        Clone images synchronously (wrapper around clone_async).
        
        Args:
            source: Path to source image file or directory
            width: Desired width for cloned images
            height: Desired height for cloned images
            format: Output format (if None, uses original format)
            style: Style guidance (photorealistic, artistic, etc.)
            guidance: Additional guidance for generation
            similarity_threshold: Maximum allowed similarity to original
            max_images: Maximum number of images to process (for directory input)
            
        Returns:
            OperationResult containing clone results
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.clone_async(
                source=source,
                width=width,
                height=height,
                format=format,
                style=style,
                guidance=guidance,
                similarity_threshold=similarity_threshold,
                max_images=max_images
            ))
        raise RuntimeError("PurpleCrayon.clone() cannot be used inside an active event loop. Use await PurpleCrayon.clone_async(...) instead.")
    
    async def augment_async(
        self,
        image_path: str | Path,
        prompt: str,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        format: Optional[str] = None,
        output_dir: Optional[str | Path] = None,
        **kwargs
    ) -> OperationResult:
        """
        Augment an existing image using AI image-to-image generation.
        
        Args:
            image_path: Path to the source image
            prompt: Modification instructions
            width: Optional output width
            height: Optional output height
            format: Output format (if None, uses original format)
            output_dir: Optional custom output directory
            **kwargs: Additional parameters
            
        Returns:
            OperationResult containing the augmented image
        """
        try:
            # Determine output directory
            if output_dir is None:
                output_dir = self.assets_dir / "ai"
            else:
                output_dir = Path(output_dir)
                
            # Determine output format
            if format is None:
                format = Path(image_path).suffix[1:] or "png"
                
            # Augment the image
            result = await augment_image(
                image_path=image_path,
                prompt=prompt,
                width=width,
                height=height,
                output_format=format,
                output_dir=output_dir,
                **kwargs
            )
            
            if result.success:
                # Create ImageResult for the augmented image
                augmented_image = ImageResult(
                    path=result.data["output_path"],
                    source="ai",
                    provider=result.data["provider"],
                    width=result.data["width"],
                    height=result.data["height"],
                    format=result.data["format"],
                    description=f"Augmented: {prompt}",
                    match_score=None
                )
                
                return OperationResult(
                    success=True,
                    message=f"Successfully augmented image: {result.data['output_path']}",
                    images=[augmented_image]
                )
            else:
                return OperationResult(
                    success=False,
                    message=f"Failed to augment image: {result.message}",
                    images=[]
                )
                
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Augment operation failed: {str(e)}",
                images=[]
            )
    
    def augment(
        self,
        image_path: str | Path,
        prompt: str,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        format: Optional[str] = None,
        output_dir: Optional[str | Path] = None,
        **kwargs
    ) -> OperationResult:
        """
        Augment an existing image synchronously (wrapper around augment_async).
        
        Args:
            image_path: Path to the source image
            prompt: Modification instructions
            width: Optional output width
            height: Optional output height
            format: Output format (if None, uses original format)
            output_dir: Optional custom output directory
            **kwargs: Additional parameters
            
        Returns:
            OperationResult containing the augmented image
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.augment_async(
                image_path=image_path,
                prompt=prompt,
                width=width,
                height=height,
                format=format,
                output_dir=output_dir,
                **kwargs
            ))
        raise RuntimeError("PurpleCrayon.augment() cannot be used inside an active event loop. Use await PurpleCrayon.augment_async(...) instead.")
    
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
