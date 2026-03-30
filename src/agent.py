"""Website researcher agent."""

import os

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from src.tools import TOOLS

load_dotenv()

_SYSTEM_PROMPT = """You are an expert business analyst and account researcher. \
Your job is to thoroughly research a company's website and produce a structured report.

When given a website URL, follow these steps:
1. Fetch the main page to understand the company's core business.
2. Use extract_links to discover important pages (About, Products, Services, Team, Contact, Pricing).
3. Visit the most relevant pages to gather detailed information.
4. Compile everything into a clear, structured research report.

Your final report MUST include the following sections (skip any section where no information is found):
- **Company Name**
- **Company Description** – what the company does in 1-2 sentences
- **Products / Services** – what they sell or offer
- **Target Market** – who their customers are
- **Pricing** – pricing model or plans (if publicly available)
- **Team / Leadership** – key founders or executives
- **Contact Information** – email, phone, address
- **Key Takeaways** – 3-5 bullet points summarising the most important findings

Be concise and factual. Only report information you found on the website.
Do not speculate or add information from external sources."""


def create_website_researcher(model: str | None = None) -> AgentExecutor:
    """Create and return a website researcher agent.

    Args:
        model: The OpenAI model to use. Defaults to the OPENAI_MODEL env variable
               or ``gpt-4o-mini``.

    Returns:
        A configured :class:`AgentExecutor` ready to research websites.
    """
    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0)

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=_SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=True, max_iterations=15)


def research_website(url: str, model: str | None = None) -> str:
    """Research a customer website and return a structured report.

    Args:
        url: The URL of the website to research.
        model: Optional OpenAI model override.

    Returns:
        A markdown-formatted research report as a string.
    """
    executor = create_website_researcher(model=model)
    result = executor.invoke({"input": f"Research the following website: {url}"})
    return result["output"]
