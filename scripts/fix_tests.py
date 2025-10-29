#!/usr/bin/env python3
"""
Script to fix test issues and categorize tests properly.
"""

import os
import re
from pathlib import Path

def fix_test_file(file_path: Path):
    """Fix common test issues in a file."""
    content = file_path.read_text()
    original_content = content
    
    # Fix 1: Add unit markers to basic tests
    if "test_asset_catalog.py" in str(file_path):
        # Add unit markers to basic catalog tests
        unit_patterns = [
            r'(def test_asset_catalog_creation_\w+\([^)]*\):)',
            r'(def test_catalog_\w+\([^)]*\):)',
            r'(def test_scan_\w+\([^)]*\):)',
            r'(def test_rename_\w+\([^)]*\):)',
            r'(def test_statistics_\w+\([^)]*\):)',
            r'(def test_search_\w+\([^)]*\):)',
            r'(def test_error_handling_\w+\([^)]*\):)',
        ]
        
        for pattern in unit_patterns:
            content = re.sub(
                pattern,
                r'    @pytest.mark.unit\n\1',
                content
            )
    
    # Fix 2: Fix AssetRequest parameter issues
    if "AssetRequest" in content:
        # Replace 'prompt' with 'description' in AssetRequest calls
        content = re.sub(
            r'AssetRequest\(\s*prompt=',
            'AssetRequest(\n            description=',
            content
        )
    
    # Fix 3: Fix clone_image parameter issues
    if "clone_image" in content:
        # Replace 'source_image_path' with 'source'
        content = re.sub(
            r'clone_image\(\s*source_image_path=',
            'clone_image(\n            source=',
            content
        )
    
    # Fix 4: Fix async/await issues
    if "async def test_" in content:
        # Add await to async function calls
        content = re.sub(
            r'(\s+)(result = )([a-zA-Z_][a-zA-Z0-9_]*_async\()',
            r'\1\2await \3',
            content
        )
    
    # Fix 5: Fix import issues
    if "generate_with_imagen" in content:
        content = content.replace("generate_with_imagen", "generate_with_replicate")
    
    # Fix 6: Add stress markers to comprehensive tests
    stress_patterns = [
        r'(def test_.*_different_\w+.*:)',  # Tests with multiple variations
        r'(def test_.*_all_\w+.*:)',        # Tests that test all options
        r'(def test_.*_comprehensive.*:)',  # Comprehensive tests
        r'(def test_.*_workflow_complete.*:)',  # Complete workflow tests
    ]
    
    for pattern in stress_patterns:
        # Only add stress marker if not already marked
        if not re.search(r'@pytest\.mark\.(stress|unit|integration)', content):
            content = re.sub(
                pattern,
                r'    @pytest.mark.stress\n\1',
                content
            )
    
    # Fix 7: Add integration markers to API-dependent tests
    api_patterns = [
        r'(def test_.*_gemini.*:)',
        r'(def test_.*_replicate.*:)',
        r'(def test_.*_unsplash.*:)',
        r'(def test_.*_pexels.*:)',
        r'(def test_.*_pixabay.*:)',
        r'(def test_.*_firecrawl.*:)',
        r'(def test_.*_api.*:)',
    ]
    
    for pattern in api_patterns:
        # Only add integration marker if not already marked
        if not re.search(r'@pytest\.mark\.(stress|unit|integration)', content):
            content = re.sub(
                pattern,
                r'    @pytest.mark.integration\n\1',
                content
            )
    
    if content != original_content:
        file_path.write_text(content)
        print(f"✅ Fixed {file_path}")
        return True
    else:
        print(f"⏭️  No changes needed for {file_path}")
        return False

def main():
    """Fix all test files."""
    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py"))
    
    print("Fixing test issues and categorizing tests...")
    print("=" * 60)
    
    modified_count = 0
    for test_file in test_files:
        if fix_test_file(test_file):
            modified_count += 1
    
    print("=" * 60)
    print(f"✅ Modified {modified_count} test files")
    print("\nTest categories:")
    print("1. Unit tests: pytest -m unit -v")
    print("2. Integration tests: pytest -m integration -v")
    print("3. Stress tests: pytest -m stress -v")
    print("4. All tests: pytest -v")

if __name__ == "__main__":
    main()
