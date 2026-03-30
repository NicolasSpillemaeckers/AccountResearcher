# AccountResearcher

An AI-powered agent that researches a customer account using dedicated sources and produces a structured business report.

## What it does

Given one or more source URLs for a company, the agent will research each source and compile a single structured report. Supported source types are:

- **Company website** – crawls key pages (About, Products, Services, Team, Contact, Pricing)
- **LinkedIn page** – extracts publicly available company or profile information

The final report includes:
- Company name and description
- Products / services offered
- Target market
- Pricing model
- Team and leadership
- Contact information
- Key takeaways

## Requirements

- Python 3.12+
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

## Usage

```bash
# Research a website only
python -m src.main https://www.example.com

# Research a LinkedIn page only
python -m src.main https://www.linkedin.com/company/example

# Research both sources together (recommended)
python -m src.main https://www.example.com https://www.linkedin.com/company/example

# Use a specific OpenAI model
python -m src.main https://www.example.com --model gpt-4o
```

You can also use the agent programmatically:

```python
from src.agent import research_account

# Website only
report = research_account(["https://www.example.com"])

# LinkedIn only
report = research_account(["https://www.linkedin.com/company/example"])

# Both sources
report = research_account([
    "https://www.example.com",
    "https://www.linkedin.com/company/example",
])

print(report)
```

## Configuration

| Environment variable | Default       | Description                        |
|----------------------|---------------|------------------------------------|
| `OPENAI_API_KEY`     | *(required)*  | Your OpenAI API key                |
| `OPENAI_MODEL`       | `gpt-4o-mini` | OpenAI model to use for the agent  |

## Running the tests

```bash
pip install pytest
pytest tests/
```