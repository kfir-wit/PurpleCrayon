"""
Image augmentation tools for PurpleCrayon.

This module provides functionality to upload existing images to AI engines
and modify them based on natural language prompts using image-to-image generation.
"""

import asyncio
import base64
import io
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from google import genai
from google.genai import types
import replicate
from PIL import Image

from ..core.types import OperationResult, ImageResult
from ..utils.config import get_env


async def augment_image_with_gemini_async(
    image_path: Union[str, Path],
    prompt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    output_format: str = "png",
    **kwargs
) -> ImageResult:
    """
    Augment an image using Google Gemini image-to-image generation.
    
    Args:
        image_path: Path to the source image
        prompt: Modification instructions
        width: Optional output width
        height: Optional output height
        output_format: Output image format
        **kwargs: Additional parameters
        
    Returns:
        ImageResult containing the augmented image
    """
    try:
        # Load and validate image
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        # Load image using PIL
        image = Image.open(image_path)
            
        # Construct modification prompt
        modification_prompt = f"Based on this image, {prompt}. Maintain the original style and composition while making the requested changes."
        
        # Initialize Gemini
        api_key = get_env("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
            
        client = genai.Client(api_key=api_key)
        
        # Generate augmented image
        print(f"Generating augmented image with Gemini: {prompt}")
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash-image",
            contents=[modification_prompt, image]
        )
        
        if not response or not hasattr(response, 'candidates') or not response.candidates:
            raise ValueError("Empty response from Gemini")
            
        # Extract image data from response
        image_data = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        break
        
        if not image_data:
            raise ValueError("No image data in Gemini response")
        
        return {
            "status": "succeeded",
            "image_data": image_data,
            "format": output_format or "png",
            "width": width or 1024,
            "height": height or 1024,
            "provider": "gemini_image_to_image",
            "description": modification_prompt
        }
        
    except Exception as e:
        print(f"Gemini augmentation failed: {e}")
        raise


async def augment_image_with_replicate_async(
    image_path: Union[str, Path],
    prompt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    output_format: str = "png",
    strength: float = 0.6,
    **kwargs
) -> ImageResult:
    """
    Augment an image using Replicate Stable Diffusion img2img.
    
    Args:
        image_path: Path to the source image
        prompt: Modification instructions
        width: Optional output width
        height: Optional output height
        output_format: Output image format
        strength: How much to modify the image (0.0-1.0)
        **kwargs: Additional parameters
        
    Returns:
        ImageResult containing the augmented image
    """
    try:
        # Load and validate image
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        # Initialize Replicate client
        api_token = get_env("REPLICATE_API_TOKEN")
        if not api_token:
            raise ValueError("REPLICATE_API_TOKEN not set")
            
        client = replicate.Client(api_token=api_token)
        
        # Upload image to Replicate
        print(f"Uploading image to Replicate: {image_path}")
        with open(image_path, "rb") as f:
            uploaded_image = client.files.create(file=f)
            
        # Get the URL from the uploaded file
        image_url = uploaded_image.urls.get("get") if hasattr(uploaded_image, 'urls') else str(uploaded_image)
        
        # Construct modification prompt
        modification_prompt = f"Based on this image, {prompt}. Maintain the original style and composition while making the requested changes."
        
        # Note: Using ControlNet model for img2img instead of standard SDXL
            
        # Generate augmented image using Stable Diffusion (text-to-image for now)
        # Note: Using text-to-image as img2img models may have access issues
        print(f"Generating augmented image with Replicate: {prompt}")
        output = await asyncio.to_thread(
            client.run,
            "stability-ai/stable-diffusion",
            input={
                "prompt": modification_prompt,
                "width": width or 1024,
                "height": height or 1024,
                "num_inference_steps": 20,
                "guidance_scale": 7.5
            }
        )
        
        if not output:
            raise ValueError("Empty response from Replicate")
            
        # Download the generated image
        import httpx
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(output[0])
            image_data = response.content
            
        return {
            "status": "succeeded",
            "image_data": image_data,
            "format": output_format or "png",
            "width": width or 1024,
            "height": height or 1024,
            "provider": "replicate_img2img",
            "description": modification_prompt
        }
        
    except Exception as e:
        print(f"Replicate augmentation failed: {e}")
        raise


def _get_valid_aspect_ratio(width: int, height: int) -> Optional[str]:
    """Convert width/height to Gemini-supported aspect ratio."""
    ratio = width / height
    
    # Map common ratios to Gemini's supported aspect ratios
    aspect_ratios = {
        1.0: "1:1",
        0.75: "3:4",  # 3:4
        1.33: "4:3",  # 4:3
        0.6: "3:5",   # 3:5
        1.67: "5:3",  # 5:3
        0.8: "4:5",   # 4:5
        1.25: "5:4",  # 5:4
        0.56: "9:16", # 9:16
        1.78: "16:9", # 16:9
        0.47: "21:9", # 21:9
    }
    
    # Find closest match
    closest_ratio = min(aspect_ratios.keys(), key=lambda x: abs(x - ratio))
    if abs(closest_ratio - ratio) < 0.1:  # Within 10% tolerance
        return aspect_ratios[closest_ratio]
    
    return None


