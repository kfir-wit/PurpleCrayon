from __future__ import annotations

from typing import Any, Dict, List

import asyncio
import httpx

from ..utils.config import get_env


async def serper_search(query: str, num: int = 10) -> List[Dict[str, Any]]:
    api_key = get_env("SERPER_API_KEY")
    if not api_key:
        return []
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": num}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post("https://google.serper.dev/search", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    results: List[Dict[str, Any]] = []
    for item in data.get("organic", [])[:num]:
        results.append({
            "title": item.get("title"),
            "url": item.get("link"),
            "snippet": item.get("snippet"),
        })
    return results


async def firecrawl_scrape(url: str) -> Dict[str, Any]:
    api_key = get_env("FIRECRAWL_API_KEY")
    if not api_key:
        return {"status": "skipped", "reason": "FIRECRAWL_API_KEY missing"}
    
    try:
        # Use the proper Firecrawl SDK
        from firecrawl import Firecrawl
        
        # Initialize Firecrawl client
        firecrawl = Firecrawl(api_key=api_key)
        
        # Scrape with images format to extract all image URLs off the main loop
        result = await asyncio.to_thread(
            firecrawl.scrape,
            url=url,
            formats=["images", "html"],  # Request images format specifically
        )
        
        # Extract images from the response
        images = []
        if hasattr(result, 'images') and result.images:
            images = result.images
        elif hasattr(result, 'data') and 'images' in result.data:
            images = result.data['images']
        elif hasattr(result, 'data') and 'html' in result.data:
            # Fallback: extract from HTML if images format not available
            html_content = result.data['html']
            import re
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            img_matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            
            for img_url in img_matches:
                # Convert relative URLs to absolute
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    from urllib.parse import urljoin
                    img_url = urljoin(url, img_url)
                elif not img_url.startswith('http'):
                    from urllib.parse import urljoin
                    img_url = urljoin(url, img_url)
                
                images.append(img_url)
        
        return {
            "status": "success",
            "images": images,
            "url": url,
            "total_images": len(images)
        }
        
    except ImportError:
        return {"status": "error", "error": "firecrawl-py package not installed. Run: uv add firecrawl-py"}
    except Exception as e:
        return {"status": "error", "error": f"Firecrawl error: {str(e)}"}
