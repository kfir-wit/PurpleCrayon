#!/usr/bin/env python3
"""
Standalone script to clean up corrupted images in a directory.
Usage: python -m src.utils.cleanup_corrupted_images <directory_path>
Example: python -m src.utils.cleanup_corrupted_images downloads/downloaded/
"""

import sys
from pathlib import Path
from ..tools.image_validation_tools import cleanup_corrupted_images


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python -m src.utils.cleanup_corrupted_images <directory_path> [--keep-junk]")
        print("Example: python -m src.utils.cleanup_corrupted_images downloads/downloaded/")
        print("Example: python -m src.utils.cleanup_corrupted_images downloads/downloaded/ --keep-junk")
        sys.exit(1)
    
    directory = sys.argv[1]
    remove_junk = "--keep-junk" not in sys.argv
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"❌ Directory does not exist: {directory}")
        sys.exit(1)
    
    if not directory_path.is_dir():
        print(f"❌ Path is not a directory: {directory}")
        sys.exit(1)
    
    print(f"🧹 Cleaning up images in: {directory}")
    if remove_junk:
        print("🗑️ Junk file removal: ENABLED")
    else:
        print("🗑️ Junk file removal: DISABLED")
    print("=" * 50)
    
    stats = cleanup_corrupted_images(directory, remove_junk)
    
    print("=" * 50)
    print(f"📊 Cleanup Results:")
    print(f"  ✅ Valid images: {stats['valid']}")
    print(f"  ❌ Corrupted images removed: {stats['corrupted']}")
    if remove_junk:
        print(f"  🗑️ Junk files removed: {stats['junk']}")
    print(f"  ⚠️ Errors: {stats['errors']}")
    
    total_removed = stats['corrupted'] + stats.get('junk', 0)
    if total_removed > 0:
        print(f"\n🎉 Successfully cleaned up {total_removed} files!")
    else:
        print(f"\n✨ No files needed cleaning - all {stats['valid']} images are valid!")


if __name__ == "__main__":
    main()
