# PurpleCrayon Scrape API Documentation

## Overview

The Scrape API allows you to download all images from any website using multiple scraping engines. This feature provides robust web scraping capabilities with anti-detection mechanisms, multiple fallback engines, and comprehensive image validation and organization.

## Core Concepts

### Web Scraping Process
1. **URL Processing**: Validates and processes the target URL
2. **Engine Selection**: Chooses appropriate scraping engine
3. **Content Extraction**: Extracts all images from the webpage
4. **Image Discovery**: Finds images in various formats and locations
5. **Download Management**: Downloads images with retry logic
6. **Validation**: Validates downloaded images for quality
7. **Organization**: Saves images to organized directory structure
8. **Catalog Integration**: Adds scraped images to the asset catalog

### Supported Scraping Engines
- **Firecrawl**: AI-powered web scraping with content extraction
- **Playwright**: Browser automation with stealth capabilities
- **BeautifulSoup**: Fast HTML parsing with anti-detection

### Key Features
- **Multi-Engine Support**: Three different scraping approaches
- **Anti-Detection**: Stealth mechanisms to avoid blocking
- **Robust Downloading**: Retry logic and error handling
- **Image Validation**: Quality checks and format validation
- **Batch Processing**: Efficient handling of multiple images
- **Verbose Debugging**: Detailed logging and progress tracking

## API Reference

### PurpleCrayon Class Methods

#### `scrape_async(url, engine=None, verbose=False)`
Asynchronously scrape all images from a URL.

**Parameters:**
- `url` (str): URL to scrape images from
- `engine` (str, optional): Scraping engine to use ("firecrawl", "playwright", "beautifulsoup", or None for auto-fallback)
- `verbose` (bool, optional): Enable verbose debugging output

**Returns:**
- `OperationResult`: Contains success status, message, and list of `ImageResult` objects

**Example:**
```python
from purplecrayon import PurpleCrayon

crayon = PurpleCrayon()

# Scrape images from a website
result = await crayon.scrape_async(
    url="https://example.com/gallery",
    engine="firecrawl",
    verbose=True
)
```

#### `scrape(url, engine=None, verbose=False)`
Synchronous wrapper for `scrape_async()`.

**Parameters:**
- `url` (str): URL to scrape images from
- `engine` (str, optional): Scraping engine to use
- `verbose` (bool, optional): Enable verbose debugging output

**Returns:**
- `OperationResult`: Contains success status, message, and list of `ImageResult` objects

**Example:**
```python
# Synchronous usage
result = crayon.scrape("https://example.com/gallery", verbose=True)
```

### Direct Tool Functions

#### `scrape_website_comprehensive(url, **kwargs)`
Comprehensive scraping with automatic engine selection and fallback.

**Parameters:**
- `url` (str): URL to scrape
- `engine` (str, optional): Preferred engine
- `verbose` (bool, optional): Enable verbose output
- `max_images` (int, optional): Maximum images to download

**Returns:**
- `List[ImageResult]`: List of scraped image results

#### `scrape_with_engine(url, engine, **kwargs)`
Scrape using a specific engine.

**Parameters:**
- `url` (str): URL to scrape
- `engine` (str): Engine to use ("firecrawl", "playwright", "beautifulsoup")
- `verbose` (bool, optional): Enable verbose output

**Returns:**
- `List[ImageResult]`: List of scraped image results

#### `scrape_with_fallback(url, **kwargs)`
Scrape with automatic fallback between engines.

**Parameters:**
- `url` (str): URL to scrape
- `verbose` (bool, optional): Enable verbose output

**Returns:**
- `List[ImageResult]`: List of scraped image results

### Engine-Specific Functions

#### `firecrawl_scrape_images(url, **kwargs)`
Scrape using Firecrawl API.

**Parameters:**
- `url` (str): URL to scrape
- `max_images` (int, optional): Maximum images to download

**Returns:**
- `List[ImageResult]`: List of scraped image results

#### `playwright_scrape(url, **kwargs)`
Scrape using Playwright browser automation.

**Parameters:**
- `url` (str): URL to scrape
- `headless` (bool, optional): Run browser in headless mode

**Returns:**
- `List[ImageResult]`: List of scraped image results

#### `beautifulsoup_scrape(url, **kwargs)`
Scrape using BeautifulSoup HTML parsing.

**Parameters:**
- `url` (str): URL to scrape
- `max_images` (int, optional): Maximum images to download

**Returns:**
- `List[ImageResult]`: List of scraped image results

## CLI Usage

### Basic Scrape Command
```bash
uv run python -m main --mode scrape --url "https://example.com/gallery"
```

### Scrape with Specific Engine
```bash
# Use Firecrawl engine
uv run python -m main --mode scrape --url "https://example.com" --engine firecrawl

# Use Playwright engine
uv run python -m main --mode scrape --url "https://example.com" --engine playwright

# Use BeautifulSoup engine
uv run python -m main --mode scrape --url "https://example.com" --engine beautifulsoup
```

### Scrape with Verbose Output
```bash
uv run python -m main --mode scrape --url "https://example.com" --verbose
```

## Examples

### Example 1: Basic Website Scraping
```python
from purplecrayon import PurpleCrayon

crayon = PurpleCrayon()

# Scrape images from a website
result = crayon.scrape("https://example.com/gallery")

if result.success:
    print(f"Scraped {len(result.images)} images")
    for img in result.images:
        print(f"  - {img.path} ({img.width}x{img.height})")
else:
    print(f"Scraping failed: {result.message}")
```

### Example 2: Engine-Specific Scraping
```python
# Use specific engine
result = await crayon.scrape_async(
    url="https://wordpress.org/showcase/",
    engine="playwright",
    verbose=True
)
```

