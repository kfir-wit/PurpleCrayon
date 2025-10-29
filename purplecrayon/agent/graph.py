from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .state import GraphicsAgentState
from ..tools.catalog_tools import search_local_assets, index_asset
from ..tools.file_tools import download_file
from ..tools.stock_photo_tools import search_unsplash, search_pexels, search_pixabay
from ..tools.smart_selection_tools import select_best_images, extract_size_from_prompt
from ..tools.image_renaming_tools import rename_images_in_directory, scan_and_rename_assets
from ..tools.asset_curation_tools import curate_downloads_to_assets
from ..tools.image_validation_tools import validate_all_images
from ..tools.search_tools import serper_search
from ..tools.ai_generation_tools import generate_with_replicate_async, generate_with_gemini_async
from ..tools.image_processing_tools import convert_image, resize_image
from ..utils.config import (
    INPUT_PROMPT_PATH,
    DOWNLOADS_DIR,
    PROCESSED_DIR,
    init_environment,
)


def normalize_image_extension(filename: str) -> str:
    """Normalize image filename to use .jpg for JPEG files."""
    if filename.lower().endswith('.jpeg'):
        return filename[:-5] + '.jpg'
    return filename

# Create subdirectories for organized output
STOCK_DIR = DOWNLOADS_DIR / "stock"
AI_DIR = DOWNLOADS_DIR / "ai"
FINAL_DIR = DOWNLOADS_DIR / "final"


def read_prompt_file() -> str:
    if INPUT_PROMPT_PATH.exists():
        return INPUT_PROMPT_PATH.read_text(encoding="utf-8")
    return ""


def parse_output_path_from_prompt(prompt_md: str) -> str | None:
    lines = prompt_md.splitlines()
    for i, line in enumerate(lines):
        line_lower = line.strip().lower()
        if line_lower.startswith("**output path:**"):
            # Check if path is on the same line after the colon
            path = line.split(":", 1)[-1].strip()
            if path and path != "**":
                return path
            
            # Check if path is on the next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith("**"):
                    return next_line
    return None


def extract_description_from_prompt(prompt_md: str) -> str:
    """Extract the description from the markdown prompt."""
    lines = prompt_md.splitlines()
    
    # Look for **Description:** line
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("**description:**"):
            # Get the next line(s) until we hit another ** or empty line
            description_parts = []
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if not next_line:  # Empty line
                    break
                if next_line.startswith("**"):  # Next section
                    break
                description_parts.append(next_line)
            
            if description_parts:
                return " ".join(description_parts).strip()
    
    # Fallback: return first non-empty line that doesn't start with **
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("**") and not line.startswith("-"):
            return line
    return "graphic image"


async def node_read_prompt(state: GraphicsAgentState) -> GraphicsAgentState:
    print("🔍 Reading prompt file...")
    raw = read_prompt_file()
    out_path = parse_output_path_from_prompt(raw)
    print(f"📝 Prompt: {raw[:100]}...")
    print(f"📁 Output path: {out_path}")
    return {**state, "prompt": raw, "output_path": out_path}


async def node_search_local(state: GraphicsAgentState) -> GraphicsAgentState:
    print("🔍 Searching local assets...")
    query = state.get("prompt", "")
    description = extract_description_from_prompt(query)
    print(f"📝 Searching for: '{description}'")
    matches = search_local_assets(query=description)
    print(f"📦 Found {len(matches)} local assets")
    return {**state, "found_local_assets": matches}


async def node_search_online(state: GraphicsAgentState) -> GraphicsAgentState:
    print("🌐 Searching online for stock photos...")
    prompt = state.get("prompt", "")
    # Extract clean description for API calls
    description = extract_description_from_prompt(prompt)
    print(f"📝 Searching for: '{description}'")
    
    # Extract target size from prompt
    target_width, target_height = extract_size_from_prompt(prompt)
    print(f"🎯 Target size: {target_width}x{target_height}")
    
    # Stock photo APIs with size preference
    print("🔍 Checking Unsplash, Pexels, Pixabay...")
    target_size = f"{target_width}x{target_height}"
    
    # Create enhanced query with requirements
    clean_query = description.split('.')[0] if '.' in description else description
    
    # Extract requirements from prompt
    requirements = []
    for line in prompt.splitlines():
        if line.strip().lower().startswith("**requirements:**"):
            # Get next lines until another ** section
            for j in range(prompt.splitlines().index(line) + 1, len(prompt.splitlines())):
                req_line = prompt.splitlines()[j].strip()
                if not req_line or req_line.startswith("**"):
                    break
                if req_line.startswith("-"):
                    requirements.append(req_line[1:].strip())
    
    # Combine description with requirements
    enhanced_query = clean_query
    if requirements:
        req_text = ", ".join(requirements)
        enhanced_query = f"{clean_query}, {req_text}"
    
    print(f"🔍 Using enhanced query: '{enhanced_query}'")
    
    uns, pex, pix = await asyncio.gather(
        search_unsplash(enhanced_query, 10, target_size),
        search_pexels(enhanced_query, 10, target_size),
        search_pixabay(enhanced_query, 10, target_size),
    )
    # Serper results (metadata only)
    search = await serper_search(description, 5)
    
    # Add source labels for benchmark mode
    for item in uns:
        item["source_label"] = "unsplash"
    for item in pex:
        item["source_label"] = "pexels"
    for item in pix:
        item["source_label"] = "pixabay"
    
    all_results: List[Dict[str, Any]] = [
        *uns,
        *pex,
        *pix,
    ]
    
    # Smart selection based on size and aspect ratio
    print(f"📸 Found {len(all_results)} total stock photos")
    selected_results = select_best_images(all_results, target_width, target_height, max_images=5)
    print(f"🎯 Selected {len(selected_results)} best matches")
    
    print(f"🔍 Found {len(search)} web search results")
    return {**state, "search_results": selected_results, "messages": (state.get("messages") or []) + [{"serper": search}]}


