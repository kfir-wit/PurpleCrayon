#!/usr/bin/env python3
"""
Script to add @pytest.mark.unit markers to basic unit tests.
This helps implement fail-fast methodology where unit tests run first.
"""

import os
import re
from pathlib import Path

def add_unit_markers_to_file(file_path: Path):
    """Add @pytest.mark.unit markers to appropriate test methods."""
    content = file_path.read_text()
    
    # Patterns for basic unit tests (non-API, non-integration)
    unit_test_patterns = [
        # Asset catalog tests
        r'(def test_asset_catalog_\w+\([^)]*\):)',
        r'(def test_catalog_\w+\([^)]*\):)',
        r'(def test_scan_\w+\([^)]*\):)',
        r'(def test_rename_\w+\([^)]*\):)',
        r'(def test_statistics_\w+\([^)]*\):)',
        r'(def test_search_\w+\([^)]*\):)',
        r'(def test_error_handling_\w+\([^)]*\):)',
        r'(def test_integration_\w+\([^)]*\):)',
        
        # Model management tests (non-API)
        r'(def test_list_available_models_\w+\([^)]*\):)',
        r'(def test_check_model_updates_\w+\([^)]*\):)',
        r'(def test_model_\w+\([^)]*\):)',
        
        # Basic validation tests
        r'(def test_\w+_invalid_\w+\([^)]*\):)',
        r'(def test_\w+_error_handling_\w+\([^)]*\):)',
        r'(def test_\w+_validation_\w+\([^)]*\):)',
    ]
    
    # Skip patterns (API-dependent or integration tests)
    skip_patterns = [
        r'@pytest\.mark\.(api_|integration|slow)',
        r'def test_.*_(api|integration|async|sync).*:',
        r'def test_.*_gemini.*:',
        r'def test_.*_replicate.*:',
        r'def test_.*_unsplash.*:',
        r'def test_.*_pexels.*:',
        r'def test_.*_pixabay.*:',
        r'def test_.*_firecrawl.*:',
    ]
    
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        # Skip if already has a marker
        if '@pytest.mark.' in line:
            continue
            
        # Check if this is a unit test method
        is_unit_test = False
        for pattern in unit_test_patterns:
            if re.search(pattern, line):
                is_unit_test = True
                break
        
        # Skip if it's an API or integration test
        if is_unit_test:
            for skip_pattern in skip_patterns:
                if re.search(skip_pattern, line):
                    is_unit_test = False
                    break
        
        # Add unit marker
        if is_unit_test:
            # Find the class definition to add proper indentation
            class_indent = ""
            for j in range(i-1, -1, -1):
                if lines[j].strip().startswith('class '):
                    class_indent = "    "  # Standard class method indentation
                    break
                elif lines[j].strip().startswith('def '):
                    # Check if we're in a nested class
                    nested_class_indent = ""
                    for k in range(j-1, -1, -1):
                        if lines[k].strip().startswith('class '):
                            nested_class_indent = "        "  # Nested class method indentation
                            break
                    class_indent = nested_class_indent
                    break
            
            # Add the marker
            marker_line = f"{class_indent}@pytest.mark.unit"
            lines.insert(i, marker_line)
            modified = True
    
    if modified:
        file_path.write_text('\n'.join(lines))
        print(f"✅ Added unit markers to {file_path}")
        return True
    else:
        print(f"⏭️  No changes needed for {file_path}")
        return False

def main():
    """Add unit markers to all test files."""
    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py"))
    
    print("Adding @pytest.mark.unit markers to basic unit tests...")
    print("=" * 60)
    
    modified_count = 0
    for test_file in test_files:
        if add_unit_markers_to_file(test_file):
            modified_count += 1
    
    print("=" * 60)
    print(f"✅ Modified {modified_count} test files")
    print("\nTo run tests in fail-fast mode:")
    print("1. Unit tests first: pytest -m unit -v")
    print("2. Integration tests: pytest -m 'integration and not unit' -v")
    print("3. All tests: pytest -v")

if __name__ == "__main__":
    main()
