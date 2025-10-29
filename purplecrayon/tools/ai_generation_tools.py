from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import replicate as replicate_sdk
from google import genai
from google.genai import types

from ..utils.config import get_env
from ..models.generation_models import model_manager, ModelConfig, ModelProvider


def _analyze_replicate_output(output) -> Dict[str, Any]:
    """Analyze Replicate output and determine how to parse it."""
    analysis = {
        "type": type(output).__name__,
        "is_iterable": hasattr(output, '__iter__') and not isinstance(output, str),
        "is_string": isinstance(output, str),
        "has_url": False,
        "has_image_data": False,
        "url": None,
        "image_data": None,
        "items_count": 0,
        "item_types": [],
        "recommended_action": "unknown"
    }
    
    print(f"🔍 Analyzing Replicate output: {analysis['type']}")
    
    if analysis["is_string"]:
        if output.startswith(('http://', 'https://')):
            analysis["has_url"] = True
            analysis["url"] = output
            analysis["recommended_action"] = "use_url"
            print(f"   → String URL detected: {output[:50]}...")
        else:
            analysis["recommended_action"] = "error"
            print(f"   → Non-URL string: {output[:50]}...")
    
    elif analysis["is_iterable"]:
        try:
            output_list = list(output)
            analysis["items_count"] = len(output_list)
            print(f"   → Iterable with {len(output_list)} items")
            
            # Analyze each item
            for i, item in enumerate(output_list):
                item_type = type(item).__name__
                analysis["item_types"].append(item_type)
                
                if isinstance(item, str) and item.startswith(('http://', 'https://')):
                    analysis["has_url"] = True
                    analysis["url"] = item
                    print(f"   → Item {i}: URL ({item[:50]}...)")
                elif isinstance(item, bytes) and len(item) > 100:
                    # Check if it looks like image data
                    if (item.startswith(b'RIFF') or item.startswith(b'\x89PNG') or 
                        item.startswith(b'\xff\xd8\xff') or item.startswith(b'GIF')):
                        analysis["has_image_data"] = True
                        analysis["image_data"] = item
                        print(f"   → Item {i}: Image data ({len(item)} bytes, {item[:4]})")
                    else:
                        print(f"   → Item {i}: Binary data ({len(item)} bytes, {item[:4]})")
                else:
                    print(f"   → Item {i}: {item_type} ({len(item) if hasattr(item, '__len__') else 'N/A'})")
            
            # Determine recommended action
            if analysis["has_url"]:
                analysis["recommended_action"] = "use_url"
            elif analysis["has_image_data"]:
                analysis["recommended_action"] = "use_image_data"
            else:
                analysis["recommended_action"] = "error"
                
        except Exception as e:
            print(f"   → Error analyzing iterable: {e}")
            analysis["recommended_action"] = "error"
    
    else:
        print(f"   → Unexpected type: {analysis['type']}")
        analysis["recommended_action"] = "error"
    
    return analysis


def _generate_with_replicate_sync(prompt: str, **params: Any) -> Dict[str, Any]:
    """Blocking Replicate call executed inside a worker thread."""
    token = get_env("REPLICATE_API_TOKEN")
    if not token:
        return {"status": "skipped", "reason": "REPLICATE_API_TOKEN missing"}
    replicate = replicate_sdk.Client(api_token=token)

    # Try primary model first, then fallback
    models_to_try = [
        params.pop("model", None) or "black-forest-labs/flux-1.1-pro",  # Primary: FLUX 1.1 Pro
        "stability-ai/stable-diffusion"  # Fallback: Classic Stable Diffusion
    ]
    
    for model in models_to_try:
        try:
            input_payload = {"prompt": prompt} | params
            print(f"🔄 Trying Replicate model: {model}")
            output = replicate.run(model, input=input_payload)
            
            # Analyze the output first
            analysis = _analyze_replicate_output(output)
            
            # Handle based on analysis
            if analysis["recommended_action"] == "use_url":
                print(f"✅ Model {model} succeeded, URL: {analysis['url'][:50]}...")
                return {
                    "status": "succeeded", 
                    "url": analysis["url"], 
                    "model": model,
                    "analysis": analysis
                }
            elif analysis["recommended_action"] == "use_image_data":
                print(f"✅ Model {model} succeeded, image data: {len(analysis['image_data'])} bytes")
                return {
                    "status": "succeeded", 
                    "image_data": analysis["image_data"], 
                    "model": model,
                    "analysis": analysis
                }
            else:
                print(f"⚠️ Model {model} analysis failed: {analysis['recommended_action']}")
                print(f"   Analysis: {analysis}")
                
        except Exception as e:
            print(f"⚠️ Model {model} failed: {str(e)}")
            continue
    
    return {"status": "failed", "reason": "All Replicate models failed"}


