from __future__ import annotations

import base64
import re
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from PIL import Image
import io
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()


def validate_image_file(file_path: str) -> Dict[str, Any]:
    """
    Validate if an image file is not corrupted.
    Returns validation result with status and details.
    """
    try:
        # Try to open and verify the image
        with Image.open(file_path) as img:
            # Force loading the image data to check for corruption
            img.verify()
            
            # Try to get basic info
            width, height = img.size
            format_type = img.format
            
            # Check if image has reasonable dimensions
            if width <= 0 or height <= 0:
                return {
                    "valid": False,
                    "error": "Invalid dimensions",
                    "width": width,
                    "height": height,
                    "format": format_type
                }
            
            # Check if image is too small (likely corrupted or placeholder)
            if width < 10 or height < 10:
                return {
                    "valid": False,
                    "error": "Image too small (likely corrupted)",
                    "width": width,
                    "height": height,
                    "format": format_type
                }
            
            return {
                "valid": True,
                "width": width,
                "height": height,
                "format": format_type,
                "size_bytes": Path(file_path).stat().st_size
            }
            
    except Exception as e:
        return {
            "valid": False,
            "error": f"Corrupted image: {str(e)}",
            "width": 0,
            "height": 0,
            "format": "unknown"
        }


def validate_image_with_llm(image_path: str, description: str) -> Dict[str, Any]:
    """
    Use LLM to validate if downloaded image matches the description.
    Returns confidence score and what the image actually shows.
    """
    try:
        # Load and encode image
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Check if image is valid before encoding
        try:
            Image.open(io.BytesIO(image_bytes)).verify()
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid image file: {e}",
                "description": "Could not analyze image",
                "match_score": 0.0,
                "reasoning": f"Error: Invalid image file: {e}",
                "confidence": "none"
            }

        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        prompt = f"""
        You are an expert image analysis AI. Your task is to evaluate if an image matches a given description.
        Provide a brief description of what the image shows.
        Then, provide a match score (0.0-1.0) indicating how well the image matches the following description:
        "{description}"

        Also, provide a confidence level (low, medium, high) for your match score.
        Finally, provide a brief reasoning for your score and confidence.

        Output format:
        DESCRIPTION: [brief description of image content]
        MATCH_SCORE: [0.0-1.0]
        CONFIDENCE: [low/medium/high]
        REASONING: [brief explanation]
        """
        
        # Use vision model for image analysis
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
        )
        
        response = llm.invoke([message])
        content = response.content
        
        # Parse the output
        desc_match = re.search(r"DESCRIPTION: (.*)", content)
        score_match = re.search(r"MATCH_SCORE: ([\d.]+)", content)
        confidence_match = re.search(r"CONFIDENCE: (.*)", content)
        reasoning_match = re.search(r"REASONING: (.*)", content)

        return {
            "valid": True,
            "description": desc_match.group(1).strip() if desc_match else "N/A",
            "match_score": float(score_match.group(1)) if score_match else 0.0,
            "confidence": confidence_match.group(1).strip() if confidence_match else "none",
            "reasoning": reasoning_match.group(1).strip() if reasoning_match else "N/A",
        }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "description": "Could not analyze image",
            "match_score": 0.0,
            "reasoning": f"Error: {e}",
            "confidence": "none"
        }


def validate_all_images(image_paths: List[str], description: str) -> List[Dict[str, Any]]:
    """Validates a list of image paths using the LLM."""
    results = []
    for path in image_paths:
        result = validate_image_with_llm(path, description)
        result["path"] = path # Add path to result for easier debugging
        results.append(result)
    
    # Sort by match_score for better presentation
    results.sort(key=lambda x: x.get("match_score", 0.0), reverse=True)
    return results


def cleanup_corrupted_images(directory: str) -> Dict[str, int]:
    """
    Clean up corrupted images in a directory.
    Returns statistics about cleaned files.
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        return {"valid": 0, "corrupted": 0, "errors": 0}
    
    valid_count = 0
    corrupted_count = 0
    error_count = 0
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico'}
    
    print(f"🔍 Validating images in {directory}...")
    
    for file_path in directory_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            print(f"  Checking: {file_path.name}")
            
            # Validate the image
            validation_result = validate_image_file(str(file_path))
            
            if validation_result["valid"]:
                print(f"    ✅ Valid: {validation_result['width']}x{validation_result['height']} {validation_result['format']}")
                valid_count += 1
            else:
                print(f"    ❌ Corrupted: {validation_result['error']}")
                try:
                    file_path.unlink()
                    print(f"    🗑️ Removed: {file_path.name}")
                    corrupted_count += 1
                except Exception as e:
                    print(f"    ⚠️ Could not remove {file_path.name}: {e}")
                    error_count += 1
    
    return {
        "valid": valid_count,
        "corrupted": corrupted_count,
        "errors": error_count
    }