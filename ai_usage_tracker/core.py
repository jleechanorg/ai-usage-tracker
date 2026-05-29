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


def has_rust_ccusage() -> bool:
    """Detect if ccusage is the Rust version supporting multiple subcommands."""
    try:
        result = subprocess.run(["ccusage", "--help"], capture_output=True, text=True, check=False)
        return result.returncode == 0 and ("openclaw" in result.stdout or "claude" in result.stdout)
    except Exception:
        return False


def get_claude_usage(since_date: str, is_rust: bool = False) -> Dict[str, Any]:
    """Fetch Claude usage data from ccusage."""
    if is_rust:
        cmd = ["ccusage", "claude", "daily", "--since", since_date, "--order", "desc", "--json"]
    else:
        cmd = ["ccusage", "daily", "--since", since_date, "--order", "desc", "--json"]
    output = run_command(cmd)
    return json.loads(output)


def get_codex_usage(since_date: str, is_rust: bool = False) -> Dict[str, Any]:
    """Fetch Codex usage data."""
    if is_rust:
        cmd = ["ccusage", "codex", "daily", "--since", since_date, "--order", "desc", "--json"]
    else:
        cmd = ["ccusage-codex", "daily", "--since", since_date, "--order", "desc", "--json"]
    output = run_command(cmd)
    return json.loads(output)


def get_gemini_usage(since_date: str, is_rust: bool = False) -> Dict[str, Any]:
    """Fetch Gemini (Antigravity) usage data."""
    if is_rust:
        cmd = ["ccusage", "gemini", "daily", "--since", since_date, "--order", "desc", "--json"]
        output = run_command(cmd)
        return json.loads(output)
    return {"daily": []}


def get_opencode_usage(since_date: str, is_rust: bool = False) -> Dict[str, Any]:
    """Fetch OpenCode usage data."""
    if is_rust:
        cmd = ["ccusage", "opencode", "daily", "--since", since_date, "--order", "desc", "--json"]
    else:
        cmd = ["ccusage-opencode", "daily", "--since", since_date, "--order", "desc", "--json"]
    try:
        output = run_command(cmd)
        return json.loads(output)
    except Exception:
        return {"daily": []}


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
    """Legacy compatibility function for original tests/users."""
    return combine_all_data({"claude": claude_data, "codex": codex_data})


def combine_all_data(agent_datasets: Dict[str, Dict]) -> Dict[str, Dict]:
    """Combine all agent datasets by date."""
    combined = {}
    
    # Initialize keys for all dates
    for agent_name, dataset in agent_datasets.items():
        for entry in dataset.get("daily", []):
            date = normalize_date(entry["date"])
            if date not in combined:
                combined[date] = {
                    "claude_tokens": 0,
                    "claude_cost": 0.0,
                    "codex_tokens": 0,
                    "codex_cost": 0.0,
                    "gemini_tokens": 0,
                    "gemini_cost": 0.0,
                    "opencode_tokens": 0,
                    "opencode_cost": 0.0
                }
            
            # Map cost key: ccusage uses totalCost, ccusage-codex uses costUSD, gemini uses totalCost
            tokens = entry.get("totalTokens", 0)
            cost = entry.get("totalCost", entry.get("costUSD", 0.0))
            
            combined[date][f"{agent_name}_tokens"] = tokens
            combined[date][f"{agent_name}_cost"] = cost
            
    return combined


