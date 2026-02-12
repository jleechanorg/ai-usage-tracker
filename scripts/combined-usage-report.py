#!/usr/bin/env python3
"""
Combined Claude + Codex Token Usage Report Generator

This script fetches token usage data from both ccusage (Claude) and ccusage-codex (Codex)
and generates a combined report showing usage statistics, costs, and daily averages.

Requirements:
- ccusage CLI (for Claude token usage)
- ccusage-codex CLI (for Codex token usage)
- Python 3.6+

Usage:
    python3 combined-usage-report.py [--days DAYS] [--json]

Options:
    --days DAYS    Number of days to include in report (default: 7)
    --json         Output in JSON format
    --help         Show this help message
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add repo root to sys.path to allow importing ai_usage_tracker when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_usage_tracker.core import (
    combine_data,
    get_claude_usage,
    get_codex_usage,
    print_averages,
    print_table,
)


def main():
    """Main entry point."""
    # Parse arguments
    days = 7
    output_json = False

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

    if "--json" in sys.argv:
        output_json = True

    # Calculate since date
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    # Fetch data
    print("Fetching Claude usage data...", file=sys.stderr)
    claude_data = get_claude_usage(since_date)

    print("Fetching Codex usage data...", file=sys.stderr)
    codex_data = get_codex_usage(since_date)

    # Combine data
    combined_data = combine_data(claude_data, codex_data)

    if output_json:
        # Output JSON format
        print(json.dumps({
            "combined_daily": combined_data,
            "claude_totals": claude_data.get("totals", {}),
            "codex_totals": codex_data.get("totals", {})
        }, indent=2))
    else:
        # Output table format
        totals = print_table(combined_data)
        print_averages(combined_data, totals)


if __name__ == "__main__":
    main()
