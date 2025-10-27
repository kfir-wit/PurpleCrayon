"""
Simple Clone Tools - Generate AI images based on existing image descriptions

This module implements the clone functionality as described:
1. Analyze an existing image to generate a detailed description
2. Create an AssetRequest from that description
3. Use the standard generation pipeline (like generate_example.py)
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from PIL import Image
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..core.types import AssetRequest
from ..utils.config import get_env


async def analyze_image_for_description(image_path: str | Path) -> Dict[str, Any]:
    """
    Analyze an image and generate a detailed description for AI generation.
    
    Args:
        image_path: Path to the source image
        
    Returns:
        Dictionary with analysis results including description and metadata
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
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Determine MIME type
        mime_type = "image/jpeg"
        if image_path.suffix.lower() in ['.png']:
            mime_type = "image/png"
        elif image_path.suffix.lower() in ['.webp']:
            mime_type = "image/webp"
        elif image_path.suffix.lower() in ['.gif']:
            mime_type = "image/gif"
        
        # Create the prompt for image analysis
        prompt = """
        Analyze this image and create a detailed, descriptive prompt that could be used to generate a similar image with AI. 
        
        Focus on:
        - Main subjects and objects
        - Composition and framing
        - Colors and lighting
        - Style and mood
        - Technical details (resolution, format)
        
        Make the description specific enough that an AI could recreate a similar image, but general enough to be creative.
        Return only the descriptive prompt, no additional text.
        """
        
        # Generate description
        try:
            response = model.generate_content([
                prompt,
                {
                    "mime_type": mime_type,
                    "data": image_data
                }
            ], safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            })
            
            # Extract description from response
            if response and hasattr(response, 'text') and response.text:
                description = response.text.strip()
            else:
                # Fallback to filename-based description
                with Image.open(image_path) as img:
                    width, height = img.size
                    img_format = img.format.lower() if img.format else "jpeg"
                
                filename = image_path.stem
                description = f"A high-quality {filename.replace('_', ' ')} image, {width}x{height} {img_format}, professional photography style, detailed and clear"
            
        except Exception as e:
            print(f"⚠️ Vision analysis failed: {str(e)}, using filename-based description")
            # Fallback to filename-based description
            with Image.open(image_path) as img:
                width, height = img.size
                img_format = img.format.lower() if img.format else "jpeg"
            
            filename = image_path.stem
            description = f"A high-quality {filename.replace('_', ' ')} image, {width}x{height} {img_format}, professional photography style, detailed and clear"
        
        # Get image metadata
        with Image.open(image_path) as img:
            width, height = img.size
            img_format = img.format.lower() if img.format else "jpeg"
        
        return {
            "success": True,
            "description": description,
            "original_dimensions": (width, height),
            "original_format": img_format,
            "original_path": str(image_path)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to analyze image: {str(e)}"
        }


def create_asset_request_from_image(
    image_path: str | Path,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    format: Optional[str] = None,
    style: Optional[str] = None,
    guidance: Optional[str] = None,
    description: Optional[str] = None
) -> AssetRequest:
    """
    Create an AssetRequest from an image analysis.
    
    Args:
        image_path: Path to the source image
        width: Desired width (maintains aspect ratio if only one dimension provided)
        height: Desired height (maintains aspect ratio if only one dimension provided)
        format: Output format (if None, uses original format)
        style: Style guidance (photorealistic, artistic, etc.)
        guidance: Additional guidance for generation
        description: Custom description (if None, will analyze the image)
        
    Returns:
        AssetRequest ready for generation
    """
    image_path = Path(image_path)
    
    # Get image metadata for dimensions and format
    with Image.open(image_path) as img:
        original_width, original_height = img.size
        original_format = img.format.lower() if img.format else "jpeg"
    
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
    
    # Use provided description or create a basic one
    if description is None:
        filename = image_path.stem
        description = f"A high-quality {filename.replace('_', ' ')} image, {target_width}x{target_height} {format}, professional photography style, detailed and clear"
    
    # Add style guidance
    if style:
        description = f"{style} style, {description}"
    
    # Add additional guidance
    if guidance:
        description = f"{description}, {guidance}"
    
    # Add technical specifications
    description = f"{description}, {target_width}x{target_height} resolution, high quality"
    
    return AssetRequest(
        description=description,
        width=target_width,
        height=target_height,
        format=format,
        style=style,
        preferred_sources=["gemini", "imagen"],  # Use AI generation
        max_results=1  # Just one clone
    )


