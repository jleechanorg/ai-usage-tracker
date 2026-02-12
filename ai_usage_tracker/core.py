"""Core functionality shared between CLI and standalone script."""

import json
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict

DEPS = {
    "ccusage": "ccusage",
    "ccusage-codex": "@ccusage/codex",
}


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


def print_averages(combined_data: Dict[str, Dict], totals: Dict[str, float]):
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
