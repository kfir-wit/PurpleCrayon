# PurpleCrayon Source API Documentation

## Overview

The Source API provides a comprehensive workflow that combines local asset search, stock photo fetching, and AI image generation into a single operation. This is the main entry point for finding or creating images across all available sources, providing a unified interface for asset discovery and creation.

## Core Concepts

### Source Workflow Process
1. **Local Search**: Searches existing assets in the local catalog
2. **Stock Photo Fetching**: Downloads relevant images from stock photo providers
3. **AI Generation**: Creates new images using AI providers
4. **Result Aggregation**: Combines results from all sources
5. **Quality Ranking**: Ranks results by relevance and quality
6. **Catalog Integration**: Updates catalog with new findings

### Source Types
- **Local Assets**: Images already in your asset catalog
- **Stock Photos**: Downloaded from Unsplash, Pexels, Pixabay
- **AI Generated**: Created using Gemini, Imagen, Stable Diffusion
- **Cloned Images**: Royalty-free alternatives (if using clone functionality)

### Key Features
- **Unified Search**: Single interface for all image sources
- **Smart Ranking**: Results ranked by relevance and quality
- **Comprehensive Coverage**: Searches all available sources
- **Flexible Filtering**: Customizable source preferences
- **Batch Processing**: Efficient handling of multiple sources
- **Result Deduplication**: Avoids duplicate results across sources

## API Reference

### PurpleCrayon Class Methods

#### `source_async(request)`
Asynchronously search all sources for images matching the request.

**Parameters:**
- `request` (AssetRequest): Request object containing search parameters

**Returns:**
- `OperationResult`: Contains success status, message, and list of `ImageResult` objects

**Example:**
```python
from purplecrayon import PurpleCrayon, AssetRequest

crayon = PurpleCrayon()

# Create comprehensive source request
request = AssetRequest(
    description="panda wallpaper for desktop",
    width=1920,
    height=1080,
    format="jpg",
    style="high quality",
    preferred_sources=["unsplash", "gemini"],
    max_results=5,
    tags=["nature", "wildlife", "cute"]
)

# Search all sources
result = await crayon.source_async(request)
```

#### `source(request)`
Synchronous wrapper for `source_async()`.

**Parameters:**
- `request` (AssetRequest): Request object containing search parameters

**Returns:**
- `OperationResult`: Contains success status, message, and list of `ImageResult` objects

**Example:**
```python
# Synchronous usage
result = crayon.source(request)
```

### AssetRequest Parameters

#### Required Parameters
- `description` (str): Description of the desired image

#### Optional Parameters
- `width` (int): Desired image width (default: 1024)
- `height` (int): Desired image height (default: 1080)
- `format` (str): Preferred format - "jpg", "png", "webp" (default: "jpg")
- `style` (str): Style guidance for AI generation
- `preferred_sources` (List[str]): Preferred sources - ["local", "unsplash", "pexels", "pixabay", "gemini", "imagen"]
- `max_results` (int): Maximum results per source (default: 5)
- `tags` (List[str]): Additional search tags for context
- `quality` (str): Quality filter - "high", "medium", "low" (default: "high")

## CLI Usage

### Basic Source Command
```bash
uv run python -m main --mode full
```

### Source with Custom Parameters
```bash
# Source with specific requirements
uv run python -m main --mode full \
  --description "mountain landscape sunset" \
  --width 1920 --height 1080 \
  --format jpg --style photorealistic
```

## Examples

### Example 1: Basic Source Workflow
```python
from purplecrayon import PurpleCrayon, AssetRequest

crayon = PurpleCrayon()

# Create a comprehensive request
request = AssetRequest(
    description="business meeting professional",
    width=1920,
    height=1080,
    format="jpg"
)

# Search all sources
result = crayon.source(request)

if result.success:
    print(f"Found {len(result.images)} images from all sources")
    
    # Group by source
    sources = {}
    for img in result.images:
        if img.source not in sources:
            sources[img.source] = []
        sources[img.source].append(img)
    
    for source, images in sources.items():
        print(f"\n{source.upper()} ({len(images)} images):")
        for img in images:
            print(f"  - {img.path} ({img.provider})")
else:
    print(f"Source failed: {result.message}")
```

### Example 2: Specific Source Preferences
```python
# Search only local and AI sources
request = AssetRequest(
    description="abstract geometric patterns",
    width=1024,
    height=1024,
    preferred_sources=["local", "gemini"],
    max_results=3
)

result = await crayon.source_async(request)
```

### Example 3: High-Quality Search
```python
# Search for high-quality images with specific style
request = AssetRequest(
    description="luxury car advertisement",
    width=1920,
    height=1080,
    style="photorealistic",
    quality="high",
    preferred_sources=["unsplash", "pexels", "gemini"],
    max_results=5
)

result = crayon.source(request)
```

