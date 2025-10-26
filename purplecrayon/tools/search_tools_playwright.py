from __future__ import annotations

import asyncio
from typing import Any, Dict

from playwright.async_api import async_playwright


async def playwright_browse(url: str, action: str = "screenshot", path: str | None = None) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        result: Dict[str, Any] = {"url": url}
        if action == "screenshot":
            fp = path or "downloads/page.png"
            await page.screenshot(path=fp, full_page=True)
            result["screenshot"] = fp
        elif action == "pdf":
            fp = path or "downloads/page.pdf"
            await page.pdf(path=fp, print_background=True)
            result["pdf"] = fp
        result["title"] = await page.title()
        await browser.close()
        return result
