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
from ..utils.config import get_env
from ..utils.file_utils import safe_save_file


async def _try_generation_engines(
    prompt: str,
    target_width: int,
    target_height: int,
    source_image_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Try multiple AI generation engines with fallback.
    
    Args:
        prompt: Generation prompt
        target_width: Target width
        target_height: Target height
        source_image_path: Optional source image for image-to-image generation
        
    Returns:
        Generation result with success status and data
    """
    engines = [
        ("replicate", _try_imagen_generation),  # Try Replicate first for image-to-image
        ("gemini", _try_gemini_generation),
    ]
    
    last_error = None
    
    for engine_name, engine_func in engines:
        try:
            print(f"🎨 Trying {engine_name} generation engine...")
            result = await engine_func(prompt, target_width, target_height, source_image_path)
            
            if result.get("success"):
                print(f"✅ {engine_name} generation successful")
                return result
            else:
                print(f"⚠️ {engine_name} failed: {result.get('error', 'Unknown error')}")
                last_error = result.get('error', f'{engine_name} failed')
                
        except Exception as e:
            print(f"❌ {engine_name} error: {str(e)}")
            last_error = str(e)
            continue
    
    return {
        "success": False,
        "error": f"All generation engines failed. Last error: {last_error}"
    }


async def _try_gemini_generation(prompt: str, width: int, height: int, source_image_path: Optional[Path] = None) -> Dict[str, Any]:
    """Try Gemini generation with optional source image."""
    try:
        from .ai_generation_tools import generate_with_gemini_async, generate_with_gemini_image_to_image_async
        
        # Convert dimensions to valid Gemini aspect ratio
        def get_valid_aspect_ratio(w, h):
            ratio = w / h
            if abs(ratio - 1.0) < 0.1:
                return "1:1"
            elif abs(ratio - 1.5) < 0.1:
                return "3:2"
            elif abs(ratio - 0.67) < 0.1:
                return "2:3"
            elif abs(ratio - 1.33) < 0.1:
                return "4:3"
            elif abs(ratio - 0.75) < 0.1:
                return "3:4"
            elif abs(ratio - 1.78) < 0.1:
                return "16:9"
            elif abs(ratio - 0.56) < 0.1:
                return "9:16"
            else:
                return "1:1"  # Default fallback
        
        aspect_ratio = get_valid_aspect_ratio(width, height)
        
        # Use image-to-image generation if source image is provided
        if source_image_path and source_image_path.exists():
            print(f"🎨 Using Gemini image-to-image generation with source: {source_image_path}")
            result = await generate_with_gemini_image_to_image_async(
                prompt, 
                str(source_image_path), 
                aspect_ratio=aspect_ratio
            )
        else:
            print(f"🎨 Using Gemini text-to-image generation")
            result = await generate_with_gemini_async(prompt, aspect_ratio=aspect_ratio)
        
        if result.get("status") == "succeeded":
            return {
                "success": True,
                "engine": "gemini",
                "data": result
            }
        else:
            return {
                "success": False,
                "error": f"Gemini generation failed: {result.get('reason', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Gemini error: {str(e)}"
        }


async def _try_imagen_generation(prompt: str, width: int, height: int, source_image_path: Optional[Path] = None) -> Dict[str, Any]:
    """Try Imagen/Replicate generation with optional source image."""
    try:
        import replicate
        from ..utils.config import get_env
        
        api_token = get_env("REPLICATE_API_TOKEN")
        if not api_token:
            return {
                "success": False,
                "error": "REPLICATE_API_TOKEN not set"
            }
        
        client = replicate.Client(api_token=api_token)
        
        # Use image-to-image generation if source image is provided
        if source_image_path and source_image_path.exists():
            print(f"🎨 Using Replicate image-to-image generation with source: {source_image_path}")
            
            # Upload the source image to Replicate
            with open(source_image_path, "rb") as f:
                uploaded_image = client.files.create(f)
            
            # Get the URL from the uploaded file
            image_url = uploaded_image.url if hasattr(uploaded_image, 'url') else str(uploaded_image)
            
            result = client.run(
                "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e2",
                input={
                    "prompt": prompt,
                    "init_image": image_url,
                    "width": width,
                    "height": height,
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5,
                    "strength": 0.8  # How much to modify the original image
                }
            )
        else:
            print("🎨 Using Replicate text-to-image generation")
            result = client.run(
                "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e2",
                input={
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5
                }
            )
        
        # Collect URLs from result
        if isinstance(result, str):
            urls = [result]
        else:
            urls = list(result)
        
        if urls:
            return {
                "success": True,
                "engine": "replicate",
                "data": {
                    "status": "succeeded",
                    "url": urls[-1],
                    "all": urls
                }
            }
        else:
            return {
                "success": False,
                "error": "No image generated"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Replicate error: {str(e)}"
        }


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
        genai.configure(api_key=get_env("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Convert image to base64
        image_base64 = _get_image_base64(image_path)
        
        # Create the prompt with image - enhanced to populate AssetRequest properties
        prompt = """
        Analyze this image and create a detailed description for AI image generation that includes:
        
        1. MAIN SUBJECT: What is the primary subject or focus of the image?
        2. COMPOSITION: How is the image framed and composed?
        3. STYLE: What artistic or photographic style is used?
        4. MOOD/ATMOSPHERE: What feeling or mood does the image convey?
        5. COLORS: What are the dominant colors and color palette?
        6. LIGHTING: How is the image lit (natural, artificial, soft, dramatic)?
        7. TEXTURE: What textures are visible or implied?
        8. SETTING: Where is the scene taking place?
        9. TECHNICAL DETAILS: Any notable technical aspects (depth of field, etc.)
        
        Format your response as a single, flowing description that could be used to generate a similar image with AI.
        Be specific about visual elements but concise enough for effective AI generation.
        Focus on the most important visual characteristics that would help recreate the essence of this image.
        """
        
        # Generate description
        try:
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
            
            # Check if response has content
            if not response:
                return {
                    "success": False,
                    "error": "Failed to analyze image - no response from API"
                }
            
            # Check for candidates
            if not hasattr(response, 'candidates') or not response.candidates:
                return {
                    "success": False,
                    "error": "Failed to analyze image - no candidates in response"
                }
            
            # Get the first candidate
            candidate = response.candidates[0]
            if not hasattr(candidate, 'content') or not candidate.content:
                return {
                    "success": False,
                    "error": "Failed to analyze image - no content in candidate"
                }
            
            # Extract text from content parts
            description_parts = []
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    description_parts.append(part.text)
            
            if not description_parts:
                return {
                    "success": False,
                    "error": "Failed to analyze image - no text content found"
                }
            
            # Join all text parts
            description = " ".join(description_parts).strip()
            
            # Print the generated description for debugging
            print(f"📝 Generated Description for {image_path.name}:")
            print(f"   {description[:200]}{'...' if len(description) > 200 else ''}")
            print()
            
        except Exception as e:
            print(f"⚠️ Vision analysis failed: {str(e)}, using filename-based description")
            # Fallback to filename-based description
            with Image.open(image_path) as img:
                width, height = img.size
                img_format = img.format.lower() if img.format else "jpeg"
            
            filename = image_path.stem
            description = f"A high-quality {filename.replace('_', ' ')} image, {width}x{height} {img_format}, professional photography style, detailed and clear"
            
            print(f"📝 Fallback Description for {image_path.name}:")
            print(f"   {description}")
            print()
            
            return {
                "success": True,
                "description": description,
                "original_dimensions": (width, height),
                "original_format": img_format,
                "perceptual_hash": "",
                "extra_meta": {}
            }
        
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
        # Step 1: Analyze the source image for better cloning
        print(f"🔍 Analyzing source image: {image_path.name}")
        
        # Try vision analysis first, fallback to filename-based description
        analysis = await describe_image_for_regeneration(image_path)
        
        if not analysis.get("success"):
            print(f"⚠️ Vision analysis failed, using filename-based description: {analysis.get('error')}")
            # Fallback to filename-based description
            with Image.open(image_path) as img:
                original_width, original_height = img.size
                original_format = img.format.lower() if img.format else "jpeg"
            
            filename = image_path.stem
            analysis = {
                "success": True,
                "description": f"A high-quality {filename.replace('_', ' ')} image, professional photography style, detailed and clear, similar composition and subject matter",
                "original_dimensions": (original_width, original_height),
                "original_format": original_format,
                "perceptual_hash": "",
                "extra_meta": {}
            }
        else:
            print(f"✅ Vision analysis successful: {analysis['description'][:100]}...")
        
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
        genai.configure(api_key=get_env("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        try:
            response = model.generate_content([
                f"Generate a new image based on this description: {base_prompt}",
                "Create a unique interpretation that captures the essence but is sufficiently different from the original.",
                "Avoid literal copying of specific details, logos, or copyrighted elements."
            ])
            
            # Check if response has content
            if not response or not hasattr(response, 'text') or not response.text:
                return {
                    "success": False,
                    "error": "Failed to generate image description - no response from API"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"API call failed: {str(e)}"
            }
        
        # Try multiple AI generation engines with fallback
        generation_result = await _try_generation_engines(
            prompt=base_prompt,
            target_width=target_width,
            target_height=target_height,
            source_image_path=image_path
        )
        
        if not generation_result.get("success"):
            return {
                "success": False,
                "error": f"Image generation failed: {generation_result.get('error', 'Unknown error')}"
            }
        
        # Step 4: Save the generated image
        if output_dir is None:
            output_dir = Path("downloads/cloned")
        else:
            output_dir = Path(output_dir)
        
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
        
        # Download and save the generated image
        actual_path = None
        if generation_result["data"].get("url"):
            # Download from URL
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(generation_result["data"]["url"])
                if response.status_code == 200:
                    actual_path = safe_save_file(
                        content=response.content,
                        target_path=output_path,
                        prefix="cloned"
                    )
                    print(f"✅ Downloaded cloned image to: {actual_path}")
                else:
                    return {
                        "success": False,
                        "error": f"Failed to download generated image: HTTP {response.status_code}"
                    }
        elif generation_result["data"].get("image_data"):
            # Save from binary data
            actual_path = safe_save_file(
                content=generation_result["data"]["image_data"],
                target_path=output_path,
                prefix="cloned"
            )
            print(f"✅ Saved cloned image to: {actual_path}")
        else:
            return {
                "success": False,
                "error": "No image data found in generation result"
            }
        
        # Step 5: Calculate similarity
        clone_phash = _calculate_perceptual_hash(actual_path)
        similarity = _calculate_similarity(analysis["perceptual_hash"], clone_phash)
        
        # Check if similarity is within acceptable bounds
        if similarity < similarity_threshold:
            print(f"⚠️  Warning: Clone may be too similar to original (similarity: {similarity:.2f})")
        
        return {
            "success": True,
            "original_path": str(image_path),
            "clone_path": str(actual_path),
            "original_filename": image_path.name,
            "clone_filename": actual_path.name,
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
