#!/usr/bin/env python3
"""
PurpleCrayon Integration Test

This script runs a comprehensive integration test that:
1. Tests all major functionality with actual API calls
2. Generates real images using each engine
3. Tests async/await patterns throughout
4. Provides detailed reporting on success/failure rates
5. Validates image data parsing and saving

Usage:
    uv run python examples/integration_test.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from purplecrayon import PurpleCrayon, AssetRequest
from purplecrayon.tools.ai_generation_tools import generate_with_gemini, generate_with_replicate
from purplecrayon.tools.image_augmentation_tools import augment_image_with_gemini_async, augment_image_with_replicate_async
from purplecrayon.tools.clone_image_tools import clone_image, describe_image_for_regeneration
from purplecrayon.utils.config import get_env


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    success: bool
    duration: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    images_generated: int = 0
    image_sizes: List[int] = None
    
    def __post_init__(self):
        if self.image_sizes is None:
            self.image_sizes = []


class IntegrationTester:
    """Comprehensive integration tester for PurpleCrayon."""
    
    def __init__(self, assets_dir: str = "./test_assets"):
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(exist_ok=True)
        self.results: List[TestResult] = []
        self.crayon = PurpleCrayon(assets_dir=str(self.assets_dir))
        
        # Test configuration
        self.test_prompts = {
            "simple": "a red circle on white background",
            "complex": "a photorealistic panda eating bamboo in a misty forest",
            "artistic": "watercolor painting of a sunset over mountains",
            "abstract": "geometric abstract art with blue and yellow triangles"
        }
        
        # Check API keys
        self.api_keys = {
            "gemini": get_env("GEMINI_API_KEY"),
            "replicate": get_env("REPLICATE_API_TOKEN")
        }
        
        print(f"🔑 API Keys Status:")
        for engine, key in self.api_keys.items():
            print(f"  {engine}: {'✅' if key else '❌'}")
    
    async def run_test(self, test_name: str, test_func) -> TestResult:
        """Run a single test and record results."""
        print(f"\n🧪 Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            if isinstance(result, TestResult):
                result.duration = duration
                self.results.append(result)
                return result
            else:
                # Convert simple result to TestResult
                test_result = TestResult(
                    test_name=test_name,
                    success=bool(result),
                    duration=duration,
                    details={"result": str(result)} if result else None
                )
                self.results.append(test_result)
                return test_result
                
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"❌ Test failed: {error_msg}")
            
            test_result = TestResult(
                test_name=test_name,
                success=False,
                duration=duration,
                error=error_msg
            )
            self.results.append(test_result)
            return test_result
    
    async def test_gemini_text_to_image(self) -> TestResult:
        """Test Gemini text-to-image generation."""
        if not self.api_keys["gemini"]:
            return TestResult(
                test_name="Gemini Text-to-Image",
                success=False,
                duration=0,
                error="GEMINI_API_KEY not available"
            )
        
        print("  Testing Gemini text-to-image generation...")
        
        # Test simple prompt
        result = generate_with_gemini(
            self.test_prompts["simple"],
            aspect_ratio="1:1"
        )
        
        success = result.get("status") == "succeeded" and bool(result.get("image_data"))
        image_data = result.get("image_data", b"")
        
        return TestResult(
            test_name="Gemini Text-to-Image",
            success=success,
            duration=0,  # Will be set by run_test
            error=result.get("error") if not success else None,
            details={
                "provider": result.get("provider"),
                "status": result.get("status"),
                "image_data_length": len(image_data),
                "has_image_data": bool(image_data)
            },
            images_generated=1 if success else 0,
            image_sizes=[len(image_data)] if image_data else []
        )
    
    async def test_replicate_text_to_image(self) -> TestResult:
        """Test Replicate text-to-image generation."""
        if not self.api_keys["replicate"]:
            return TestResult(
                test_name="Replicate Text-to-Image",
                success=False,
                duration=0,
                error="REPLICATE_API_TOKEN not available"
            )
        
        print("  Testing Replicate text-to-image generation...")
        
        result = generate_with_replicate(
            self.test_prompts["artistic"],
            aspect_ratio="1:1"
        )
        
        success = result.get("status") == "succeeded" and bool(result.get("image_data"))
        image_data = result.get("image_data", b"")
        
        return TestResult(
            test_name="Replicate Text-to-Image",
            success=success,
            duration=0,
            error=result.get("error") if not success else None,
            details={
                "provider": result.get("provider"),
                "status": result.get("status"),
                "image_data_length": len(image_data),
                "has_image_data": bool(image_data)
            },
            images_generated=1 if success else 0,
            image_sizes=[len(image_data)] if image_data else []
        )
    
    async def test_purplecrayon_generate_async(self) -> TestResult:
        """Test PurpleCrayon.generate_async() method."""
        print("  Testing PurpleCrayon.generate_async()...")
        
        request = AssetRequest(
            description=self.test_prompts["complex"],
            width=512,
            height=512,
            format="png",
            max_results=1
        )
        
        result = await self.crayon.generate_async(request)
        
        return TestResult(
            test_name="PurpleCrayon Generate Async",
            success=result.success,
            duration=0,
            error=result.message if not result.success else None,
            details={
                "images_count": len(result.images),
                "message": result.message
            },
            images_generated=len(result.images),
            image_sizes=[len(img.data) if hasattr(img, 'data') else 0 for img in result.images]
        )
    
    async def test_gemini_augmentation(self) -> TestResult:
        """Test Gemini image augmentation."""
        if not self.api_keys["gemini"]:
            return TestResult(
                test_name="Gemini Augmentation",
                success=False,
                duration=0,
                error="GEMINI_API_KEY not available"
            )
        
        print("  Testing Gemini image augmentation...")
        
        # Create a test image first
        test_image_path = self.assets_dir / "test_image.png"
        if not test_image_path.exists():
            # Generate a simple test image
            from PIL import Image
            img = Image.new('RGB', (256, 256), color='red')
            img.save(test_image_path)
        
        result = await augment_image_with_gemini_async(
            test_image_path,
            "add a blue border around the image",
            width=512,
            height=512
        )
        
        success = result.get("status") == "succeeded" and bool(result.get("image_data"))
        image_data = result.get("image_data", b"")
        
        return TestResult(
            test_name="Gemini Augmentation",
            success=success,
            duration=0,
            error=result.get("error") if not success else None,
            details={
                "provider": result.get("provider"),
                "status": result.get("status"),
                "image_data_length": len(image_data),
                "has_image_data": bool(image_data)
            },
            images_generated=1 if success else 0,
            image_sizes=[len(image_data)] if image_data else []
        )
    
    async def test_replicate_augmentation(self) -> TestResult:
        """Test Replicate image augmentation."""
        if not self.api_keys["replicate"]:
            return TestResult(
                test_name="Replicate Augmentation",
                success=False,
                duration=0,
                error="REPLICATE_API_TOKEN not available"
            )
        
        print("  Testing Replicate image augmentation...")
        
        # Create a test image first
        test_image_path = self.assets_dir / "test_image.png"
        if not test_image_path.exists():
            from PIL import Image
            img = Image.new('RGB', (256, 256), color='red')
            img.save(test_image_path)
        
        result = await augment_image_with_replicate_async(
            test_image_path,
            "convert to watercolor style",
            width=512,
            height=512
        )
        
        success = result.get("status") == "succeeded" and bool(result.get("image_data"))
        image_data = result.get("image_data", b"")
        
        return TestResult(
            test_name="Replicate Augmentation",
            success=success,
            duration=0,
            error=result.get("error") if not success else None,
            details={
                "provider": result.get("provider"),
                "status": result.get("status"),
                "image_data_length": len(image_data),
                "has_image_data": bool(image_data)
            },
            images_generated=1 if success else 0,
            image_sizes=[len(image_data)] if image_data else []
        )
    
    async def test_clone_functionality(self) -> TestResult:
        """Test image cloning functionality."""
        print("  Testing image cloning...")
        
        # Create a test image first
        test_image_path = self.assets_dir / "test_image.png"
        if not test_image_path.exists():
            from PIL import Image
            img = Image.new('RGB', (256, 256), color='blue')
            img.save(test_image_path)
        
        # Test image analysis
        analysis = await describe_image_for_regeneration(test_image_path)
        
        if not analysis.get("success"):
            return TestResult(
                test_name="Clone Functionality",
                success=False,
                duration=0,
                error=f"Image analysis failed: {analysis.get('error')}"
            )
        
        # Test cloning
        clone_result = await clone_image(
            test_image_path,
            style="artistic",
            guidance="creative interpretation",
            output_dir=self.assets_dir / "cloned"
        )
        
        success = clone_result.get("success", False)
        
        return TestResult(
            test_name="Clone Functionality",
            success=success,
            duration=0,
            error=clone_result.get("error") if not success else None,
            details={
                "analysis_success": analysis.get("success"),
                "description": analysis.get("description", "")[:100] + "..." if analysis.get("description") else None,
                "clone_success": success,
                "similarity_score": clone_result.get("similarity_score", 0)
            },
            images_generated=1 if success else 0,
            image_sizes=[len(clone_result.get("image_data", b""))] if success else []
        )
    
    async def test_purplecrayon_augment_async(self) -> TestResult:
        """Test PurpleCrayon.augment_async() method."""
        print("  Testing PurpleCrayon.augment_async()...")
        
        # Create a test image first
        test_image_path = self.assets_dir / "test_image.png"
        if not test_image_path.exists():
            from PIL import Image
            img = Image.new('RGB', (256, 256), color='green')
            img.save(test_image_path)
        
        result = await self.crayon.augment_async(
            image_path=test_image_path,
            prompt="add a golden frame around the image",
            width=512,
            height=512,
            format="png"
        )
        
        return TestResult(
            test_name="PurpleCrayon Augment Async",
            success=result.success,
            duration=0,
            error=result.message if not result.success else None,
            details={
                "images_count": len(result.images),
                "message": result.message
            },
            images_generated=len(result.images),
            image_sizes=[len(img.data) if hasattr(img, 'data') else 0 for img in result.images]
        )
    
    async def test_async_patterns(self) -> TestResult:
        """Test various async patterns and error handling."""
        print("  Testing async patterns...")
        
        # Test concurrent operations
        tasks = []
        for i in range(3):
            request = AssetRequest(
                description=f"test image {i+1}",
                width=128,
                height=128,
                max_results=1
            )
            tasks.append(self.crayon.generate_async(request))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if hasattr(r, 'success') and r.success)
        total_count = len(results)
        
        return TestResult(
            test_name="Async Patterns",
            success=success_count > 0,
            duration=0,
            error=f"Only {success_count}/{total_count} concurrent operations succeeded" if success_count < total_count else None,
            details={
                "concurrent_operations": total_count,
                "successful_operations": success_count,
                "success_rate": success_count / total_count
            },
            images_generated=success_count
        )
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        total_images = sum(r.images_generated for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        
        # Group results by category
        categories = {
            "Generation": [r for r in self.results if "Text-to-Image" in r.test_name or "Generate" in r.test_name],
            "Augmentation": [r for r in self.results if "Augment" in r.test_name],
            "Cloning": [r for r in self.results if "Clone" in r.test_name],
            "Async Patterns": [r for r in self.results if "Async" in r.test_name]
        }
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
                "total_images_generated": total_images,
                "total_duration": total_duration,
                "average_duration": total_duration / total_tests if total_tests > 0 else 0
            },
            "categories": {},
            "detailed_results": [asdict(r) for r in self.results],
            "api_keys_status": self.api_keys
        }
        
        for category, tests in categories.items():
            if tests:
                cat_success = sum(1 for t in tests if t.success)
                report["categories"][category] = {
                    "total": len(tests),
                    "successful": cat_success,
                    "success_rate": cat_success / len(tests),
                    "images_generated": sum(t.images_generated for t in tests)
                }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """Print formatted test report."""
        print("\n" + "="*80)
        print("🧪 PURPLECRAYON INTEGRATION TEST REPORT")
        print("="*80)
        
        summary = report["summary"]
        print(f"\n📊 SUMMARY:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Successful: {summary['successful_tests']}")
        print(f"  Success Rate: {summary['success_rate']:.1%}")
        print(f"  Images Generated: {summary['total_images_generated']}")
        print(f"  Total Duration: {summary['total_duration']:.2f}s")
        print(f"  Average Duration: {summary['average_duration']:.2f}s")
        
        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, data in report["categories"].items():
            print(f"  {category}:")
            print(f"    Tests: {data['total']}")
            print(f"    Success Rate: {data['success_rate']:.1%}")
            print(f"    Images: {data['images_generated']}")
        
        print(f"\n🔍 DETAILED RESULTS:")
        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"  {status} {result.test_name}")
            print(f"    Duration: {result.duration:.2f}s")
            if result.images_generated > 0:
                print(f"    Images: {result.images_generated}")
            if result.error:
                print(f"    Error: {result.error}")
            if result.details:
                for key, value in result.details.items():
                    if key not in ["error", "status"]:
                        print(f"    {key}: {value}")
        
        print(f"\n🔑 API KEYS STATUS:")
        for engine, available in report["api_keys_status"].items():
            status = "✅" if available else "❌"
            print(f"  {engine}: {status}")
        
        print("\n" + "="*80)
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("🚀 Starting PurpleCrayon Integration Tests")
        print("="*50)
        
        # Define all tests
        tests = [
            ("Gemini Text-to-Image", self.test_gemini_text_to_image),
            ("Replicate Text-to-Image", self.test_replicate_text_to_image),
            ("PurpleCrayon Generate Async", self.test_purplecrayon_generate_async),
            ("Gemini Augmentation", self.test_gemini_augmentation),
            ("Replicate Augmentation", self.test_replicate_augmentation),
            ("Clone Functionality", self.test_clone_functionality),
            ("PurpleCrayon Augment Async", self.test_purplecrayon_augment_async),
            ("Async Patterns", self.test_async_patterns),
        ]
        
        # Run tests
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)
        
        # Generate and print report
        report = self.generate_report()
        self.print_report(report)
        
        # Save report to file
        report_path = self.assets_dir / "integration_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_path}")
        
        return report


async def main():
    """Main function to run integration tests."""
    tester = IntegrationTester()
    report = await tester.run_all_tests()
    
    # Exit with error code if any critical tests failed
    critical_tests = ["Gemini Text-to-Image", "PurpleCrayon Generate Async"]
    critical_failures = [
        r for r in tester.results 
        if r.test_name in critical_tests and not r.success
    ]
    
    if critical_failures:
        print(f"\n❌ {len(critical_failures)} critical test(s) failed!")
        sys.exit(1)
    else:
        print(f"\n✅ All critical tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