async def node_generate(state: GraphicsAgentState) -> GraphicsAgentState:
    print("🤖 Generating AI images...")
    prompt = state.get("prompt", "")
    # Extract clean description for generation
    description = extract_description_from_prompt(prompt)
    print(f"📝 Generating: '{description}'")
    
    gen: List[Dict[str, Any]] = []
    
    # Try Gemini first (Nano Banana)
    print("🧠 Trying Google Gemini...")
    try:
        gemini = await generate_with_gemini_async(description)
        print(f"🔍 Gemini result: {gemini.get('status')}")
        if gemini.get("status") == "succeeded" and gemini.get("image_data"):
            print("✅ Gemini generated image successfully!")
            gemini["source_label"] = "gemini"
            gen.append(gemini)
        else:
            print(f"❌ Gemini failed: {gemini.get('reason', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Gemini exception: {e}")
    
    # Try Imagen as fallback
    if not gen:
        print("🖼️ Trying Imagen...")
        try:
            im = await generate_with_replicate_async(description)
            print(f"🔍 Imagen result: {im.get('status')}")
            if im.get("url"):
                print("✅ Imagen generated image successfully!")
                im["source_label"] = "imagen"
                gen.append(im)
            else:
                print(f"❌ Imagen failed: {im.get('reason', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Imagen exception: {e}")
    
    print(f"🎯 Total AI images generated: {len(gen)}")
    return {**state, "generated_images": gen}


async def node_download(state: GraphicsAgentState) -> GraphicsAgentState:
    print("📥 Downloading images...")
    # Ensure directories exist
    STOCK_DIR.mkdir(parents=True, exist_ok=True)
    AI_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    
    stock_files: List[str] = []
    ai_files: List[str] = []
    
    # Download stock photos to stock/ directory
    search_results = state.get("search_results", [])
    print(f"📸 Downloading {len(search_results)} stock photos...")
    for i, item in enumerate(search_results[:3]):  # Take top 3
        if item.get("url"):
            try:
                # Include source label in filename for benchmark mode
                source_label = item.get("source_label", "unknown")
                target = STOCK_DIR / normalize_image_extension(f"stock_{source_label}_{i}.jpg")
                print(f"  📥 Downloading stock {i} ({source_label}): {item.get('url', 'No URL')[:50]}...")
                p = await download_file(item["url"], str(target))
                stock_files.append(p)
                print(f"  ✅ Saved to: {p}")
            except Exception as e:
                print(f"  ❌ Failed to download stock {i}: {e}")
                continue
    
    # Save AI-generated images to ai/ directory
    generated_images = state.get("generated_images", [])
    print(f"🤖 Processing {len(generated_images)} AI images...")
    for i, item in enumerate(generated_images):
        try:
            source_label = item.get("source_label", "unknown")
            if item.get("url"):  # URL-based (Imagen)
                target = AI_DIR / normalize_image_extension(f"ai_{source_label}_{i}.jpg")
                print(f"  📥 Downloading AI {i} ({source_label}): {item.get('url', 'No URL')[:50]}...")
                p = await download_file(item["url"], str(target))
                ai_files.append(p)
                print(f"  ✅ Saved to: {p}")
            elif item.get("image_data"):  # Base64 data (Gemini)
                import base64
                from ..tools.file_tools import save_file
                
                target = AI_DIR / f"ai_{source_label}_{i}.png"  # Use PNG for Gemini
                print(f"  💾 Saving {source_label} {i} (base64 data)...")
                
                # Gemini returns data as bytes, not base64 string
                if isinstance(item["image_data"], str):
                    image_bytes = base64.b64decode(item["image_data"])
                else:
                    # Already bytes from Gemini
                    image_bytes = item["image_data"]
                
                p = save_file(image_bytes, str(target))
                ai_files.append(p)
                print(f"  ✅ Saved to: {p}")
        except Exception as e:
            print(f"  ❌ Failed to save AI {i}: {e}")
            continue
    
    print(f"📊 Downloaded {len(stock_files)} stock photos, {len(ai_files)} AI images")
    
    # Validate all downloaded images
    print("🔍 Validating downloaded images with LLM...")
    description = extract_description_from_prompt(state.get("prompt", ""))
    all_files = stock_files + ai_files
    
    if all_files:
        validation_results = validate_all_images(all_files, description)
        
        print("📊 Image Validation Results:")
        for i, result in enumerate(validation_results[:5]):  # Show top 5
            score = result.get("match_score", 0)
            confidence = result.get("confidence", "none")
            desc = result.get("description", "Unknown")[:50]
            path = Path(result.get("path", "")).name
            
            print(f"  {i+1}. {path} - Score: {score:.2f} ({confidence})")
            print(f"     Shows: {desc}...")
            if result.get("reasoning"):
                print(f"     Reason: {result.get('reasoning')[:100]}...")
        
        # Update state with validation results
        state["validation_results"] = validation_results
    
    return {
        **state, 
        "stock_files": stock_files,
        "ai_files": ai_files,
        "downloaded_files": stock_files + ai_files
    }


