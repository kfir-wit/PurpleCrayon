from pathlib import Path
from typing import List, Dict, Any
from PIL import Image

from .types import ImageResult


def dict_to_image_result(data: dict, source: str) -> ImageResult:
    """Convert internal dict to ImageResult."""
    return ImageResult(
        path=data.get("url", ""),
        source=source,
        provider=data.get("source_label", "unknown"),
        width=data.get("width", 0),
        height=data.get("height", 0),
        format=data.get("format", "unknown"),
        description=data.get("description"),
        match_score=data.get("match_score")
    )


def validate_and_create_result(files: List[str], source: str) -> List[ImageResult]:
    """Validate downloaded files and create ImageResults."""
    results = []
    
    for file_path in files:
        try:
            # Get image metadata
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format.lower() if img.format else "unknown"
            
            # Create result
            result = ImageResult(
                path=file_path,
                source=source,
                provider="unknown",
                width=width,
                height=height,
                format=format_name,
                description=None,
                match_score=None
            )
            results.append(result)
            
        except Exception as e:
            # Create error result
            error_result = ImageResult(
                path=file_path,
                source=source,
                provider="unknown",
                width=0,
                height=0,
                format="unknown",
                description=None,
                match_score=None,
                error=str(e)
            )
            results.append(error_result)
    
    return results


def file_path_to_image_result(file_path: str, source: str, provider: str = None) -> ImageResult:
    """Convert a file path to ImageResult with metadata."""
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            format_name = img.format.lower() if img.format else "unknown"
        
        return ImageResult(
            path=file_path,
            source=source,
            provider=provider,
            width=width,
            height=height,
            format=format_name,
            description=None,
            match_score=None
        )
    except Exception as e:
        return ImageResult(
            path=file_path,
            source=source,
            provider=provider,
            width=0,
            height=0,
            format="unknown",
            description=None,
            match_score=None,
            error=str(e)
        )
