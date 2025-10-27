# Augment API Documentation

## Overview

The Augment API provides functionality to modify existing images using AI image-to-image generation. Unlike the Clone API which creates new images based on descriptions, the Augment API uploads actual image files to AI engines and applies modifications based on natural language prompts.

## Core Concepts

### Image-to-Image Generation
- **Upload Process**: Source images are uploaded to AI engines (Gemini or Replicate)
- **Modification Prompts**: Natural language instructions for changes
- **Style Preservation**: Maintains original composition while applying modifications
- **Output Control**: Specify dimensions, format, and output location

### Supported Engines
1. **Google Gemini 2.0 Flash** (Primary)
   - Direct image upload via API
   - High-quality image-to-image generation
   - Supports various aspect ratios
   
2. **Replicate Stable Diffusion** (Fallback)
   - File upload to Replicate servers
   - img2img with strength control
   - Robust fallback option

## API Reference

### Core Functions

#### `augment_image()`
```python
async def augment_image(
    image_path: Union[str, Path],
    prompt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    output_format: str = "png",
    output_dir: Optional[Union[str, Path]] = None,
    **kwargs
) -> OperationResult
```

**Parameters:**
- `image_path`: Path to the source image file
- `prompt`: Modification instructions in natural language
- `width`: Optional output width (defaults to original or 1024)
- `height`: Optional output height (defaults to original or 1024)
- `output_format`: Output image format (png, jpg, webp, etc.)
- `output_dir`: Custom output directory (defaults to assets/ai/)

**Returns:**
- `OperationResult` with success status and augmented image data

#### `augment_images_from_directory()`
```python
async def augment_images_from_directory(
    directory_path: Union[str, Path],
    prompt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    output_format: str = "png",
    output_dir: Optional[Union[str, Path]] = None,
    max_images: Optional[int] = None,
    **kwargs
) -> OperationResult
```

**Parameters:**
- `directory_path`: Path to directory containing images
- `prompt`: Modification instructions for all images
- `width`: Optional output width
- `height`: Optional output height
- `output_format`: Output image format
- `output_dir`: Custom output directory
- `max_images`: Maximum number of images to process

**Returns:**
- `OperationResult` with batch processing results

### PurpleCrayon Class Methods

#### `augment_async()`
```python
async def augment_async(
    self,
    image_path: str | Path,
    prompt: str,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    format: Optional[str] = None,
    output_dir: Optional[str | Path] = None,
    **kwargs
) -> OperationResult
```

**Parameters:**
- `image_path`: Path to the source image
- `prompt`: Modification instructions
- `width`: Optional output width
- `height`: Optional output height
- `format`: Output format (if None, uses original format)
- `output_dir`: Optional custom output directory
- `**kwargs`: Additional parameters

**Returns:**
- `OperationResult` containing the augmented image

#### `augment()`
```python
def augment(
    self,
    image_path: str | Path,
    prompt: str,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    format: Optional[str] = None,
    output_dir: Optional[str | Path] = None,
    **kwargs
) -> OperationResult
```

Synchronous wrapper around `augment_async()`.

## Usage Examples

### Basic Image Augmentation

```python
from purplecrayon import PurpleCrayon

# Initialize client
crayon = PurpleCrayon(assets_dir="./assets")

# Augment a single image
result = await crayon.augment_async(
    image_path="./assets/ai/portrait.jpg",
    prompt="add a professional studio lighting setup",
    width=1920,
    height=1080,
    format="png"
)

if result.success:
    print(f"Augmented image saved to: {result.images[0].path}")
else:
    print(f"Augmentation failed: {result.message}")
```

### Batch Augmentation

```python
# Augment multiple images from a directory
result = await crayon.augment_async(
    image_path="./assets/downloaded/",
    prompt="convert to watercolor painting style",
    width=1024,
    height=1024,
    format="png"
)

print(f"Successfully augmented {len(result.images)} images")
```

### Direct Tool Usage

```python
from purplecrayon import augment_image

# Use the tool directly
result = await augment_image(
    image_path="./my_image.jpg",
    prompt="add a sunset background with warm colors",
    width=1920,
    height=1080,
    output_format="png",
    output_dir="./output"
)
```

### Synchronous Usage

```python
# Synchronous wrapper (for non-async contexts)
result = crayon.augment(
    image_path="./assets/ai/image.jpg",
    prompt="add dramatic evening lighting",
    width=1280,
    height=720
)
```

## CLI Usage

### Basic Augmentation
```bash
# Augment a single image
uv run python -m main --mode augment \
  --input "./assets/ai/portrait.jpg" \
  --augment "add professional studio lighting"

# With custom dimensions and format
uv run python -m main --mode augment \
  --input "./assets/ai/image.jpg" \
  --augment "convert to watercolor style" \
  --width 1920 --height 1080 --format png

# With custom output directory
uv run python -m main --mode augment \
  --input "./assets/ai/image.jpg" \
  --augment "add magical forest background" \
  --output "./custom_output"
```

### Required Arguments
- `--input`: Path to source image file (required)
- `--augment`: Modification prompt (required)

### Optional Arguments
- `--width`: Output width
- `--height`: Output height
- `--format`: Output format (png, jpg, webp, etc.)
- `--output`: Custom output directory

## Output Organization

### File Naming
- **Pattern**: `augmented_{original_name}.{format}`
- **Example**: `augmented_portrait_1920x1080.png`

