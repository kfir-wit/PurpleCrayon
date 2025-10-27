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
    Tries multiple extensions if the original fails.
    Returns validation result with status and details.
    """
    file_path_obj = Path(file_path)
    original_extension = file_path_obj.suffix.lower()
    
    # Define possible extensions to try
    possible_extensions = [original_extension]
    
    # If it's a .jpg file, also try .svg, .png, .gif, .webp
    if original_extension in ['.jpg', '.jpeg']:
        possible_extensions.extend(['.svg', '.png', '.gif', '.webp'])
    # If it's a .png file, also try .jpg, .svg, .gif, .webp
    elif original_extension == '.png':
        possible_extensions.extend(['.jpg', '.svg', '.gif', '.webp'])
    # If it's a .gif file, also try .jpg, .png, .svg, .webp
    elif original_extension == '.gif':
        possible_extensions.extend(['.jpg', '.png', '.svg', '.webp'])
    # If it's a .webp file, also try .jpg, .png, .gif, .svg
    elif original_extension == '.webp':
        possible_extensions.extend(['.jpg', '.png', '.gif', '.svg'])
    
    # Remove duplicates while preserving order
    possible_extensions = list(dict.fromkeys(possible_extensions))
    
    last_error = None
    
    for ext in possible_extensions:
        # For testing different extensions, we need to copy the file temporarily
        if ext != original_extension:
            import shutil
            test_path = file_path_obj.with_suffix(ext)
            try:
                shutil.copy2(file_path_obj, test_path)
            except Exception as e:
                last_error = f"Could not create test copy with {ext}: {str(e)}"
                continue
        else:
            test_path = file_path_obj
        
        try:
            # Try to open and verify the image
            with Image.open(test_path) as img:
                # Force loading the image data to check for corruption
                img.verify()
                
                # Try to get basic info
                width, height = img.size
                format_type = img.format
                
                # Check if image has reasonable dimensions
                if width <= 0 or height <= 0:
                    last_error = f"Invalid dimensions: {width}x{height}"
                    continue
                
                # Check if image is too small (likely corrupted or placeholder)
                if width < 10 or height < 10:
                    last_error = f"Image too small (likely corrupted): {width}x{height}"
                    continue
                
                # Check if the detected format matches the extension
                format_matches_extension = False
                if ext == '.jpg' or ext == '.jpeg':
                    format_matches_extension = format_type in ['JPEG', 'JPG']
                elif ext == '.png':
                    format_matches_extension = format_type == 'PNG'
                elif ext == '.gif':
                    format_matches_extension = format_type == 'GIF'
                elif ext == '.webp':
                    format_matches_extension = format_type == 'WEBP'
                elif ext == '.bmp':
                    format_matches_extension = format_type == 'BMP'
                elif ext == '.tiff':
                    format_matches_extension = format_type in ['TIFF', 'TIF']
                elif ext == '.ico':
                    format_matches_extension = format_type == 'ICO'
                elif ext == '.svg':
                    format_matches_extension = format_type == 'SVG'
                
                # If format doesn't match extension, try the next extension
                if not format_matches_extension:
                    last_error = f"Format {format_type} doesn't match extension {ext}"
                    continue
                
                # If we get here, the image is valid and format matches extension
                result = {
                    "valid": True,
                    "width": width,
                    "height": height,
                    "format": format_type,
                    "size_bytes": test_path.stat().st_size,
                    "corrected_extension": ext != original_extension,
                    "original_extension": original_extension,
                    "working_extension": ext
                }
                
                # If we found a working extension different from the original, rename the file
                if ext != original_extension:
                    try:
                        # Remove the original file and rename the test file to the original name with correct extension
                        original_name = file_path_obj.stem
                        new_path = file_path_obj.parent / f"{original_name}{ext}"
                        file_path_obj.unlink()
                        test_path.rename(new_path)
                        result["file_renamed"] = True
                        result["new_filename"] = new_path.name
                        result["new_path"] = str(new_path)
                    except Exception as rename_error:
                        result["file_renamed"] = False
                        result["rename_error"] = str(rename_error)
                        # Clean up test file
                        try:
                            test_path.unlink()
                        except:
                            pass
                else:
                    # Clean up any test files we created
                    if ext != original_extension:
                        try:
                            test_path.unlink()
                        except:
                            pass
                
                return result
                
        except Exception as e:
            last_error = f"Failed with {ext}: {str(e)}"
            # Clean up test file if we created one
            if ext != original_extension and test_path.exists():
                try:
                    test_path.unlink()
                except:
                    pass
            continue
    
    # If we get here, none of the extensions worked
    return {
        "valid": False,
        "error": f"Corrupted image (tried {len(possible_extensions)} extensions): {last_error}",
        "width": 0,
        "height": 0,
        "format": "unknown",
        "tried_extensions": possible_extensions
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


def is_junk_image(file_path: Path, validation_result: Dict[str, Any]) -> bool:
    """
    Determine if an image is junk based on various criteria.
    """
    filename = file_path.name.lower()
    size_bytes = file_path.stat().st_size
    
    # Check for tracking pixels and analytics
    if any(pattern in filename for pattern in ['pixel', 'tracking', 'analytics', 'g.gif', 'beacon']):
        return True
    
    # Check for very small files (likely tracking pixels)
    if size_bytes < 100:  # Less than 100 bytes
        return True
    
    # Check for 1x1 pixel images (tracking pixels)
    if (validation_result.get("width") == 1 and validation_result.get("height") == 1):
        return True
    
    # Check for extremely small dimensions
    if (validation_result.get("width", 0) < 5 or validation_result.get("height", 0) < 5):
        return True
    
    # Check for common junk file patterns
    if any(pattern in filename for pattern in ['spacer', 'blank', 'transparent', 'clear']):
        return True
    
    return False


def cleanup_corrupted_images(directory: str, remove_junk: bool = True) -> Dict[str, int]:
    """
    Clean up corrupted images and optionally junk files in a directory.
    Returns statistics about cleaned files.
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        return {"valid": 0, "corrupted": 0, "junk": 0, "errors": 0}
    
    valid_count = 0
    corrupted_count = 0
    junk_count = 0
    error_count = 0
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg'}
    
    print(f"🔍 Validating images in {directory}...")
    if remove_junk:
        print("🧹 Junk file removal enabled")
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            print(f"  Checking: {file_path.name}")
            
            # Validate the image
            validation_result = validate_image_file(str(file_path))
            
            if not validation_result["valid"]:
                print(f"    ❌ Corrupted: {validation_result['error']}")
                try:
                    file_path.unlink()
                    print(f"    🗑️ Removed corrupted: {file_path.name}")
                    corrupted_count += 1
                except Exception as e:
                    print(f"    ⚠️ Could not remove {file_path.name}: {e}")
                    error_count += 1
            elif remove_junk and is_junk_image(file_path, validation_result):
                print(f"    🗑️ Junk file: {file_path.name} ({validation_result.get('width', 0)}x{validation_result.get('height', 0)})")
                try:
                    file_path.unlink()
                    print(f"    🗑️ Removed junk: {file_path.name}")
                    junk_count += 1
                except Exception as e:
                    print(f"    ⚠️ Could not remove {file_path.name}: {e}")
                    error_count += 1
            else:
                # Check if extension was corrected
                if validation_result.get("corrected_extension", False):
                    print(f"    ✅ Valid: {validation_result['width']}x{validation_result['height']} {validation_result['format']} (corrected from {validation_result['original_extension']} to {validation_result['working_extension']})")
                    if validation_result.get("file_renamed", False):
                        print(f"    📝 Renamed: {validation_result['new_filename']}")
                    elif not validation_result.get("file_renamed", True):  # False means rename failed
                        print(f"    ⚠️ Could not rename file: {validation_result.get('rename_error', 'Unknown error')}")
                else:
                    print(f"    ✅ Valid: {validation_result['width']}x{validation_result['height']} {validation_result['format']}")
                valid_count += 1
    
    return {
        "valid": valid_count,
        "corrupted": corrupted_count,
        "junk": junk_count,
        "errors": error_count
    }