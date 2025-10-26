#!/usr/bin/env python3
"""
Example: Scrape images from a website using PurpleCrayon package
Demonstrates different scraping engines and their usage.
"""

import argparse
from purplecrayon import PurpleCrayon


def scrape_with_engine(crayon, url, engine=None):
    """Scrape using a specific engine or auto-fallback."""
    if engine:
        print(f"🕷️ Scraping with {engine.upper()} engine from: {url}")
        result = crayon.scrape(url, engine=engine)
    else:
        print(f"🕷️ Scraping with auto-fallback from: {url}")
        result = crayon.scrape(url)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Scrape images from a website")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--engine", choices=["firecrawl", "playwright", "beautifulsoup"], 
                       help="Specific scraping engine to use (default: auto-fallback)")
    parser.add_argument("--assets-dir", default="./example_assets", 
                       help="Assets directory for downloads")
    
    args = parser.parse_args()
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir=args.assets_dir)
    
    # Scrape with specified engine or auto-fallback
    result = scrape_with_engine(crayon, args.url, args.engine)
    
    if result.success:
        print(f"✅ {result.message}")
        print(f"📸 Found {len(result.images)} images:")
        
        for i, img in enumerate(result.images, 1):
            print(f"  {i}. {img.path}")
            print(f"     Source: {img.source}/{img.provider}")
            if img.description:
                print(f"     Description: {img.description}")
            if img.error:
                print(f"     ❌ Error: {img.error}")
            print()
    else:
        print(f"❌ Scraping failed: {result.message}")
        if result.error_code:
            print(f"   Error Code: {result.error_code}")


def demo_all_engines():
    """Demonstrate all engines on the same URL."""
    url = "https://wordpress.org/showcase/"
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    engines = ["firecrawl", "playwright", "beautifulsoup"]
    
    print("🔧 Testing all engines on WordPress showcase:")
    print("=" * 50)
    
    for engine in engines:
        print(f"\n--- Testing {engine.upper()} ---")
        result = crayon.scrape(url, engine=engine)
        
        if result.success:
            print(f"✅ Found {len(result.images)} images")
        else:
            print(f"❌ Failed: {result.message}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # No arguments provided, show demo
        print("🚀 PurpleCrayon Scraping Example")
        print("=" * 40)
        print("Usage examples:")
        print("  python scrape_example.py https://example.com")
        print("  python scrape_example.py https://example.com --engine playwright")
        print("  python scrape_example.py --help")
        print()
        print("Running demo with all engines...")
        demo_all_engines()
    else:
        main()
