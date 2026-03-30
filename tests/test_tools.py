"""Tests for web research tools."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.tools import extract_links, fetch_linkedin_page, fetch_webpage

_SAMPLE_HTML = """
<html>
<head>
  <title>Acme Corp - Cloud Solutions</title>
  <meta name="description" content="Acme Corp provides cloud solutions for enterprise.">
</head>
<body>
  <nav>
    <a href="/about">About Us</a>
    <a href="/products">Products</a>
    <a href="/pricing">Pricing</a>
    <a href="/contact">Contact</a>
    <a href="/team">Our Team</a>
    <a href="/blog">Blog</a>
  </nav>
  <main>
    <h1>Welcome to Acme Corp</h1>
    <p>We help enterprises scale with our cloud platform.</p>
  </main>
  <script>alert("ignored")</script>
  <style>.ignored { color: red; }</style>
</body>
</html>
"""

_LINKEDIN_HTML = """
<html>
<head>
  <title>Acme Corp | LinkedIn</title>
  <meta property="og:title" content="Acme Corp | LinkedIn">
  <meta property="og:description"
        content="Acme Corp is a cloud software company with 500 employees.">
  <meta property="og:image" content="https://media.licdn.com/acme-logo.png">
</head>
<body>
  <p>Sign in to view full profile</p>
