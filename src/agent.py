"""Website researcher agent."""

import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from src.tools import TOOLS

load_dotenv()

_SYSTEM_PROMPT = """You are an expert business analyst and account researcher. \
Your job is to thoroughly research a company using all provided sources and produce \
a single structured report that combines findings from every source.

The sources you receive can be:
- A **website URL** – the company's own website (e.g. https://acme.com)
- A **LinkedIn URL** – the company's LinkedIn page (e.g. https://linkedin.com/company/acme)

For each source, apply the appropriate research strategy:

**Website sources:**
1. Fetch the main page to understand the company's core business.
2. Use extract_links to discover important sub-pages (About, Products, Services, Team, \
Contact, Pricing).
3. Visit the most relevant sub-pages to gather detailed information.

**LinkedIn sources:**
1. Use fetch_linkedin_page to retrieve publicly available company or profile information.
2. Note any limitations if LinkedIn requires authentication to display full content.

After researching all sources, combine the findings into one clear, structured report.
Your final report MUST include the following sections \
(skip any section where no information is found):

- **Company Name**
- **Company Description** – what the company does in 1-2 sentences
- **Products / Services** – what they sell or offer
- **Target Market** – who their customers are
- **Pricing** – pricing model or plans (if publicly available)
- **Team / Leadership** – key founders or executives
- **Contact Information** – email, phone, address
- **Key Takeaways** – 3-5 bullet points summarising the most important findings

Be concise and factual. Only report information you found in the provided sources.
Do not speculate or add information from external sources."""


def _is_linkedin_url(url: str) -> bool:
    """Return True if the URL belongs to linkedin.com."""
    return urlparse(url).netloc.lower() in {"linkedin.com", "www.linkedin.com"}


def _describe_sources(sources: list[str]) -> str:
    """Build a human-readable list of sources for the agent prompt."""
    lines = []
    for url in sources:
        kind = "LinkedIn page" if _is_linkedin_url(url) else "website"
        lines.append(f"- {kind}: {url}")
    return "\n".join(lines)


def create_account_researcher(model: str | None = None) -> CompiledStateGraph:
    """Create and return a website researcher agent.

    Args:
        model: The OpenAI model to use. Defaults to the OPENAI_MODEL env variable
               or ``gpt-4o-mini``.

    Returns:
        A compiled LangGraph agent ready to research customer accounts.
    """
    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0)
    return create_agent(llm, tools=TOOLS, system_prompt=_SYSTEM_PROMPT)


def research_account(sources: list[str], model: str | None = None) -> str:
    """Research a customer account using one or more sources and return a report.

    Args:
        sources: A list of source URLs to research. Each URL can be either a
                 company website (e.g. ``https://acme.com``) or a LinkedIn page
                 (e.g. ``https://www.linkedin.com/company/acme``).
        model: Optional OpenAI model override.

    Returns:
        A markdown-formatted research report combining information from all sources.

    Raises:
        ValueError: If ``sources`` is empty.
    """
    if not sources:
        raise ValueError("At least one source URL must be provided.")

    agent = create_account_researcher(model=model)
    source_list = _describe_sources(sources)
    prompt = f"Research the following customer sources and compile a report:\n\n{source_list}"
    result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
    return result["messages"][-1].content