async def generate_with_replicate_async(prompt: str, **params: Any) -> Dict[str, Any]:
    """Run Replicate generation without blocking the event loop."""
    return await asyncio.to_thread(_generate_with_replicate_sync, prompt, **params)


def generate_with_gemini(prompt: str, aspect_ratio: str = "1:1", **params: Any) -> Dict[str, Any]:
    """Use Google Gemini for image generation.
    
    Args:
        prompt: Text description for image generation
        aspect_ratio: Aspect ratio (1:1, 16:9, 3:2, etc.)
        **params: Additional parameters
    
    Returns:
        Dict with status, image data, and metadata
    """
    # Check for GEMINI_API_KEY
    api_key = get_env("GEMINI_API_KEY")
    if not api_key:
        return {"status": "skipped", "reason": "GEMINI_API_KEY missing"}
    
    try:
        # Use the new Gemini API client
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
            config=config
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
    # Check for GEMINI_API_KEY
    api_key = get_env("GEMINI_API_KEY")
    if not api_key:
        return {"status": "skipped", "reason": "GEMINI_API_KEY missing"}
    
    try:
        from pathlib import Path
        import base64
        from PIL import Image
        from io import BytesIO
        
        source_path = Path(source_image_path)
        if not source_path.exists():
            return {"status": "failed", "reason": f"Source image not found: {source_image_path}"}
        
        # Use the new Gemini API client
        client = genai.Client(api_key=api_key)
        
        # Load the image using PIL
        image = Image.open(source_path)
        
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
            contents=[prompt, image],
            config=config
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


def generate_with_replicate(prompt: str, aspect_ratio: str = "1:1", **params: Any) -> Dict[str, Any]:
    """Use Replicate for image generation.
    
    Args:
        prompt: Text description for image generation
        aspect_ratio: Aspect ratio (1:1, 16:9, 3:2, etc.)
        **params: Additional parameters
    
    Returns:
        Dict with status, image data, and metadata
    """
    # Check for REPLICATE_API_TOKEN
    api_key = get_env("REPLICATE_API_TOKEN")
    if not api_key:
        return {"status": "skipped", "reason": "REPLICATE_API_TOKEN missing"}
    
    try:
        import requests
        import base64
        
        # Use the existing Replicate function
        result = _generate_with_replicate_sync(prompt, **params)
        
        if result.get("status") != "succeeded":
            return result
        
        # Check if we got binary data directly or need to download from URL
        if "image_data" in result:
            # Replicate returned binary data directly
            image_data = result["image_data"]
        elif "url" in result:
            # Download the image from the URL
            response = requests.get(result["url"])
            response.raise_for_status()
            image_data = response.content
        else:
            return {"status": "failed", "reason": "No image data or URL returned"}
        
        # Validate that we have image data
        if len(image_data) < 100:  # Too small to be a real image
            return {"status": "failed", "reason": f"Image data too small: {len(image_data)} bytes"}
        
        # Check if it's a valid image by looking for common image headers
        if not (image_data.startswith(b'\x89PNG') or image_data.startswith(b'\xff\xd8\xff') or image_data.startswith(b'GIF')):
            return {"status": "failed", "reason": f"Data doesn't appear to be a valid image"}
        
        return {
            "status": "succeeded",
            "image_data": image_data,
            "format": "png",  # Replicate typically returns PNG
            "aspect_ratio": aspect_ratio,
            "provider": "replicate",
            "model": result.get("model", "black-forest-labs/flux-1.1-pro"),
            "url": result["url"]
        }
        
    except Exception as e:
        return {"status": "failed", "reason": str(e)}


