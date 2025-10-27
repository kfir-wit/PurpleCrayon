# PurpleCrayon Examples Index

## Overview

This document provides a comprehensive index of all available examples in the PurpleCrayon package, organized by functionality and use case.

## Core Functionality Examples

### AI Generation
- **[generate_example.py](../examples/generate_example.py)**: Basic AI image generation using Gemini and Imagen
- **[test_image_to_image.py](../examples/test_image_to_image.py)**: Image-to-image generation testing

### Stock Photo Fetching
- **[fetch_example.py](../examples/fetch_example.py)**: Stock photo search and download from Unsplash, Pexels, Pixabay

### Web Scraping
- **[scrape_example.py](../examples/scrape_example.py)**: Website image scraping with multiple engines
- **[scrape_comparison.py](../examples/scrape_comparison.py)**: Compare different scraping engines side-by-side

### Image Cloning
- **[clone_example.py](../examples/clone_example.py)**: Comprehensive image cloning examples
- **[simple_clone_example.py](../examples/simple_clone_example.py)**: Basic text-to-image cloning
- **[simple_clone_assetrequest_example.py](../examples/simple_clone_assetrequest_example.py)**: AssetRequest-based cloning

### Asset Management
- **[catalog_example.py](../examples/catalog_example.py)**: Asset catalog management and organization

### Complete Workflows
- **[source_example.py](../examples/source_example.py)**: End-to-end sourcing workflow across all sources
- **[api_example.py](../examples/api_example.py)**: Package API usage examples

## Example Categories

### 1. **AI Generation Examples**

#### generate_example.py
**Purpose**: Demonstrate basic AI image generation
**Key Features**:
- Create AssetRequest with description and parameters
- Generate images using Gemini and Imagen
- Handle results and display metadata
- Error handling and validation

**Usage**:
```bash
uv run python examples/generate_example.py
```

**Code Highlights**:
```python
request = AssetRequest(
    description="artistic panda illustration in watercolor style",
    width=1024,
    height=1024,
    format="png",
    style="watercolor",
    preferred_sources=["gemini", "imagen"],
    max_results=2
)

result = crayon.generate(request)
```

#### test_image_to_image.py
**Purpose**: Test image-to-image generation functionality
**Key Features**:
- Image-to-image generation with source image
- Prompt-based image transformation
- File handling and validation

**Usage**:
```bash
uv run python examples/test_image_to_image.py
```

### 2. **Stock Photo Examples**

#### fetch_example.py
**Purpose**: Demonstrate stock photo fetching
**Key Features**:
- Search multiple stock photo providers
- Download and save images
- Handle different image formats
- Provider-specific configuration

**Usage**:
```bash
uv run python examples/fetch_example.py
```

**Code Highlights**:
```python
request = AssetRequest(
    description="panda eating bamboo in forest",
    width=1920,
    height=1080,
    format="jpg",
    preferred_sources=["unsplash", "pexels"],
    max_results=3
)

result = crayon.fetch(request)
```

### 3. **Web Scraping Examples**

#### scrape_example.py
**Purpose**: Demonstrate website image scraping
**Key Features**:
- Multiple scraping engines (Firecrawl, Playwright, BeautifulSoup)
- Anti-detection mechanisms
- Batch image downloading
- Error handling and validation

**Usage**:
```bash
uv run python examples/scrape_example.py https://example.com/gallery
```

**Code Highlights**:
```python
result = crayon.scrape(
    url="https://example.com/gallery",
    engine="firecrawl",
    verbose=True
)
```

#### scrape_comparison.py
**Purpose**: Compare different scraping engines
**Key Features**:
- Side-by-side engine comparison
- Performance metrics
- Success rate analysis
- Detailed logging

**Usage**:
```bash
uv run python examples/scrape_comparison.py https://wordpress.org/showcase/
```

### 4. **Image Cloning Examples**

#### clone_example.py
**Purpose**: Comprehensive image cloning demonstration
**Key Features**:
- Single image cloning
- Batch directory cloning
- Style detection and inheritance
- Similarity checking
- Error handling and fallbacks

**Usage**:
```bash
uv run python examples/clone_example.py
```

**Code Highlights**:
```python
result = await crayon.clone_async(
    source="./assets/downloaded/image.jpg",
    width=1024,
    height=1024,
    style="photorealistic",
    similarity_threshold=0.7
)
```

#### simple_clone_example.py
**Purpose**: Basic text-to-image cloning
**Key Features**:
- Simple filename-based prompts
- Direct tool usage
- Basic error handling

**Usage**:
```bash
uv run python examples/simple_clone_example.py
```

#### simple_clone_assetrequest_example.py
**Purpose**: AssetRequest-based cloning workflow
**Key Features**:
- AssetRequest creation from image analysis
- Standard generation pipeline integration
- Comprehensive error handling

**Usage**:
```bash
uv run python examples/simple_clone_assetrequest_example.py
```

