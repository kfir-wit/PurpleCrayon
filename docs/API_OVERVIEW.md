# PurpleCrayon API Overview

## Introduction

PurpleCrayon is a comprehensive AI graphics sourcing and generation toolkit that provides unified access to multiple image sources and creation methods. This document provides an overview of all available APIs and their use cases.

## Core Functionalities

### 1. **Generate API** - AI Image Generation
Create high-quality images using AI providers like Google Gemini and Replicate.

**Use Cases:**
- Creating custom artwork and illustrations
- Generating images from text descriptions
- Producing images in specific artistic styles
- Creating images when stock photos aren't suitable

**Key Features:**
- Multiple AI providers (Gemini, Imagen, Stable Diffusion)
- Style control and customization
- High-quality output with validation
- Automatic catalog integration

**Documentation:** [GENERATE_API.md](GENERATE_API.md)

### 2. **Fetch API** - Stock Photo Search
Search and download royalty-free images from stock photo providers.

**Use Cases:**
- Finding professional photography
- Sourcing high-quality stock images
- Building image libraries
- Finding specific types of content

**Key Features:**
- Multiple providers (Unsplash, Pexels, Pixabay)
- Advanced search capabilities
- Quality filtering and validation
- Automatic organization

**Documentation:** [FETCH_API.md](FETCH_API.md)

### 3. **Source API** - Comprehensive Asset Discovery
Unified search across all available sources (local, stock, AI).

**Use Cases:**
- Finding images from any available source
- Comprehensive asset discovery
- Comparing options across sources
- Building complete image collections

**Key Features:**
- Multi-source search
- Smart result ranking
- Unified interface
- Comprehensive coverage

**Documentation:** [SOURCE_API.md](SOURCE_API.md)

### 4. **Scrape API** - Web Image Extraction
Download all images from websites using multiple scraping engines.

**Use Cases:**
- Extracting images from websites
- Building image collections from specific sites
- Gathering reference materials
- Archiving website content

**Key Features:**
- Multiple scraping engines (Firecrawl, Playwright, BeautifulSoup)
- Anti-detection mechanisms
- Robust error handling
- Automatic validation

**Documentation:** [SCRAPE_API.md](SCRAPE_API.md)

### 5. **Clone API** - Royalty-Free Alternatives
Create royalty-free alternatives to existing images using AI.

**Use Cases:**
- Creating copyright-free alternatives
- Maintaining visual intent while avoiding copyright issues
- Generating variations of existing images
- Building royalty-free image libraries

**Key Features:**
- AI-powered image analysis
- Style detection and inheritance
- Similarity checking
- Batch processing

**Documentation:** [CLONE_API.md](CLONE_API.md)

### 6. **Catalog API** - Asset Management
Comprehensive asset catalog management and organization.

**Use Cases:**
- Organizing and managing image collections
- Searching and filtering assets
- Tracking asset metadata
- Maintaining asset quality

**Key Features:**
- Multi-format catalogs (YAML, JSON)
- Advanced search capabilities
- Asset validation and cleanup
- Statistics and analytics

**Documentation:** [CATALOG_API.md](CATALOG_API.md)

## Quick Start Guide

### Installation
```bash
# Install with uv
uv add purplecrayon

# Or install from source
git clone https://github.com/kfir-wit/PurpleCrayon.git
cd PurpleCrayon
uv pip install -e .
```

### Basic Usage
```python
from purplecrayon import PurpleCrayon, AssetRequest

# Initialize PurpleCrayon
crayon = PurpleCrayon(assets_dir="./my_assets")

# Create a request
request = AssetRequest(
    description="beautiful sunset over mountains",
    width=1920,
    height=1080,
    format="jpg"
)

# Search all sources
result = crayon.source(request)

# Generate AI images
ai_result = crayon.generate(request)

# Fetch stock photos
stock_result = crayon.fetch(request)

# Scrape a website
scrape_result = crayon.scrape("https://example.com/gallery")

# Clone an image
clone_result = await crayon.clone_async("./assets/downloaded/image.jpg")
```

## CLI Usage

### Available Modes
```bash
# Full workflow (search all sources)
uv run python -m main --mode full

# Generate AI images only
uv run python -m main --mode generate

# Fetch stock photos only
uv run python -m main --mode search

# Scrape website images
uv run python -m main --mode scrape --url "https://example.com"

# Clone images for alternatives
uv run python -m main --mode clone --source "./assets/downloaded/image.jpg"

# Manage catalog
uv run python -m main --sort-catalog
uv run python -m main --cleanup
```

## API Architecture

### Core Classes

#### `PurpleCrayon`
Main client class providing unified access to all functionality.

**Key Methods:**
- `source()` / `source_async()` - Search all sources
- `generate()` / `generate_async()` - Generate AI images
- `fetch()` / `fetch_async()` - Fetch stock photos
- `scrape()` / `scrape_async()` - Scrape website images
- `clone()` / `clone_async()` - Clone images
- `sort_catalog()` - Manage asset catalog
- `cleanup_assets()` - Clean up assets

#### `AssetRequest`
Request object for specifying image requirements.

**Key Parameters:**
- `description` - Image description
- `width` / `height` - Dimensions
- `format` - File format
- `style` - Artistic style
- `preferred_sources` - Source preferences
- `max_results` - Result limits

