# PurpleCrayon Fetch API Documentation

## Overview

The Fetch API allows you to search and download stock photos from multiple providers including Unsplash, Pexels, and Pixabay. This feature provides access to high-quality, royalty-free images with comprehensive search capabilities and automatic organization.

## Core Concepts

### Stock Photo Fetching Process
1. **Search Query**: Processes the AssetRequest description into search terms
2. **Provider Selection**: Searches across multiple stock photo providers
3. **Image Discovery**: Finds relevant images based on search criteria
4. **Download**: Downloads images from provider APIs
5. **Validation**: Validates downloaded images for quality and format
6. **Organization**: Saves images to appropriate directories
7. **Catalog Integration**: Adds fetched images to the asset catalog

### Supported Stock Photo Providers
- **Unsplash**: High-quality photography with generous licensing
- **Pexels**: Free stock photos and videos
- **Pixabay**: Free images, vectors, and illustrations

### Key Features
- **Multi-Provider Search**: Simultaneous search across all providers
- **Smart Filtering**: Automatic filtering by dimensions and quality
- **Batch Download**: Download multiple images efficiently
- **Format Support**: JPG, PNG, WebP image formats
- **Metadata Preservation**: Maintains original image metadata
- **Catalog Integration**: Automatic cataloging with source attribution

## API Reference

### PurpleCrayon Class Methods

#### `fetch_async(request)`
Asynchronously fetch stock photos from all configured providers.

**Parameters:**
- `request` (AssetRequest): Request object containing search parameters

**Returns:**
- `OperationResult`: Contains success status, message, and list of `ImageResult` objects

**Example:**
```python
from purplecrayon import PurpleCrayon, AssetRequest

crayon = PurpleCrayon()

# Create fetch request
request = AssetRequest(
    description="panda eating bamboo in forest",
    width=1920,
    height=1080,
    format="jpg",
    preferred_sources=["unsplash", "pexels"],
    max_results=3
)

# Fetch stock photos
result = await crayon.fetch_async(request)
```

#### `fetch(request)`
Synchronous wrapper for `fetch_async()`.

**Parameters:**
- `request` (AssetRequest): Request object containing search parameters

**Returns:**
- `OperationResult`: Contains success status, message, and list of `ImageResult` objects

**Example:**
```python
# Synchronous usage
result = crayon.fetch(request)
```

### AssetRequest Parameters

#### Required Parameters
- `description` (str): Search description for finding relevant images

#### Optional Parameters
- `width` (int): Desired image width (default: 1024)
- `height` (int): Desired image height (default: 1080)
- `format` (str): Preferred format - "jpg", "png", "webp" (default: "jpg")
- `preferred_sources` (List[str]): Preferred providers - ["unsplash", "pexels", "pixabay"]
- `max_results` (int): Maximum results per provider (default: 5)
- `tags` (List[str]): Additional search tags for context
- `quality` (str): Quality filter - "high", "medium", "low" (default: "high")

### Direct Tool Functions

#### `search_unsplash(query, **kwargs)`
Search Unsplash directly for images.

**Parameters:**
- `query` (str): Search query
- `count` (int, optional): Number of results
- `orientation` (str, optional): Image orientation ("landscape", "portrait", "squarish")

**Returns:**
- `List[dict]`: List of image metadata dictionaries

#### `search_pexels(query, **kwargs)`
Search Pexels directly for images.

**Parameters:**
- `query` (str): Search query
- `per_page` (int, optional): Results per page
- `orientation` (str, optional): Image orientation

**Returns:**
- `List[dict]`: List of image metadata dictionaries

#### `search_pixabay(query, **kwargs)`
Search Pixabay directly for images.

**Parameters:**
- `query` (str): Search query
- `per_page` (int, optional): Results per page
- `image_type` (str, optional): Image type ("photo", "illustration", "vector")

**Returns:**
- `List[dict]`: List of image metadata dictionaries

## CLI Usage

### Basic Fetch Command
```bash
uv run python -m main --mode search
```

### Fetch with Custom Parameters
```bash
# Fetch with specific search terms and dimensions
uv run python -m main --mode search \
  --description "mountain landscape sunset" \
  --width 1920 --height 1080 \
  --format jpg --sources unsplash,pexels
```

## Examples

### Example 1: Basic Stock Photo Fetching
```python
from purplecrayon import PurpleCrayon, AssetRequest

crayon = PurpleCrayon()

# Create a simple fetch request
request = AssetRequest(
    description="beautiful sunset over ocean",
    width=1920,
    height=1080,
    format="jpg"
)

# Fetch stock photos
result = crayon.fetch(request)

if result.success:
    print(f"Fetched {len(result.images)} images")
    for img in result.images:
        print(f"  - {img.path} ({img.provider})")
else:
    print(f"Fetch failed: {result.message}")
```

### Example 2: Multi-Provider Search
```python
# Search across all providers
request = AssetRequest(
    description="urban architecture modern city",
    width=1920,
    height=1080,
    preferred_sources=["unsplash", "pexels", "pixabay"],
    max_results=5  # 5 per provider = 15 total
)

result = await crayon.fetch_async(request)
```