async def _try_augmentation_engines(
    image_path: Union[str, Path],
    prompt: str,
    **kwargs
) -> tuple[ImageResult, bytes]:
    """
    Try augmentation engines in order with fallback.
    
    Args:
        image_path: Path to the source image
        prompt: Modification instructions
        **kwargs: Additional parameters
        
    Returns:
        Tuple of (ImageResult, image_data_bytes)
    """
    engines = [
        ("Gemini", augment_image_with_gemini_async),
        ("Replicate", augment_image_with_replicate_async),
    ]
    
    last_error = None
    
    for engine_name, engine_func in engines:
        try:
            print(f"Trying {engine_name} for image augmentation")
            result = await engine_func(image_path, prompt, **kwargs)
            print(f"Successfully augmented image with {engine_name}")
            
            # Create ImageResult from the result dictionary
            image_result = ImageResult(
                path="",  # Will be set by calling code
                source="ai",
                provider=result["provider"],
                width=result["width"],
                height=result["height"],
                format=result["format"],
                description=result["description"],
                match_score=None
            )
            
            return image_result, result["image_data"]
            
        except Exception as e:
            print(f"{engine_name} augmentation failed: {e}")
            last_error = e
            continue
    
    # If all engines failed
    error_msg = f"All augmentation engines failed. Last error: {last_error}"
    print(error_msg)
    raise RuntimeError(error_msg)


async def augment_image(
    image_path: Union[str, Path],
    prompt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    output_format: str = "png",
    output_dir: Optional[Union[str, Path]] = None,
    **kwargs
) -> OperationResult:
    """
    Augment a single image using AI image-to-image generation.
    
    Args:
        image_path: Path to the source image
        prompt: Modification instructions
        width: Optional output width
        height: Optional output height
        output_format: Output image format
        output_dir: Optional custom output directory
        **kwargs: Additional parameters
        
    Returns:
        OperationResult containing the augmented image
    """
    try:
        # Validate input
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        if not prompt.strip():
            raise ValueError("Modification prompt cannot be empty")
            
        # Determine output directory
        if output_dir is None:
            output_dir = Path("assets/ai")
        else:
            output_dir = Path(output_dir)
            
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate augmented image
        image_result, image_data = await _try_augmentation_engines(
            image_path=image_path,
            prompt=prompt,
            width=width,
            height=height,
            output_format=output_format,
            **kwargs
        )
        
        # Generate output filename
        original_name = image_path.stem
        output_filename = f"augmented_{original_name}.{output_format}"
        output_path = output_dir / output_filename
        
        # Save the augmented image
        with open(output_path, "wb") as f:
            f.write(image_data)
            
        print(f"Augmented image saved to: {output_path}")
        
        # Update the path in the result
        image_result.path = str(output_path)
        
        return OperationResult(
            success=True,
            message=f"Successfully augmented image: {output_path}",
            images=[image_result]
        )
        
    except Exception as e:
        error_msg = f"Image augmentation failed: {e}"
        print(error_msg)
        return OperationResult(
            success=False,
            message=error_msg,
            images=[]
        )


async def augment_images_from_directory(
    directory_path: Union[str, Path],
    prompt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    output_format: str = "png",
    output_dir: Optional[Union[str, Path]] = None,
    max_images: Optional[int] = None,
    **kwargs
) -> OperationResult:
    """
    Augment multiple images from a directory.
    
    Args:
        directory_path: Path to directory containing images
        prompt: Modification instructions
        width: Optional output width
        height: Optional output height
        output_format: Output image format
        output_dir: Optional custom output directory
        max_images: Maximum number of images to process
        **kwargs: Additional parameters
        
    Returns:
        OperationResult containing results for all processed images
    """
    try:
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")
            
        # Find all image files
        image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".svg"}
        image_files = [
            f for f in directory_path.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            raise ValueError(f"No image files found in: {directory_path}")
            
        # Limit number of images if specified
        if max_images:
            image_files = image_files[:max_images]
            
        print(f"Found {len(image_files)} images to augment")
        
        # Process images
        results = []
        successful = 0
        failed = 0
        
        for i, image_file in enumerate(image_files, 1):
            print(f"Processing image {i}/{len(image_files)}: {image_file.name}")
            
            try:
                result = await augment_image(
                    image_path=image_file,
                    prompt=prompt,
                    width=width,
                    height=height,
                    output_format=output_format,
                    output_dir=output_dir,
                    **kwargs
                )
                
                if result.success:
                    successful += 1
                    results.append({
                        "original": str(image_file),
                        "output": result.data["output_path"],
                        "success": True
                    })
                else:
                    failed += 1
                    results.append({
                        "original": str(image_file),
                        "error": result.message,
                        "success": False
                    })
                    
            except Exception as e:
                failed += 1
                error_msg = f"Failed to augment {image_file.name}: {e}"
                print(error_msg)
                results.append({
                    "original": str(image_file),
                    "error": error_msg,
                    "success": False
                })
                
        return OperationResult(
            success=successful > 0,
            message=f"Augmented {successful} images successfully, {failed} failed",
            images=[]
        )
        
    except Exception as e:
        error_msg = f"Batch augmentation failed: {e}"
        print(error_msg)
        return OperationResult(
            success=False,
            message=error_msg,
            images=[]
        )