### 5. **Asset Management Examples**

#### catalog_example.py
**Purpose**: Asset catalog management demonstration
**Key Features**:
- Catalog creation and updating
- Asset search and filtering
- Statistics and analytics
- Export in multiple formats

**Usage**:
```bash
uv run python examples/catalog_example.py
```

**Code Highlights**:
```python
catalog = AssetCatalog(Path("./example_assets/catalog.yaml"))

# Search assets
results = catalog.search_assets(
    query="panda",
    source="ai",
    format="png"
)

# Export catalog
export_paths = catalog.export_catalog(format="both")
```

### 6. **Complete Workflow Examples**

#### source_example.py
**Purpose**: End-to-end sourcing workflow
**Key Features**:
- Multi-source search (local, stock, AI)
- Result aggregation and ranking
- Comprehensive error handling
- Performance monitoring

**Usage**:
```bash
uv run python examples/source_example.py
```

**Code Highlights**:
```python
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

result = crayon.source(request)
```

#### api_example.py
**Purpose**: Package API usage demonstration
**Key Features**:
- Main client usage
- Individual tool functions
- Batch processing
- Error handling patterns

**Usage**:
```bash
uv run python examples/api_example.py
```

## Running Examples

### Prerequisites
1. **Install Dependencies**:
   ```bash
   uv add purplecrayon
   ```

2. **Set Environment Variables**:
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your API keys
   GEMINI_API_KEY=your_gemini_key
   UNSPLASH_ACCESS_KEY=your_unsplash_key
   PEXELS_API_KEY=your_pexels_key
   PIXABAY_API_KEY=your_pixabay_key
   FIRECRAWL_API_KEY=your_firecrawl_key
   REPLICATE_API_TOKEN=your_replicate_token
   ```

3. **Install Browser Dependencies** (for Playwright):
   ```bash
   uv run playwright install
   ```

### Running Individual Examples
```bash
# AI Generation
uv run python examples/generate_example.py

# Stock Photos
uv run python examples/fetch_example.py

# Web Scraping
uv run python examples/scrape_example.py https://example.com

# Image Cloning
uv run python examples/clone_example.py

# Asset Management
uv run python examples/catalog_example.py

# Complete Workflow
uv run python examples/source_example.py
```

### Running All Examples
```bash
# Run all examples in sequence
for example in examples/*.py; do
    echo "Running $example..."
    uv run python "$example"
    echo "Completed $example"
    echo "---"
done
```

## Example Output Structure

### Generated Files
All examples create files in the `example_assets/` directory:
```
example_assets/
├── ai/                       # AI-generated images
├── stock/                    # Stock photos
├── downloaded/               # Scraped images
├── cloned/                   # Cloned images
├── catalog.yaml              # YAML catalog
├── catalog.json              # JSON catalog
└── ...
```

### Console Output
Examples provide detailed console output including:
- Progress indicators
- Success/failure messages
- File paths and metadata
- Error messages and debugging
- Statistics and summaries

## Customizing Examples

### Modifying Parameters
Most examples can be customized by editing the parameters:

```python
# Customize AssetRequest
request = AssetRequest(
    description="your custom description",
    width=1920,
    height=1080,
    format="jpg",
    style="your preferred style",
    preferred_sources=["gemini"],
    max_results=5
)
```

### Adding Error Handling
```python
try:
    result = crayon.source(request)
    if result.success:
        print(f"Success: {result.message}")
    else:
        print(f"Failed: {result.message}")
except Exception as e:
    print(f"Error: {str(e)}")
```

### Enabling Debug Mode
```python
# Enable verbose output
crayon = PurpleCrayon(verbose=True)

# Or for specific operations
result = crayon.scrape(url, verbose=True)
```

## Troubleshooting Examples

### Common Issues
1. **API Key Missing**: Check environment variables
2. **Network Errors**: Check internet connection
3. **File Permissions**: Ensure write access to example_assets/
4. **Dependencies**: Install required packages

### Debug Mode
Enable verbose output for detailed debugging:
```python
crayon = PurpleCrayon(verbose=True)
```

### Error Logging
Check console output for detailed error messages and debugging information.

## Contributing Examples

### Adding New Examples
1. Create new file in `examples/` directory
2. Follow existing naming convention
3. Include comprehensive docstring
4. Add error handling and validation
5. Update this index file

### Example Template
```python
#!/usr/bin/env python3
"""
Example: Brief description of functionality
"""

from purplecrayon import PurpleCrayon, AssetRequest

def main():
    # Initialize
    crayon = PurpleCrayon(assets_dir="./example_assets")
    
    # Your example code here
    
    print("✅ Example completed successfully")

if __name__ == "__main__":
    main()
```

## Additional Resources

- **API Documentation**: See individual API docs in `docs/` directory
- **CLI Reference**: Command-line interface documentation
- **Configuration Guide**: Environment and configuration setup
- **Troubleshooting Guide**: Common issues and solutions
