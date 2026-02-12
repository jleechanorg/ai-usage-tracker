#!/usr/bin/env python3
"""
Combined Claude + Codex Token Usage Report Generator

Fetches token usage data from both ccusage (Claude) and ccusage-codex (Codex)
and generates a combined report showing usage statistics, costs, and daily averages.

Requirements:
- ccusage CLI (for Claude token usage)
- ccusage-codex CLI (for Codex token usage)
- Python 3.7+

Usage:
    ai-usage-tracker [--days DAYS] [--json]

Options:
    --days DAYS    Number of days to include in report (default: 7)
    --json         Output in JSON format
    --help         Show this help message
"""

import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from ai_usage_tracker import __version__
from ai_usage_tracker.core import (
    DEPS,
    combine_data,
    get_claude_usage,
    get_codex_usage,
    print_averages,
    print_table,
)


def check_dependencies():
    """Check that ccusage and ccusage-codex are installed; offer to install if missing."""
    missing = {cmd: pkg for cmd, pkg in DEPS.items() if not shutil.which(cmd)}
    if not missing:
        return

    names = ", ".join(missing.keys())
    pkgs = " ".join(missing.values())
    print(f"Error: Required commands not found: {names}", file=sys.stderr)
    print("", file=sys.stderr)

    try:
        answer = input(f"Install them now? (npm install -g {pkgs}) [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"
        print("", file=sys.stderr)

    if answer in ("", "y", "yes"):
        print(f"Running: npm install -g {pkgs}", file=sys.stderr)
        ret = subprocess.call(["npm", "install", "-g"] + list(missing.values()))
        if ret != 0:
            print("Installation failed.", file=sys.stderr)
            sys.exit(1)
        # Verify
        still_missing = [cmd for cmd in missing if not shutil.which(cmd)]
        if still_missing:
            print(f"Error: Commands still not found after install: {', '.join(still_missing)}", file=sys.stderr)
            sys.exit(1)
        print("Dependencies installed successfully.", file=sys.stderr)
    else:
        print(f"Install manually with:", file=sys.stderr)
        print(f"  npm install -g {pkgs}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    days = 7
    output_json = False

    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"ai-usage-tracker {__version__}")
        sys.exit(0)

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    check_dependencies()

    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

    if "--json" in sys.argv:
        output_json = True

    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    print("Fetching Claude and Codex usage data in parallel...", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=2) as pool:
        claude_future = pool.submit(get_claude_usage, since_date)
        codex_future = pool.submit(get_codex_usage, since_date)
        claude_data = claude_future.result()
        codex_data = codex_future.result()

    combined_data = combine_data(claude_data, codex_data)

    if output_json:
        print(json.dumps({
            "combined_daily": combined_data,
            "claude_totals": claude_data.get("totals", {}),
            "codex_totals": codex_data.get("totals", {})
        }, indent=2))
    else:
        totals = print_table(combined_data)
        print_averages(combined_data, totals)


if __name__ == "__main__":
    main()
