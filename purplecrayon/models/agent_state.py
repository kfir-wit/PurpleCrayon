"""
Agent state models for PurpleCrayon.

This module contains models for managing agent state and workflow.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
from datetime import datetime
from enum import Enum

from .image_result import ImageResult, OperationResult
from .asset_request import AssetRequest, ImageModificationRequest, ImageCloneRequest


class AgentMode(str, Enum):
    """Available agent modes."""
    GENERATE = "generate"
    MODIFY = "modify"
    CLONE = "clone"
    SEARCH = "search"
    PROCESS = "process"
    BENCHMARK = "benchmark"


class AgentState(BaseModel):
    """State model for PurpleCrayon agent operations."""
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        extra="forbid",
    )
    
    # Basic state
    mode: AgentMode = Field(..., description="Current agent mode")
    session_id: str = Field(..., description="Unique session identifier")
    started_at: datetime = Field(default_factory=datetime.now, description="Session start time")
    
    # Current operation
    current_request: Optional[Union[AssetRequest, ImageModificationRequest, ImageCloneRequest]] = Field(
        default=None, description="Current operation request"
    )
    current_operation: Optional[OperationResult] = Field(
        default=None, description="Current operation result"
    )
    
    # Results and history
    completed_operations: List[OperationResult] = Field(
        default_factory=list, description="History of completed operations"
    )
    all_images: List[ImageResult] = Field(
        default_factory=list, description="All images from this session"
    )
    
    # Configuration
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Agent configuration"
    )
    
    # Status tracking
    is_processing: bool = Field(default=False, description="Whether agent is currently processing")
    last_activity: datetime = Field(default_factory=datetime.now, description="Last activity timestamp")
    
    # Error handling
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    
    # Statistics
    total_operations: int = Field(default=0, description="Total operations performed")
    total_images_generated: int = Field(default=0, description="Total images generated")
    total_processing_time: float = Field(default=0.0, description="Total processing time in seconds")
    
    def start_operation(self, request: Union[AssetRequest, ImageModificationRequest, ImageCloneRequest]) -> None:
        """Start a new operation."""
        self.current_request = request
        self.current_operation = OperationResult(
            success=False,
            operation_type=request.__class__.__name__,
            total_images=0
        )
        self.is_processing = True
        self.last_activity = datetime.now()
    
    def complete_operation(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Complete the current operation."""
        if self.current_operation:
            self.current_operation.success = success
            self.current_operation.mark_completed()
            
            if error_message:
                self.current_operation.error_message = error_message
                self.errors.append(error_message)
            
            # Add to history
            self.completed_operations.append(self.current_operation)
            
            # Update statistics
            self.total_operations += 1
            if self.current_operation.duration_seconds:
                self.total_processing_time += self.current_operation.duration_seconds
            
            # Add images to session
            for image in self.current_operation.images:
                self.all_images.append(image)
                if image.status.value == "completed":
                    self.total_images_generated += 1
        
        # Reset current operation
        self.current_operation = None
        self.current_request = None
        self.is_processing = False
        self.last_activity = datetime.now()
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.last_activity = datetime.now()
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        self.last_activity = datetime.now()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session."""
        successful_operations = [op for op in self.completed_operations if op.success]
        failed_operations = [op for op in self.completed_operations if not op.success]
        
        return {
            "session_id": self.session_id,
            "mode": self.mode.value,
            "started_at": self.started_at.isoformat(),
            "duration_seconds": (datetime.now() - self.started_at).total_seconds(),
            "total_operations": self.total_operations,
            "successful_operations": len(successful_operations),
            "failed_operations": len(failed_operations),
            "total_images_generated": self.total_images_generated,
            "total_processing_time": self.total_processing_time,
            "is_processing": self.is_processing,
            "errors": len(self.errors),
            "warnings": len(self.warnings)
        }
    
    def get_recent_images(self, limit: int = 10) -> List[ImageResult]:
        """Get the most recently generated images."""
        return sorted(self.all_images, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def clear_errors(self) -> None:
        """Clear all error messages."""
        self.errors.clear()
    
    def clear_warnings(self) -> None:
        """Clear all warning messages."""
        self.warnings.clear()
    