### Example 3: Specific Provider Search
```python
# Search only Unsplash for high-quality photos
request = AssetRequest(
    description="professional business meeting",
    width=1920,
    height=1080,
    preferred_sources=["unsplash"],
    max_results=10,
    quality="high"
)

result = crayon.fetch(request)
```

### Example 4: Direct Provider Usage
```python
from purplecrayon.tools.stock_photo_tools import search_unsplash

# Use Unsplash directly
images = search_unsplash(
    query="nature landscape mountains",
    count=5,
    orientation="landscape"
)

for img in images:
    print(f"Found: {img['alt_description']} - {img['urls']['regular']}")
```

## Output Organization

### File Structure
```
assets/
├── stock/                     # Stock photos directory
│   ├── unsplash_123456.jpg   # Unsplash image
│   ├── pexels_789012.jpg     # Pexels image
│   ├── pixabay_345678.jpg    # Pixabay image
│   └── ...
├── catalog.yaml              # Updated catalog with stock entries
└── ...
```

### Naming Convention
- **Unsplash**: `unsplash_{id}.{format}`
- **Pexels**: `pexels_{id}.{format}`
- **Pixabay**: `pixabay_{id}.{format}`

### Catalog Integration
Fetched images are automatically added to the catalog with:
- `source`: "stock"
- `provider`: "unsplash", "pexels", or "pixabay"
- `description`: Original image description
- `width`/`height`: Actual dimensions
- `format`: File format
- `path`: Relative path to fetched file
- `url`: Original source URL
- `photographer`: Photographer attribution

## Provider-Specific Features

### Unsplash
- **High Quality**: Professional photography
- **Generous Licensing**: Free for most commercial uses
- **Rich Metadata**: Detailed image information
- **API Limits**: 50 requests per hour (free tier)

### Pexels
- **Diverse Content**: Photos and videos
- **Good Quality**: High-resolution images
- **Simple Licensing**: Free for commercial use
- **API Limits**: 200 requests per hour (free tier)

### Pixabay
- **Multiple Types**: Photos, illustrations, vectors
- **Good Selection**: Wide variety of content
- **Free License**: Commercial use allowed
- **API Limits**: 5000 requests per hour (free tier)

## Search Optimization

### Effective Search Terms
- **Be Specific**: "mountain sunset" vs "nature"
- **Use Adjectives**: "dramatic mountain sunset"
- **Include Context**: "business meeting office"
- **Add Style**: "minimalist architecture"

### Quality Filters
- **High**: Professional quality, high resolution
- **Medium**: Good quality, standard resolution
- **Low**: Basic quality, lower resolution

### Orientation Preferences
- **Landscape**: Wide images for backgrounds
- **Portrait**: Tall images for mobile
- **Square**: Social media posts

## Error Handling

### Common Errors
- **API Key Missing**: Ensure provider API keys are set
- **Rate Limiting**: API rate limits exceeded
- **Network Issues**: Connection problems
- **Invalid Query**: Search terms too vague or specific
- **No Results**: No images found for query

### Error Recovery
- **Automatic Retry**: Built-in retry for transient failures
- **Provider Fallback**: Tries other providers if one fails
- **Detailed Logging**: Comprehensive error messages

## Performance Considerations

### Optimization Tips
- Use appropriate `max_results` to control download count
- Choose specific providers for faster searches
- Use quality filters to reduce download time
- Monitor API usage and rate limits

### Resource Usage
- **API Calls**: One call per provider per search
- **Storage**: Downloaded images saved to `assets/stock/`
- **Bandwidth**: Efficient downloading with progress tracking

## Configuration

### Environment Variables
```bash
# Required for stock photo fetching
UNSPLASH_ACCESS_KEY=your_unsplash_key
PEXELS_API_KEY=your_pexels_key
PIXABAY_API_KEY=your_pixabay_key
```

### Provider Configuration
```python
# Customize provider preferences
request = AssetRequest(
    description="your search query",
    preferred_sources=["unsplash"],  # Only use Unsplash
    max_results=10
)
```

## Troubleshooting

### Common Issues
1. **No Results**: Try broader or different search terms
2. **API Errors**: Check API keys and rate limits
3. **Download Failures**: Check network connection and permissions
4. **Poor Quality**: Adjust quality filters or search terms

### Debug Mode
Enable verbose output:
```python
crayon = PurpleCrayon(verbose=True)
```

This will show detailed information about the search and download process.

## Best Practices

### Search Strategy
- Start with broad terms, then narrow down
- Use multiple related keywords
- Test different providers for variety
- Save successful search terms for reuse

### Performance
- Use appropriate result limits
- Monitor API usage and costs
- Cache results when possible
- Use quality filters to reduce downloads

### Legal Compliance
- Respect provider terms of service
- Attribute photographers when required
- Use appropriate licensing for your use case
- Keep track of image sources and licenses
