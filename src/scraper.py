"""Utilities for fetching and parsing web pages."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Pages worth visiting beyond the homepage.
RESEARCH_PATHS = ["/about", "/about-us", "/products", "/services", "/contact"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AccountResearcher/1.0; "
        "+https://github.com/NicolasSpillemaeckers/AccountResearcher)"
    )
}


def fetch_page(url: str, timeout: int = 10) -> str | None:
    """Return the text content of *url*, or *None* if the request fails."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def extract_text(html: str) -> str:
    """Return the visible text of an HTML document, collapsed to single spaces."""
    soup = BeautifulSoup(html, "lxml")
    # Remove script / style noise.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def extract_metadata(html: str) -> dict[str, str]:
    """Return a dict of meta-tag content keyed by name/property."""
    soup = BeautifulSoup(html, "lxml")
    meta: dict[str, str] = {}
    title_tag = soup.find("title")
    if title_tag:
        meta["title"] = title_tag.get_text(strip=True)
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property") or ""
        content = tag.get("content") or ""
        if name and content:
            meta[name.lower()] = content
    return meta


def extract_links(html: str, base_url: str) -> list[str]:
    """Return absolute internal links found in *html*."""
    soup = BeautifulSoup(html, "lxml")
    base = urlparse(base_url)
    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc == base.netloc and parsed.scheme in ("http", "https"):
            links.append(absolute)
    return list(dict.fromkeys(links))  # deduplicate, preserve order


def collect_pages(base_url: str, max_pages: int = 5, timeout: int = 10) -> dict[str, str]:
    """
    Fetch the homepage plus a small set of well-known sub-pages.

    Returns a mapping of *url -> visible text*.
    """
    pages: dict[str, str] = {}

    # Always start with the homepage.
    homepage_html = fetch_page(base_url, timeout=timeout)
    if homepage_html:
        pages[base_url] = extract_text(homepage_html)

    # Try common research paths.
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"

    for path in RESEARCH_PATHS:
        if len(pages) >= max_pages:
            break
        candidate = root + path
        if candidate in pages:
            continue
        html = fetch_page(candidate, timeout=timeout)
        if html:
            pages[candidate] = extract_text(html)

    return pages