async def generate_with_replicate_async(prompt: str, aspect_ratio: str = "1:1", **params: Any) -> Dict[str, Any]:
    """Async wrapper for Replicate image generation."""
    return await asyncio.to_thread(generate_with_replicate, prompt, aspect_ratio, **params)


def generate_with_gemini_image_to_image(prompt: str, image_path: str, aspect_ratio: str = "1:1", **params: Any) -> Dict[str, Any]:
    """Generate image using Gemini image-to-image generation."""
    api_key = get_env("GEMINI_API_KEY")
    if not api_key:
        return {"status": "skipped", "reason": "GEMINI_API_KEY missing"}
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Load image
        from PIL import Image
        image = Image.open(image_path)
        
        # Generate with image-to-image
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, image]
        )
        
        if not response or not hasattr(response, 'candidates') or not response.candidates:
            return {"status": "failed", "reason": "Empty response from Gemini"}
        
        # Extract image data
        image_data = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        break
        
        if not image_data:
            return {"status": "failed", "reason": "No image data in Gemini response"}
        
        return {
            "status": "succeeded",
            "image_data": image_data,
            "provider": "gemini_image_to_image"
        }
        
    except Exception as e:
        return {"status": "failed", "reason": str(e)}


def generate_with_replicate_image_to_image(prompt: str, image_path: str, **params: Any) -> Dict[str, Any]:
    """Generate image using Replicate image-to-image generation."""
    token = get_env("REPLICATE_API_TOKEN")
    if not token:
        return {"status": "skipped", "reason": "REPLICATE_API_TOKEN missing"}
    
    try:
        import replicate
        client = replicate.Client(api_token=token)
        
        # Upload image
        with open(image_path, "rb") as f:
            uploaded_image = client.files.create(f)
        
        # Generate with image-to-image
        output = client.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "prompt": prompt,
                "image": uploaded_image.url,
                "strength": params.get("strength", 0.6),
                "num_inference_steps": params.get("num_inference_steps", 20),
                "guidance_scale": params.get("guidance_scale", 7.5)
            }
        )
        
        if not output:
            return {"status": "failed", "reason": "Empty response from Replicate"}
        
        # Handle different output formats
        if isinstance(output, str):
            return {"status": "succeeded", "url": output, "provider": "replicate_image_to_image"}
        else:
            # Handle FileOutput or other formats
            url = str(output) if hasattr(output, 'url') else str(output)
            return {"status": "succeeded", "url": url, "provider": "replicate_image_to_image"}
        
    except Exception as e:
        return {"status": "failed", "reason": str(e)}


def analyze_image_with_gemini_vision(image_path: str, prompt: str = "Analyze this image and provide a detailed description") -> Dict[str, Any]:
    """Analyze image using Gemini vision model."""
    api_key = get_env("GEMINI_API_KEY")
    if not api_key:
        return {"status": "skipped", "reason": "GEMINI_API_KEY missing"}
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Load image
        from PIL import Image
        image = Image.open(image_path)
        
        # Analyze with vision model
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[prompt, image]
        )
        
        if not response or not hasattr(response, 'candidates') or not response.candidates:
            return {"status": "failed", "reason": "Empty response from Gemini"}
        
        # Extract text description
        description = ""
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        description += part.text
        
        if not description:
            return {"status": "failed", "reason": "No text description in Gemini response"}
        
        return {
            "status": "succeeded",
            "description": description,
            "provider": "gemini_vision"
        }
        
    except Exception as e:
        return {"status": "failed", "reason": str(e)}


