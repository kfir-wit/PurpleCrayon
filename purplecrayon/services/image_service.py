from pathlib import Path
from typing import List, Optional
import asyncio

from ..core.types import AssetRequest, ImageResult
from ..tools.asset_management_tools import AssetCatalog
from ..tools.stock_photo_tools import search_unsplash, search_pexels, search_pixabay
from ..tools.ai_generation_tools import generate_with_gemini_async, generate_with_imagen
from ..tools.scraping_tools import scrape_with_engine, scrape_with_fallback, scrape_website_comprehensive
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

        def format_matches(asset_format: str) -> bool:
            if not request.format:
                return True
            desired = request.format.lower()
            asset_format = (asset_format or "").lower()
            if asset_format == desired:
                return True
            if desired in {"jpg", "jpeg"} and asset_format in {"jpg", "jpeg"}:
                return True
            return False

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

            if not format_matches(fmt):
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
        preferred = {src.lower() for src in request.preferred_sources if src}
        exclude = {src.lower() for src in request.exclude_sources if src}

        def provider_allowed(name: str, category: str) -> bool:
            name = name.lower()
            category = category.lower()
            if name in exclude or category in exclude:
                return False
            if not preferred:
                return True
            return (
                name in preferred
                or category in preferred
                or "all" in preferred
            )
        
        # Extract target size/orientation hint for downstream services
        target_hint: Optional[str] = None
        if request.orientation:
            target_hint = request.orientation
        elif request.width and request.height:
            target_hint = f"{request.width}x{request.height}"
        elif request.aspect_ratio:
            target_hint = request.aspect_ratio
        
        # Search all stock photo APIs
        if provider_allowed("unsplash", "stock"):
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
        
        if provider_allowed("pexels", "stock"):
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
        
        if provider_allowed("pixabay", "stock"):
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
        preferred = {src.lower() for src in request.preferred_sources if src}
        exclude = {src.lower() for src in request.exclude_sources if src}

        def provider_allowed(name: str, category: str) -> bool:
            name = name.lower()
            category = category.lower()
            if name in exclude or category in exclude:
                return False
            if not preferred:
                return True
            return (
                name in preferred
                or category in preferred
                or "all" in preferred
            )
        
        # Generate with Gemini
        if provider_allowed("gemini", "ai"):
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
        if provider_allowed("imagen", "ai"):
            try:
                imagen_result = await generate_with_imagen(request.description)
                if imagen_result.get("status") in {"success", "succeeded"}:
                    results.append(self._dict_to_image_result(imagen_result, "ai", "imagen"))
            except Exception as e:
                print(f"Imagen generation failed: {e}")
        
        return results
    
    async def scrape_website(self, url: str, engine: Optional[str] = None, verbose: bool = False) -> List[ImageResult]:
        """Scrape images from URL using specified engine or fallback with downloading."""
        results = []
        
        try:
            # Set up download directory
            download_dir = self.assets_dir / "downloaded"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Use comprehensive scraping with downloading
            scrape_result = await scrape_website_comprehensive(url, download_dir, verbose, engine)
            
            if scrape_result.get("status") == "success":
                used_engine = scrape_result.get("engine", "unknown")
                downloaded_images = scrape_result.get("downloaded_images", [])
                
                # Create results for downloaded images
                for i, img_data in enumerate(downloaded_images):
                    if img_data.get("status") in ["success", "skipped"]:
                        # Get image dimensions if possible
                        try:
                            from PIL import Image
                            img_path = Path(img_data["path"])
                            if img_path.exists():
                                with Image.open(img_path) as img:
                                    width, height = img.size
                            else:
                                width, height = 0, 0
                        except Exception:
                            width, height = 0, 0
                        
                        # Determine format from filename
                        filename = img_data.get("filename", "")
                        if filename.endswith(('.jpg', '.jpeg')):
                            format_ext = "jpg"
                        elif filename.endswith('.png'):
                            format_ext = "png"
                        elif filename.endswith('.gif'):
                            format_ext = "gif"
                        elif filename.endswith('.webp'):
                            format_ext = "webp"
                        else:
                            format_ext = "unknown"
                        
                        results.append(ImageResult(
                            path=img_data["path"],
                            source="scraped",
                            provider=used_engine,
                            width=width,
                            height=height,
                            format=format_ext,
                            description=f"Scraped image {i+1}",
                            match_score=None
                        ))
                    elif img_data.get("status") == "skipped":
                        if verbose:
                            print(f"  ⏭️  Skipped: {img_data.get('filename', 'unknown')} ({img_data.get('reason', 'unknown reason')})")
                
                if verbose:
                    print(f"✅ Scraping completed: {len(results)} images processed")
            else:
                error_msg = scrape_result.get('error', 'Unknown error')
                if verbose:
                    print(f"❌ Website scraping failed: {error_msg}")
                else:
                    print(f"Website scraping failed: {error_msg}")
                
        except Exception as e:
            error_msg = f"Website scraping failed: {e}"
            if verbose:
                print(f"❌ {error_msg}")
            else:
                print(error_msg)
        
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
