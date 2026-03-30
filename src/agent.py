"""Website research agent powered by OpenAI."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from src.models import ContactInfo, ResearchReport
from src.scraper import collect_pages, extract_metadata, fetch_page

load_dotenv()

_SYSTEM_PROMPT = """
You are an expert business analyst. You will be given the text content scraped
from a company's website. Analyse it and return a JSON object with exactly the
following keys:

- company_name        (string | null)
- description         (string | null)  – one to two sentence company overview
- products_and_services (list[string]) – key offerings, max 10 items
- target_audience     (string | null)  – who the company serves
- key_differentiators (list[string])   – what sets the company apart, max 5 items
- contact_info        (object)         – keys: email, phone, address, linkedin, twitter
                                         (all string | null)
- technologies        (list[string])   – tech stack / tools mentioned, max 10 items
- summary             (string | null)  – concise 3-5 sentence executive summary

Return ONLY valid JSON. Do not include any explanatory text outside the JSON.
""".strip()


class WebsiteResearchAgent:
    """
    An AI-powered agent that researches a customer's website and returns a
    structured :class:`ResearchReport`.

    Parameters
    ----------
    api_key:
        OpenAI API key.  Falls back to the ``OPENAI_API_KEY`` environment
        variable when not supplied.
    model:
        OpenAI model name.  Falls back to the ``OPENAI_MODEL`` environment
        variable, then ``gpt-4o``.
    max_pages:
        Maximum number of pages to scrape from the target website.
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_pages: int | None = None,
        timeout: int | None = None,
    ) -> None:
        self._client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self._max_pages = max_pages or int(os.getenv("MAX_PAGES", "5"))
        self._timeout = timeout or int(os.getenv("REQUEST_TIMEOUT", "10"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def research(self, url: str) -> ResearchReport:
        """
        Research the customer website at *url* and return a
        :class:`ResearchReport`.

        Parameters
        ----------
        url:
            The homepage URL of the customer's website
            (e.g. ``"https://example.com"``).
        """
        pages = collect_pages(url, max_pages=self._max_pages, timeout=self._timeout)
        if not pages:
            return ResearchReport(url=url)

        content = self._build_content(pages)
        raw = self._call_llm(content)
        return self._parse_report(url, raw)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_content(self, pages: dict[str, str]) -> str:
        """Concatenate scraped page texts into a single prompt-ready string."""
        sections: list[str] = []
        for page_url, text in pages.items():
            # Trim individual pages to avoid exceeding context limits.
            trimmed = text[:4000]
            sections.append(f"=== Page: {page_url} ===\n{trimmed}")
        return "\n\n".join(sections)

    def _call_llm(self, content: str) -> dict[str, Any]:
        """Send *content* to the LLM and return the parsed JSON response."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        text = response.choices[0].message.content or "{}"
        return json.loads(text)

    @staticmethod
    def _parse_report(url: str, data: dict[str, Any]) -> ResearchReport:
        """Map raw LLM JSON output to a :class:`ResearchReport`."""
        contact_raw = data.get("contact_info") or {}
        contact = ContactInfo(
            email=contact_raw.get("email"),
            phone=contact_raw.get("phone"),
            address=contact_raw.get("address"),
            linkedin=contact_raw.get("linkedin"),
            twitter=contact_raw.get("twitter"),
        )
        return ResearchReport(
            url=url,
            company_name=data.get("company_name"),
            description=data.get("description"),
            products_and_services=data.get("products_and_services") or [],
            target_audience=data.get("target_audience"),
            key_differentiators=data.get("key_differentiators") or [],
            contact_info=contact,
            technologies=data.get("technologies") or [],
            summary=data.get("summary"),
        )
