"""Tests for the web scraper utilities."""

from __future__ import annotations

import responses

from src.scraper import (
    collect_pages,
    extract_links,
    extract_metadata,
    extract_text,
    fetch_page,
)

SAMPLE_HTML = """
<html>
<head>
  <title>Acme Corp</title>
  <meta name="description" content="We build rockets.">
  <meta property="og:title" content="Acme Corp">
</head>
<body>
  <script>var x = 1;</script>
  <h1>Welcome to Acme</h1>
  <p>We build the best rockets in the world.</p>
  <a href="/about">About</a>
  <a href="https://other.com/page">External</a>
  <a href="/contact">Contact</a>
</body>
</html>
"""


def test_extract_text_removes_scripts():
    text = extract_text(SAMPLE_HTML)
    assert "var x = 1" not in text
    assert "Welcome to Acme" in text
    assert "best rockets" in text


def test_extract_text_collapses_whitespace():
    text = extract_text(SAMPLE_HTML)
    assert "  " not in text


def test_extract_metadata_title():
    meta = extract_metadata(SAMPLE_HTML)
    assert meta["title"] == "Acme Corp"


def test_extract_metadata_description():
    meta = extract_metadata(SAMPLE_HTML)
    assert meta["description"] == "We build rockets."


def test_extract_metadata_og_title():
    meta = extract_metadata(SAMPLE_HTML)
    assert meta["og:title"] == "Acme Corp"


def test_extract_links_returns_internal_only():
    links = extract_links(SAMPLE_HTML, "https://acme.com")
    assert "https://acme.com/about" in links
    assert "https://acme.com/contact" in links
    # External link should be excluded.
    assert "https://other.com/page" not in links


def test_extract_links_deduplicates():
    html = '<a href="/page">A</a><a href="/page">B</a>'
    links = extract_links(html, "https://example.com")
    assert links.count("https://example.com/page") == 1


@responses.activate
def test_fetch_page_success():
    responses.add(responses.GET, "https://acme.com", body="<html>Hello</html>", status=200)
    result = fetch_page("https://acme.com")
    assert result == "<html>Hello</html>"


@responses.activate
def test_fetch_page_http_error_returns_none():
    responses.add(responses.GET, "https://acme.com/404", status=404)
    result = fetch_page("https://acme.com/404")
    assert result is None


@responses.activate
def test_fetch_page_connection_error_returns_none():
    import requests as req_lib
    responses.add(
        responses.GET,
        "https://broken.example.com",
        body=req_lib.exceptions.ConnectionError("conn err"),
    )
    result = fetch_page("https://broken.example.com")
    assert result is None


@responses.activate
def test_collect_pages_returns_homepage():
    responses.add(responses.GET, "https://acme.com", body=SAMPLE_HTML, status=200)
    # All sub-pages return 404 so only homepage is collected.
    for path in ["/about", "/about-us", "/products", "/services", "/contact"]:
        responses.add(responses.GET, f"https://acme.com{path}", status=404)

    pages = collect_pages("https://acme.com", max_pages=5, timeout=5)
    assert "https://acme.com" in pages
    assert "Welcome to Acme" in pages["https://acme.com"]


@responses.activate
def test_collect_pages_respects_max_pages():
    responses.add(responses.GET, "https://acme.com", body=SAMPLE_HTML, status=200)
    for path in ["/about", "/about-us", "/products", "/services", "/contact"]:
        responses.add(responses.GET, f"https://acme.com{path}", body="<html>Page</html>", status=200)

    pages = collect_pages("https://acme.com", max_pages=2, timeout=5)
    assert len(pages) <= 2