# Unified Generation API
def generate_with_models(prompt: str, 
                        aspect_ratio: str = "1:1",
                        model_type: str = "text_to_image",
                        with_models: Optional[List[str]] = None,
                        exclude_models: Optional[List[str]] = None,
                        all_models: bool = False,
                        **params: Any) -> Dict[str, Any]:
    """Generate images using specified models with unified API.
    
    Args:
        prompt: Text description for image generation
        aspect_ratio: Aspect ratio (1:1, 16:9, 3:2, etc.)
        model_type: Type of generation (text_to_image, image_to_image, image_to_text)
        with_models: Specific models to use (if None, use fallback order)
        exclude_models: Models to exclude from generation
        all_models: If True, generate with all available models
        **params: Additional parameters for generation
        
    Returns:
        Dict with results from all attempted models
    """
    # Get available models based on criteria and model type
    if all_models:
        available_models = model_manager.get_available_models(model_type=model_type, exclude_models=exclude_models)
    elif with_models:
        available_models = model_manager.get_available_models(model_type=model_type, with_models=with_models, exclude_models=exclude_models)
    else:
        available_models = model_manager.get_fallback_models(model_type=model_type, exclude_models=exclude_models)
    
    if not available_models:
        return {
            "status": "failed",
            "reason": "No available models found",
            "results": {}
        }
    
    results = {}
    successful_generations = 0
    
    for model_config in available_models:
        try:
            print(f"🎨 Generating with {model_config.display_name} ({model_type})...")
            
            if model_config.provider == ModelProvider.GEMINI:
                if model_type == "text_to_image":
                    result = generate_with_gemini(prompt, aspect_ratio, **params)
                elif model_type == "image_to_image":
                    if "image_path" not in params:
                        result = {"status": "failed", "reason": "image_path required for image_to_image"}
                    else:
                        result = generate_with_gemini_image_to_image(prompt, params["image_path"], aspect_ratio, **params)
                elif model_type == "image_to_text":
                    if "image_path" not in params:
                        result = {"status": "failed", "reason": "image_path required for image_to_text"}
                    else:
                        result = analyze_image_with_gemini_vision(params["image_path"], prompt)
                else:
                    result = {"status": "skipped", "reason": f"Unsupported model type for Gemini: {model_type}"}
            elif model_config.provider == ModelProvider.REPLICATE:
                if model_type == "text_to_image":
                    result = generate_with_replicate(prompt, aspect_ratio, **params)
                elif model_type == "image_to_image":
                    if "image_path" not in params:
                        result = {"status": "failed", "reason": "image_path required for image_to_image"}
                    else:
                        result = generate_with_replicate_image_to_image(prompt, params["image_path"], **params)
                else:
                    result = {"status": "skipped", "reason": f"Unsupported model type for Replicate: {model_type}"}
            else:
                result = {"status": "skipped", "reason": f"Unknown provider: {model_config.provider}"}
            
            results[model_config.name] = {
                "model": model_config.display_name,
                "provider": model_config.provider.value,
                "result": result
            }
            
            if result.get("status") == "succeeded":
                successful_generations += 1
                print(f"✅ {model_config.display_name} succeeded")
            else:
                print(f"❌ {model_config.display_name} failed: {result.get('reason', 'Unknown error')}")
                
        except Exception as e:
            results[model_config.name] = {
                "model": model_config.display_name,
                "provider": model_config.provider.value,
                "result": {"status": "failed", "reason": str(e)}
            }
            print(f"❌ {model_config.display_name} error: {e}")
    
    return {
        "status": "succeeded" if successful_generations > 0 else "failed",
        "successful_generations": successful_generations,
        "total_attempts": len(available_models),
        "results": results
    }


async def generate_with_models_async(prompt: str, 
                                   aspect_ratio: str = "1:1",
                                   model_type: str = "text_to_image",
                                   with_models: Optional[List[str]] = None,
                                   exclude_models: Optional[List[str]] = None,
                                   all_models: bool = False,
                                   **params: Any) -> Dict[str, Any]:
    """Async wrapper for generate_with_models."""
    return await asyncio.to_thread(
        generate_with_models, 
        prompt, 
        aspect_ratio, 
        model_type,
        with_models, 
        exclude_models, 
        all_models, 
        **params
    )


def list_available_models() -> Dict[str, Any]:
    """List all available generation models.
    
    Returns:
        Dictionary with model information
    """
    return model_manager.get_model_info()


def check_model_updates(force: bool = False) -> bool:
    """Check for model configuration updates.
    
    Args:
        force: If True, check for updates even if recently checked
        
    Returns:
        True if updates were found and applied
    """
    return model_manager.check_for_updates(force=force)