### Directory Structure
```
assets/
├── ai/                    # Default output directory
│   ├── augmented_image1.png
│   ├── augmented_image2.jpg
│   └── ...
└── custom_output/         # Custom output directory
    └── augmented_image3.png
```

### Catalog Integration
- **Source**: `"ai"`
- **Provider**: `"gemini"` or `"replicate"`
- **Description**: `"Augmented: {prompt}"`
- **Metadata**: Includes original image path, modification prompt, and engine used

## Error Handling

### Common Errors

#### File Not Found
```python
# Error: Image not found
result = await crayon.augment_async(
    image_path="./nonexistent.jpg",
    prompt="add lighting"
)
# Returns: OperationResult(success=False, message="Image not found: ./nonexistent.jpg")
```

#### Empty Prompt
```python
# Error: Empty modification prompt
result = await crayon.augment_async(
    image_path="./image.jpg",
    prompt=""
)
# Returns: OperationResult(success=False, message="Modification prompt cannot be empty")
```

#### API Key Missing
```python
# Error: No API keys available
result = await crayon.augment_async(
    image_path="./image.jpg",
    prompt="add background"
)
# Returns: OperationResult(success=False, message="All augmentation engines failed")
```

### Engine Fallback
The system automatically tries engines in order:
1. **Gemini** (primary)
2. **Replicate** (fallback)

If both fail, returns detailed error information.

## Performance Considerations

### Image Upload
- **Gemini**: Inline blob upload (faster for small images)
- **Replicate**: File upload to servers (better for large images)
- **Timeout**: 30 seconds per engine attempt

### Batch Processing
- **Concurrent**: Images processed sequentially to avoid rate limits
- **Memory**: Each image loaded individually to manage memory usage
- **Progress**: Detailed logging for batch operations

### Rate Limits
- **Gemini**: Respects API rate limits
- **Replicate**: Handles queue-based processing
- **Retry**: Automatic retry with exponential backoff

## Configuration

### Environment Variables
```bash
# Required for Gemini
GEMINI_API_KEY=your_gemini_api_key

# Required for Replicate (fallback)
REPLICATE_API_TOKEN=your_replicate_token
```

### Engine Selection
The system automatically selects the best available engine:
1. Try Gemini if `GEMINI_API_KEY` is set
2. Fall back to Replicate if Gemini fails
3. Return error if both engines fail

## Troubleshooting

### Common Issues

#### "All augmentation engines failed"
- **Cause**: Missing API keys or API errors
- **Solution**: Check API keys in `.env` file
- **Debug**: Enable verbose logging to see specific errors

#### "Empty response from Gemini"
- **Cause**: Gemini API returned no content
- **Solution**: Try different prompt or check image format
- **Debug**: Check Gemini API status and quotas

#### "Invalid version or not permitted" (Replicate)
- **Cause**: Replicate model version issue
- **Solution**: Update to latest model version
- **Debug**: Check Replicate model availability

### Debug Mode
Enable verbose logging to see detailed process information:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Best Practices

### Prompt Writing
- **Be Specific**: "add professional studio lighting with soft key light"
- **Include Style**: "convert to watercolor painting style"
- **Mention Colors**: "add warm orange and pink sunset colors"
- **Preserve Elements**: "maintain the original composition while adding..."

### Image Quality
- **High Resolution**: Use high-quality source images
- **Good Composition**: Well-composed images work better
- **Clear Subjects**: Images with clear subjects respond better to modifications

### Performance Optimization
- **Batch Processing**: Process multiple images with same prompt
- **Format Selection**: Use PNG for quality, JPG for size
- **Dimension Planning**: Specify target dimensions upfront

### Error Handling
- **Check Results**: Always verify `result.success`
- **Handle Failures**: Implement fallback strategies
- **Log Errors**: Use proper logging for debugging

## Advanced Usage

### Custom Output Directories
```python
# Save to custom location
result = await crayon.augment_async(
    image_path="./source.jpg",
    prompt="add background",
    output_dir="./custom_output"
)
```

### Batch Processing with Limits
```python
# Process limited number of images
result = await augment_images_from_directory(
    directory_path="./images/",
    prompt="convert to oil painting style",
    max_images=5
)
```

### Engine-Specific Parameters
```python
# Pass additional parameters to engines
result = await crayon.augment_async(
    image_path="./image.jpg",
    prompt="add lighting",
    strength=0.7,  # For Replicate
    guidance_scale=7.5  # For Replicate
)
```

## Integration Examples

### With Asset Management
```python
# Augment and add to catalog
result = await crayon.augment_async(
    image_path="./assets/ai/portrait.jpg",
    prompt="add professional lighting"
)

if result.success:
    # Update catalog
    crayon.catalog.update_catalog_from_assets(crayon.assets_dir)
    print("Image augmented and added to catalog")
```

### With Image Validation
```python
# Augment and validate result
result = await crayon.augment_async(
    image_path="./image.jpg",
    prompt="add background"
)

if result.success:
    # Validate the augmented image
    from purplecrayon import validate_image_file
    validation = validate_image_file(result.images[0].path)
    print(f"Augmented image validation: {validation}")
```

This comprehensive API documentation covers all aspects of the Augment functionality, providing users with detailed information on how to effectively use image augmentation in their projects.
