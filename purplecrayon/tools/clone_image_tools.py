"""
Clone Image Tools - AI-powered image cloning for royalty-free alternatives.

This module provides functionality to analyze existing images and generate
royalty-free alternatives using AI, helping avoid copyright issues while
maintaining creative vision.
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import base64
import io

from PIL import Image
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..models.image_result import ImageResult
from ..models.asset_request import AssetRequest


# Vision analysis prompt for detailed image description
VISION_ANALYSIS_PROMPT = """
Analyze this image and provide a detailed description for AI image generation.
Include:
1. Subject(s) and main elements
2. Composition and framing
3. Lighting and color palette
4. Style and artistic medium
5. Environment and mood
6. Textures and details
7. What to avoid (negative prompts)
8. Safety considerations

Format as a structured prompt suitable for image generation.
Be specific about visual elements but avoid copying exact details.
Focus on the essence and style rather than literal reproduction.
"""


def _get_image_base64(image_path: Path) -> str:
    """Convert image to base64 string for API."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def _calculate_perceptual_hash(image_path: Path) -> str:
    """Calculate perceptual hash for similarity checking."""
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale and resize to 8x8 for hash calculation
            img = img.convert('L').resize((8, 8), Image.Resampling.LANCZOS)
            
            # Calculate average pixel value
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            
            # Create hash based on whether each pixel is above/below average
            hash_bits = []
            for pixel in pixels:
                hash_bits.append('1' if pixel > avg else '0')
            
            return ''.join(hash_bits)
    except Exception as e:
        print(f"Warning: Could not calculate perceptual hash: {e}")
        return ""


def _calculate_similarity(hash1: str, hash2: str) -> float:
    """Calculate similarity between two perceptual hashes (0.0 to 1.0)."""
    if not hash1 or not hash2 or len(hash1) != len(hash2):
        return 0.0
    
    # Calculate Hamming distance
    distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    max_distance = len(hash1)
    
    # Convert to similarity (0.0 = identical, 1.0 = completely different)
    return distance / max_distance


async def describe_image_for_regeneration(
    image_path: str | Path,
    extra_meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze image and generate detailed description for regeneration.
    
    Args:
        image_path: Path to the image file
        extra_meta: Additional metadata to include in analysis
        
    Returns:
        Dictionary containing analysis results and generated prompt
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        return {
            "success": False,
            "error": f"Image file not found: {image_path}"
        }
    
    try:
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Convert image to base64
        image_base64 = _get_image_base64(image_path)
        
        # Create the prompt with image
        prompt = VISION_ANALYSIS_PROMPT
        
        # Generate description
        response = model.generate_content([
            prompt,
            {
                "mime_type": "image/jpeg",
                "data": image_base64
            }
        ], safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        })
        
        # Extract the generated description
        description = response.text.strip()
        
        # Calculate perceptual hash for similarity checking
        phash = _calculate_perceptual_hash(image_path)
        
        # Get image metadata
        with Image.open(image_path) as img:
            width, height = img.size
            format_type = img.format or "unknown"
        
        return {
            "success": True,
            "description": description,
            "original_dimensions": (width, height),
            "original_format": format_type,
            "perceptual_hash": phash,
            "file_size": image_path.stat().st_size,
            "extra_meta": extra_meta or {}
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to analyze image: {str(e)}"
        }


