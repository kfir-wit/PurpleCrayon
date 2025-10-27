# PurpleCrayon Generate API Documentation

## Overview

The Generate API allows you to create AI-generated images using various AI providers including Google Gemini and Replicate (Imagen/Stable Diffusion). This feature provides high-quality image generation with customizable parameters for style, dimensions, and content.

## Core Concepts

### AI Image Generation Process
1. **Request Processing**: Validates and processes the AssetRequest
2. **Provider Selection**: Chooses appropriate AI providers based on preferences
3. **Prompt Generation**: Creates detailed prompts for AI generation
4. **Image Generation**: Generates images using selected AI providers
5. **Post-processing**: Validates and saves generated images
6. **Catalog Integration**: Adds generated images to the asset catalog

### Supported AI Providers
- **Google Gemini 2.5 Flash Image**: Primary provider for high-quality generation
- **Replicate Imagen**: Fallback provider for additional options
- **Replicate Stable Diffusion**: Alternative generation engine

### Key Features
- **Multiple Providers**: Automatic fallback between AI providers
- **Style Control**: Customizable artistic styles and guidance
- **Dimension Control**: Precise width and height specification
- **Format Support**: PNG, JPG, WebP output formats
- **Quality Control**: High-quality generation with validation
- **Catalog Integration**: Automatic cataloging of generated images

## API Reference

### PurpleCrayon Class Methods

#### `generate_async(request)`
Asynchronously generate AI images using specified providers.

**Parameters:**
- `request` (AssetRequest): Request object containing generation parameters

**Returns:**
- `OperationResult`: Contains success status, message, and list of `ImageResult` objects

**Example:**
```python
from purplecrayon import PurpleCrayon, AssetRequest

crayon = PurpleCrayon()

# Create generation request
request = AssetRequest(
    description="artistic panda illustration in watercolor style",
    width=1024,
    height=1024,
    format="png",
    style="watercolor",
    preferred_sources=["gemini", "imagen"],
    max_results=2
)

# Generate images
result = await crayon.generate_async(request)
```

#### `generate(request)`
Synchronous wrapper for `generate_async()`.

**Parameters:**
- `request` (AssetRequest): Request object containing generation parameters

**Returns:**
- `OperationResult`: Contains success status, message, and list of `ImageResult` objects

**Example:**
```python
# Synchronous usage
result = crayon.generate(request)
```

### AssetRequest Parameters

#### Required Parameters
- `description` (str): Detailed description of the image to generate

#### Optional Parameters
- `width` (int): Desired image width (default: 1024)
- `height` (int): Desired image height (default: 1024)
- `format` (str): Output format - "png", "jpg", "webp" (default: "png")
- `style` (str): Artistic style guidance (e.g., "photorealistic", "watercolor", "artistic")
- `quality` (str): Quality level - "high", "medium", "low" (default: "high")
- `preferred_sources` (List[str]): Preferred AI providers - ["gemini", "imagen", "stable-diffusion"]
- `max_results` (int): Maximum number of images to generate per provider (default: 1)
- `tags` (List[str]): Additional search tags for context

### Direct Tool Functions

#### `generate_with_gemini_async(prompt, **kwargs)`
Generate images using Google Gemini directly.

**Parameters:**
- `prompt` (str): Text prompt for generation
- `aspect_ratio` (str, optional): Aspect ratio (e.g., "16:9", "1:1")
- `width` (int, optional): Image width
- `height` (int, optional): Image height

**Returns:**
- `dict`: Result dictionary with success status and image data

#### `generate_with_imagen(prompt, **kwargs)`
Generate images using Replicate Imagen directly.

**Parameters:**
- `prompt` (str): Text prompt for generation
- `width` (int, optional): Image width
- `height` (int, optional): Image height

**Returns:**
- `dict`: Result dictionary with success status and image URL

## CLI Usage

### Basic Generate Command
```bash
uv run python -m main --mode generate
```

### Generate with Custom Parameters
```bash
# Generate with specific prompt and dimensions
uv run python -m main --mode generate \
  --description "mountain landscape at sunset" \
  --width 1920 --height 1080 \
  --format png --style photorealistic
```

## Examples

### Example 1: Basic AI Generation
```python
from purplecrayon import PurpleCrayon, AssetRequest

crayon = PurpleCrayon()

# Create a simple request
request = AssetRequest(
    description="cute panda eating bamboo",
    width=512,
    height=512
)

# Generate image
result = crayon.generate(request)

if result.success:
    print(f"Generated {len(result.images)} images")
    for img in result.images:
        print(f"  - {img.path}")
else:
    print(f"Generation failed: {result.message}")
```