async def node_process(state: GraphicsAgentState) -> GraphicsAgentState:
    """Process images to final format and size, save to final/ directory."""
    processed: List[str] = []
    
    # Process stock photos
    for p in (state.get("stock_files") or []):
        try:
            # Extract filename and create final path
            filename = Path(p).stem + "_stock.jpg"
            final_path = FINAL_DIR / filename
            out = resize_image(p, 1920, 1080, mode="crop", keep_aspect=True, output_path=str(final_path))
            processed.append(out)
        except Exception:
            continue
    
    # Process AI images
    for p in (state.get("ai_files") or []):
        try:
            # Extract filename and create final path
            filename = Path(p).stem + "_ai.jpg"
            final_path = FINAL_DIR / filename
            out = resize_image(p, 1920, 1080, mode="crop", keep_aspect=True, output_path=str(final_path))
            processed.append(out)
        except Exception:
            continue
    
    # If user specified a custom output path, copy the first processed image there
    custom_path = state.get("output_path")
    if custom_path and processed:
        try:
            from ..tools.file_tools import copy_file
            copy_file(processed[0], custom_path)
        except Exception:
            pass
    
    return {**state, "processed_files": processed, "final_output": custom_path or (processed[0] if processed else None)}


async def node_catalog(state: GraphicsAgentState) -> GraphicsAgentState:
    for p in (state.get("processed_files") or []):
        try:
            index_asset(p, source="processed", description="processed image")
        except Exception:
            continue
    return state


def build_graph(mode: str = "full") -> StateGraph:
    graph = StateGraph(GraphicsAgentState)
    
    # Always start with reading the prompt
    graph.add_node("read_prompt", node_read_prompt)
    
    if mode in ["full", "search", "benchmark"]:
        graph.add_node("search_local", node_search_local)
        graph.add_node("search_online", node_search_online)
    
    if mode in ["full", "generate", "benchmark"]:
        graph.add_node("generate", node_generate)
    
    if mode in ["full", "search", "generate", "benchmark"]:
        graph.add_node("download", node_download)
    
    if mode in ["full", "process", "benchmark"]:
        graph.add_node("process", node_process)
    
    if mode == "full":
        graph.add_node("catalog", node_catalog)
    
    # Set up the flow based on mode
    graph.set_entry_point("read_prompt")
    
    if mode == "full":
        graph.add_edge("read_prompt", "search_local")
        graph.add_edge("search_local", "search_online")
        graph.add_edge("search_online", "generate")
        graph.add_edge("generate", "download")
        graph.add_edge("download", "process")
        graph.add_edge("process", "catalog")
        graph.add_edge("catalog", END)
    elif mode == "search":
        graph.add_edge("read_prompt", "search_local")
        graph.add_edge("search_local", "search_online")
        graph.add_edge("search_online", "download")
        graph.add_edge("download", END)
    elif mode == "generate":
        graph.add_edge("read_prompt", "generate")
        graph.add_edge("generate", "download")
        graph.add_edge("download", END)
    elif mode == "process":
        graph.add_edge("read_prompt", "process")
        graph.add_edge("process", END)
    elif mode == "benchmark":
        graph.add_edge("read_prompt", "search_local")
        graph.add_edge("search_local", "search_online")
        graph.add_edge("search_online", "generate")
        graph.add_edge("generate", "download")
        graph.add_edge("download", "process")
        graph.add_edge("process", END)
    
    return graph


