"""Web research tools for the website researcher agent."""

from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AccountResearcher/1.0; "
        "+https://github.com/NicolasSpillemaeckers/AccountResearcher)"
    )
}
_TIMEOUT = 10
_MAX_CONTENT_LENGTH = 8000

_LINKEDIN_DOMAINS = {"linkedin.com", "www.linkedin.com"}


def _is_linkedin_url(url: str) -> bool:
    """Return True if the URL belongs to linkedin.com."""
    return urlparse(url).netloc.lower() in _LINKEDIN_DOMAINS


def _fetch_html(url: str) -> tuple[str, str]:
    """Fetch a URL and return (html_content, final_url)."""
    response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    return response.text, response.url


def _clean_text(soup: BeautifulSoup) -> str:
    """Extract and clean visible text from a BeautifulSoup object."""
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _extract_meta_tags(soup: BeautifulSoup) -> dict[str, str]:
    """Extract Open Graph and standard meta tags from a BeautifulSoup object."""
    meta: dict[str, str] = {}
    for tag in soup.find_all("meta"):
        name = tag.get("property") or tag.get("name") or ""
        content = tag.get("content", "")
        if name and content:
            meta[name.lower()] = content
    if soup.title:
        meta["title"] = soup.title.get_text(strip=True)
    return meta


@tool
def fetch_webpage(url: str) -> str:
    """Fetch a webpage and return its visible text content.

    Use this tool to read the content of any page on the customer's website.
    The returned text is stripped of HTML tags, scripts, and navigation elements.

    Args:
        url: The full URL of the page to fetch (e.g. https://example.com/about).

    Returns:
        The visible text content of the page, truncated to avoid very large responses.
    """
    try:
        html, final_url = _fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        title = soup.title.get_text(strip=True) if soup.title else ""
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"]

        text = _clean_text(soup)
        if len(text) > _MAX_CONTENT_LENGTH:
            text = text[:_MAX_CONTENT_LENGTH] + "\n...[content truncated]"

        result_parts = []
        if title:
            result_parts.append(f"Page title: {title}")
        if description:
            result_parts.append(f"Meta description: {description}")
        if final_url != url:
            result_parts.append(f"Redirected to: {final_url}")
        result_parts.append("")
        result_parts.append(text)
        return "\n".join(result_parts)
    except requests.exceptions.Timeout:
        return f"Error: Request timed out for {url}"
    except requests.exceptions.ConnectionError:
        return f"Error: Could not connect to {url}"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} for {url}"
    except Exception as e:  # noqa: BLE001
        return f"Error fetching {url}: {e}"


@tool
def fetch_linkedin_page(url: str) -> str:
    """Fetch a LinkedIn company or profile page and extract available public information.

    LinkedIn restricts access to logged-in users for most content, so this tool
    extracts whatever is publicly visible: Open Graph metadata, page title, and
    any text that is rendered without authentication.

    Use this tool whenever a LinkedIn URL is provided as a source.

    Args:
        url: The LinkedIn URL to fetch (e.g. https://www.linkedin.com/company/example).

    Returns:
        A summary of the publicly available information from the LinkedIn page,
        including company name, description, and any other accessible details.
    """
    if not _is_linkedin_url(url):
        return f"Error: {url} is not a LinkedIn URL. Use fetch_webpage for non-LinkedIn pages."
    try:
        html, final_url = _fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        meta = _extract_meta_tags(soup)

        lines = [f"LinkedIn page: {final_url}", ""]

        og_title = meta.get("og:title") or meta.get("title", "")
        if og_title:
            name = og_title.replace(" | LinkedIn", "").strip()
            lines.append(f"Name: {name}")

        og_description = meta.get("og:description") or meta.get("description", "")
        if og_description:
            lines.append(f"Description: {og_description}")

        og_image = meta.get("og:image", "")
        if og_image:
            lines.append(f"Image URL: {og_image}")

        visible_text = _clean_text(soup)
        auth_wall_signals = [
            "sign in", "log in", "join linkedin", "join now to see",
            "authwall", "sign up",
        ]
        is_blocked = any(sig in visible_text.lower() for sig in auth_wall_signals)
        if is_blocked:
            lines.append("")
            lines.append(
                "Note: LinkedIn requires authentication to display full content. "
                "Only publicly available metadata is shown above."
            )
        else:
            if len(visible_text) > _MAX_CONTENT_LENGTH:
                visible_text = visible_text[:_MAX_CONTENT_LENGTH] + "\n...[content truncated]"
            if visible_text:
                lines.append("")
                lines.append(visible_text)

        return "\n".join(lines)
    except requests.exceptions.Timeout:
        return f"Error: Request timed out for {url}"
    except requests.exceptions.ConnectionError:
        return f"Error: Could not connect to {url}"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} for {url}"
    except Exception as e:  # noqa: BLE001
        return f"Error fetching LinkedIn page {url}: {e}"


@tool
def extract_links(url: str) -> str:
    """Extract links from a webpage grouped by likely page type.

    Use this tool to discover other pages on a website, such as About, Products,
    Services, Team, Contact, Blog, and Pricing pages.

    Args:
        url: The full URL of the page to extract links from.

    Returns:
        A formatted list of links with their anchor text, grouped by category.
    """
    try:
        html, _ = _fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        base_domain = urlparse(url).netloc

        categories = {
            "about": ["about", "company", "mission", "vision", "story", "who-we-are"],
            "products": ["product", "solution", "platform", "software", "tool", "feature"],
            "services": ["service", "offering", "consulting", "support"],
            "pricing": ["pricing", "price", "plan", "cost"],
            "team": ["team", "people", "leadership", "staff", "founder", "executive"],
            "contact": ["contact", "reach", "sales", "demo", "trial"],
            "blog": ["blog", "news", "insight", "resource", "article", "press"],
        }

        found: dict[str, list[str]] = {cat: [] for cat in categories}
        other: list[str] = []

        seen = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith("#") or href.startswith("mailto:"):
                continue
            full_url = urljoin(url, href)
            parsed = urlparse(full_url)
            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc and parsed.netloc != base_domain:
                continue
            if full_url in seen:
                continue
            seen.add(full_url)

            anchor = a_tag.get_text(strip=True) or parsed.path
            link_str = f"  - {anchor}: {full_url}"
            path_lower = parsed.path.lower()

            categorised = False
            for cat, keywords in categories.items():
                if any(kw in path_lower for kw in keywords):
                    found[cat].append(link_str)
                    categorised = True
                    break
            if not categorised:
                other.append(link_str)

        lines = [f"Links found on {url}:"]
        for cat, links in found.items():
            if links:
                lines.append(f"\n{cat.capitalize()} pages:")
                lines.extend(links[:5])
        if other:
            lines.append("\nOther internal pages:")
            lines.extend(other[:10])
        return "\n".join(lines)
    except requests.exceptions.Timeout:
        return f"Error: Request timed out for {url}"
    except requests.exceptions.ConnectionError:
        return f"Error: Could not connect to {url}"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} for {url}"
    except Exception as e:  # noqa: BLE001
        return f"Error extracting links from {url}: {e}"


TOOLS = [fetch_webpage, fetch_linkedin_page, extract_links]
