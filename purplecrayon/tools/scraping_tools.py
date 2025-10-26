from __future__ import annotations

import asyncio
import time
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from ..utils.config import get_env


async def beautifulsoup_scrape(url: str) -> Dict[str, List[str]]:
    """Scrape images using BeautifulSoup4 with httpx."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0, headers=headers) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

    images: List[str] = []
    links: List[str] = []

    # Extract images with various lazy-loading attributes
    for img in soup.find_all("img"):
        src = (img.get("src") or 
               img.get("data-src") or 
               img.get("data-lazy-src") or 
               img.get("data-original"))
        if src:
            # Convert relative URLs to absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(url, src)
            elif not src.startswith('http'):
                src = urljoin(url, src)
            images.append(src)
    
    # Extract links
    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = urljoin(url, href)
            elif not href.startswith('http'):
                href = urljoin(url, href)
            links.append(href)
    
    return {"images": images, "links": links}


async def playwright_scrape(url: str) -> Dict[str, List[str]]:
    """Scrape images using Playwright with full browser automation."""
    images: List[str] = []
    links: List[str] = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set user agent to avoid detection
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        try:
            # Navigate to page and wait for network to be idle
            await page.goto(url, wait_until="networkidle")
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)  # Wait for lazy loading
            
            # Scroll back up
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            
            # Extract all image sources
            img_sources = await page.evaluate("""
                () => {
                    const images = [];
                    const imgs = document.querySelectorAll('img');
                    imgs.forEach(img => {
                        const src = img.src || img.dataset.src || img.dataset.lazySrc || img.dataset.original;
                        if (src) images.push(src);
                    });
                    return images;
                }
            """)
            
            # Extract all links
            link_hrefs = await page.evaluate("""
                () => {
                    const links = [];
                    const anchors = document.querySelectorAll('a[href]');
                    anchors.forEach(a => {
                        if (a.href) links.push(a.href);
                    });
                    return links;
                }
            """)
            
            images = img_sources
            links = link_hrefs
            
        except Exception as e:
            print(f"Playwright scraping error: {e}")
        finally:
            await browser.close()
    
    return {"images": images, "links": links}


async def firecrawl_scrape_images(url: str) -> Dict[str, List[str]]:
    """Scrape images using Firecrawl API."""
    api_key = get_env("FIRECRAWL_API_KEY")
    if not api_key:
        return {"images": [], "links": [], "error": "FIRECRAWL_API_KEY missing"}
    
    try:
        from firecrawl import Firecrawl
        
        firecrawl = Firecrawl(api_key=api_key)
        
        # Scrape with images format to extract all image URLs on a worker thread
        result = await asyncio.to_thread(
            firecrawl.scrape,
            url=url,
            formats=["images", "html"],
        )
        
        images = []
        links = []
        
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
                    img_url = urljoin(url, img_url)
                elif not img_url.startswith('http'):
                    img_url = urljoin(url, img_url)
                
                images.append(img_url)
        
        return {"images": images, "links": links}
        
    except ImportError:
        return {"images": [], "links": [], "error": "firecrawl-py package not installed"}
    except Exception as e:
        return {"images": [], "links": [], "error": f"Firecrawl error: {str(e)}"}


async def scrape_with_engine(url: str, engine: str) -> Dict[str, Any]:
    """Scrape using a specific engine."""
    start_time = time.time()
    
    try:
        if engine == "beautifulsoup" or engine == "bs4":
            result = await beautifulsoup_scrape(url)
        elif engine == "playwright":
            result = await playwright_scrape(url)
        elif engine == "firecrawl":
            result = await firecrawl_scrape_images(url)
        else:
            return {
                "status": "error",
                "error": f"Unknown engine: {engine}",
                "images": [],
                "links": [],
                "engine": engine,
                "duration": 0
            }
        
        duration = time.time() - start_time
        
        return {
            "status": "success",
            "images": result.get("images", []),
            "links": result.get("links", []),
            "engine": engine,
            "duration": duration,
            "error": result.get("error")
        }
        
    except Exception as e:
        duration = time.time() - start_time
        return {
            "status": "error",
            "error": str(e),
            "images": [],
            "links": [],
            "engine": engine,
            "duration": duration
        }


async def scrape_with_fallback(url: str) -> Dict[str, Any]:
    """Try scraping engines in fallback order: firecrawl → playwright → bs4."""
    engines = ["firecrawl", "playwright", "beautifulsoup"]
    
    last_result: Optional[Dict[str, Any]] = None
    
    for engine in engines:
        result = await scrape_with_engine(url, engine)
        last_result = result
        
        # If successful and found images, return result
        if (result["status"] == "success" and 
            result.get("images") and 
            len(result["images"]) > 0):
            result["fallback_used"] = engine != engines[0]
            result["attempted_engines"] = engines[:engines.index(engine) + 1]
            return result
        
        # If firecrawl failed due to missing API key, try next engine
        if (engine == "firecrawl" and 
            result.get("error") and 
            "FIRECRAWL_API_KEY missing" in result["error"]):
            continue
    
    # If all engines failed, return the last result (or a generic failure)
    if last_result is None:
        return {
            "status": "error",
            "error": "No scraping engines configured",
            "images": [],
            "links": [],
            "engine": None,
            "duration": 0,
            "fallback_used": True,
            "attempted_engines": engines,
        }
    
    last_result["fallback_used"] = True
    last_result["attempted_engines"] = engines
    return last_result