async def run_agent(mode: str = "full", url: str = None) -> GraphicsAgentState:
    init_environment()
    
    # Clean up downloads directory before starting
    print("🧹 Cleaning up downloads directory...")
    for dir_path in [STOCK_DIR, AI_DIR, FINAL_DIR]:
        if dir_path.exists():
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                    except Exception:
                        pass
    
    # Create downloaded directory for scrape mode
    DOWNLOADED_DIR = Path("downloads/downloaded")
    if DOWNLOADED_DIR.exists():
        # Remove all files in downloaded directory
        for file_path in DOWNLOADED_DIR.iterdir():
            if file_path.is_file():
                try:
                    file_path.unlink()
                except Exception:
                    pass
        # Remove directory and recreate to ensure clean state
        try:
            DOWNLOADED_DIR.rmdir()
        except Exception:
            pass
    DOWNLOADED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Handle scrape mode
    if mode == "scrape":
        if not url:
            raise ValueError("URL is required for scrape mode")
        
        print(f"🕷️ Scraping images from: {url}")
        from ..tools.search_tools import firecrawl_scrape
        
        # Scrape the URL for images
        scrape_result = await firecrawl_scrape(url)
        if scrape_result.get("status") == "success":
            images = scrape_result.get("images", [])
            print(f"📸 Found {len(images)} images to download")
            
            downloaded_files = []
            for i, image_url in enumerate(images):
                try:
                    filename = f"scraped_{i}.jpg"  # Default to jpg
                    if image_url.lower().endswith('.png'):
                        filename = f"scraped_{i}.png"
                    elif image_url.lower().endswith('.gif'):
                        filename = f"scraped_{i}.gif"
                    elif image_url.lower().endswith('.ico'):
                        filename = f"scraped_{i}.ico"
                    elif image_url.lower().endswith('.jpeg'):
                        filename = f"scraped_{i}.jpg"  # Normalize JPEG to JPG
                    
                    target_path = DOWNLOADED_DIR / filename
                    print(f"  📥 Downloading: {filename}")
                    
                    # Download the image
                    from ..tools.file_tools import download_file
                    downloaded_path = await download_file(image_url, str(target_path))
                    downloaded_files.append(downloaded_path)
                    print(f"  ✅ Saved: {downloaded_path}")
                    
                except Exception as e:
                    print(f"  ❌ Failed to download {image_url}: {e}")
                    continue
            
            # Clean up corrupted images
            print("🔍 Validating downloaded images...")
            from ..tools.image_validation_tools import cleanup_corrupted_images
            cleanup_stats = cleanup_corrupted_images(str(DOWNLOADED_DIR))
            print(f"📊 Validation results: {cleanup_stats['valid']} valid, {cleanup_stats['corrupted']} corrupted files removed")
            
            # Update downloaded_files list to only include remaining valid files
            remaining_files = []
            for file_path in DOWNLOADED_DIR.iterdir():
                if file_path.is_file():
                    remaining_files.append(str(file_path))
            
            result = {
                "downloaded_files": remaining_files,
                "final_output": str(DOWNLOADED_DIR) if remaining_files else None
            }
        else:
            print(f"❌ Scraping failed: {scrape_result.get('error', 'Unknown error')}")
            result = {"downloaded_files": [], "final_output": None}
    else:
        g = build_graph(mode)
        app = g.compile()
        result: GraphicsAgentState = await app.ainvoke({})
    
    # Validate and clean up corrupted images
    print("🔍 Validating downloaded images...")
    from ..tools.image_validation_tools import cleanup_corrupted_images
    
    for dir_path in [STOCK_DIR, AI_DIR, FINAL_DIR]:
        if dir_path.exists():
            cleanup_stats = cleanup_corrupted_images(str(dir_path))
            if cleanup_stats['corrupted'] > 0:
                print(f"📊 {dir_path.name}: {cleanup_stats['valid']} valid, {cleanup_stats['corrupted']} corrupted files removed")
    
    # Update catalog from assets directory
    assets_dir = Path("assets")
    if assets_dir.exists():
        from ..tools.asset_management_tools import AssetCatalog
        catalog_path = assets_dir / "catalog.yaml"
        catalog = AssetCatalog(catalog_path)
        catalog.update_catalog_from_assets(assets_dir)
    
    # Note: Files remain in downloads/ for manual curation
    print("📁 Files saved to downloads/ - manually move to assets/ if you want to keep them")
    print("💡 Downloads will be cleared on next run")
    
    return result
