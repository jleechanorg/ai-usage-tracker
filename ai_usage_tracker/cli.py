#!/usr/bin/env python3
"""
Combined Claude + Codex Token Usage Report Generator

Fetches token usage data from both ccusage (Claude) and ccusage-codex (Codex)
and generates a combined report showing usage statistics, costs, and daily averages.

Requirements:
- ccusage CLI (for Claude token usage)
- ccusage-codex CLI (for Codex token usage)
- Python 3.6+

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
from datetime import datetime, timedelta
from typing import Any, Dict

from ai_usage_tracker import __version__

DEPS = {
    "ccusage": "ccusage",
    "ccusage-codex": "@ccusage/codex",
}


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


def run_command(cmd: list) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        pkg = DEPS.get(cmd[0], cmd[0])
        print(f"Error: Command not found: {cmd[0]}", file=sys.stderr)
        print(f"  npm install -g {pkg}", file=sys.stderr)
        sys.exit(1)


def get_claude_usage(since_date: str) -> Dict[str, Any]:
    """Fetch Claude usage data from ccusage."""
    cmd = ["ccusage", "daily", "--since", since_date, "--order", "desc", "--json"]
    output = run_command(cmd)
    return json.loads(output)


def get_codex_usage(since_date: str) -> Dict[str, Any]:
    """Fetch Codex usage data from ccusage-codex."""
    cmd = ["ccusage-codex", "daily", "--since", since_date, "--order", "desc", "--json"]
    output = run_command(cmd)
    return json.loads(output)


def normalize_date(date_str: str) -> str:
    """Normalize date string to YYYY-MM-DD format."""
    try:
        if "-" in date_str:
            return date_str
        else:
            dt = datetime.strptime(date_str, "%b %d, %Y")
            return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str


def combine_data(claude_data: Dict, codex_data: Dict) -> Dict[str, Dict]:
    """Combine Claude and Codex data by date."""
    combined = {}

    for entry in claude_data.get("daily", []):
        date = normalize_date(entry["date"])
        combined[date] = {
            "claude_tokens": entry.get("totalTokens", 0),
            "claude_cost": entry.get("totalCost", 0.0),
            "codex_tokens": 0,
            "codex_cost": 0.0
        }

    for entry in codex_data.get("daily", []):
        date = normalize_date(entry["date"])
        if date not in combined:
            combined[date] = {
                "claude_tokens": 0,
                "claude_cost": 0.0,
                "codex_tokens": 0,
                "codex_cost": 0.0
            }
        combined[date]["codex_tokens"] = entry.get("totalTokens", 0)
        combined[date]["codex_cost"] = entry.get("costUSD", 0.0)

    return combined


def print_table(combined_data: Dict[str, Dict]):
    """Print the combined usage table."""
    print("\n╔════════════╦═══════════════╦════════════╦═══════════════╦════════════╦═══════════════╦════════════╗")
    print("║    Date    ║ Claude Tokens ║ Claude $   ║ Codex Tokens  ║  Codex $   ║ Total Tokens  ║  Total $   ║")
    print("╠════════════╬═══════════════╬════════════╬═══════════════╬════════════╬═══════════════╬════════════╣")

    total_claude_tokens = 0
    total_codex_tokens = 0
    total_claude_cost = 0.0
    total_codex_cost = 0.0

    for date in sorted(combined_data.keys(), reverse=True):
        data = combined_data[date]
        claude_tokens = data["claude_tokens"]
        claude_cost = data["claude_cost"]
        codex_tokens = data["codex_tokens"]
        codex_cost = data["codex_cost"]

        total_tokens = claude_tokens + codex_tokens
        total_cost = claude_cost + codex_cost

        total_claude_tokens += claude_tokens
        total_codex_tokens += codex_tokens
        total_claude_cost += claude_cost
        total_codex_cost += codex_cost

        date_short = date[5:]
        print(f"║ {date_short} ║ {claude_tokens:>13,} ║ ${claude_cost:>9.2f} ║ {codex_tokens:>13,} ║ ${codex_cost:>9.2f} ║ {total_tokens:>13,} ║ ${total_cost:>9.2f} ║")

    print("╠════════════╬═══════════════╬════════════╬═══════════════╬════════════╬═══════════════╬════════════╣")
    total_all_tokens = total_claude_tokens + total_codex_tokens
    total_all_cost = total_claude_cost + total_codex_cost

    print(f"║   TOTAL    ║ {total_claude_tokens:>13,} ║ ${total_claude_cost:>9.2f} ║ {total_codex_tokens:>13,} ║ ${total_codex_cost:>9.2f} ║ {total_all_tokens:>13,} ║ ${total_all_cost:>9.2f} ║")
    print("╚════════════╩═══════════════╩════════════╩═══════════════╩════════════╩═══════════════╩════════════╝")

    return {
        "total_claude_tokens": total_claude_tokens,
        "total_codex_tokens": total_codex_tokens,
        "total_claude_cost": total_claude_cost,
        "total_codex_cost": total_codex_cost,
        "total_all_tokens": total_all_tokens,
        "total_all_cost": total_all_cost
    }


def print_averages(combined_data: Dict[str, Dict], totals: Dict[str, float], days: int):
    """Print daily averages."""
    sorted_dates = sorted(combined_data.keys())
    complete_days = sorted_dates[:-1] if len(sorted_dates) > 1 else sorted_dates

    if len(complete_days) > 0:
        claude_7d = sum(combined_data[d]["claude_tokens"] for d in complete_days)
        codex_7d = sum(combined_data[d]["codex_tokens"] for d in complete_days)
        claude_cost_7d = sum(combined_data[d]["claude_cost"] for d in complete_days)
        codex_cost_7d = sum(combined_data[d]["codex_cost"] for d in complete_days)

        print("\n" + "=" * 90)
        print(f"DAILY AVERAGES (Last {len(complete_days)} complete days)")
        print("=" * 90)
        print(f"Claude:  {claude_7d/len(complete_days):>15,.0f} tokens/day  |  ${claude_cost_7d/len(complete_days):>9.2f}/day")
        print(f"Codex:   {codex_7d/len(complete_days):>15,.0f} tokens/day  |  ${codex_cost_7d/len(complete_days):>9.2f}/day")
        print(f"TOTAL:   {(claude_7d+codex_7d)/len(complete_days):>15,.0f} tokens/day  |  ${(claude_cost_7d+codex_cost_7d)/len(complete_days):>9.2f}/day")

    num_days = len(sorted_dates)
    if num_days > 0:
        print("\n" + "=" * 90)
        print(f"DAILY AVERAGES (All {num_days} days including today)")
        print("=" * 90)
        print(f"Claude:  {totals['total_claude_tokens']/num_days:>15,.0f} tokens/day  |  ${totals['total_claude_cost']/num_days:>9.2f}/day")
        print(f"Codex:   {totals['total_codex_tokens']/num_days:>15,.0f} tokens/day  |  ${totals['total_codex_cost']/num_days:>9.2f}/day")
        print(f"TOTAL:   {totals['total_all_tokens']/num_days:>15,.0f} tokens/day  |  ${totals['total_all_cost']/num_days:>9.2f}/day")
        print("=" * 90)


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

    print("Fetching Claude usage data...", file=sys.stderr)
    claude_data = get_claude_usage(since_date)

    print("Fetching Codex usage data...", file=sys.stderr)
    codex_data = get_codex_usage(since_date)

    combined_data = combine_data(claude_data, codex_data)

    if output_json:
        print(json.dumps({
            "combined_daily": combined_data,
            "claude_totals": claude_data.get("totals", {}),
            "codex_totals": codex_data.get("totals", {})
        }, indent=2))
    else:
        totals = print_table(combined_data)
        print_averages(combined_data, totals, days)


if __name__ == "__main__":
    main()
