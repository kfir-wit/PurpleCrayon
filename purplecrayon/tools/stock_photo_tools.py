from __future__ import annotations

from typing import Any, Dict, List

import httpx

from ..utils.config import get_env


def _standardize(items: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
    for it in items:
        it.setdefault("source", source)
    return items


async def search_unsplash(query: str, per_page: int = 10, target_size: str = None) -> List[Dict[str, Any]]:
    key = get_env("UNSPLASH_ACCESS_KEY")
    if not key:
        return []
    headers = {"Authorization": f"Client-ID {key}"}
    
    # Add size preference to query for better results
    enhanced_query = query
    if target_size:
        if "wallpaper" in query.lower() or "background" in query.lower():
            enhanced_query = f"{query} high resolution wallpaper"
        elif "portrait" in target_size.lower():
            enhanced_query = f"{query} portrait orientation"
        elif "landscape" in target_size.lower():
            enhanced_query = f"{query} landscape orientation"
    
    params = {"query": enhanced_query, "per_page": per_page}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get("https://api.unsplash.com/search/photos", headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
    items: List[Dict[str, Any]] = []
    for res in data.get("results", []):
        # Get the best quality URL available
        urls = res.get("urls", {})
        best_url = urls.get("raw") or urls.get("full") or urls.get("regular")
        
        items.append({
            "url": best_url,
            "thumb": urls.get("thumb"),
            "description": res.get("alt_description"),
            "license": "unsplash-license",
            "width": res.get("width"),
            "height": res.get("height"),
            "aspect_ratio": res.get("width", 1) / res.get("height", 1) if res.get("height") else 1,
        })
    return _standardize(items, "unsplash")


async def search_pexels(query: str, per_page: int = 10, target_size: str = None) -> List[Dict[str, Any]]:
    key = get_env("PEXELS_API_KEY")
    if not key:
        return []
    headers = {"Authorization": key}
    
    # Add size preference to query
    enhanced_query = query
    if target_size:
        if "wallpaper" in query.lower() or "background" in query.lower():
            enhanced_query = f"{query} high resolution"
    
    params = {"query": enhanced_query, "per_page": per_page}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get("https://api.pexels.com/v1/search", headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
    items: List[Dict[str, Any]] = []
    for res in data.get("photos", []):
        src = res.get("src", {})
        # Get the best quality URL available
        best_url = src.get("large2x") or src.get("original") or src.get("large")
        
        items.append({
            "url": best_url,
            "thumb": src.get("tiny"),
            "description": res.get("alt"),
            "license": "pexels-license",
            "width": res.get("width"),
            "height": res.get("height"),
            "aspect_ratio": res.get("width", 1) / res.get("height", 1) if res.get("height") else 1,
        })
    return _standardize(items, "pexels")


async def search_pixabay(query: str, per_page: int = 10, target_size: str = None) -> List[Dict[str, Any]]:
    key = get_env("PIXABAY_API_KEY")
    if not key:
        return []
    
    # Add size preference to query
    enhanced_query = query
    if target_size:
        if "wallpaper" in query.lower() or "background" in query.lower():
            enhanced_query = f"{query} high resolution"
    
    params = {"key": key, "q": enhanced_query, "image_type": "photo", "per_page": per_page}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get("https://pixabay.com/api/", params=params)
        r.raise_for_status()
        data = r.json()
    items: List[Dict[str, Any]] = []
    for res in data.get("hits", []):
        items.append({
            "url": res.get("largeImageURL"),
            "thumb": res.get("previewURL"),
            "description": res.get("tags"),
            "license": "pixabay-license",
            "width": res.get("imageWidth"),
            "height": res.get("imageHeight"),
            "aspect_ratio": res.get("imageWidth", 1) / res.get("imageHeight", 1) if res.get("imageHeight") else 1,
        })
    return _standardize(items, "pixabay")
