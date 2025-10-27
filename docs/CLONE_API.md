# PurpleCrayon Clone API Documentation

## Overview

The Clone API allows you to create royalty-free alternatives to existing images by analyzing them with AI vision and generating new images based on detailed descriptions. This feature helps avoid copyright issues while maintaining visual intent.

## Core Concepts

### Image Cloning Process
1. **Vision Analysis**: Uses Gemini Vision API to analyze the source image
2. **Style Detection**: Automatically detects and inherits the original image's style
3. **Description Generation**: Creates detailed prompts for AI image generation
4. **AI Generation**: Generates new images using Gemini 2.5 Flash Image or Replicate
5. **Similarity Checking**: Ensures cloned images are sufficiently different from originals
6. **File Management**: Saves cloned images to `assets/cloned/` directory

### Key Features
- **Style Inheritance**: Automatically detects and preserves original image style
- **Similarity Control**: Configurable similarity thresholds to prevent literal copies
- **Batch Processing**: Clone multiple images from a directory
- **Fallback Generation**: Multiple AI engines for reliability
- **Catalog Integration**: Cloned files categorized as "ai" source

## API Reference

### PurpleCrayon Class Methods

#### `clone_async(source, **kwargs)`
Asynchronously clone an image or directory of images.

**Parameters:**
- `source` (str | Path): Path to source image file or directory
- `width` (int, optional): Desired width for cloned images
- `height` (int, optional): Desired height for cloned images
- `format` (str, optional): Output format (png, jpg, webp, etc.)
- `style` (str, optional): Style guidance (photorealistic, artistic, watercolor, etc.)
- `guidance` (str, optional): Additional guidance for image generation
- `similarity_threshold` (float, optional): Maximum similarity threshold (0.0-1.0, default 0.7)
- `max_images` (int, optional): Maximum number of images to process (for directory input)

**Returns:**
- `OperationResult`: Contains success status, message, and list of `ImageResult` objects

**Example:**
```python
from purplecrayon import PurpleCrayon

crayon = PurpleCrayon()

# Clone single image
result = await crayon.clone_async(
    source="./assets/downloaded/image.jpg",
    width=1024,
    height=1024,
    style="photorealistic"
)

# Batch clone directory
result = await crayon.clone_async(
    source="./assets/downloaded/",
    max_images=5,
    similarity_threshold=0.7
)
```

#### `clone(source, **kwargs)`
Synchronous wrapper for `clone_async()`.

**Parameters:** Same as `clone_async()`

**Returns:** Same as `clone_async()`

**Example:**
```python
# Synchronous usage
result = crayon.clone(
    source="./assets/downloaded/image.jpg",
    width=512,
    height=512
)
```

### Direct Tool Functions

#### `clone_image(image_path, **kwargs)`
Clone a single image using the complex image-to-image approach.

**Parameters:**
- `image_path` (str | Path): Path to source image
- `width` (int, optional): Desired width
- `height` (int, optional): Desired height
- `format` (str, optional): Output format
- `style` (str, optional): Style guidance
- `guidance` (str, optional): Additional guidance
- `similarity_threshold` (float, optional): Similarity threshold
- `output_dir` (Path, optional): Output directory

**Returns:**
- `dict`: Result dictionary with success status and metadata

#### `clone_images_from_directory(directory_path, **kwargs)`
Clone all images from a directory.

**Parameters:**
- `directory_path` (str | Path): Path to source directory
- `output_dir` (Path, optional): Output directory
- `width` (int, optional): Desired width
- `height` (int, optional): Desired height
- `format` (str, optional): Output format
- `style` (str, optional): Style guidance
- `guidance` (str, optional): Additional guidance
- `similarity_threshold` (float, optional): Similarity threshold
- `max_images` (int, optional): Maximum number of images to process

**Returns:**
- `dict`: Result dictionary with success status and list of results

#### `describe_image_for_regeneration(image_path, **kwargs)`
Analyze an image and generate a detailed description for regeneration.

**Parameters:**
- `image_path` (str | Path): Path to source image
- `extra_meta` (dict, optional): Additional metadata

**Returns:**
- `dict`: Analysis result with description and metadata

#### `check_similarity(original_path, clone_path)`
Check similarity between original and clone images.

**Parameters:**
- `original_path` (Path): Path to original image
- `clone_path` (Path): Path to clone image

**Returns:**
- `float`: Similarity score (0.0 to 1.0)

#### `is_sufficiently_different(original_path, clone_path, threshold=0.7)`
Check if clone is sufficiently different from original.

**Parameters:**
- `original_path` (Path): Path to original image
- `clone_path` (Path): Path to clone image
- `threshold` (float, optional): Similarity threshold (default 0.7)

**Returns:**
- `bool`: True if sufficiently different

### Simple Clone Tools

#### `simple_clone_image_assetrequest(image_path, **kwargs)`
Clone an image using the simplified AssetRequest approach.

