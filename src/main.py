#!/usr/bin/env python3
"""Command-line entry point for the website researcher agent."""

import argparse
import sys

from src.agent import research_account


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Research a customer account using one or more sources "
            "(website URL and/or LinkedIn page URL) and produce a structured report."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m src.main https://www.example.com\n"
            "  python -m src.main https://www.example.com "
            "https://www.linkedin.com/company/example\n"
            "  python -m src.main https://www.example.com --model gpt-4o\n"
        ),
    )
    parser.add_argument(
        "sources",
        nargs="+",
        metavar="URL",
        help=(
            "One or more source URLs to research. "
            "Each URL can be a company website or a LinkedIn page."
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model to use (default: value of OPENAI_MODEL env var or gpt-4o-mini).",
    )
    args = parser.parse_args()

    print(f"Researching {len(args.sources)} source(s):")
    for url in args.sources:
        print(f"  - {url}")
    print("=" * 60)
    print()

    try:
        report = research_account(args.sources, model=args.model)
        print(report)
    except KeyboardInterrupt:
        print("\nResearch interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

