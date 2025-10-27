from __future__ import annotations

import asyncio
from typing import Any, Dict

import replicate as replicate_sdk
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..utils.config import get_env


def _generate_with_imagen_sync(prompt: str, **params: Any) -> Dict[str, Any]:
    """Blocking Imagen call executed inside a worker thread."""
    token = get_env("REPLICATE_API_TOKEN")
    if not token:
        return {"status": "skipped", "reason": "REPLICATE_API_TOKEN missing"}
    replicate = replicate_sdk.Client(api_token=token)

    model = params.pop("model", None) or "stability-ai/sdxl"  # sensible default
    input_payload = {"prompt": prompt} | params

    output = replicate.run(model, input=input_payload)
    # replicate.run may return generator/iterator; collect URLs
    if isinstance(output, str):
        urls = [output]
    else:
        urls = list(output)
    url = urls[-1] if urls else None
    return {"status": "succeeded", "url": url, "all": urls}


async def generate_with_imagen(prompt: str, **params: Any) -> Dict[str, Any]:
    """Run Imagen generation without blocking the event loop."""
    return await asyncio.to_thread(_generate_with_imagen_sync, prompt, **params)


def generate_with_gemini(prompt: str, aspect_ratio: str = "1:1", **params: Any) -> Dict[str, Any]:
    """Use Google Gemini (Nano Banana) for image generation.
    
    Args:
        prompt: Text description for image generation
        aspect_ratio: Aspect ratio (1:1, 16:9, 3:2, etc.)
        **params: Additional parameters
    
    Returns:
        Dict with status, image data, and metadata
    """
    # Check for both GEMINI_API_KEY and GOOGLE_API_KEY (prefer GEMINI_API_KEY)
    api_key = get_env("GEMINI_API_KEY") or get_env("GOOGLE_API_KEY")
    if get_env("GEMINI_API_KEY") and get_env("GOOGLE_API_KEY"):
        print("Both GEMINI_API_KEY and GOOGLE_API_KEY are set. Using GEMINI_API_KEY.")
    if not api_key:
        return {"status": "skipped", "reason": "GEMINI_API_KEY or GOOGLE_API_KEY missing"}
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Configure aspect ratio if provided
        generation_config = None
        if aspect_ratio != "1:1":
            generation_config = genai.types.GenerationConfig(
                # Note: aspect_ratio is not directly supported in GenerationConfig
                # We'll use the prompt to specify aspect ratio instead
                temperature=0.7,
                top_p=0.8,
                top_k=40
            )
        
        # Add aspect ratio to prompt if specified
        enhanced_prompt = prompt
        if aspect_ratio != "1:1":
            enhanced_prompt = f"{prompt}\n\nAspect ratio: {aspect_ratio}"
        
        response = model.generate_content(
            contents=[enhanced_prompt],
            generation_config=generation_config
        )
        
        print(f"🔍 Gemini response: {response}")
        
        # Extract image data from response
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data is not None:
                        # Convert base64 to bytes
                        image_bytes = part.inline_data.data
                        print(f"✅ Gemini generated image data: {len(image_bytes)} bytes")
                        return {
                            "status": "succeeded",
                            "image_data": image_bytes,
                            "format": "png",
                            "aspect_ratio": aspect_ratio,
                            "model": "gemini-2.5-flash-image"
                        }
        
        print(f"❌ No image data found in Gemini response")
        return {"status": "failed", "reason": "No image data in response"}
        
    except Exception as e:
        return {"status": "failed", "reason": str(e)}


async def generate_with_gemini_async(prompt: str, aspect_ratio: str = "1:1", **params: Any) -> Dict[str, Any]:
    """Async wrapper for Gemini image generation."""
    return await asyncio.to_thread(generate_with_gemini, prompt, aspect_ratio, **params)


def generate_with_gemini_image_to_image(prompt: str, source_image_path: str, aspect_ratio: str = "1:1", **params: Any) -> Dict[str, Any]:
    """Use Google Gemini for image-to-image generation.
    
    Args:
        prompt: Text description for image modification
        source_image_path: Path to source image file
        aspect_ratio: Aspect ratio (1:1, 16:9, 3:2, etc.)
        **params: Additional parameters
    
    Returns:
        Dict with status, image data, and metadata
    """
    # Check for both GEMINI_API_KEY and GOOGLE_API_KEY (prefer GEMINI_API_KEY)
    api_key = get_env("GEMINI_API_KEY") or get_env("GOOGLE_API_KEY")
    if get_env("GEMINI_API_KEY") and get_env("GOOGLE_API_KEY"):
        print("Both GEMINI_API_KEY and GOOGLE_API_KEY are set. Using GEMINI_API_KEY.")
    if not api_key:
        return {"status": "skipped", "reason": "GEMINI_API_KEY or GOOGLE_API_KEY missing"}
    
    try:
        from pathlib import Path
        import base64
        
        source_path = Path(source_image_path)
        if not source_path.exists():
            return {"status": "failed", "reason": f"Source image not found: {source_image_path}"}
        
        # Read and encode the source image
        with open(source_path, "rb") as f:
            image_data = f.read()
        
        # Determine MIME type based on file extension
        mime_type = "image/jpeg"
        if source_path.suffix.lower() in ['.png']:
            mime_type = "image/png"
        elif source_path.suffix.lower() in ['.webp']:
            mime_type = "image/webp"
        elif source_path.suffix.lower() in ['.gif']:
            mime_type = "image/gif"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Create the content with both text and image
        # For Gemini, we need to use the proper Content structure
        contents = [
            {
                "text": prompt,
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_data
                }
            }
        ]
        
        response = model.generate_content(
            contents=contents
        )
        
        print(f"🔍 Gemini image-to-image response: {response}")
        
        # Extract image data from response
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data is not None:
                        # Convert base64 to bytes
                        image_bytes = part.inline_data.data
                        print(f"✅ Gemini generated image-to-image data: {len(image_bytes)} bytes")
                        return {
                            "status": "succeeded",
                            "image_data": image_bytes,
                            "format": "png",
                            "aspect_ratio": aspect_ratio,
                            "model": "gemini-2.5-flash-image",
                            "source_image": str(source_path)
                        }
        
        print(f"❌ No image data found in Gemini image-to-image response")
        return {"status": "failed", "reason": "No image data in response"}
        
    except Exception as e:
        return {"status": "failed", "reason": str(e)}


async def generate_with_gemini_image_to_image_async(prompt: str, source_image_path: str, aspect_ratio: str = "1:1", **params: Any) -> Dict[str, Any]:
    """Async wrapper for Gemini image-to-image generation."""
    return await asyncio.to_thread(generate_with_gemini_image_to_image, prompt, source_image_path, aspect_ratio, **params)