**Parameters:**
- `image_path` (str | Path): Path to source image
- `output_dir` (Path, optional): Output directory
- `width` (int, optional): Desired width
- `height` (int, optional): Desired height
- `format` (str, optional): Output format
- `style` (str, optional): Style guidance
- `guidance` (str, optional): Additional guidance

**Returns:**
- `dict`: Result dictionary with success status and metadata

## CLI Usage

### Basic Clone Command
```bash
uv run python -m main --mode clone --source "./assets/downloaded/image.jpg"
```

### Advanced Clone Command
```bash
uv run python -m main --mode clone \
  --source "./assets/downloaded/" \
  --width 1920 --height 1080 \
  --format png --style photorealistic \
  --similarity-threshold 0.7 --max-images 5
```

### Clone Parameters
- `--source`: Path to source image file or directory (required)
- `--width`: Desired width for cloned images
- `--height`: Desired height for cloned images
- `--format`: Output format (png, jpg, webp, etc.)
- `--style`: Style guidance (photorealistic, artistic, watercolor, etc.)
- `--guidance`: Additional guidance for image generation
- `--similarity-threshold`: Maximum similarity threshold (0.0-1.0, default 0.7)
- `--max-images`: Maximum number of images to process (for directory input)

## Examples

### Example 1: Basic Image Cloning
```python
from purplecrayon import PurpleCrayon

crayon = PurpleCrayon()

# Clone a single image
result = await crayon.clone_async(
    source="./assets/downloaded/logo.jpg",
    width=512,
    height=512
)

if result.success:
    print(f"Cloned image saved to: {result.images[0].path}")
else:
    print(f"Clone failed: {result.message}")
```

### Example 2: Batch Directory Cloning
```python
# Clone all images from a directory
result = await crayon.clone_async(
    source="./assets/downloaded/",
    max_images=10,
    similarity_threshold=0.6,
    style="photorealistic"
)

print(f"Successfully cloned {len(result.images)} images")
for image in result.images:
    print(f"  - {image.path}")
```

### Example 3: Custom Style and Guidance
```python
# Clone with specific style and guidance
result = await crayon.clone_async(
    source="./assets/downloaded/portrait.jpg",
    width=1024,
    height=1024,
    style="watercolor",
    guidance="soft lighting, artistic interpretation",
    similarity_threshold=0.5
)
```

### Example 4: Direct Tool Usage
```python
from purplecrayon.tools.clone_image_tools import clone_image
from pathlib import Path

# Use direct tool function
result = await clone_image(
    image_path="./assets/downloaded/image.jpg",
    width=512,
    height=512,
    output_dir=Path("./assets/cloned")
)

if result["success"]:
    print(f"Clone saved to: {result['clone_path']}")
```

## Output Organization

### File Structure
```
assets/
├── cloned/                    # Cloned images directory
│   ├── image1.jpg            # Cloned image
│   ├── image2.png            # Another cloned image
│   └── ...
├── catalog.yaml              # Updated catalog with cloned entries
└── ...
```

### Catalog Integration
Cloned images are automatically added to the catalog with:
- `source`: "ai"
- `provider`: "ai_clone"
- `description`: Generated description from vision analysis
- `width`/`height`: Actual dimensions
- `format`: File format
- `path`: Relative path to cloned file

## Error Handling

### Common Errors
- **File Not Found**: Source image doesn't exist
- **Invalid Format**: Unsupported image format
- **API Failures**: Gemini or Replicate API errors
- **Similarity Too High**: Clone too similar to original
- **Permission Denied**: Cannot write to output directory

### Error Recovery
- **Fallback Generation**: Automatically tries Replicate if Gemini fails
- **Graceful Degradation**: Continues processing other images if one fails
- **Detailed Logging**: Comprehensive error messages and debugging output

## Performance Considerations

### Optimization Tips
- Use `max_images` parameter for large directories
- Adjust `similarity_threshold` based on your needs
- Consider using batch processing for multiple images
- Monitor API rate limits and usage

### Resource Usage
- **Memory**: Efficient image processing with PIL
- **API Calls**: Minimized through intelligent caching
- **Storage**: Cloned images saved to organized directory structure

## Legal and Safety Considerations

### Copyright Compliance
- Generated images are new works, not copies
- Users responsible for ensuring compliance with copyright laws
- Feature designed for transformative use cases
- Similarity thresholds help prevent literal copies

### Safety Features
- Similarity checking prevents overly literal copies
- Style detection maintains transformative nature
- Comprehensive error handling for edge cases
- Clear documentation about copyright compliance

## Troubleshooting

### Common Issues
1. **API Key Missing**: Ensure `GEMINI_API_KEY` is set in `.env`
2. **Similarity Too High**: Lower `similarity_threshold` parameter
3. **Style Not Detected**: Check if image is clear and well-lit
4. **Generation Fails**: Try different style or guidance parameters

### Debug Mode
Enable verbose output by setting `verbose=True` in the PurpleCrayon constructor:
```python
crayon = PurpleCrayon(verbose=True)
```

This will show detailed information about the cloning process, including vision analysis results and generation steps.