### Example 4: Tagged Search
```python
# Search with additional tags for context
request = AssetRequest(
    description="technology innovation",
    width=1920,
    height=1080,
    tags=["tech", "innovation", "futuristic", "modern"],
    preferred_sources=["unsplash", "pixabay", "imagen"],
    max_results=10
)

result = await crayon.source_async(request)
```

## Output Organization

### File Structure
```
assets/
├── ai/                        # AI-generated images
│   ├── gemini_123456.png
│   └── imagen_789012.png
├── stock/                     # Stock photos
│   ├── unsplash_345678.jpg
│   ├── pexels_901234.jpg
│   └── pixabay_567890.jpg
├── downloaded/                # Scraped images
│   └── scraped_123456.jpg
├── cloned/                    # Cloned images
│   └── cloned_789012.jpg
├── proprietary/               # User-provided images
│   └── custom_345678.jpg
└── catalog.yaml              # Updated catalog
```

### Result Grouping
Results are automatically grouped by source:
- **Local**: Images from existing catalog
- **Stock**: Downloaded from stock photo providers
- **AI**: Generated using AI providers
- **Downloaded**: Scraped from websites
- **Cloned**: Royalty-free alternatives

### Catalog Integration
All found images are added to the catalog with:
- `source`: Source type (local, stock, ai, downloaded, cloned)
- `provider`: Specific provider (unsplash, gemini, etc.)
- `description`: Image description
- `width`/`height`: Actual dimensions
- `format`: File format
- `path`: Relative path to image
- `match_score`: Relevance score (if available)

## Search Strategy

### Local Asset Search
- **Catalog Query**: Searches existing asset catalog
- **Metadata Matching**: Matches against descriptions and tags
- **Dimension Filtering**: Filters by size requirements
- **Format Matching**: Matches preferred formats

### Stock Photo Search
- **Multi-Provider**: Searches Unsplash, Pexels, Pixabay
- **Query Optimization**: Optimizes search terms for each provider
- **Quality Filtering**: Filters by quality requirements
- **Download Management**: Efficient batch downloading

### AI Generation
- **Provider Selection**: Chooses appropriate AI providers
- **Prompt Generation**: Creates detailed generation prompts
- **Style Application**: Applies requested artistic styles
- **Quality Control**: Ensures generated image quality

## Result Ranking

### Ranking Factors
- **Relevance**: How well the image matches the description
- **Quality**: Image resolution and technical quality
- **Source Preference**: User-specified source preferences
- **Match Score**: AI-calculated relevance score
- **Dimension Match**: How well dimensions match requirements

### Result Ordering
1. **Exact Matches**: Perfect dimension and format matches
2. **High Relevance**: High match scores
3. **Preferred Sources**: User-specified source preferences
4. **Quality Matches**: High-quality images
5. **Fallback Results**: Other available options

## Error Handling

### Common Errors
- **No Results**: No images found across all sources
- **API Failures**: Provider API errors
- **Network Issues**: Connection problems
- **Invalid Request**: Malformed request parameters
- **Permission Errors**: File system access issues

### Error Recovery
- **Source Fallback**: Tries other sources if one fails
- **Partial Results**: Returns available results even if some sources fail
- **Detailed Logging**: Comprehensive error reporting
- **Graceful Degradation**: Continues with available sources

## Performance Considerations

### Optimization Tips
- Use specific source preferences to reduce search time
- Set appropriate `max_results` to control processing time
- Use quality filters to reduce download time
- Monitor API usage and rate limits

### Resource Usage
- **API Calls**: Multiple calls across different providers
- **Storage**: Images saved to appropriate directories
- **Memory**: Efficient processing with streaming
- **Bandwidth**: Optimized downloading with progress tracking

## Configuration

### Environment Variables
```bash
# Required for full functionality
GEMINI_API_KEY=your_gemini_key
UNSPLASH_ACCESS_KEY=your_unsplash_key
PEXELS_API_KEY=your_pexels_key
PIXABAY_API_KEY=your_pixabay_key
REPLICATE_API_TOKEN=your_replicate_token
```

### Source Configuration
```python
# Customize source preferences
request = AssetRequest(
    description="your search query",
    preferred_sources=["local", "unsplash", "gemini"],  # Specific sources
    max_results=5  # Results per source
)
```

## Troubleshooting

### Common Issues
1. **No Results**: Try broader search terms or different sources
2. **Slow Performance**: Reduce max_results or use specific sources
3. **API Errors**: Check API keys and rate limits
4. **Poor Quality**: Adjust quality filters or search terms

### Debug Mode
Enable verbose output:
```python
crayon = PurpleCrayon(verbose=True)
```

This will show detailed information about the search process across all sources.

## Best Practices

### Search Strategy
- Start with broad terms, then narrow down
- Use multiple related keywords and tags
- Test different source combinations
- Save successful search patterns

### Performance
- Use specific source preferences for faster results
- Set appropriate result limits
- Monitor API usage and costs
- Cache results when possible

### Quality
- Use quality filters to ensure good results
- Review and curate results before use
- Keep track of successful search patterns
- Maintain organized asset catalogs
