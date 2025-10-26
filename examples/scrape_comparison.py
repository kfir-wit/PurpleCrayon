#!/usr/bin/env python3
"""
Scraping Engine Comparison Tool

This script tests all three scraping engines (Firecrawl, Playwright, BeautifulSoup4)
on a given URL and provides a detailed comparison of their performance.
"""

import asyncio
import argparse
import time
from typing import Dict, List, Any
from pathlib import Path

from purplecrayon import PurpleCrayon
from purplecrayon.tools.scraping_tools import scrape_with_engine


class ScrapingComparison:
    def __init__(self, assets_dir: str = "./test_assets"):
        """Initialize with test assets directory."""
        self.crayon = PurpleCrayon(assets_dir=assets_dir)
        self.engines = ["firecrawl", "playwright", "beautifulsoup"]
        self.results = {}
    
    async def test_engine(self, url: str, engine: str) -> Dict[str, Any]:
        """Test a specific engine on the given URL."""
        print(f"\n🔧 Testing {engine.upper()} engine...")
        
        start_time = time.time()
        
        try:
            # Use the scraping tools directly for more detailed results
            result = await scrape_with_engine(url, engine)
            
            duration = time.time() - start_time
            
            # Count unique images found
            images = result.get("images", [])
            unique_images = list(set(images))  # Remove duplicates
            
            return {
                "engine": engine,
                "status": result.get("status", "error"),
                "duration": duration,
                "total_images": len(images),
                "unique_images": len(unique_images),
                "images": unique_images,
                "error": result.get("error"),
                "success": result.get("status") == "success" and len(unique_images) > 0
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                "engine": engine,
                "status": "error",
                "duration": duration,
                "total_images": 0,
                "unique_images": 0,
                "images": [],
                "error": str(e),
                "success": False
            }
    
    async def compare_engines(self, url: str) -> Dict[str, Any]:
        """Compare all engines on the given URL."""
        print(f"🕷️  Comparing scraping engines on: {url}")
        print("=" * 60)
        
        results = {}
        
        for engine in self.engines:
            result = await self.test_engine(url, engine)
            results[engine] = result
            
            # Print immediate results
            if result["success"]:
                print(f"✅ {engine.upper()}: Found {result['unique_images']} images in {result['duration']:.2f}s")
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"❌ {engine.upper()}: Failed - {error_msg}")
        
        return results
    
    def print_summary(self, results: Dict[str, Any], url: str):
        """Print a detailed summary of the comparison."""
        print("\n" + "=" * 60)
        print("📊 SCRAPING ENGINE COMPARISON SUMMARY")
        print("=" * 60)
        print(f"URL: {url}")
        print(f"Tested at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Find best performing engine
        successful_engines = {k: v for k, v in results.items() if v["success"]}
        
        if successful_engines:
            best_engine = max(successful_engines.items(), 
                            key=lambda x: (x[1]["unique_images"], -x[1]["duration"]))
            print(f"\n🏆 BEST PERFORMER: {best_engine[0].upper()}")
            print(f"   Images found: {best_engine[1]['unique_images']}")
            print(f"   Duration: {best_engine[1]['duration']:.2f}s")
        
        print(f"\n📈 DETAILED RESULTS:")
        print("-" * 40)
        
        for engine, result in results.items():
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {engine.upper():<12} | "
                  f"Images: {result['unique_images']:<3} | "
                  f"Time: {result['duration']:.2f}s")
            
            if result.get("error"):
                print(f"    Error: {result['error']}")
        
        # Engine-specific insights
        print(f"\n💡 INSIGHTS:")
        if "firecrawl" in results and results["firecrawl"]["success"]:
            print("• Firecrawl: Best for API-based scraping, handles complex sites")
        if "playwright" in results and results["playwright"]["success"]:
            print("• Playwright: Best for JavaScript-heavy sites and lazy loading")
        if "beautifulsoup" in results and results["beautifulsoup"]["success"]:
            print("• BeautifulSoup: Fastest for simple sites, good fallback")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        if successful_engines:
            if len(successful_engines) == 1:
                print(f"• Use {list(successful_engines.keys())[0]} for this URL")
            else:
                fastest = min(successful_engines.items(), key=lambda x: x[1]["duration"])
                most_images = max(successful_engines.items(), key=lambda x: x[1]["unique_images"])
                print(f"• Fastest: {fastest[0]} ({fastest[1]['duration']:.2f}s)")
                print(f"• Most images: {most_images[0]} ({most_images[1]['unique_images']} images)")
        else:
            print("• All engines failed - site may have strong anti-scraping protection")
            print("• Consider using a proxy or different approach")
    
    def save_report(self, results: Dict[str, Any], url: str, output_file: str = None):
        """Save detailed report to file."""
        if not output_file:
            timestamp = int(time.time())
            output_file = f"scraping_comparison_{timestamp}.txt"
        
        report_path = Path(output_file)
        
        with open(report_path, 'w') as f:
            f.write("SCRAPING ENGINE COMPARISON REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"URL: {url}\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for engine, result in results.items():
                f.write(f"{engine.upper()} RESULTS:\n")
                f.write(f"  Status: {result['status']}\n")
                f.write(f"  Duration: {result['duration']:.2f}s\n")
                f.write(f"  Images found: {result['unique_images']}\n")
                if result.get("error"):
                    f.write(f"  Error: {result['error']}\n")
                f.write("\n")
        
        print(f"\n📄 Report saved to: {report_path}")


async def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="Compare scraping engines on a URL")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--engine", choices=["firecrawl", "playwright", "beautifulsoup"], 
                       help="Test only specific engine")
    parser.add_argument("--output", help="Output file for detailed report")
    parser.add_argument("--assets-dir", default="./test_assets", 
                       help="Assets directory for downloads")
    
    args = parser.parse_args()
    
    # Initialize comparison tool
    comparison = ScrapingComparison(assets_dir=args.assets_dir)
    
    if args.engine:
        # Test single engine
        print(f"🔧 Testing {args.engine.upper()} engine on: {args.url}")
        result = await comparison.test_engine(args.url, args.engine)
        
        if result["success"]:
            print(f"✅ Success: Found {result['unique_images']} images in {result['duration']:.2f}s")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    else:
        # Compare all engines
        results = await comparison.compare_engines(args.url)
        comparison.print_summary(results, args.url)
        
        if args.output:
            comparison.save_report(results, args.url, args.output)


if __name__ == "__main__":
    # Example WordPress URLs for testing
    example_urls = [
        "https://wordpress.org/showcase/",
        "https://www.smashingmagazine.com/",
        "https://www.cnn.com/",
        "https://www.nytimes.com/",
    ]
    
    print("🚀 PurpleCrayon Scraping Engine Comparison")
    print("=" * 50)
    print("Example URLs you can test:")
    for i, url in enumerate(example_urls, 1):
        print(f"  {i}. {url}")
    print()
    
    asyncio.run(main())
