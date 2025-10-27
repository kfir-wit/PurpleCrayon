from __future__ import annotations

import asyncio
import time
import random
import hashlib
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from ..utils.config import get_env


# Anti-detection user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
]

# Common headers to avoid detection
COMMON_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}


async def download_image_robust(url: str, output_dir: Path, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """Download an image with robust error handling and anti-detection."""
    try:
        # Generate filename from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        parsed_url = urlparse(url)
        filename = f"scraped_{url_hash}_{Path(parsed_url.path).name}"
        if not filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            filename += '.jpg'  # Default extension
        
        output_path = output_dir / filename
        
        # Skip if already exists
        if output_path.exists():
            if verbose:
                print(f"  ⏭️  Skipping existing: {filename}")
            return {
                "path": str(output_path),
                "filename": filename,
                "status": "skipped",
                "reason": "already_exists"
            }
        
        # Random delay to avoid rate limiting
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Create headers with random user agent
        headers = COMMON_HEADERS.copy()
        headers['User-Agent'] = random.choice(USER_AGENTS)
        headers['Referer'] = parsed_url.netloc
        
        if verbose:
            print(f"  📥 Downloading: {url}")
            print(f"     → {filename}")
        
        # Download with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True, 
                    timeout=30.0, 
                    headers=headers,
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if not any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
                        if verbose:
                            print(f"     ❌ Invalid content type: {content_type}")
                        return None
                    
                    # Check file size
                    content_length = len(response.content)
                    if content_length < 1024:  # Less than 1KB
                        if verbose:
                            print(f"     ❌ File too small: {content_length} bytes")
                        return None
                    
                    # Save file
                    output_path.write_bytes(response.content)
                    
                    if verbose:
                        print(f"     ✅ Downloaded: {content_length:,} bytes")
                    
                    return {
                        "path": str(output_path),
                        "filename": filename,
                        "status": "success",
                        "size_bytes": content_length,
                        "content_type": content_type,
                        "attempt": attempt + 1
                    }
                    
            except httpx.TimeoutException:
                if verbose:
                    print(f"     ⏰ Timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(1, 3))
                    continue
                else:
                    return None
                    
            except httpx.HTTPStatusError as e:
                if verbose:
                    print(f"     ❌ HTTP {e.response.status_code}: {e.response.reason_phrase}")
                if e.response.status_code in [429, 503, 504] and attempt < max_retries - 1:
                    # Rate limited, wait longer
                    await asyncio.sleep(random.uniform(5, 10))
                    continue
                else:
                    return None
                    
            except Exception as e:
                if verbose:
                    print(f"     ❌ Error: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(1, 2))
                    continue
                else:
                    return None
        
        return None
        
    except Exception as e:
        if verbose:
            print(f"  ❌ Download failed: {str(e)}")
        return None


async def beautifulsoup_scrape(url: str, verbose: bool = False) -> Dict[str, List[str]]:
    """Scrape images using BeautifulSoup4 with httpx and anti-detection."""
    if verbose:
        print(f"  🔍 BeautifulSoup: Analyzing {url}")
    
    # Use random user agent and common headers
    headers = COMMON_HEADERS.copy()
    headers['User-Agent'] = random.choice(USER_AGENTS)
    
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, 
            timeout=30.0, 
            headers=headers,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        if verbose:
            print(f"  ❌ BeautifulSoup failed: {str(e)}")
        return {"images": [], "links": [], "error": str(e)}

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


async def playwright_scrape(url: str, verbose: bool = False) -> Dict[str, List[str]]:
    """Scrape images using Playwright with full browser automation and anti-detection."""
    if verbose:
        print(f"  🎭 Playwright: Loading {url}")
    
    images: List[str] = []
    links: List[str] = []
    
    async with async_playwright() as p:
        # Launch browser with stealth options
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        
        # Create context with stealth settings
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        page = await context.new_page()
        
        # Set extra headers
        await page.set_extra_http_headers(COMMON_HEADERS)
        
        # Override navigator properties to avoid detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            window.chrome = {
                runtime: {},
            };
        """)
        
        try:
            # Navigate to page with random delay
            await asyncio.sleep(random.uniform(1, 3))
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            if verbose:
                print(f"  📄 Page loaded, extracting images...")
            
            # Scroll to trigger lazy loading with human-like behavior
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 4)")
            await page.wait_for_timeout(random.uniform(1000, 2000))
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await page.wait_for_timeout(random.uniform(1000, 2000))
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(random.uniform(2000, 3000))
            
            # Scroll back up
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(random.uniform(500, 1000))
            
            # Extract all image sources with better detection
            img_sources = await page.evaluate("""
                () => {
                    const images = [];
                    const imgs = document.querySelectorAll('img');
                    imgs.forEach(img => {
                        const src = img.src || 
                                   img.dataset.src || 
                                   img.dataset.lazySrc || 
                                   img.dataset.original ||
                                   img.dataset.lazy ||
                                   img.getAttribute('data-lazy-src') ||
                                   img.getAttribute('data-original');
                        if (src && src.startsWith('http')) {
                            images.push(src);
                        }
                    });
                    
                    // Also check for background images
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bgImage = style.backgroundImage;
                        if (bgImage && bgImage !== 'none') {
                            const match = bgImage.match(/url\\(["']?([^"']+)["']?\\)/);
                            if (match && match[1] && match[1].startsWith('http')) {
                                images.push(match[1]);
                            }
                        }
                    });
                    
                    return [...new Set(images)]; // Remove duplicates
                }
            """)
            
            # Extract all links
            link_hrefs = await page.evaluate("""
                () => {
                    const links = [];
                    const anchors = document.querySelectorAll('a[href]');
                    anchors.forEach(a => {
                        if (a.href && a.href.startsWith('http')) {
                            links.push(a.href);
                        }
                    });
                    return [...new Set(links)]; // Remove duplicates
                }
            """)
            
            images = img_sources
            links = link_hrefs
            
            if verbose:
                print(f"  🖼️  Found {len(images)} images, {len(links)} links")
            
        except Exception as e:
            if verbose:
                print(f"  ❌ Playwright error: {str(e)}")
            return {"images": [], "links": [], "error": str(e)}
        finally:
            await context.close()
            await browser.close()
    
    return {"images": images, "links": links}


async def firecrawl_scrape_images(url: str, verbose: bool = False) -> Dict[str, List[str]]:
    """Scrape images using Firecrawl API."""
    if verbose:
        print(f"  🔥 Firecrawl: Processing {url}")
    
    api_key = get_env("FIRECRAWL_API_KEY")
    if not api_key:
        if verbose:
            print(f"  ⚠️  Firecrawl API key missing, skipping...")
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


async def scrape_with_engine(url: str, engine: str, download_dir: Optional[Path] = None, verbose: bool = False) -> Dict[str, Any]:
    """Scrape using a specific engine with optional downloading."""
    start_time = time.time()
    
    if verbose:
        print(f"🚀 Starting {engine.upper()} scraping...")
    
    try:
        if engine == "beautifulsoup" or engine == "bs4":
            result = await beautifulsoup_scrape(url, verbose)
        elif engine == "playwright":
            result = await playwright_scrape(url, verbose)
        elif engine == "firecrawl":
            result = await firecrawl_scrape_images(url, verbose)
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
        
        # Download images if download_dir is provided
        downloaded_images = []
        if download_dir and result.get("images"):
            download_dir.mkdir(parents=True, exist_ok=True)
            
            if verbose:
                print(f"  📥 Downloading {len(result['images'])} images...")
            
            # Download images concurrently with rate limiting
            semaphore = asyncio.Semaphore(3)  # Limit concurrent downloads
            
            async def download_with_semaphore(img_url):
                async with semaphore:
                    return await download_image_robust(img_url, download_dir, verbose)
            
            download_tasks = [download_with_semaphore(img_url) for img_url in result["images"]]
            download_results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            # Process download results
            successful_downloads = 0
            for i, download_result in enumerate(download_results):
                if isinstance(download_result, dict) and download_result.get("status") == "success":
                    downloaded_images.append({
                        "url": result["images"][i],
                        "path": download_result["path"],
                        "filename": download_result["filename"],
                        "size_bytes": download_result.get("size_bytes", 0),
                        "content_type": download_result.get("content_type", "unknown")
                    })
                    successful_downloads += 1
                elif isinstance(download_result, dict) and download_result.get("status") == "skipped":
                    downloaded_images.append({
                        "url": result["images"][i],
                        "path": download_result["path"],
                        "filename": download_result["filename"],
                        "status": "skipped",
                        "reason": download_result.get("reason", "unknown")
                    })
            
            if verbose:
                print(f"  ✅ Successfully downloaded: {successful_downloads}/{len(result['images'])} images")
        
        return {
            "status": "success",
            "images": result.get("images", []),
            "links": result.get("links", []),
            "downloaded_images": downloaded_images,
            "engine": engine,
            "duration": duration,
            "error": result.get("error")
        }
        
    except Exception as e:
        duration = time.time() - start_time
        if verbose:
            print(f"  ❌ {engine.upper()} failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "images": [],
            "links": [],
            "downloaded_images": [],
            "engine": engine,
            "duration": duration
        }


async def scrape_with_fallback(url: str, download_dir: Optional[Path] = None, verbose: bool = False) -> Dict[str, Any]:
    """Try scraping engines in fallback order: firecrawl → playwright → bs4."""
    engines = ["firecrawl", "playwright", "beautifulsoup"]
    
    if verbose:
        print(f"🔄 Trying engines in fallback order: {', '.join(engines)}")
    
    last_result: Optional[Dict[str, Any]] = None
    
    for i, engine in enumerate(engines):
        if verbose:
            print(f"\n--- Attempt {i+1}/{len(engines)}: {engine.upper()} ---")
        
        result = await scrape_with_engine(url, engine, download_dir, verbose)
        last_result = result
        
        # If successful and found images, return result
        if (result["status"] == "success" and 
            result.get("images") and 
            len(result["images"]) > 0):
            result["fallback_used"] = engine != engines[0]
            result["attempted_engines"] = engines[:engines.index(engine) + 1]
            
            if verbose:
                print(f"✅ {engine.upper()} succeeded with {len(result['images'])} images")
            
            return result
        
        # If firecrawl failed due to missing API key, try next engine
        if (engine == "firecrawl" and 
            result.get("error") and 
            "FIRECRAWL_API_KEY missing" in result["error"]):
            if verbose:
                print(f"⚠️  {engine.upper()} skipped (no API key)")
            continue
        
        if verbose:
            print(f"❌ {engine.upper()} failed: {result.get('error', 'Unknown error')}")
    
    # If all engines failed, return the last result (or a generic failure)
    if last_result is None:
        return {
            "status": "error",
            "error": "No scraping engines configured",
            "images": [],
            "links": [],
            "downloaded_images": [],
            "engine": None,
            "duration": 0,
            "fallback_used": True,
            "attempted_engines": engines,
        }
    
    last_result["fallback_used"] = True
    last_result["attempted_engines"] = engines
    
    if verbose:
        print(f"\n❌ All engines failed. Last error: {last_result.get('error', 'Unknown')}")
    
    return last_result


async def scrape_website_comprehensive(url: str, download_dir: Optional[Path] = None, verbose: bool = False, engine: Optional[str] = None) -> Dict[str, Any]:
    """Comprehensive website scraping with downloading and verbose debugging."""
    if verbose:
        print(f"🌐 Comprehensive scraping: {url}")
        print("=" * 60)
    
    # Use specific engine or fallback approach
    if engine:
        if verbose:
            print(f"🎯 Using specific engine: {engine.upper()}")
        result = await scrape_with_engine(url, engine, download_dir, verbose)
    else:
        if verbose:
            print(f"🔄 Using fallback approach")
        result = await scrape_with_fallback(url, download_dir, verbose)
    
    if verbose:
        print(f"\n📊 Final Results:")
        print(f"  Status: {'✅ Success' if result['status'] == 'success' else '❌ Failed'}")
        print(f"  Engine: {result.get('engine', 'None')}")
        print(f"  Duration: {result.get('duration', 0):.2f}s")
        print(f"  Images found: {len(result.get('images', []))}")
        print(f"  Images downloaded: {len(result.get('downloaded_images', []))}")
        print(f"  Links found: {len(result.get('links', []))}")
        
        if result.get('downloaded_images'):
            print(f"\n📁 Downloaded files:")
            for img in result['downloaded_images']:
                status_icon = "✅" if img.get('status') == 'success' else "⏭️"
                size_info = f" ({img.get('size_bytes', 0):,} bytes)" if img.get('size_bytes') else ""
                print(f"  {status_icon} {img.get('filename', 'unknown')}{size_info}")
    
    return result
