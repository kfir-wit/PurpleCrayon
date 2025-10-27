"""
Asset request models for PurpleCrayon.

This module contains models for requesting and processing assets.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from pathlib import Path


class AssetRequest(BaseModel):
    """Request model for asset operations."""
    
    # Basic request parameters
    query: str = Field(..., description="Search query or prompt for asset generation")
    max_results: int = Field(default=1, ge=1, le=50, description="Maximum number of results to return")
    
    # Image specifications
    width: Optional[int] = Field(default=None, ge=1, le=4096, description="Image width in pixels")
    height: Optional[int] = Field(default=None, ge=1, le=4096, description="Image height in pixels")
    format: str = Field(default="png", description="Image format (png, jpg, webp)")
    style: Optional[str] = Field(default=None, description="Artistic style or theme")
    
    # Provider settings
    providers: List[str] = Field(default=["gemini"], description="AI providers to use")
    quality: str = Field(default="high", description="Generation quality (low, medium, high)")
    
    # Advanced options
    guidance: Optional[str] = Field(default=None, description="Additional guidance for generation")
    negative_prompt: Optional[str] = Field(default=None, description="What to avoid in generation")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducible results")
    
    # Output settings
    output_dir: Optional[Path] = Field(default=None, description="Output directory for generated assets")
    catalog_entry: bool = Field(default=True, description="Whether to add to asset catalog")
    
    @validator('format')
    def validate_format(cls, v):
        """Validate image format."""
        allowed_formats = ['png', 'jpg', 'jpeg', 'webp', 'gif']
        if v.lower() not in allowed_formats:
            raise ValueError(f"Format must be one of: {', '.join(allowed_formats)}")
        return v.lower()
    
    @validator('quality')
    def validate_quality(cls, v):
        """Validate quality setting."""
        allowed_qualities = ['low', 'medium', 'high']
        if v.lower() not in allowed_qualities:
            raise ValueError(f"Quality must be one of: {', '.join(allowed_qualities)}")
        return v.lower()
    
    @validator('providers')
    def validate_providers(cls, v):
        """Validate AI providers."""
        allowed_providers = ['gemini', 'dalle', 'imagen', 'midjourney']
        for provider in v:
            if provider.lower() not in allowed_providers:
                raise ValueError(f"Provider '{provider}' not supported. Allowed: {', '.join(allowed_providers)}")
        return [p.lower() for p in v]
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"


class ImageModificationRequest(AssetRequest):
    """Request model for image modification operations."""
    
    # Required for modification
    input_image: Path = Field(..., description="Path to the image to modify")
    modification_prompt: str = Field(..., description="Description of desired modifications")
    
    # Modification-specific options
    preserve_aspect_ratio: bool = Field(default=True, description="Whether to preserve original aspect ratio")
    modification_strength: float = Field(default=0.8, ge=0.0, le=1.0, description="Strength of modifications")
    
    @validator('input_image')
    def validate_input_image(cls, v):
        """Validate that input image exists and is readable."""
        if not v.exists():
            raise ValueError(f"Input image does not exist: {v}")
        if not v.is_file():
            raise ValueError(f"Input path is not a file: {v}")
        return v


class ImageCloneRequest(AssetRequest):
    """Request model for image cloning operations."""
    
    # Required for cloning
    source_image: Path = Field(..., description="Path to the reference image to clone")
    
    # Clone-specific options
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Maximum similarity to original")
    include_metadata: bool = Field(default=True, description="Whether to include original metadata")
    safety_filters: bool = Field(default=True, description="Whether to apply safety filters")
    
    @validator('source_image')
    def validate_source_image(cls, v):
        """Validate that source image exists and is readable."""
        if not v.exists():
            raise ValueError(f"Source image does not exist: {v}")
        if not v.is_file():
            raise ValueError(f"Source path is not a file: {v}")
        return v