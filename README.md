# AccountResearcher

An AI-powered agent that researches a customer's website and produces a structured business report.

## What it does

Given any company website URL, the agent will:

1. Fetch the main page to understand the company's core business
2. Discover and visit key pages (About, Products, Services, Team, Contact, Pricing)
3. Compile a structured research report including:
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
# Research a website via the CLI
python -m src.main https://www.example.com

# Use a specific OpenAI model
python -m src.main https://www.example.com --model gpt-4o
```

You can also use the agent programmatically:

```python
from src.agent import research_website

report = research_website("https://www.example.com")
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