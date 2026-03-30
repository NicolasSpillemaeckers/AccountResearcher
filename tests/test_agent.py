"""Tests for the website research agent."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.agent import WebsiteResearchAgent
from src.models import ResearchReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_LLM_RESPONSE = {
    "company_name": "Acme Corp",
    "description": "Acme builds world-class rockets.",
    "products_and_services": ["Rockets", "Spacecraft"],
    "target_audience": "Space agencies and private companies",
    "key_differentiators": ["Best price-to-thrust ratio"],
    "contact_info": {
        "email": "hello@acme.com",
        "phone": "+1-800-ROCKETS",
        "address": "1 Rocket Way, Houston TX",
        "linkedin": "https://linkedin.com/company/acme",
        "twitter": "@acmecorp",
    },
    "technologies": ["Python", "Kubernetes"],
    "summary": "Acme Corp is a leading rocket manufacturer based in Houston.",
}


def _make_agent() -> WebsiteResearchAgent:
    """Return an agent with a mocked OpenAI client."""
    with patch("src.agent.OpenAI"):
        agent = WebsiteResearchAgent(api_key="test-key")
    return agent


def _mock_completion(data: dict) -> MagicMock:
    """Build a mock OpenAI chat completion whose content is *data* as JSON."""
    message = MagicMock()
    message.content = json.dumps(data)
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    return completion


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_research_returns_report(monkeypatch):
    agent = _make_agent()

    # Patch scraper so no real HTTP calls are made.
    monkeypatch.setattr(
        "src.agent.collect_pages",
        lambda url, **kw: {url: "Acme builds rockets. Contact: hello@acme.com"},
    )

    # Patch OpenAI client call.
    agent._client.chat.completions.create = MagicMock(
        return_value=_mock_completion(MOCK_LLM_RESPONSE)
    )

    report = agent.research("https://acme.com")

    assert isinstance(report, ResearchReport)
    assert report.url == "https://acme.com"
    assert report.company_name == "Acme Corp"
    assert "Rockets" in report.products_and_services
    assert report.contact_info.email == "hello@acme.com"
    assert report.contact_info.twitter == "@acmecorp"
    assert "Python" in report.technologies
    assert report.summary is not None


def test_research_empty_site_returns_minimal_report(monkeypatch):
    agent = _make_agent()

    # No pages fetched.
    monkeypatch.setattr("src.agent.collect_pages", lambda url, **kw: {})

    report = agent.research("https://empty.com")

    assert report.url == "https://empty.com"
    assert report.company_name is None
    assert report.products_and_services == []


def test_parse_report_handles_missing_fields():
    report = WebsiteResearchAgent._parse_report("https://example.com", {})

    assert report.url == "https://example.com"
    assert report.company_name is None
    assert report.products_and_services == []
    assert report.contact_info.email is None


def test_parse_report_full_data():
    report = WebsiteResearchAgent._parse_report("https://acme.com", MOCK_LLM_RESPONSE)

    assert report.company_name == "Acme Corp"
    assert report.target_audience == "Space agencies and private companies"
    assert report.key_differentiators == ["Best price-to-thrust ratio"]
    assert report.contact_info.linkedin == "https://linkedin.com/company/acme"


def test_build_content_truncates_long_pages():
    agent = _make_agent()
    long_text = "x" * 10_000
    pages = {"https://acme.com": long_text, "https://acme.com/about": "Short page"}
    content = agent._build_content(pages)

    # Each page is capped at 4 000 chars.
    assert content.count("x") <= 4000
    assert "Short page" in content


def test_build_content_includes_urls():
    agent = _make_agent()
    pages = {"https://acme.com": "Homepage", "https://acme.com/about": "About page"}
    content = agent._build_content(pages)

    assert "https://acme.com" in content
    assert "https://acme.com/about" in content


def test_research_report_model_dump():
    """Verify that ResearchReport serialises without errors."""
    agent = _make_agent()
    report = WebsiteResearchAgent._parse_report("https://acme.com", MOCK_LLM_RESPONSE)
    data = report.model_dump()

    assert data["url"] == "https://acme.com"
    assert isinstance(data["products_and_services"], list)
    assert isinstance(data["contact_info"], dict)
