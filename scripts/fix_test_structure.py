#!/usr/bin/env python3
"""
Fix test file structure and indentation issues.
"""

import re
from pathlib import Path

def fix_test_structure(file_path: Path):
    """Fix test file structure issues."""
    content = file_path.read_text()
    original_content = content
    
    # Fix 1: Move markers inside class definitions
    # Pattern: marker outside class + def inside class
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content
    )
    
    # Fix 2: Fix markers that are outside class definitions
    lines = content.split('\n')
    fixed_lines = []
    in_class = False
    class_indent = 0
    
    for i, line in enumerate(lines):
        # Check if we're entering a class
        if re.match(r'^class Test\w+:', line):
            in_class = True
            class_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue
        
        # Check if we're leaving a class (next class or end of file)
        if in_class and (re.match(r'^class Test\w+:', line) or 
                        (i < len(lines) - 1 and re.match(r'^class Test\w+:', lines[i+1]))):
            in_class = False
            class_indent = 0
        
        # If we're in a class and find a marker outside, move it inside
        if in_class and re.match(r'^\s*@pytest\.mark\.(unit|integration|stress)', line):
            # Check if next line is a def
            if i < len(lines) - 1 and re.match(r'^\s+def test_', lines[i+1]):
                # Move marker to proper indentation
                marker_line = line.strip()
                fixed_lines.append(' ' * (class_indent + 4) + marker_line)
                continue
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Fix 3: Ensure proper indentation for all markers
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content
    )
    
    if content != original_content:
        file_path.write_text(content)
        print(f"✅ Fixed structure in {file_path}")
        return True
    else:
        print(f"⏭️  No structure issues in {file_path}")
        return False

def main():
    """Fix structure in all test files."""
    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py"))
    
    print("Fixing test file structure...")
    print("=" * 60)
    
    modified_count = 0
    for test_file in test_files:
        if fix_test_structure(test_file):
            modified_count += 1
    
    print("=" * 60)
    print(f"✅ Fixed structure in {modified_count} test files")

if __name__ == "__main__":
    main()