### Example 3: Direct Tool Usage
```python
from purplecrayon.tools.scraping_tools import scrape_website_comprehensive

# Use comprehensive scraping tool
images = scrape_website_comprehensive(
    url="https://example.com/gallery",
    verbose=True,
    max_images=50
)

for img in images:
    print(f"Found: {img.path}")
```

### Example 4: Engine Comparison
```python
from purplecrayon.tools.scraping_tools import (
    firecrawl_scrape_images,
    playwright_scrape,
    beautifulsoup_scrape
)

url = "https://example.com/gallery"

# Compare different engines
firecrawl_results = firecrawl_scrape_images(url)
playwright_results = playwright_scrape(url)
beautifulsoup_results = beautifulsoup_scrape(url)

print(f"Firecrawl: {len(firecrawl_results)} images")
print(f"Playwright: {len(playwright_results)} images")
print(f"BeautifulSoup: {len(beautifulsoup_results)} images")
```

## Output Organization

### File Structure
```
assets/
├── downloaded/                # Scraped images directory
│   ├── scraped_fc_a_123456.jpg    # Firecrawl image
│   ├── scraped_pw_b_789012.jpg    # Playwright image
│   ├── scraped_bs_c_345678.jpg    # BeautifulSoup image
│   └── ...
├── catalog.yaml              # Updated catalog with scraped entries
└── ...
```

### Naming Convention
- **Firecrawl**: `scraped_fc_{id}.{format}`
- **Playwright**: `scraped_pw_{id}.{format}`
- **BeautifulSoup**: `scraped_bs_{id}.{format}`

### Catalog Integration
Scraped images are automatically added to the catalog with:
- `source`: "downloaded"
- `provider`: "firecrawl", "playwright", or "beautifulsoup"
- `description`: Extracted from image alt text or filename
- `width`/`height`: Actual dimensions
- `format`: File format
- `path`: Relative path to scraped file
- `url`: Original image URL

## Engine Comparison

### Firecrawl
- **Best For**: Complex websites, JavaScript-heavy sites
- **Features**: AI-powered content extraction, handles dynamic content
- **Performance**: Medium speed, high accuracy
- **Limitations**: Requires API key, rate limits

### Playwright
- **Best For**: Modern websites, SPAs, complex interactions
- **Features**: Full browser automation, stealth mode, handles JavaScript
- **Performance**: Slower but most comprehensive
- **Limitations**: Requires browser installation, more resource intensive

### BeautifulSoup
- **Best For**: Simple websites, fast scraping
- **Features**: Fast HTML parsing, lightweight
- **Performance**: Fastest, good for simple sites
- **Limitations**: No JavaScript support, basic anti-detection

## Anti-Detection Features

### User Agent Rotation
- **Random User Agents**: Rotates between different browser user agents
- **Realistic Headers**: Uses common browser headers
- **Referrer Spoofing**: Sets appropriate referrer headers

### Request Patterns
- **Random Delays**: Adds random delays between requests
- **Rate Limiting**: Respects website rate limits
- **Session Management**: Maintains consistent sessions

### Stealth Mode (Playwright)
- **Browser Fingerprinting**: Masks browser characteristics
- **WebRTC Blocking**: Prevents WebRTC leaks
- **Canvas Fingerprinting**: Randomizes canvas fingerprints

## Error Handling

### Common Errors
- **Network Issues**: Connection timeouts, DNS failures
- **Rate Limiting**: Too many requests to target site
- **Access Denied**: 403 Forbidden, blocked IP
- **Invalid URLs**: Malformed or unreachable URLs
- **No Images Found**: No images on the target page

### Error Recovery
- **Engine Fallback**: Automatically tries other engines
- **Retry Logic**: Built-in retry for transient failures
- **Partial Results**: Returns available images even if some fail
- **Detailed Logging**: Comprehensive error reporting

## Performance Considerations

### Optimization Tips
- Use appropriate engine for website type
- Enable verbose mode for debugging
- Set reasonable image limits
- Monitor network usage and rate limits

### Resource Usage
- **Memory**: Efficient image processing with streaming
- **Storage**: Images saved to organized directory structure
- **Bandwidth**: Optimized downloading with progress tracking
- **CPU**: Multi-threaded processing for efficiency

## Configuration

### Environment Variables
```bash
# Required for Firecrawl
FIRECRAWL_API_KEY=your_firecrawl_key

# Optional for enhanced functionality
LANGCHAIN_API_KEY=your_langchain_key  # For tracing
```

### Engine Configuration
```python
# Customize scraping behavior
result = crayon.scrape(
    url="https://example.com",
    engine="playwright",  # Specific engine
    verbose=True  # Enable debugging
)
```

## Troubleshooting

### Common Issues
1. **No Images Found**: Check if site has images, try different engine
2. **Access Denied**: Try different engine or add delays
3. **Slow Performance**: Use BeautifulSoup for simple sites
4. **JavaScript Issues**: Use Playwright for dynamic content

### Debug Mode
Enable verbose output:
```python
result = crayon.scrape(url, verbose=True)
```

This will show detailed information about the scraping process, including:
- Engine selection and fallback
- Image discovery process
- Download progress and errors
- Validation results

## Best Practices

### Website Selection
- Choose appropriate engine for website type
- Test with different engines for best results
- Respect website terms of service
- Use reasonable rate limits

### Performance
- Use BeautifulSoup for simple, static sites
- Use Playwright for complex, dynamic sites
- Use Firecrawl for AI-powered extraction
- Monitor and respect rate limits

### Legal Compliance
- Respect robots.txt and terms of service
- Use appropriate rate limiting
- Don't overload target servers
- Consider copyright and licensing issues
