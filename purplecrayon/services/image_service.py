from pathlib import Path
from typing import List, Optional
import asyncio

from ..core.types import AssetRequest, ImageResult
from ..tools.asset_management_tools import AssetCatalog
from ..tools.stock_photo_tools import search_unsplash, search_pexels, search_pixabay
from ..tools.ai_generation_tools import generate_with_gemini_async, generate_with_imagen
from ..tools.scraping_tools import scrape_with_engine, scrape_with_fallback
from ..tools.smart_selection_tools import select_best_images, extract_size_from_prompt
from ..tools.file_tools import download_file
from ..tools.image_validation_tools import validate_all_images


class ImageService:
    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir
        self.catalog = AssetCatalog(assets_dir / "catalog.yaml")
    
    async def search_local_assets(self, request: AssetRequest) -> List[ImageResult]:
        """Search the local catalog and return matching assets."""
        if "local" in request.exclude_sources:
            return []
        if request.preferred_sources and "local" not in request.preferred_sources:
            return []

        query = request.description or ""
        tags = request.tags or []
        candidates = self.catalog.search_assets(query=query, tags=tags)

        results: List[ImageResult] = []
        for asset in candidates:
            rel_path = asset.get("path")
            if not rel_path:
                continue

            file_path = self.assets_dir / rel_path
            if not file_path.exists():
                # Skip missing files silently; catalog sync will remove them later
                continue

            width = asset.get("width")
            height = asset.get("height")
            fmt = (asset.get("format") or "").lower()
            has_alpha = asset.get("has_alpha")

            if request.format and fmt and fmt != request.format.lower():
                continue
            if request.has_alpha is True and not has_alpha:
                continue
            if request.has_alpha is False and has_alpha:
                continue

            if request.width and width and width < request.width:
                continue
            if request.height and height and height < request.height:
                continue
            if request.min_width and width and width < request.min_width:
                continue
            if request.min_height and height and height < request.min_height:
                continue

            if request.orientation and width and height:
                if width == height:
                    orientation = "square"
                elif width > height:
                    orientation = "landscape"
                else:
                    orientation = "portrait"
                if orientation != request.orientation:
                    continue

            results.append(
                ImageResult(
                    path=str(file_path),
                    source="local",
                    provider="catalog",
                    width=width or 0,
                    height=height or 0,
                    format=fmt or "unknown",
                    description=asset.get("description"),
                    match_score=None,
                )
            )

            if len(results) >= request.max_results:
                break

        return results
    
    async def fetch_stock_images(self, request: AssetRequest) -> List[ImageResult]:
        """Fetch from all stock photo APIs."""
        results = []
        
        # Extract target size/orientation hint for downstream services
        target_hint: Optional[str] = None
        if request.orientation:
            target_hint = request.orientation
        elif request.width and request.height:
            target_hint = f"{request.width}x{request.height}"
        elif request.aspect_ratio:
            target_hint = request.aspect_ratio
        
        # Search all stock photo APIs
        if "unsplash" not in request.exclude_sources:
            try:
                unsplash_results = await search_unsplash(
                    request.description, 
                    per_page=request.max_results,
                    target_size=target_hint
                )
                for item in unsplash_results:
                    results.append(self._dict_to_image_result(item, "stock", "unsplash"))
            except Exception as e:
                print(f"Unsplash search failed: {e}")
        
        if "pexels" not in request.exclude_sources:
            try:
                pexels_results = await search_pexels(
                    request.description,
                    per_page=request.max_results,
                    target_size=target_hint
                )
                for item in pexels_results:
                    results.append(self._dict_to_image_result(item, "stock", "pexels"))
            except Exception as e:
                print(f"Pexels search failed: {e}")
        
        if "pixabay" not in request.exclude_sources:
            try:
                pixabay_results = await search_pixabay(
                    request.description,
                    per_page=request.max_results,
                    target_size=target_hint
                )
                for item in pixabay_results:
                    results.append(self._dict_to_image_result(item, "stock", "pixabay"))
            except Exception as e:
                print(f"Pixabay search failed: {e}")
        
        return results
    
    async def generate_ai_images(self, request: AssetRequest) -> List[ImageResult]:
        """Generate using all AI providers."""
        results = []
        
        # Generate with Gemini
        if "gemini" not in request.exclude_sources:
            try:
                gemini_result = await generate_with_gemini_async(
                    request.description,
                    aspect_ratio=request.aspect_ratio or "1:1"
                )
                if gemini_result.get("status") == "succeeded":
                    results.append(self._dict_to_image_result(gemini_result, "ai", "gemini"))
            except Exception as e:
                print(f"Gemini generation failed: {e}")
        
        # Generate with Imagen
        if "imagen" not in request.exclude_sources:
            try:
                imagen_result = await generate_with_imagen(request.description)
                if imagen_result.get("status") in {"success", "succeeded"}:
                    results.append(self._dict_to_image_result(imagen_result, "ai", "imagen"))
            except Exception as e:
                print(f"Imagen generation failed: {e}")
        
        return results
    
    async def scrape_website(self, url: str, engine: Optional[str] = None) -> List[ImageResult]:
        """Scrape images from URL using specified engine or fallback."""
        results = []
        
        try:
            # Use specific engine or fallback
            if engine:
                scrape_result = await scrape_with_engine(url, engine)
            else:
                scrape_result = await scrape_with_fallback(url)
            
            if scrape_result.get("status") == "success":
                images = scrape_result.get("images", [])
                used_engine = scrape_result.get("engine", "unknown")
                
                for i, image_url in enumerate(images):
                    # Create basic result for scraped image
                    results.append(ImageResult(
                        path=image_url,
                        source="scraped",
                        provider=used_engine,
                        width=0,  # Will be updated after download
                        height=0,
                        format="unknown",
                        description=f"Scraped image {i+1}",
                        match_score=None
                    ))
            else:
                print(f"Website scraping failed: {scrape_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Website scraping failed: {e}")
        
        return results
    
    def _dict_to_image_result(self, data: dict, source: str, provider: str) -> ImageResult:
        """Convert internal dict to ImageResult."""
        # Handle image data (bytes) by saving to disk
        if "image_data" in data and data["image_data"]:
            from ..tools.file_tools import save_file
            import time
            
            # Generate filename with timestamp
            timestamp = int(time.time())
            format_ext = data.get("format", "png")
            filename = f"{provider}_{timestamp}.{format_ext}"
            file_path = self.assets_dir / "ai" / filename
            
            # Save image data to disk
            saved_path = save_file(data["image_data"], str(file_path))
            
            # Get image dimensions
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(data["image_data"]))
            width, height = img.size
            
            return ImageResult(
                path=saved_path,
                source=source,
                provider=provider,
                width=width,
                height=height,
                format=format_ext,
                description=data.get("description"),
                match_score=data.get("match_score")
            )
        else:
            # Handle URL-based results (stock photos, etc.)
            return ImageResult(
                path=data.get("url", ""),
                source=source,
                provider=provider,
                width=data.get("width", 0),
                height=data.get("height", 0),
                format=data.get("format", "unknown"),
                description=data.get("description"),
                match_score=data.get("match_score")
            )
