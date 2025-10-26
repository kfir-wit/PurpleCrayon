from pathlib import Path
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import json

from .types import AssetRequest


class AssetRequestSchema(BaseModel):
    """Pydantic schema for parsing markdown into AssetRequest."""
    
    description: str = Field(..., description="Natural language description of the desired image")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    aspect_ratio: Optional[str] = Field(None, description="Aspect ratio like '16:9', '1:1', '4:3'")
    format: Optional[Literal["jpg", "png", "gif", "webp", "ico"]] = Field(None, description="Image format")
    has_alpha: Optional[bool] = Field(None, description="Require/prefer transparency")
    style: Optional[str] = Field(None, description="Style like 'artistic', 'photorealistic', 'watercolor'")
    quality: Optional[Literal["low", "medium", "high"]] = Field("high", description="Quality level")
    preferred_sources: List[str] = Field(default_factory=list, description="List of preferred sources")
    exclude_sources: List[str] = Field(default_factory=list, description="List of sources to exclude")
    max_results: int = Field(3, description="Maximum number of results")
    output_dir: Optional[str] = Field(None, description="Output directory path")
    filename: Optional[str] = Field(None, description="Custom filename without extension")
    orientation: Optional[Literal["landscape", "portrait", "square"]] = Field(None, description="Image orientation")
    min_width: Optional[int] = Field(None, description="Minimum width requirement")
    min_height: Optional[int] = Field(None, description="Minimum height requirement")
    tags: List[str] = Field(default_factory=list, description="Additional search tags")
    
    @field_validator('format', mode='before')
    def normalize_format(cls, v):
        """Normalize format to lowercase."""
        if v:
            return v.lower()
        return v
    
    @field_validator('preferred_sources', mode='before')
    def normalize_sources(cls, v):
        """Normalize source names to lowercase."""
        if isinstance(v, list):
            return [source.lower() for source in v]
        return v


def markdownRequest(markdown_content: str) -> AssetRequest:
    """Parse a markdown prompt into an AssetRequest object using LLM + Pydantic.
    
    This approach uses an LLM to extract structured data from natural language
    markdown and validates it with Pydantic for type safety.
    """
    try:
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Create prompt for LLM
        prompt = f"""
You are an expert at parsing image generation requests from markdown text.

Extract the following information from the markdown and return it as a JSON object:

{{
    "description": "Natural language description of the desired image",
    "width": 1920,  // Optional: image width in pixels
    "height": 1080, // Optional: image height in pixels  
    "aspect_ratio": "16:9", // Optional: aspect ratio like "16:9", "1:1", "4:3"
    "format": "jpg", // Optional: "jpg", "png", "gif", "webp", "ico"
    "has_alpha": false, // Optional: require/prefer transparency
    "style": "artistic", // Optional: style like "artistic", "photorealistic", "watercolor"
    "quality": "high", // Optional: "low", "medium", "high"
    "preferred_sources": ["unsplash", "gemini"], // Optional: list of preferred sources
    "exclude_sources": [], // Optional: list of sources to exclude
    "max_results": 3, // Optional: maximum number of results
    "output_dir": "downloads/final", // Optional: output directory
    "filename": "panda", // Optional: custom filename without extension
    "orientation": "landscape", // Optional: "landscape", "portrait", "square"
    "min_width": 800, // Optional: minimum width requirement
    "min_height": 600, // Optional: minimum height requirement
    "tags": ["nature", "wildlife"] // Optional: additional search tags
}}

Rules:
- Only include fields that are explicitly mentioned or can be reasonably inferred
- For "description", extract the main subject/object being requested
- For "width" and "height", parse from size specifications like "1920x1080"
- For "format", normalize to lowercase (jpg, png, etc.)
- For "preferred_sources", normalize to lowercase (unsplash, gemini, etc.)
- For "style", extract descriptive style words
- For "tags", extract relevant keywords from the description
- Return only valid JSON, no additional text

Markdown content to parse:
{markdown_content}
"""
        
        # Get LLM response
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        
        # Parse JSON response
        try:
            json_data = json.loads(response.content.strip())
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group())
            else:
                raise ValueError("Could not extract JSON from LLM response")
        
        # Validate with Pydantic
        schema = AssetRequestSchema(**json_data)
        
        # Convert to AssetRequest
        return AssetRequest(
            description=schema.description,
            width=schema.width,
            height=schema.height,
            aspect_ratio=schema.aspect_ratio,
            format=schema.format,
            has_alpha=schema.has_alpha,
            style=schema.style,
            quality=schema.quality,
            preferred_sources=schema.preferred_sources,
            exclude_sources=schema.exclude_sources,
            max_results=schema.max_results,
            output_dir=Path(schema.output_dir) if schema.output_dir else None,
            filename=schema.filename,
            orientation=schema.orientation,
            min_width=schema.min_width,
            min_height=schema.min_height,
            tags=schema.tags
        )
        
    except Exception as e:
        # Fallback to basic parsing if LLM fails
        print(f"⚠️ LLM parsing failed: {e}")
        print("🔄 Falling back to basic parsing...")
        
        # Extract basic description (first non-empty line after title)
        lines = markdown_content.strip().split('\n')
        description = "Image asset"
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('**'):
                description = line
                break
        
        return AssetRequest(description=description)
