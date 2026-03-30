#!/usr/bin/env python3
"""Command-line entry point for the website researcher agent."""

import argparse
import sys

from src.agent import research_website


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Research a customer website and produce a structured report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m src.main https://www.example.com\n"
            "  python -m src.main https://www.example.com --model gpt-4o\n"
        ),
    )
    parser.add_argument("url", help="The URL of the website to research.")
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model to use (default: value of OPENAI_MODEL env var or gpt-4o-mini).",
    )
    args = parser.parse_args()

    print(f"Researching website: {args.url}\n{'=' * 60}\n")
    try:
        report = research_website(args.url, model=args.model)
        print(report)
    except KeyboardInterrupt:
        print("\nResearch interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
