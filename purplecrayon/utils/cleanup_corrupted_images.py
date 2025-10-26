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
    if len(sys.argv) != 2:
        print("Usage: python -m src.utils.cleanup_corrupted_images <directory_path>")
        print("Example: python -m src.utils.cleanup_corrupted_images downloads/downloaded/")
        sys.exit(1)
    
    directory = sys.argv[1]
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"❌ Directory does not exist: {directory}")
        sys.exit(1)
    
    if not directory_path.is_dir():
        print(f"❌ Path is not a directory: {directory}")
        sys.exit(1)
    
    print(f"🧹 Cleaning up corrupted images in: {directory}")
    print("=" * 50)
    
    stats = cleanup_corrupted_images(directory)
    
    print("=" * 50)
    print(f"📊 Cleanup Results:")
    print(f"  ✅ Valid images: {stats['valid']}")
    print(f"  ❌ Corrupted images removed: {stats['corrupted']}")
    print(f"  ⚠️ Errors: {stats['errors']}")
    
    if stats['corrupted'] > 0:
        print(f"\n🎉 Successfully cleaned up {stats['corrupted']} corrupted images!")
    else:
        print(f"\n✨ No corrupted images found - all {stats['valid']} images are valid!")


if __name__ == "__main__":
    main()
