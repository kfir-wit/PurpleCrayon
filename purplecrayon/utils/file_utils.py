"""
File utility functions for PurpleCrayon.

This module provides utilities for safe file operations, including
unique filename generation to prevent overwrites.
"""

from pathlib import Path
from typing import Optional


def get_unique_filename(base_path: Path, prefix: str = "", suffix: str = "", extension: str = "") -> Path:
    """
    Generate a unique filename to prevent overwrites.
    
    Args:
        base_path: The desired file path
        prefix: Optional prefix to add before the filename
        suffix: Optional suffix to add before the extension
        extension: File extension (with or without dot)
        
    Returns:
        A unique Path that doesn't exist
        
    Example:
        >>> get_unique_filename(Path("output/image.png"), "augmented", "_v1", ".png")
        Path("output/augmented_image_v1.png")
    """
    # Get the directory and base name
    directory = base_path.parent
    base_name = base_path.stem
    original_extension = base_path.suffix  # Get the original extension
    
    # Use provided extension or fall back to original
    if extension:
        if not extension.startswith('.'):
            extension = f".{extension}"
    else:
        extension = original_extension
    
    # Construct the desired filename
    if prefix:
        desired_name = f"{prefix}_{base_name}"
    else:
        desired_name = base_name
        
    if suffix:
        desired_name = f"{desired_name}{suffix}"
        
    desired_name = f"{desired_name}{extension}"
    target_path = directory / desired_name
    
    # If the file doesn't exist, return it
    if not target_path.exists():
        return target_path
    
    # Try variations with numeric suffixes
    counter = 1
    while counter <= 999:  # Safety limit
        if prefix:
            alt_name = f"{prefix}_{base_name}{suffix}_{counter}{extension}"
        else:
            alt_name = f"{base_name}{suffix}_{counter}{extension}"
            
        alt_path = directory / alt_name
        
        if not alt_path.exists():
            print(f"  🔄 Resolved filename conflict: {desired_name} -> {alt_name}")
            return alt_path
            
        counter += 1
    
    # If we reach here, something went wrong
    raise RuntimeError(f"Could not generate unique filename for {base_path} after 999 attempts")


def safe_save_file(content: bytes, target_path: Path, prefix: str = "", suffix: str = "") -> Path:
    """
    Safely save content to a file with a unique filename.
    
    Args:
        content: The content to save (bytes)
        target_path: The desired target path
        prefix: Optional prefix for the filename
        suffix: Optional suffix for the filename
        
    Returns:
        The actual path where the file was saved
    """
    # Get unique filename
    unique_path = get_unique_filename(target_path, prefix, suffix)
    
    # Ensure directory exists
    unique_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the file
    with open(unique_path, "wb") as f:
        f.write(content)
    
    return unique_path


def safe_save_text(content: str, target_path: Path, prefix: str = "", suffix: str = "") -> Path:
    """
    Safely save text content to a file with a unique filename.
    
    Args:
        content: The text content to save
        target_path: The desired target path
        prefix: Optional prefix for the filename
        suffix: Optional suffix for the filename
        
    Returns:
        The actual path where the file was saved
    """
    # Get unique filename
    unique_path = get_unique_filename(target_path, prefix, suffix)
    
    # Ensure directory exists
    unique_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the file
    with open(unique_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return unique_path
