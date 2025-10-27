"""
Image result models for PurpleCrayon.

This module contains models for image generation and processing results.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from pathlib import Path
from datetime import datetime
from enum import Enum


class ImageStatus(str, Enum):
    """Status of image processing operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImageSource(str, Enum):
    """Source of the image."""
    GENERATED = "generated"
    STOCK = "stock"
    CLONE = "clone"
    MODIFIED = "modified"
    UPLOADED = "uploaded"


class ImageResult(BaseModel):
    """Result of a single image generation or processing operation."""
    
    # Basic information
    id: str = Field(..., description="Unique identifier for the image")
    filename: str = Field(..., description="Generated filename")
    path: Path = Field(..., description="Full path to the image file")
    
    # Image properties
    width: int = Field(..., ge=1, description="Image width in pixels")
    height: int = Field(..., ge=1, description="Image height in pixels")
    format: str = Field(..., description="Image format (png, jpg, etc.)")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    
    # Generation details
    prompt: str = Field(..., description="Prompt used for generation")
    provider: str = Field(..., description="AI provider used")
    model: str = Field(..., description="Specific model used")
    source: ImageSource = Field(..., description="Source of the image")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    status: ImageStatus = Field(default=ImageStatus.COMPLETED, description="Processing status")
    
    # Optional metadata
    seed: Optional[int] = Field(default=None, description="Random seed used")
    style: Optional[str] = Field(default=None, description="Artistic style applied")
    guidance: Optional[str] = Field(default=None, description="Additional guidance used")
    negative_prompt: Optional[str] = Field(default=None, description="Negative prompt used")
    
    # Quality metrics
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="AI-generated quality score")
    similarity_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Similarity to reference")
    
    # Error information
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    
    @validator('format')
    def validate_format(cls, v):
        """Validate image format."""
        allowed_formats = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff']
        if v.lower() not in allowed_formats:
            raise ValueError(f"Format must be one of: {', '.join(allowed_formats)}")
        return v.lower()
    
    @validator('path')
    def validate_path(cls, v):
        """Validate that path is absolute."""
        if not v.is_absolute():
            raise ValueError("Path must be absolute")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.dict()
    
    def to_catalog_entry(self) -> Dict[str, Any]:
        """Convert to catalog entry format."""
        return {
            "id": self.id,
            "filename": self.filename,
            "path": str(self.path),
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "size_bytes": self.size_bytes,
            "prompt": self.prompt,
            "provider": self.provider,
            "model": self.model,
            "source": self.source.value,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "seed": self.seed,
            "style": self.style,
            "guidance": self.guidance,
            "negative_prompt": self.negative_prompt,
            "quality_score": self.quality_score,
            "similarity_score": self.similarity_score
        }
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"


class OperationResult(BaseModel):
    """Result of a complete operation (may include multiple images)."""
    
    # Operation details
    success: bool = Field(..., description="Whether the operation succeeded")
    operation_type: str = Field(..., description="Type of operation performed")
    total_images: int = Field(..., ge=0, description="Total number of images processed")
    
    # Results
    images: List[ImageResult] = Field(default_factory=list, description="List of generated/processed images")
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.now, description="Operation start time")
    completed_at: Optional[datetime] = Field(default=None, description="Operation completion time")
    duration_seconds: Optional[float] = Field(default=None, ge=0, description="Total duration in seconds")
    
    # Error information
    error_message: Optional[str] = Field(default=None, description="Error message if operation failed")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    
    # Statistics
    total_size_bytes: int = Field(default=0, ge=0, description="Total size of all images in bytes")
    average_quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Average quality score")
    
    def add_image(self, image: ImageResult) -> None:
        """Add an image to the result."""
        self.images.append(image)
        self.total_images = len(self.images)
        self.total_size_bytes += image.size_bytes
    
    def mark_completed(self) -> None:
        """Mark the operation as completed."""
        self.completed_at = datetime.now()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        
        # Calculate average quality score
        quality_scores = [img.quality_score for img in self.images if img.quality_score is not None]
        if quality_scores:
            self.average_quality_score = sum(quality_scores) / len(quality_scores)
    
    def get_successful_images(self) -> List[ImageResult]:
        """Get only successfully processed images."""
        return [img for img in self.images if img.status == ImageStatus.COMPLETED]
    
    def get_failed_images(self) -> List[ImageResult]:
        """Get only failed images."""
        return [img for img in self.images if img.status == ImageStatus.FAILED]
    
    def to_summary(self) -> Dict[str, Any]:
        """Get a summary of the operation."""
        successful = self.get_successful_images()
        failed = self.get_failed_images()
        
        return {
            "success": self.success,
            "operation_type": self.operation_type,
            "total_images": self.total_images,
            "successful_images": len(successful),
            "failed_images": len(failed),
            "duration_seconds": self.duration_seconds,
            "total_size_bytes": self.total_size_bytes,
            "average_quality_score": self.average_quality_score,
            "error_message": self.error_message,
            "warnings": self.warnings
        }
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"