</body>
</html>
"""


def _make_response(html: str, url: str = "https://acme.com") -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.url = url
    resp.raise_for_status.return_value = None
    return resp


class TestFetchWebpage:
    def test_returns_title_and_description(self):
        with patch("src.tools.requests.get", return_value=_make_response(_SAMPLE_HTML)):
            result = fetch_webpage.invoke("https://acme.com")
        assert "Acme Corp - Cloud Solutions" in result
        assert "cloud solutions for enterprise" in result

    def test_strips_scripts_and_styles(self):
        with patch("src.tools.requests.get", return_value=_make_response(_SAMPLE_HTML)):
            result = fetch_webpage.invoke("https://acme.com")
        assert "alert" not in result
        assert ".ignored" not in result

    def test_includes_visible_text(self):
        with patch("src.tools.requests.get", return_value=_make_response(_SAMPLE_HTML)):
            result = fetch_webpage.invoke("https://acme.com")
        assert "Welcome to Acme Corp" in result
        assert "cloud platform" in result

    def test_timeout_returns_error_message(self):
        with patch("src.tools.requests.get", side_effect=requests.exceptions.Timeout):
            result = fetch_webpage.invoke("https://acme.com")
        assert "Error" in result
        assert "timed out" in result

    def test_connection_error_returns_error_message(self):
        with patch("src.tools.requests.get", side_effect=requests.exceptions.ConnectionError):
            result = fetch_webpage.invoke("https://acme.com")
        assert "Error" in result
        assert "connect" in result.lower()

    def test_http_error_returns_status_code(self):
        error_response = MagicMock()
        error_response.status_code = 404
        http_error = requests.exceptions.HTTPError(response=error_response)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = http_error
        with patch("src.tools.requests.get", return_value=mock_resp):
            result = fetch_webpage.invoke("https://acme.com/missing")
        assert "404" in result

    def test_redirect_shown_in_output(self):
        resp = _make_response(_SAMPLE_HTML, url="https://www.acme.com")
        with patch("src.tools.requests.get", return_value=resp):
            result = fetch_webpage.invoke("https://acme.com")
        assert "www.acme.com" in result

    def test_long_content_is_truncated(self):
        long_html = f"<html><body>{'<p>word</p>' * 2000}</body></html>"
        with patch("src.tools.requests.get", return_value=_make_response(long_html)):
            result = fetch_webpage.invoke("https://acme.com")
        assert "truncated" in result


class TestFetchLinkedInPage:
    def test_extracts_company_name_from_og_title(self):
        resp = _make_response(_LINKEDIN_HTML, url="https://www.linkedin.com/company/acme")
        with patch("src.tools.requests.get", return_value=resp):
            result = fetch_linkedin_page.invoke("https://www.linkedin.com/company/acme")
        assert "Acme Corp" in result
        assert "| LinkedIn" not in result

    def test_extracts_og_description(self):
        resp = _make_response(_LINKEDIN_HTML, url="https://www.linkedin.com/company/acme")
        with patch("src.tools.requests.get", return_value=resp):
            result = fetch_linkedin_page.invoke("https://www.linkedin.com/company/acme")
        assert "500 employees" in result

    def test_notes_auth_wall(self):
        resp = _make_response(_LINKEDIN_HTML, url="https://www.linkedin.com/company/acme")
        with patch("src.tools.requests.get", return_value=resp):
            result = fetch_linkedin_page.invoke("https://www.linkedin.com/company/acme")
        assert "authentication" in result.lower() or "sign in" in result.lower()

    def test_rejects_non_linkedin_url(self):
        result = fetch_linkedin_page.invoke("https://acme.com")
        assert "Error" in result
        assert "not a LinkedIn URL" in result

    def test_timeout_returns_error_message(self):
        with patch("src.tools.requests.get", side_effect=requests.exceptions.Timeout):
            result = fetch_linkedin_page.invoke("https://www.linkedin.com/company/acme")
        assert "Error" in result
        assert "timed out" in result

    def test_connection_error_returns_error_message(self):
        with patch("src.tools.requests.get", side_effect=requests.exceptions.ConnectionError):
            result = fetch_linkedin_page.invoke("https://www.linkedin.com/company/acme")
        assert "Error" in result
        assert "connect" in result.lower()

    def test_http_error_returns_status_code(self):
        error_response = MagicMock()
        error_response.status_code = 999
        http_error = requests.exceptions.HTTPError(response=error_response)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = http_error
        with patch("src.tools.requests.get", return_value=mock_resp):
            result = fetch_linkedin_page.invoke("https://www.linkedin.com/company/acme")
        assert "999" in result

    def test_includes_linkedin_url_in_output(self):
        resp = _make_response(_LINKEDIN_HTML, url="https://www.linkedin.com/company/acme")
        with patch("src.tools.requests.get", return_value=resp):
            result = fetch_linkedin_page.invoke("https://www.linkedin.com/company/acme")
        assert "linkedin.com" in result


class TestExtractLinks:
    def test_categorises_about_link(self):
        with patch("src.tools.requests.get", return_value=_make_response(_SAMPLE_HTML)):
            result = extract_links.invoke("https://acme.com")
        assert "About" in result
        assert "https://acme.com/about" in result

    def test_categorises_products_link(self):
        with patch("src.tools.requests.get", return_value=_make_response(_SAMPLE_HTML)):
            result = extract_links.invoke("https://acme.com")
        assert "Products" in result
        assert "https://acme.com/products" in result

    def test_categorises_pricing_link(self):
        with patch("src.tools.requests.get", return_value=_make_response(_SAMPLE_HTML)):
            result = extract_links.invoke("https://acme.com")
        assert "Pricing" in result
        assert "https://acme.com/pricing" in result

    def test_excludes_external_links(self):
        html = """
        <html><body>
          <a href="https://other.com/page">External</a>
          <a href="/internal">Internal</a>
        </body></html>
        """
        with patch("src.tools.requests.get", return_value=_make_response(html)):
            result = extract_links.invoke("https://acme.com")
        assert "other.com" not in result

    def test_excludes_mailto_links(self):
        html = '<html><body><a href="mailto:info@acme.com">Email</a></body></html>'
        with patch("src.tools.requests.get", return_value=_make_response(html)):
            result = extract_links.invoke("https://acme.com")
        assert "mailto:" not in result

    def test_timeout_returns_error_message(self):
        with patch("src.tools.requests.get", side_effect=requests.exceptions.Timeout):
            result = extract_links.invoke("https://acme.com")
        assert "Error" in result
        assert "timed out" in result

    def test_deduplicates_links(self):
        html = """
        <html><body>
          <a href="/about">About</a>
          <a href="/about">About Us</a>
        </body></html>
        """
        with patch("src.tools.requests.get", return_value=_make_response(html)):
            result = extract_links.invoke("https://acme.com")
        assert result.count("https://acme.com/about") == 1
