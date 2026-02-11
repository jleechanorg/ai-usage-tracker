# AI Usage Tracker

A comprehensive token usage and cost tracking tool for Claude Code and Codex CLI.

## Overview

This tool combines usage data from both `ccusage` (Claude) and `ccusage-codex` (Codex) to provide a unified view of your AI token consumption and associated costs.

## Features

- **Combined Reporting**: View Claude and Codex usage side-by-side
- **Cost Analysis**: Track spending across both platforms
- **Daily Averages**: Calculate average usage over time
- **Cache Efficiency**: Monitor cache read rates and savings
- **Flexible Output**: Table format for humans, JSON for automation
- **Claude Skill**: Invoke directly from Claude Code CLI

## Installation

### Prerequisites

- Python 3.6 or higher
- `ccusage` CLI (for Claude token usage)
- `ccusage-codex` CLI (for Codex token usage)

### Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd ai-usage-tracker
```

2. Make the script executable:
```bash
chmod +x scripts/combined-usage-report.py
```

3. (Optional) Install as a Claude skill by symlinking:
```bash
ln -s $(pwd)/.claude/skills/combined-usage ~/.claude/skills/combined-usage
```

## Usage

### Command Line

```bash
# Default: Last 7 days
python3 scripts/combined-usage-report.py

# Custom date range
python3 scripts/combined-usage-report.py --days 14

# JSON output
python3 scripts/combined-usage-report.py --json
```

### Claude Skill

If installed as a skill:
```
/combined-usage
```

## Example Output

```
╔════════════╦═══════════════╦════════════╦═══════════════╦════════════╦═══════════════╦════════════╗
║    Date    ║ Claude Tokens ║ Claude $   ║ Codex Tokens  ║  Codex $   ║ Total Tokens  ║  Total $   ║
╠════════════╬═══════════════╬════════════╬═══════════════╬════════════╬═══════════════╬════════════╣
║ 02-11      ║    88,155,247 ║ $    37.31 ║    67,371,956 ║ $    12.82 ║   155,527,203 ║ $    50.13 ║
║ 02-10      ║   368,293,666 ║ $   160.69 ║   764,117,407 ║ $   144.86 ║ 1,132,411,073 ║ $   305.55 ║
...
╚════════════╩═══════════════╩════════════╩═══════════════╩════════════╩═══════════════╩════════════╝

DAILY AVERAGES (Last 7 complete days)
Claude:      237,410,924 tokens/day  |  $123.39/day
Codex:       511,863,756 tokens/day  |  $98.76/day
TOTAL:       749,274,679 tokens/day  |  $222.15/day
```

## Documentation

See [docs/usage-report.md](docs/usage-report.md) for a complete example report with insights and recommendations.

## Repository Structure

```
ai-usage-tracker/
├── README.md                           # This file
├── docs/
│   └── usage-report.md                 # Example report with analysis
├── scripts/
│   └── combined-usage-report.py        # Main script
└── .claude/
    └── skills/
        └── combined-usage              # Claude skill definition
```

## Key Insights

Based on typical usage patterns:

- **Token Distribution**: Codex typically accounts for ~67% of total tokens
- **Cost Ratio**: Claude tokens are ~2.8x more expensive than Codex tokens
- **Cache Efficiency**: Both tools maintain 90%+ cache read rates
- **Average Daily Cost**: Typically ranges from $150-250/day for heavy usage

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## License

MIT License - Feel free to use and modify as needed.

## Credits

Built for tracking usage across:
- [Claude Code](https://github.com/anthropics/claude-code)
- [Codex CLI](https://github.com/codex-cli)
