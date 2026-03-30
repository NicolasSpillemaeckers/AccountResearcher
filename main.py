#!/usr/bin/env python3
"""CLI entry point for the AccountResearcher website research agent."""

from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="account-researcher",
        description="Research a customer website and produce a structured report.",
    )
    parser.add_argument("url", help="Homepage URL of the customer website to research.")
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model to use (default: gpt-4o or $OPENAI_MODEL).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to scrape (default: 5).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="HTTP request timeout in seconds (default: 10).",
    )
    args = parser.parse_args()

    # Import here so that tests that don't set OPENAI_API_KEY still work.
    from src.agent import WebsiteResearchAgent

    agent = WebsiteResearchAgent(
        model=args.model,
        max_pages=args.max_pages,
        timeout=args.timeout,
    )

    print(f"Researching {args.url} …", file=sys.stderr)
    report = agent.research(args.url)
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