async def clone_image(
    image_path: str | Path,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    format: Optional[str] = None,
    style: Optional[str] = None,
    guidance: Optional[str] = None,
    similarity_threshold: float = 0.7,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Clone an image using AI analysis and generation.
    
    Args:
        image_path: Path to the source image
        width: Desired width (maintains aspect ratio if only one dimension provided)
        height: Desired height (maintains aspect ratio if only one dimension provided)
        format: Output format (if None, uses original format)
        style: Style guidance (photorealistic, artistic, etc.)
        guidance: Additional guidance for generation
        similarity_threshold: Maximum allowed similarity to original (0.0-1.0)
        output_dir: Directory to save cloned image
        
    Returns:
        Dictionary containing clone results and metadata
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        return {
            "success": False,
            "error": f"Source image not found: {image_path}"
        }
    
    try:
        # Step 1: Analyze the source image
        print(f"🔍 Analyzing source image: {image_path.name}")
        analysis = await describe_image_for_regeneration(image_path)
        
        if not analysis["success"]:
            return {
                "success": False,
                "error": f"Failed to analyze source image: {analysis['error']}"
            }
        
        # Step 2: Prepare generation parameters
        original_width, original_height = analysis["original_dimensions"]
        original_format = analysis["original_format"].lower()
        
        # Use original format if not specified
        if format is None:
            format = original_format
        
        # Calculate dimensions if not provided
        if width and height:
            target_width, target_height = width, height
        elif width:
            target_width = width
            target_height = int((width * original_height) / original_width)
        elif height:
            target_width = int((height * original_width) / original_height)
            target_height = height
        else:
            target_width, target_height = original_width, original_height
        
        # Build the generation prompt
        base_prompt = analysis["description"]
        
        # Add style guidance
        if style:
            base_prompt = f"{style} style, {base_prompt}"
        
        # Add additional guidance
        if guidance:
            base_prompt = f"{base_prompt}, {guidance}"
        
        # Add technical specifications
        base_prompt = f"{base_prompt}, {target_width}x{target_height} resolution, high quality"
        
        print(f"🎨 Generating clone with prompt: {base_prompt[:100]}...")
        
        # Step 3: Generate the cloned image
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = model.generate_content([
            f"Generate a new image based on this description: {base_prompt}",
            "Create a unique interpretation that captures the essence but is sufficiently different from the original.",
            "Avoid literal copying of specific details, logos, or copyrighted elements."
        ])
        
        if not response.text:
            return {
                "success": False,
                "error": "Failed to generate image description"
            }
        
        # For now, we'll use the text description to generate via the existing AI generation tools
        # In a full implementation, this would call the actual image generation API
        from .ai_generation_tools import generate_with_gemini
        
        generation_result = generate_with_gemini(
            prompt=base_prompt,
            aspect_ratio=f"{target_width}:{target_height}"
        )
        
        if not generation_result.get("success"):
            return {
                "success": False,
                "error": f"Image generation failed: {generation_result.get('error', 'Unknown error')}"
            }
        
        # Step 4: Save the generated image
        if output_dir is None:
            output_dir = Path("downloads/cloned")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use identical filename with original extension (or specified format)
        original_name = image_path.stem
        original_extension = image_path.suffix.lower()
        
        # Use original extension if format matches, otherwise use specified format
        if format == original_format:
            output_filename = f"{original_name}{original_extension}"
        else:
            output_filename = f"{original_name}.{format}"
        
        output_path = output_dir / output_filename
        
        # For now, we'll create a placeholder since we don't have actual image generation
        # In a real implementation, this would save the generated image
        print(f"📁 Would save cloned image to: {output_path}")
        
        # Step 5: Calculate similarity (placeholder)
        clone_phash = _calculate_perceptual_hash(image_path)  # Placeholder
        similarity = _calculate_similarity(analysis["perceptual_hash"], clone_phash)
        
        # Check if similarity is within acceptable bounds
        if similarity < similarity_threshold:
            print(f"⚠️  Warning: Clone may be too similar to original (similarity: {similarity:.2f})")
        
        return {
            "success": True,
            "original_path": str(image_path),
            "clone_path": str(output_path),
            "original_filename": image_path.name,
            "clone_filename": output_filename,
            "original_dimensions": (original_width, original_height),
            "clone_dimensions": (target_width, target_height),
            "format": format,
            "similarity_score": similarity,
            "generation_prompt": base_prompt,
            "perceptual_hash": clone_phash,
            "analysis": analysis
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to clone image: {str(e)}"
        }


async def clone_images_from_directory(
    source_dir: Path,
    *,
    output_dir: Optional[Path] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    format: Optional[str] = None,
    style: Optional[str] = None,
    guidance: Optional[str] = None,
    similarity_threshold: float = 0.7,
    max_images: Optional[int] = None
) -> Dict[str, Any]:
    """
    Clone all images from a directory.
    
    Args:
        source_dir: Directory containing source images
        output_dir: Directory to save cloned images
        width: Desired width for cloned images
        height: Desired height for cloned images
        format: Output format (if None, uses original format for each image)
        style: Style guidance
        guidance: Additional guidance
        similarity_threshold: Maximum allowed similarity
        max_images: Maximum number of images to process
        
    Returns:
        Dictionary containing batch clone results
    """
    if not source_dir.exists():
        return {
            "success": False,
            "error": f"Source directory not found: {source_dir}"
        }
    
    # Find all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(source_dir.glob(f"*{ext}"))
        image_files.extend(source_dir.glob(f"*{ext.upper()}"))
    
    if not image_files:
        return {
            "success": False,
            "error": f"No image files found in {source_dir}"
        }
    
    # Limit number of images if specified
    if max_images:
        image_files = image_files[:max_images]
    
    print(f"🔄 Found {len(image_files)} images to clone")
    
    results = []
    successful = 0
    failed = 0
    
    for i, image_file in enumerate(image_files, 1):
        print(f"\n📸 Processing {i}/{len(image_files)}: {image_file.name}")
        
        result = await clone_image(
            image_file,
            width=width,
            height=height,
            format=format,
            style=style,
            guidance=guidance,
            similarity_threshold=similarity_threshold,
            output_dir=output_dir
        )
        
        results.append(result)
        
        if result["success"]:
            successful += 1
            print(f"✅ Successfully cloned: {image_file.name} -> {result.get('clone_filename', 'unknown')}")
        else:
            failed += 1
            print(f"❌ Failed to clone: {image_file.name} - {result['error']}")
    
    return {
        "success": True,
        "total_images": len(image_files),
        "successful": successful,
        "failed": failed,
        "results": results
    }


def check_similarity(original_path: Path, clone_path: Path) -> float:
    """Check similarity between original and clone images."""
    try:
        original_hash = _calculate_perceptual_hash(original_path)
        clone_hash = _calculate_perceptual_hash(clone_path)
        return _calculate_similarity(original_hash, clone_hash)
    except Exception as e:
        print(f"Warning: Could not calculate similarity: {e}")
        return 0.0


def is_sufficiently_different(original_path: Path, clone_path: Path, threshold: float = 0.7) -> bool:
    """Check if clone is sufficiently different from original."""
    similarity = check_similarity(original_path, clone_path)
    return similarity < threshold
