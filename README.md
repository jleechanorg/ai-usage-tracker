# AI Usage Tracker

A comprehensive token usage and cost tracking tool for Claude Code and Codex CLI.

## Overview

This tool combines usage data from both `ccusage` (Claude) and `ccusage-codex` (Codex) to provide a unified view of your AI token consumption and associated costs.

## Quick Start

### Install via pip (Python)

```bash
pip install ai-usage-tracker
ai-usage-tracker
```

### Install via npm (Node.js)

```bash
npm install -g ai-usage-tracker
ai-usage-tracker-js
```

### Install from source

```bash
git clone https://github.com/jleechanorg/ai-usage-tracker.git
cd ai-usage-tracker

# Install dependencies (ccusage and ccusage-codex)
./scripts/install-dependencies.sh

# Run the report
python3 scripts/combined-usage-report.py

# Or install as a Claude skill
ln -s $(pwd)/.claude/skills/combined-usage ~/.claude/skills/combined-usage
# Then use: /combined-usage
```

## Features

- **Combined Reporting**: View Claude and Codex usage side-by-side
- **Cost Analysis**: Track spending across both platforms
- **Daily Averages**: Calculate average usage over time
- **Cache Efficiency**: Monitor cache read rates and savings
- **Flexible Output**: Table format for humans, JSON for automation
- **Claude Skill**: Invoke directly from Claude Code CLI

## Installation

### Option 1: pip (Recommended)

```bash
pip install ai-usage-tracker
```

### Option 2: npm

```bash
npm install -g ai-usage-tracker
```

### Option 3: From source

```bash
git clone https://github.com/jleechanorg/ai-usage-tracker.git
cd ai-usage-tracker
pip install .
```

### Prerequisites

Both the pip and npm packages require `ccusage` and `ccusage-codex` CLI tools:

```bash
npm install -g ccusage @ccusage/codex
```

Or use the automated installation script:

```bash
./scripts/install-dependencies.sh
```

### Optional: Claude Skill

```bash
ln -s $(pwd)/.claude/skills/combined-usage ~/.claude/skills/combined-usage
```

## Usage

### Python (pip install)

```bash
# Default: Last 7 days
ai-usage-tracker

# Custom date range
ai-usage-tracker --days 14

# JSON output
ai-usage-tracker --json
```

### Node.js (npm install)

```bash
# Default: Last 7 days
ai-usage-tracker-js

# Custom date range
ai-usage-tracker-js --days 14

# JSON output
ai-usage-tracker-js --json
```

### From source

```bash
python3 scripts/combined-usage-report.py
python3 scripts/combined-usage-report.py --days 14
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

## Packages

| Package | Registry | Install |
|---------|----------|---------|
| [ai-usage-tracker](https://pypi.org/project/ai-usage-tracker/) | PyPI | `pip install ai-usage-tracker` |
| [ai-usage-tracker](https://www.npmjs.com/package/ai-usage-tracker) | npm | `npm install -g ai-usage-tracker` |

## Repository Structure

```
ai-usage-tracker/
├── README.md                           # This file
├── CHANGELOG.md                        # Version history
├── pyproject.toml                      # Python package config (PyPI)
├── ai_usage_tracker/                   # Python package source
│   ├── __init__.py
│   └── cli.py                          # CLI entry point
├── npm/                                # Node.js package source
│   ├── package.json                    # npm package config
│   ├── tsconfig.json
│   └── src/
│       ├── index.ts                    # Library exports
│       ├── tracker.ts                  # Core logic
│       └── cli.ts                      # CLI entry point
├── docs/
│   └── usage-report.md                 # Example report with analysis
├── scripts/
│   ├── install-dependencies.sh         # Automated installation script
│   └── combined-usage-report.py        # Original report generator
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
