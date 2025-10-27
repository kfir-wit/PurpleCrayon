from dataclasses import dataclass, field
from typing import Optional, Literal, List
from pathlib import Path


@dataclass
class AssetRequest:
    """Request specification for fetching, generating, or sourcing images."""
    
    # Mandatory field
    description: str  # Natural language description of desired image
    
    # Optional - Size/dimensions
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None  # e.g., "16:9", "1:1", "4:3"
    
    # Optional - Format specifications
    format: Optional[Literal["jpg", "jpeg", "png", "gif", "webp", "ico"]] = None
    has_alpha: Optional[bool] = None  # Require/prefer transparency
    
    # Optional - Quality/style preferences
    style: Optional[str] = None  # e.g., "artistic", "photorealistic", "watercolor"
    quality: Optional[Literal["low", "medium", "high"]] = "high"
    
    # Optional - Source preferences
    preferred_sources: List[str] = field(default_factory=list)  # ["unsplash", "gemini", etc.]
    exclude_sources: List[str] = field(default_factory=list)
    
    # Optional - Result limits
    max_results: int = 3
    
    # Optional - Output configuration
    output_dir: Optional[Path] = None  # Override default downloads/
    filename: Optional[str] = None  # Custom filename (without extension)
    
    # Optional - Advanced options
    orientation: Optional[Literal["landscape", "portrait", "square"]] = None
    min_width: Optional[int] = None
    min_height: Optional[int] = None
    tags: List[str] = field(default_factory=list)  # Additional search tags


@dataclass
class ImageResult:
    path: str
    source: Literal["stock", "ai", "local", "scraped"]
    provider: Optional[str]  # "unsplash", "gemini", etc.
    width: int
    height: int
    format: str
    description: Optional[str]
    match_score: Optional[float]
    error: Optional[str] = None


@dataclass
class OperationResult:
    success: bool
    message: str
    images: List[ImageResult]
    error_code: Optional[str] = None