### Example 2: Artistic Style Generation
```python
# Generate with specific artistic style
request = AssetRequest(
    description="abstract geometric patterns",
    width=1024,
    height=1024,
    format="png",
    style="watercolor",
    quality="high",
    preferred_sources=["gemini"],
    max_results=3
)

result = await crayon.generate_async(request)
```

### Example 3: Multiple Providers
```python
# Generate using multiple AI providers
request = AssetRequest(
    description="futuristic city skyline",
    width=1920,
    height=1080,
    preferred_sources=["gemini", "imagen", "stable-diffusion"],
    max_results=2  # 2 images per provider = 6 total
)

result = crayon.generate(request)
```

### Example 4: Direct Tool Usage
```python
from purplecrayon.tools.ai_generation_tools import generate_with_gemini_async

# Use direct tool function
result = await generate_with_gemini_async(
    prompt="beautiful sunset over ocean",
    aspect_ratio="16:9"
)

if result.get("status") == "succeeded":
    print("Generation successful!")
    # Save image data
    with open("generated_image.png", "wb") as f:
        f.write(result["image_data"])
```

## Output Organization

### File Structure
```
assets/
├── ai/                        # AI-generated images directory
│   ├── gemini_1234567890.png  # Gemini-generated image
│   ├── imagen_1234567891.png  # Imagen-generated image
│   └── ...
├── catalog.yaml              # Updated catalog with AI entries
└── ...
```

### Naming Convention
- **Gemini**: `gemini_{timestamp}.{format}`
- **Imagen**: `imagen_{timestamp}.{format}`
- **Stable Diffusion**: `stable_diffusion_{timestamp}.{format}`

### Catalog Integration
Generated images are automatically added to the catalog with:
- `source`: "ai"
- `provider`: "gemini", "imagen", or "stable_diffusion"
- `description`: Original generation prompt
- `width`/`height`: Actual dimensions
- `format`: File format
- `path`: Relative path to generated file

## Style Guidelines

### Supported Styles
- **photorealistic**: Realistic, photographic style
- **artistic**: Artistic, creative interpretation
- **watercolor**: Watercolor painting style
- **oil painting**: Oil painting style
- **digital art**: Digital art style
- **sketch**: Pencil sketch style
- **cartoon**: Cartoon/animated style
- **abstract**: Abstract art style
- **minimalist**: Clean, minimal design

### Quality Levels
- **high**: Maximum quality, longer generation time
- **medium**: Balanced quality and speed
- **low**: Faster generation, lower quality

## Error Handling

### Common Errors
- **API Key Missing**: Ensure `GEMINI_API_KEY` and `REPLICATE_API_TOKEN` are set
- **Invalid Dimensions**: Check width/height parameters
- **Unsupported Format**: Use supported formats (png, jpg, webp)
- **Rate Limiting**: API rate limits exceeded
- **Generation Failure**: AI provider unable to generate image

### Error Recovery
- **Automatic Fallback**: Tries multiple providers if one fails
- **Retry Logic**: Built-in retry for transient failures
- **Detailed Logging**: Comprehensive error messages and debugging

## Performance Considerations

### Optimization Tips
- Use appropriate `max_results` to control generation count
- Choose single provider for faster generation
- Use lower quality settings for faster generation
- Monitor API usage and rate limits

### Resource Usage
- **API Calls**: One call per provider per generation
- **Storage**: Generated images saved to `assets/ai/`
- **Memory**: Efficient image processing with PIL

## Configuration

### Environment Variables
```bash
# Required for AI generation
GEMINI_API_KEY=your_gemini_api_key
REPLICATE_API_TOKEN=your_replicate_token

# Optional for enhanced functionality
LANGCHAIN_API_KEY=your_langchain_key  # For tracing
```

### Provider Configuration
```python
# Customize provider preferences
request = AssetRequest(
    description="your prompt",
    preferred_sources=["gemini"],  # Only use Gemini
    max_results=1
)
```

## Troubleshooting

### Common Issues
1. **No Images Generated**: Check API keys and network connection
2. **Poor Quality**: Try different style or quality settings
3. **Wrong Dimensions**: Verify width/height parameters
4. **Slow Generation**: Reduce max_results or use single provider

### Debug Mode
Enable verbose output:
```python
crayon = PurpleCrayon(verbose=True)
```

This will show detailed information about the generation process, including API calls and responses.

## Best Practices

### Prompt Writing
- Be specific and descriptive
- Include style and mood details
- Mention important visual elements
- Use clear, concise language

### Performance
- Start with single provider for testing
- Use appropriate dimensions for your use case
- Monitor API usage and costs
- Cache results when possible

### Quality
- Use high quality for final images
- Test different styles for best results
- Validate generated images before use
- Keep original prompts for reference
