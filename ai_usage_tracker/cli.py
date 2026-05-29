#!/usr/bin/env python3
"""
Combined Claude + Codex Token Usage Report Generator

Fetches token usage data from both ccusage (Claude) and ccusage-codex (Codex)
and generates a combined report showing usage statistics, costs, and daily averages.
With the high-performance Rust ccusage version, it also dynamically supports
Gemini (Antigravity) and OpenCode tracking.

Requirements:
- ccusage CLI (Rust version or legacy JS version)
- Python 3.7+

Usage:
- ai-usage-tracker [--days DAYS] [--json]
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
    combine_all_data,
    get_claude_usage,
    get_codex_usage,
    get_gemini_usage,
    get_opencode_usage,
    has_rust_ccusage,
    print_averages,
    print_table,
)


def check_dependencies(is_rust: bool):
    """Check that ccusage is installed; offer to install if missing."""
    if shutil.which("ccusage"):
        if is_rust:
            # Rust version is completely self-contained!
            return
        if shutil.which("ccusage-codex"):
            return
        missing = {"ccusage-codex": "@ccusage/codex"}
    else:
        missing = {"ccusage": "ccusage", "ccusage-codex": "@ccusage/codex"}

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
        try:
            ret = subprocess.call(["npm", "install", "-g"] + list(missing.values()))
        except FileNotFoundError:
            print("Error: npm not found. Please install Node.js and npm first.", file=sys.stderr)
            print("  Visit: https://nodejs.org/", file=sys.stderr)
            sys.exit(1)
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
        print("Install manually with:", file=sys.stderr)
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

    # Detect Rust version of ccusage (supports Claude, Codex, Gemini, OpenCode natively)
    is_rust = has_rust_ccusage()
    check_dependencies(is_rust)

    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            try:
                days = int(sys.argv[idx + 1])
            except ValueError:
                print("Error: --days must be a positive integer", file=sys.stderr)
                sys.exit(1)
            if days < 1:
                print("Error: --days must be a positive integer", file=sys.stderr)
                sys.exit(1)

    if "--json" in sys.argv:
        output_json = True

    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    if is_rust:
        print("Fetching Claude, Codex, Gemini, and OpenCode usage data in parallel...", file=sys.stderr)
        with ThreadPoolExecutor(max_workers=4) as pool:
            claude_future = pool.submit(get_claude_usage, since_date, is_rust=True)
            codex_future = pool.submit(get_codex_usage, since_date, is_rust=True)
            gemini_future = pool.submit(get_gemini_usage, since_date, is_rust=True)
            opencode_future = pool.submit(get_opencode_usage, since_date, is_rust=True)
            
            claude_data = claude_future.result()
            codex_data = codex_future.result()
            gemini_data = gemini_future.result()
            opencode_data = opencode_future.result()
            
        combined_data = combine_all_data({
            "claude": claude_data,
            "codex": codex_data,
            "gemini": gemini_data,
            "opencode": opencode_data
        })
    else:
        print("Fetching Claude and Codex usage data in parallel...", file=sys.stderr)
        with ThreadPoolExecutor(max_workers=2) as pool:
            claude_future = pool.submit(get_claude_usage, since_date, is_rust=False)
            codex_future = pool.submit(get_codex_usage, since_date, is_rust=False)
            
            claude_data = claude_future.result()
            codex_data = codex_future.result()
            
        combined_data = combine_all_data({
            "claude": claude_data,
            "codex": codex_data
        })

    if output_json:
        result_json = {
            "combined_daily": combined_data,
            "claude_totals": claude_data.get("totals", {}),
            "codex_totals": codex_data.get("totals", {})
        }
        if is_rust:
            result_json["gemini_totals"] = gemini_data.get("totals", {})
            result_json["opencode_totals"] = opencode_data.get("totals", {})
        print(json.dumps(result_json, indent=2))
    else:
        totals = print_table(combined_data)
        print_averages(combined_data, totals)


if __name__ == "__main__":
    main()
