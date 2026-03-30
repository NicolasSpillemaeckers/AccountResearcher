# AccountResearcher

An AI-powered agent that researches a customer's website and produces a structured report.

## What it does

Given a URL, the agent:
1. Fetches the homepage and a set of well-known sub-pages (`/about`, `/products`, `/services`, `/contact`, …).
2. Extracts the visible text content from each page.
3. Sends the content to an OpenAI LLM that analyses it and returns structured JSON.
4. Returns a typed `ResearchReport` containing:
   - Company name & description
   - Products / services
   - Target audience
   - Key differentiators
   - Contact information (email, phone, address, LinkedIn, Twitter)
   - Technologies used
   - Executive summary

## Requirements

- Python 3.11+
- An OpenAI API key

## Setup

```bash
# 1. Create and activate a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your OpenAI API key
cp .env.example .env
# Then edit .env and set OPENAI_API_KEY=<your key>
```

## Usage

### CLI

```bash
python main.py https://example.com
```

Optional flags:

| Flag | Default | Description |
|---|---|---|
| `--model` | `gpt-4o` | OpenAI model to use |
| `--max-pages` | `5` | Maximum pages to scrape |
| `--timeout` | `10` | HTTP timeout (seconds) |

### Python API

```python
from src.agent import WebsiteResearchAgent

agent = WebsiteResearchAgent()          # reads OPENAI_API_KEY from env
report = agent.research("https://example.com")

print(report.company_name)
print(report.summary)
print(report.contact_info.email)
```

The `ResearchReport` object can be serialised to a plain dict or JSON:

```python
import json
print(json.dumps(report.model_dump(), indent=2))
```

## Running the tests

```bash
pytest tests/ -v
```

## Project structure

```
AccountResearcher/
├── main.py              # CLI entry point
├── requirements.txt
├── .env.example
├── src/
│   ├── agent.py         # WebsiteResearchAgent – orchestrates research
│   ├── scraper.py       # Web fetching and HTML parsing utilities
│   └── models.py        # Pydantic data models (ResearchReport, ContactInfo)
└── tests/
    ├── test_agent.py
    └── test_scraper.py
```
