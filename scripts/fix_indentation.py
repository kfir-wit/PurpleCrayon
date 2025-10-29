#!/usr/bin/env python3
"""
Fix indentation issues in test files.
"""

import re
from pathlib import Path

def fix_indentation(file_path: Path):
    """Fix indentation issues in a test file."""
    content = file_path.read_text()
    original_content = content
    
    # Fix incorrect indentation for pytest markers
    # Pattern: spaces + @pytest.mark.unit + newline + spaces + def
    content = re.sub(
        r'(\s+)@pytest\.mark\.unit\n(\s+)def ',
        r'\1@pytest.mark.unit\n\1def ',
        content
    )
    
    # Fix any remaining indentation issues with markers
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content
    )
    
    if content != original_content:
        file_path.write_text(content)
        print(f"✅ Fixed indentation in {file_path}")
        return True
    else:
        print(f"⏭️  No indentation issues in {file_path}")
        return False

def main():
    """Fix indentation in all test files."""
    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py"))
    
    print("Fixing indentation issues in test files...")
    print("=" * 60)
    
    modified_count = 0
    for test_file in test_files:
        if fix_indentation(test_file):
            modified_count += 1
    
    print("=" * 60)
    print(f"✅ Fixed indentation in {modified_count} test files")

if __name__ == "__main__":
    main()
