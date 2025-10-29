#!/usr/bin/env python3
"""
Comprehensive script to fix ALL indentation issues in test files.
"""

import re
from pathlib import Path

def fix_all_indentation_comprehensive(file_path: Path):
    """Fix all indentation issues comprehensively."""
    content = file_path.read_text()
    original_content = content
    
    # Fix 1: Fix all markers that are incorrectly indented
    # Pattern: any number of spaces + @pytest.mark.unit + newline + more spaces + def
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content,
        flags=re.MULTILINE
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
        if in_class and (i < len(lines) - 1 and re.match(r'^class Test\w+:', lines[i+1])):
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
    
    # Fix 3: Fix any remaining markers that are incorrectly indented
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content,
        flags=re.MULTILINE
    )
    
    # Fix 4: Fix markers that are outside class definitions (more aggressive)
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content,
        flags=re.MULTILINE
    )
    
    # Fix 5: Fix any remaining markers that are incorrectly indented
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content,
        flags=re.MULTILINE
    )
    
    # Fix 6: Fix markers that are outside class definitions (even more aggressive)
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content,
        flags=re.MULTILINE
    )
    
    # Fix 7: Fix any remaining markers that are incorrectly indented
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content,
        flags=re.MULTILINE
    )
    
    # Fix 8: Fix markers that are outside class definitions (final attempt)
    content = re.sub(
        r'(\s+)@pytest\.mark\.(unit|integration|stress)\n(\s+)def ',
        r'\1@pytest.mark.\2\n\1def ',
        content,
        flags=re.MULTILINE
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
    
    print("Fixing all indentation issues in test files...")
    print("=" * 60)
    
    modified_count = 0
    for test_file in test_files:
        if fix_all_indentation_comprehensive(test_file):
            modified_count += 1
    
    print("=" * 60)
    print(f"✅ Fixed indentation in {modified_count} test files")

if __name__ == "__main__":
    main()
