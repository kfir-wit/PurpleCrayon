from __future__ import annotations

from typing import List, Optional, TypedDict


class GraphicsAgentState(TypedDict, total=False):
    prompt: str
    output_path: Optional[str]
    found_local_assets: List[dict]
    search_results: List[dict]
    generated_images: List[dict]
    stock_files: List[str]  # Stock photo downloads
    ai_files: List[str]     # AI-generated files
    downloaded_files: List[str]
    processed_files: List[str]
    final_output: Optional[str]
    messages: List[dict]
