from __future__ import annotations

import asyncio
from typing import Any, Dict

import replicate as replicate_sdk
from google import genai
from google.genai import types

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
        client = genai.Client(api_key=api_key)
        
        # Configure aspect ratio if provided
        config = None
        if aspect_ratio != "1:1":
            config = types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                )
            )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
            config=config,
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