#### `ImageResult`
Result object containing image information.

**Key Properties:**
- `path` - File path
- `source` - Source type
- `provider` - Specific provider
- `width` / `height` - Dimensions
- `format` - File format
- `description` - Image description

#### `OperationResult`
Generic result wrapper for operations.

**Key Properties:**
- `success` - Operation success status
- `message` - Result message
- `images` - List of ImageResult objects
- `error_code` - Error code if failed

### Service Layer

#### `ImageService`
Core service handling image operations.

**Key Methods:**
- `search_local_assets()` - Search local catalog
- `fetch_stock_images()` - Fetch from stock providers
- `generate_ai_images()` - Generate with AI providers
- `scrape_website()` - Scrape website images

#### `AssetCatalog`
Catalog management system.

**Key Methods:**
- `search_assets()` - Search catalog
- `update_catalog_from_assets()` - Update catalog
- `get_stats()` - Get statistics
- `export_catalog()` - Export catalog

## File Organization

### Directory Structure
```
assets/
├── catalog.yaml              # Main catalog file
├── catalog.json              # JSON catalog file
├── ai/                       # AI-generated images
├── stock/                    # Stock photos
├── downloaded/               # Scraped images
├── cloned/                   # Cloned images
├── proprietary/              # User-provided images
└── ...
```

### Naming Conventions
- **AI Images**: `{provider}_{timestamp}.{format}`
- **Stock Photos**: `{provider}_{id}.{format}`
- **Scraped Images**: `scraped_{engine}_{id}.{format}`
- **Cloned Images**: `{original_name}.{format}`

## Configuration

### Environment Variables
```bash
# AI Generation
GEMINI_API_KEY=your_gemini_key
REPLICATE_API_TOKEN=your_replicate_token

# Stock Photos
UNSPLASH_ACCESS_KEY=your_unsplash_key
PEXELS_API_KEY=your_pexels_key
PIXABAY_API_KEY=your_pixabay_key

# Web Scraping
FIRECRAWL_API_KEY=your_firecrawl_key

# Optional
LANGCHAIN_API_KEY=your_langchain_key  # For tracing
```

### Configuration Options
```python
# Initialize with custom configuration
crayon = PurpleCrayon(
    assets_dir="./custom_assets",
    config={
        "max_results_per_provider": 10,
        "quality_threshold": "high",
        "auto_cleanup": True
    }
)
```

## Error Handling

### Common Error Types
- **API Errors**: Provider API failures
- **Network Errors**: Connection issues
- **Validation Errors**: Invalid parameters
- **File System Errors**: Permission or disk space issues

### Error Recovery
- **Automatic Fallback**: Tries alternative providers
- **Retry Logic**: Built-in retry for transient failures
- **Graceful Degradation**: Continues with available sources
- **Detailed Logging**: Comprehensive error reporting

## Performance Considerations

### Optimization Tips
- Use specific source preferences to reduce processing time
- Set appropriate result limits
- Enable verbose mode for debugging
- Regular catalog cleanup and maintenance

### Resource Usage
- **Memory**: Efficient image processing with streaming
- **Storage**: Organized directory structure
- **Bandwidth**: Optimized downloading and caching
- **CPU**: Multi-threaded processing where possible

## Best Practices

### General Usage
- Start with broad searches, then narrow down
- Use appropriate source preferences for your needs
- Regular catalog maintenance and cleanup
- Monitor API usage and rate limits

### Performance
- Use specific source preferences for faster results
- Set reasonable result limits
- Enable verbose mode for debugging
- Regular catalog optimization

### Legal Compliance
- Respect provider terms of service
- Use appropriate licensing for your use case
- Monitor copyright and licensing requirements
- Keep track of image sources and licenses

## Examples

### Complete Workflow
```python
from purplecrayon import PurpleCrayon, AssetRequest

# Initialize
crayon = PurpleCrayon(assets_dir="./project_assets")

# Create request
request = AssetRequest(
    description="professional business meeting",
    width=1920,
    height=1080,
    format="jpg",
    preferred_sources=["unsplash", "gemini"],
    max_results=5
)

# Search all sources
result = crayon.source(request)

# Generate additional AI images
ai_result = crayon.generate(request)

# Scrape reference images
scrape_result = crayon.scrape("https://business-photos.com")

# Clone specific images
clone_result = await crayon.clone_async("./assets/downloaded/meeting.jpg")

# Organize and clean up
catalog_result = crayon.sort_catalog()
cleanup_result = crayon.cleanup_assets()

print(f"Found {len(result.images)} total images")
print(f"Generated {len(ai_result.images)} AI images")
print(f"Scraped {len(scrape_result.images)} reference images")
print(f"Cloned {len(clone_result.images)} alternatives")
```

## Support and Documentation

### Additional Resources
- **API Documentation**: Individual API docs in `docs/` directory
- **Examples**: Working examples in `examples/` directory
- **CLI Reference**: Command-line interface documentation
- **Configuration Guide**: Environment and configuration setup

### Getting Help
- Check the individual API documentation files
- Review the examples in the `examples/` directory
- Enable verbose mode for detailed debugging
- Check environment variables and API keys

### Contributing
- Report issues on GitHub
- Submit pull requests for improvements
- Follow the existing code style and patterns
- Add tests for new functionality
