# PurpleCrayon - AI Graphics Agent

Runs a LangGraph-based agent that searches local assets, stock sites, scrapes the web, and generates images using Google Gemini (Nano Banana) and Imagen (via Replicate). It can convert/resize images while preserving originals and maintains a local asset catalog.

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

4. Run the agent:

```bash
# Full workflow (default)
uv run python -m main --mode full

# Only search for stock photos
uv run python -m main --mode search

# Only generate AI images
uv run python -m main --mode generate

# Scrape mode - download all images from a URL
uv run python -m main --mode scrape --url "https://example.com/gallery"

# Sort and update catalog in assets/ directory
uv run python -m main --sort-catalog

# (Reserved) Additional modes
# `process` and `benchmark` are placeholders for future workflows; the CLI currently reports them as not yet implemented.
```

The output paths will be printed to stdout. Processed images are written to `downloads/` or the file path specified in the prompt.

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
request = AssetRequest(description="hero background", width=1920, height=1080)
result = crayon.generate(request)
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

This lets you compare stock photos vs AI-generated options and choose your favorite!

**Manual Curation**: Files are saved to `downloads/` subdirectories. You manually move files you like to `assets/` folder. Downloads are cleared between runs.

## Ideal Storage Organization

**For keeping assets you like:**

```
assets/
├── catalog.yaml     # YAML catalog with metadata
├── stock/          # Your curated stock photos
├── ai/             # Your curated AI-generated images  
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