async def clone_image_simple(
    image_path: str | Path,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    format: Optional[str] = None,
    style: Optional[str] = None,
    guidance: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Clone an image using the simple approach: analyze -> AssetRequest -> generate.
    
    This is the approach you described - no file uploads, just description-based generation.
    
    Args:
        image_path: Path to the source image
        width: Desired width (maintains aspect ratio if only one dimension provided)
        height: Desired height (maintains aspect ratio if only one dimension provided)
        format: Output format (if None, uses original format)
        style: Style guidance (photorealistic, artistic, etc.)
        guidance: Additional guidance for generation
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
        print(f"🔍 Analyzing source image: {image_path.name}")
        
        # Step 1: Analyze the image to get a description
        analysis = await analyze_image_for_description(image_path)
        
        if not analysis.get("success"):
            print(f"⚠️ Analysis failed: {analysis.get('error')}, using basic description")
            # Fallback to basic description
            description = None
        else:
            description = analysis["description"]
            print(f"✅ Analysis successful: {description[:100]}...")
        
        # Step 2: Create AssetRequest from the analysis
        print(f"📝 Creating AssetRequest...")
        request = create_asset_request_from_image(
            image_path,
            width=width,
            height=height,
            format=format,
            style=style,
            guidance=guidance,
            description=description
        )
        
        print(f"🎨 AssetRequest created:")
        print(f"   Description: {request.description[:100]}...")
        print(f"   Dimensions: {request.width}x{request.height}")
        print(f"   Format: {request.format}")
        print(f"   Style: {request.style}")
        
        # Step 3: Use the standard generation pipeline
        print(f"🤖 Generating AI image using standard pipeline...")
        
        from ..core.runner import PurpleCrayon
        
        # Create a PurpleCrayon instance for generation
        crayon = PurpleCrayon(assets_dir=output_dir.parent if output_dir else Path("."))
        
        # Generate the image using the standard pipeline
        result = await crayon.generate_async(request)
        
        if not result.success:
            return {
                "success": False,
                "error": f"Image generation failed: {result.message}"
            }
        
        if not result.images:
            return {
                "success": False,
                "error": "No images generated"
            }
        
        # Get the generated image
        generated_image = result.images[0]
        
        # Step 4: Move to the correct output directory if specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Use identical filename with original extension (or specified format)
            original_name = image_path.stem
            original_extension = image_path.suffix.lower()
            
            # Get original format from analysis
            original_format = analysis.get("original_format", "jpeg")
            
            # Use original extension if format matches, otherwise use specified format
            if format == original_format:
                output_filename = f"{original_name}{original_extension}"
            else:
                output_filename = f"{original_name}.{format}"
            
            output_path = output_dir / output_filename
            
            # Move the generated image to the desired location
            import shutil
            shutil.move(generated_image.path, output_path)
            generated_image.path = str(output_path)
            
            print(f"✅ Moved cloned image to: {output_path}")
        
        return {
            "success": True,
            "original_path": str(image_path),
            "clone_path": generated_image.path,
            "original_filename": image_path.name,
            "clone_filename": Path(generated_image.path).name,
            "original_dimensions": analysis.get("original_dimensions", (0, 0)),
            "clone_dimensions": (generated_image.width, generated_image.height),
            "format": generated_image.format,
            "generation_prompt": request.description,
            "analysis": analysis,
            "generated_image": generated_image
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to clone image: {str(e)}"
        }
