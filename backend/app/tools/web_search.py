"""DuckDuckGo web search and URL content fetching for online mode."""

from __future__ import annotations

import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_FETCH_TIMEOUT = httpx.Timeout(timeout=15.0, connect=5.0)
_MAX_CONTENT_LENGTH = 4000


async def search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search the web via DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of dicts with keys: title, url, snippet.
    """
    try:
        from duckduckgo_search import DDGS  # type: ignore[import-untyped]
    except ImportError:
        logger.error("duckduckgo-search is not installed")
        return []

    results: list[dict[str, str]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as exc:
        logger.error("DuckDuckGo search failed: %s", exc)

    return results


async def fetch_url(url: str) -> str:
    """Fetch a web page and return its plain-text content.

    Strips HTML tags and truncates to a maximum length suitable for
    injection into an LLM context window.

    Args:
        url: The URL to fetch.

    Returns:
        Plain text content, truncated to 4000 characters.
    """
    try:
        async with httpx.AsyncClient(timeout=_FETCH_TIMEOUT) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
    except (httpx.HTTPError, httpx.RequestError) as exc:
        logger.error("Failed to fetch URL %s: %s", url, exc)
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text[:_MAX_CONTENT_LENGTH]