def print_table(combined_data: Dict[str, Dict]):
    """Print the combined usage table."""
    active_agents = []
    for agent in ["claude", "codex", "gemini", "opencode"]:
        total_tokens_for_agent = sum(data.get(f"{agent}_tokens", 0) for data in combined_data.values())
        if total_tokens_for_agent > 0 or agent in ["claude", "codex"]:
            active_agents.append(agent)

    # Column configuration: (key_suffix, header_tokens, header_cost, tokens_width, cost_width)
    agent_configs = {
        "claude": ("claude", "Claude Tokens", "Claude $", 15, 12),
        "codex": ("codex", "Codex Tokens", "Codex $", 15, 12),
        "gemini": ("gemini", "Gemini Tokens", "Gemini $", 15, 12),
        "opencode": ("opencode", "OpenCode Toks", "OpenCode $", 15, 12),
    }

    # Format of column: (header_text, width, align, value_fn)
    columns = [
        ("Date", 12, "^", lambda d, date: date[5:] if len(date) > 5 else date)
    ]
    for agent in active_agents:
        cfg = agent_configs[agent]
        columns.append((cfg[1], cfg[3], ">", lambda d, date, a=cfg[0]: f"{d.get(f'{a}_tokens', 0):,}"))
        columns.append((cfg[2], cfg[4], ">", lambda d, date, a=cfg[0]: f"${d.get(f'{a}_cost', 0.0):>9.2f}"))
    
    # Add Totals
    columns.append(("Total Tokens", 15, ">", lambda d, date: f"{sum(d.get(f'{a}_tokens', 0) for a in active_agents):,}"))
    columns.append(("Total $", 12, ">", lambda d, date: f"${sum(d.get(f'{a}_cost', 0.0) for a in active_agents):>9.2f}"))

    # Print top border
    top_border = "╔" + "╦".join("═" * col[1] for col in columns) + "╗"
    header_row = "║" + "║".join(f"{col[0]:^{col[1]}}" for col in columns) + "║"
    middle_border = "╠" + "╬".join("═" * col[1] for col in columns) + "╣"
    bottom_border = "╚" + "╩".join("═" * col[1] for col in columns) + "╝"

    print("\n" + top_border)
    print(header_row)
    print(middle_border)

    # Initialize totals
    totals = {f"{a}_tokens": 0 for a in active_agents}
    totals.update({f"{a}_cost": 0.0 for a in active_agents})

    for date in sorted(combined_data.keys(), reverse=True):
        data = combined_data[date]
        
        # Accumulate totals
        for a in active_agents:
            totals[f"{a}_tokens"] += data.get(f"{a}_tokens", 0)
            totals[f"{a}_cost"] += data.get(f"{a}_cost", 0.0)
            
        row_cells = []
        for col in columns:
            val = col[3](data, date)
            if col[2] == "^":
                cell = f"{val:^{col[1]}}"
            elif col[2] == ">":
                cell = f"{val:>{col[1]}}"
            else:
                cell = f"{val:<{col[1]}}"
            row_cells.append(cell)
        print("║" + "║".join(row_cells) + "║")

    print(middle_border)
    
    total_tokens_sum = sum(totals[f"{a}_tokens"] for a in active_agents)
    total_cost_sum = sum(totals[f"{a}_cost"] for a in active_agents)
    
    total_row_cells = []
    total_row_cells.append(f"{'TOTAL':^12}")
    for agent in active_agents:
        cfg = agent_configs[agent]
        tok_val = f"{totals[f'{agent}_tokens']:,}"
        cost_val = f"${totals[f'{agent}_cost']:>9.2f}"
        total_row_cells.append(f"{tok_val:>{cfg[3]}}")
        total_row_cells.append(f"{cost_val:>{cfg[4]}}")
        
    tok_sum_val = f"{total_tokens_sum:,}"
    cost_sum_val = f"${total_cost_sum:>9.2f}"
    total_row_cells.append(f"{tok_sum_val:>15}")
    total_row_cells.append(f"{cost_sum_val:>12}")
    
    print("║" + "║".join(total_row_cells) + "║")
    print(bottom_border)

    return {
        "total_claude_tokens": totals.get("claude_tokens", 0),
        "total_codex_tokens": totals.get("codex_tokens", 0),
        "total_claude_cost": totals.get("claude_cost", 0.0),
        "total_codex_cost": totals.get("codex_cost", 0.0),
        "total_all_tokens": total_tokens_sum,
        "total_all_cost": total_cost_sum
    }


def print_averages(combined_data: Dict[str, Dict], totals: Dict[str, float]):
    """Print daily averages."""
    active_agents = []
    for agent in ["claude", "codex", "gemini", "opencode"]:
        total_tokens_for_agent = sum(data.get(f"{agent}_tokens", 0) for data in combined_data.values())
        if total_tokens_for_agent > 0 or agent in ["claude", "codex"]:
            active_agents.append(agent)

    agent_names = {
        "claude": "Claude",
        "codex": "Codex",
        "gemini": "Gemini",
        "opencode": "OpenCode",
    }

    sorted_dates = sorted(combined_data.keys())
    complete_days = sorted_dates[:-1] if len(sorted_dates) > 1 else sorted_dates

    if len(complete_days) > 0:
        print("\n" + "=" * 90)
        print(f"DAILY AVERAGES (Last {len(complete_days)} complete days)")
        print("=" * 90)
        
        total_tokens_sum = 0
        total_cost_sum = 0.0
        for agent in active_agents:
            agent_tokens = sum(combined_data[d].get(f"{agent}_tokens", 0) for d in complete_days)
            agent_cost = sum(combined_data[d].get(f"{agent}_cost", 0.0) for d in complete_days)
            total_tokens_sum += agent_tokens
            total_cost_sum += agent_cost
            print(f"{agent_names[agent]:<8}: {agent_tokens/len(complete_days):>15,.0f} tokens/day  |  ${agent_cost/len(complete_days):>9.2f}/day")
            
        print("-" * 90)
        print(f"TOTAL   : {total_tokens_sum/len(complete_days):>15,.0f} tokens/day  |  ${total_cost_sum/len(complete_days):>9.2f}/day")

    num_days = len(sorted_dates)
    if num_days > 0:
        print("\n" + "=" * 90)
        print(f"DAILY AVERAGES (All {num_days} days including today)")
        print("=" * 90)
        
        total_tokens_sum = 0
        total_cost_sum = 0.0
        for agent in active_agents:
            agent_tokens = sum(combined_data[d].get(f"{agent}_tokens", 0) for d in sorted_dates)
            agent_cost = sum(combined_data[d].get(f"{agent}_cost", 0.0) for d in sorted_dates)
            total_tokens_sum += agent_tokens
            total_cost_sum += agent_cost
            print(f"{agent_names[agent]:<8}: {agent_tokens/num_days:>15,.0f} tokens/day  |  ${agent_cost/num_days:>9.2f}/day")
            
        print("-" * 90)
        print(f"TOTAL   : {total_tokens_sum/num_days:>15,.0f} tokens/day  |  ${total_cost_sum/num_days:>9.2f}/day")
        print("=" * 90)
