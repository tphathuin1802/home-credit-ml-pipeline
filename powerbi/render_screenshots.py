"""Render preview.html to PNG screenshots (one per page) using Playwright."""

from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "powerbi" / "preview.html").as_uri()
OUT_DIR = ROOT / "powerbi" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1400, "height": 1100},
                                        device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto(HTML, wait_until="networkidle")
        # Wait a bit for fonts
        await page.wait_for_timeout(800)
        # Take full screenshot
        full = OUT_DIR / "dashboard_full.png"
        await page.screenshot(path=str(full), full_page=True)
        print(f"[OK] {full}")
        # Per-page screenshots
        sections = await page.query_selector_all("section.page")
        for i, sec in enumerate(sections, start=1):
            try:
                name = await sec.query_selector_eval(".page-name", "el => el.textContent")
                slug = name.split("·")[0].strip().replace(" ", "_").lower() if "·" in name else f"page_{i}"
            except Exception:
                slug = f"page_{i}"
            out = OUT_DIR / f"page_{i}_{slug}.png"
            await sec.screenshot(path=str(out))
            print(f"[OK] {out}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
