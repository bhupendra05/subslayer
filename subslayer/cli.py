"""Command-line entrypoint: `subslayer`."""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from .detect import analyze_csv
from .report import to_json, to_text


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="subslayer",
        description="Find recurring subscriptions in a bank-statement CSV and what you could save.",
    )
    p.add_argument("file", help="Path to the bank-statement CSV")
    p.add_argument("--json", action="store_true", help="Output JSON instead of text")
    p.add_argument("--currency", default="₹", help="Currency symbol (default: ₹)")
    p.add_argument("--out", default=None, help="Write the report to a file")
    args = p.parse_args(argv)

    try:
        report = analyze_csv(args.file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 3

    report.currency = args.currency
    rendered = to_json(report) if args.json else to_text(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"Report written to {args.out}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
