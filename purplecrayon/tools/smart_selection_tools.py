from __future__ import annotations

from typing import List, Dict, Any, Tuple


def select_best_images(
    images: List[Dict[str, Any]], 
    target_width: int, 
    target_height: int,
    max_images: int = 3
) -> List[Dict[str, Any]]:
    """
    Smart image selection based on size, aspect ratio, and quality.
    Prioritizes: exact size -> aspect ratio match -> orientation match
    """
    if not images:
        return []
    
    target_aspect = target_width / target_height
    target_orientation = "landscape" if target_width > target_height else "portrait"
    
    def score_image(img: Dict[str, Any]) -> Tuple[int, float]:
        """Score image based on how well it matches requirements"""
        width = img.get("width", 0)
        height = img.get("height", 0)
        aspect_ratio = img.get("aspect_ratio", 1)
        
        if not width or not height:
            return 0, 0
        
        # Score 1: Exact size match (highest priority)
        if width == target_width and height == target_height:
            return 100, aspect_ratio
        
        # Score 2: Size within 20% tolerance
        width_ratio = min(width, target_width) / max(width, target_width)
        height_ratio = min(height, target_height) / max(height, target_height)
        size_score = (width_ratio + height_ratio) / 2
        
        if size_score >= 0.8:  # Within 20%
            return 80, aspect_ratio
        
        # Score 3: Aspect ratio match
        aspect_diff = abs(aspect_ratio - target_aspect)
        if aspect_diff <= 0.1:  # Very close aspect ratio
            return 60, aspect_ratio
        
        # Score 4: Orientation match
        img_orientation = "landscape" if width > height else "portrait"
        if img_orientation == target_orientation:
            return 40, aspect_ratio
        
        # Score 5: Any image
        return 20, aspect_ratio
    
    # Score and sort images
    scored_images = []
    for img in images:
        score, aspect = score_image(img)
        scored_images.append((score, aspect, img))
    
    # Sort by score (descending) then by aspect ratio closeness
    scored_images.sort(key=lambda x: (-x[0], abs(x[1] - target_aspect)))
    
    # Return top images
    return [img for _, _, img in scored_images[:max_images]]


def extract_size_from_prompt(prompt: str) -> Tuple[int, int]:
    """Extract target dimensions from prompt text"""
    import re
    
    # Look for explicit dimensions like "1920x1080", "1024x1024"
    size_match = re.search(r'(\d+)\s*[x×]\s*(\d+)', prompt)
    if size_match:
        return int(size_match.group(1)), int(size_match.group(2))
    
    # Look for common size keywords
    if "wallpaper" in prompt.lower() or "background" in prompt.lower():
        return 1920, 1080  # Common wallpaper size
    
    if "square" in prompt.lower():
        return 1024, 1024
    
    if "portrait" in prompt.lower():
        return 1080, 1920
    
    # Default to 1024x1024
    return 1024, 1024