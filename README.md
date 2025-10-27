# PurpleCrayon - AI Graphics Agent

Runs a LangGraph-based agent that searches local assets, stock sites, scrapes the web, generates images using Google Gemini (Nano Banana) and Imagen (via Replicate), and clones images for royalty-free alternatives. It can convert/resize images while preserving originals and maintains a local asset catalog.

## Quickstart

1. Copy `.env.example` to `.env` and fill in keys:
   - `OPENAI_API_KEY` (for reasoning/tools via LangChain)
   - `GEMINI_API_KEY` (for Google Gemini/Nano Banana image generation)
   - `SERPER_API_KEY` (for web search)
   - `FIRECRAWL_API_KEY` (for web scraping)
   - `REPLICATE_API_TOKEN` (for Imagen/Stable Diffusion)
   - `UNSPLASH_ACCESS_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`
   - `LANGCHAIN_API_KEY` (optional, for LangSmith tracing)

2. Install dependencies (with [uv](https://github.com/astral-sh/uv)):

```bash
uv add beautifulsoup4 firecrawl-py google-genai httpx langchain langchain-core \
  langchain-openai langgraph lxml openai pillow playwright pydantic python-dotenv \
  pyyaml replicate
uv run playwright install
```

3. Place your prompt in `input/prompt.md`.

4. (Optional) Review the sample `assets/` directory. It contains a starter `catalog.yaml` and a few example files you can use to validate local catalog lookups.

5. Run the agent:

```bash
# Full workflow (default)
uv run python -m main --mode full

# Only search for stock photos
uv run python -m main --mode search

# Only generate AI images
uv run python -m main --mode generate

# Scrape mode - download all images from a URL
uv run python -m main --mode scrape --url "https://example.com/gallery"

# Clone mode - create royalty-free alternatives to existing images
uv run python -m main --mode clone --source "./assets/downloaded/image.jpg"

# Clone with custom parameters
uv run python -m main --mode clone \
  --source "./assets/downloaded/" \
  --width 1920 --height 1080 \
  --format png --style photorealistic \
  --similarity-threshold 0.7 --max-images 5

# Augment mode - modify existing images with AI
uv run python -m main --mode augment \
  --input "./assets/ai/image.jpg" \
  --augment "add sunset background"

# Augment with custom parameters
uv run python -m main --mode augment \
  --input "./assets/ai/portrait.jpg" \
  --augment "add professional studio lighting" \
  --width 1920 --height 1080 --format png

# Sort and update catalog in assets/ directory
uv run python -m main --sort-catalog

# (Reserved) Additional modes
# `process` and `benchmark` are placeholders for future workflows; the CLI currently reports them as not yet implemented.
```

The output paths will be printed to stdout. Processed images are written to `downloads/` or the file path specified in the prompt.

## Sample Assets & Examples

- `assets/` – contains a starter catalog plus a few example images so you can exercise local lookups immediately.
- `examples/` – runnable scripts that demonstrate the core APIs.

Run them with uv (or your preferred Python entry point):

```bash
# Generate AI artwork with the packaged APIs
uv run python examples/generate_example.py

# Fetch and download stock photos (saves into ./example_assets/stock)
uv run python examples/fetch_example.py

# End-to-end sourcing workflow
uv run python examples/source_example.py

# Clone images for royalty-free alternatives
uv run python examples/clone_example.py

# Simple clone using AssetRequest approach
uv run python examples/simple_clone_assetrequest_example.py

# Augment existing images with AI modifications
uv run python examples/augment_example.py
```

Each script creates an `example_assets/` workspace so it does not interfere with the curated `assets/` directory. Scraping demos are also available:

```bash
# Auto-select an engine (or pass --engine firecrawl/playwright/beautifulsoup)
uv run python examples/scrape_example.py https://example.com/gallery

# Compare scraping engines side-by-side
uv run python examples/scrape_comparison.py https://wordpress.org/showcase/
```

## Using from another project

- Install (editable for development):

```bash
uv pip install -e .
```

- Or install after publishing to an index:

```bash
pip install purple-crayon
```

- Import and use:

```python
from purplecrayon import PurpleCrayon, AssetRequest

crayon = PurpleCrayon(assets_dir="./assets")

# Generate AI images
request = AssetRequest(description="hero background", width=1920, height=1080)
result = crayon.generate(request)

# Clone images for royalty-free alternatives
clone_result = await crayon.clone_async(
    source="./assets/downloaded/image.jpg",
    width=1024,
    height=1024,
    style="photorealistic"
)

# Augment existing images with AI modifications
augment_result = await crayon.augment_async(
    image_path="./assets/ai/image.jpg",
    prompt="add sunset background",
    width=1920,
    height=1080
)
```

- Output locations when installed:
  - Files and folders (downloads/, originals/, processed/, input/, config/, data/) are resolved relative to your current working directory (CWD), not inside site-packages.
  - This means running your script from `/path/to/app` will write to `/path/to/app/downloads/` etc.

- Running examples from source without installing:
  - From repo root, you can run examples by installing editable as above, or uncomment the two sys.path lines at the top of `examples/generate_example.py`.

## Notes
- The catalog is stored in `assets/catalog.yaml`.
- You can override the output path via the "Output Path" in `input/prompt.md`.
- **AI Generation Priority**: Google Gemini (Nano Banana) → Imagen (Replicate)
- Gemini requires `GEMINI_API_KEY` for image generation via the [Google Gemini API](https://ai.google.dev/gemini-api/docs/image-generation#python_2).
- **Debugging**: The agent provides verbose output showing each step and API responses.
- **LangSmith Tracing**: Uncomment the tracing lines in `purplecrayon/agent/graph.py` and add `LANGCHAIN_API_KEY` to enable detailed tracing.

## Output Organization

The agent creates organized folders for easy selection:
- `downloads/stock/` - Stock photos from Unsplash, Pexels, Pixabay
- `downloads/ai/` - AI-generated images from Gemini, Imagen
- `downloads/downloaded/` - Images scraped from URLs (scrape mode)
- `downloads/final/` - Processed images ready for use (resized to your specs)
- `assets/cloned/` - Royalty-free alternatives created from existing images (clone mode)
- `assets/ai/` - Augmented images with AI modifications (augment mode)

This lets you compare stock photos vs AI-generated options vs cloned alternatives and choose your favorite!

**Manual Curation**: Files are saved to `downloads/` subdirectories. You manually move files you like to `assets/` folder. Downloads are cleared between runs.

## Ideal Storage Organization

**For keeping assets you like:**

```
assets/
├── catalog.yaml     # YAML catalog with metadata
├── stock/          # Your curated stock photos
├── ai/             # Your curated AI-generated images  
├── cloned/         # Your curated royalty-free alternatives
├── augmented/      # Your curated augmented images
├── proprietary/    # Customer-provided images
└── downloaded/     # Your curated scraped images
```

**Benefits:**
- **Organized by source** - Easy to find what you need
- **Separate from downloads** - Downloads auto-clean between runs
- **Manual curation** - You choose what to keep
- **Proper naming** - Images automatically renamed with dimensions and content
- **YAML catalog** - Searchable metadata for all assets

## Scrape Mode

Use `--mode scrape --url "URL"` to download all images from a website:
- **Firecrawl Integration**: Uses Firecrawl to extract all images from the URL
- **Output Location**: All images saved to `downloads/downloaded/`
- **No Structure Preservation**: Images are flattened into a single folder
- **Example**: `uv run python -m main --mode scrape --url "https://example.com/gallery"`

## Clone Mode

Use `--mode clone` to create royalty-free alternatives to existing images:
- **AI Vision Analysis**: Uses Gemini Vision API to analyze source images and generate detailed descriptions
- **Style Detection**: Automatically detects and inherits the original image's style (photorealistic, artistic, watercolor, etc.)
- **AI Generation**: Creates new images using Gemini 2.5 Flash Image or Replicate Stable Diffusion
- **Similarity Checking**: Ensures cloned images are sufficiently different from originals using perceptual hashing
- **Batch Processing**: Clone multiple images from a directory
- **Output Location**: Saves cloned images to `assets/cloned/` directory
- **Catalog Integration**: Cloned files are categorized as "ai" source with "ai_clone" provider

### Clone Parameters:
- `--source`: Path to source image file or directory (required)
- `--width`: Desired width for cloned images
- `--height`: Desired height for cloned images  
- `--format`: Output format (png, jpg, webp, etc.)
- `--style`: Style guidance (photorealistic, artistic, watercolor, etc.)
- `--guidance`: Additional guidance for image generation
- `--similarity-threshold`: Maximum similarity threshold (0.0-1.0, default 0.7)
- `--max-images`: Maximum number of images to process (for directory input)

### Examples:
```bash
# Clone single image
uv run python -m main --mode clone --source "./assets/downloaded/image.jpg"

# Clone with custom dimensions and style
uv run python -m main --mode clone \
  --source "./assets/downloaded/image.jpg" \
  --width 1920 --height 1080 \
  --format png --style photorealistic

# Batch clone directory with similarity control
uv run python -m main --mode clone \
  --source "./assets/downloaded/" \
  --similarity-threshold 0.6 --max-images 10
```

## Augment Mode

Use `--mode augment` to modify existing images using AI image-to-image generation:
- **AI Vision Analysis**: Uses Gemini Vision API to analyze source images and generate detailed descriptions
- **Image Upload**: Uploads actual image files to AI engines (Gemini or Replicate)
- **Modification Prompts**: Natural language instructions for changes (add elements, change style, etc.)
- **Style Preservation**: Maintains original composition while applying modifications
- **Batch Processing**: Augment multiple images from a directory
- **Output Location**: Saves augmented images to `assets/ai/` directory
- **Catalog Integration**: Augmented files are categorized as "ai" source with "gemini" or "replicate" provider

### Augment Parameters:
- `--input`: Path to source image file (required)
- `--augment`: Modification prompt (required)
- `--width`: Desired width for augmented images
- `--height`: Desired height for augmented images  
- `--format`: Output format (png, jpg, webp, etc.)
- `--output`: Custom output directory (optional)

### Examples:
```bash
# Augment single image
uv run python -m main --mode augment \
  --input "./assets/ai/portrait.jpg" \
  --augment "add professional studio lighting"

# Augment with custom dimensions and style
uv run python -m main --mode augment \
  --input "./assets/ai/image.jpg" \
  --augment "convert to watercolor painting style" \
  --width 1920 --height 1080 --format png

# Augment with custom output directory
uv run python -m main --mode augment \
  --input "./assets/ai/image.jpg" \
  --augment "add magical forest background" \
  --output "./custom_output"
```

## Sort Catalog Mode

Use `--sort-catalog` to organize and update your assets directory:
- **Rename Images**: Automatically rename files based on content, size, and alpha layer (description_dimensions[_alpha].ext)
- **Content Analysis**: Extracts meaningful descriptions from filenames using pattern matching
- **LLM Analysis**: For unstructured filenames, uses AI to analyze image content and generate descriptive names
- **Size Detection**: Gets actual image dimensions and includes in filename
- **Alpha Detection**: Detects PNG files with transparent pixels and adds _alpha suffix
- **Smart Naming**: Only uses LLM for files that aren't properly structured (saves time and tokens)
- **Update Catalog**: Scan assets directory and update YAML catalog with current files
- **Remove Orphaned Entries**: Remove catalog entries for files that no longer exist
- **Show Statistics**: Display updated catalog statistics
- **Example**: `uv run python -m main --sort-catalog`

## Benchmark Mode

Use `--mode benchmark` to test all available tools and compare results:
- **Stock Photos**: Downloads from Unsplash, Pexels, and Pixabay with source labels
- **AI Generation**: Tests Gemini and Imagen with source labels
- **Filename Format**: `stock_unsplash_0.jpg`, `ai_gemini_0.jpg`, etc.
- **Purpose**: Compare quality and performance of different tools

## Smart Image Selection

The agent now uses intelligent image selection:
1. **Exact size match** - Prioritizes images with your exact dimensions
2. **Aspect ratio match** - Finds images with matching proportions
3. **Orientation match** - Prefers landscape for wallpapers, portrait for social media
4. **Quality preservation** - Downloads highest resolution available
5. **Auto-renaming** - Images renamed with content and dimensions (e.g., `giant_panda_1920x1080.jpg`)

## Auto-Cleanup

- **Downloads cleared** between runs - no accumulation of old files
- **Manual curation** - Move files you like to your `assets/` folder
- **Proper naming** - All images automatically renamed with dimensions and content description

## Documentation

### Comprehensive API Documentation
- **[API Overview](docs/API_OVERVIEW.md)**: Complete overview of all APIs and functionality
- **[Generate API](docs/GENERATE_API.md)**: AI image generation with Gemini and Replicate
- **[Fetch API](docs/FETCH_API.md)**: Stock photo search and download from Unsplash, Pexels, Pixabay
- **[Source API](docs/SOURCE_API.md)**: Unified search across all available sources
- **[Scrape API](docs/SCRAPE_API.md)**: Web scraping with multiple engines and anti-detection
- **[Clone API](docs/CLONE_API.md)**: Create royalty-free alternatives using AI
- **[Catalog API](docs/CATALOG_API.md)**: Asset management and organization system

### Quick Reference
- **API Reference**: All functions and classes are documented in the package `__init__.py`
- **Examples Index**: [Complete examples guide](docs/EXAMPLES_INDEX.md) with detailed usage instructions
- **Examples Directory**: Working code samples in the `examples/` directory
- **CLI Reference**: Command-line interface documentation in this README
