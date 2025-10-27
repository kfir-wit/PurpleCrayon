#!/usr/bin/env python3
"""
Example: Scrape images from a website using PurpleCrayon package
Demonstrates different scraping engines and their usage.
"""

import argparse
from purplecrayon import PurpleCrayon


def scrape_with_engine(crayon, url, engine=None, verbose=False, override=False, cleanup=True, keep_junk=False):
    """Scrape using a specific engine or auto-fallback."""
    if engine and override:
        print(f"🎯 Override mode: Using ONLY {engine.upper()} engine from: {url}")
        result = crayon.scrape(url, engine=engine, verbose=verbose)
    elif engine:
        print(f"🕷️ Scraping with {engine.upper()} engine (fallback enabled) from: {url}")
        result = crayon.scrape(url, engine=engine, verbose=verbose)
    else:
        print(f"🕷️ Scraping with auto-fallback from: {url}")
        result = crayon.scrape(url, verbose=verbose)
    
    # Clean up scraped files if requested and scraping was successful
    if cleanup and result.success and result.images:
        print(f"\n🧹 Cleaning up scraped files...")
        cleanup_result = crayon.cleanup_assets(remove_junk=not keep_junk)
        
        if cleanup_result["success"]:
            cleanup_stats = cleanup_result["cleanup_stats"]
            print(f"✅ Cleanup completed:")
            print(f"  📸 Valid images: {cleanup_stats['valid']}")
            if cleanup_stats['corrupted'] > 0:
                print(f"  ❌ Corrupted files removed: {cleanup_stats['corrupted']}")
            if not keep_junk and cleanup_stats['junk'] > 0:
                print(f"  🗑️ Junk files removed: {cleanup_stats['junk']}")
            if cleanup_stats['corrupted'] > 0 or (not keep_junk and cleanup_stats['junk'] > 0):
                print(f"  📝 Files corrected/renamed: {cleanup_stats.get('total_removed', 0)}")
        else:
            print(f"⚠️ Cleanup failed: {cleanup_result['error']}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Scrape images from a website")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--engine", choices=["firecrawl", "playwright", "beautifulsoup"], 
                       help="Specific scraping engine to use (default: auto-fallback)")
    parser.add_argument("--override", action="store_true",
                       help="Override fallback behavior - use only the specified engine")
    parser.add_argument("--assets-dir", default="./example_assets", 
                       help="Assets directory for downloads")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose debugging output")
    parser.add_argument("--no-cleanup", action="store_true",
                       help="Skip automatic cleanup after scraping")
    parser.add_argument("--keep-junk", action="store_true",
                       help="Keep junk files during cleanup (only remove corrupted files)")
    
    args = parser.parse_args()
    
    # Initialize PurpleCrayon
    crayon = PurpleCrayon(assets_dir=args.assets_dir)
    
    # Scrape with specified engine or auto-fallback
    result = scrape_with_engine(crayon, args.url, args.engine, args.verbose, args.override, 
                               cleanup=not args.no_cleanup, keep_junk=args.keep_junk)
    
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
        print(f"\n--- Testing {engine.upper()} ONLY ---")
        result = scrape_with_engine(crayon, url, engine, verbose=True, override=True, cleanup=True)
        
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
        print("  python scrape_example.py https://example.com --no-cleanup")
        print("  python scrape_example.py https://example.com --keep-junk")
        print("  python scrape_example.py --help")
        print()
        print("Running demo with all engines...")
        demo_all_engines()
    else:
        main()
