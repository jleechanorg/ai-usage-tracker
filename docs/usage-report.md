# Combined Claude + Codex Token Usage Report

Generated: February 11, 2026

## Summary

This report provides a comprehensive overview of token usage and costs across both Claude Code and Codex CLI for the past 7-8 days.

## Usage Table

```
╔════════════╦═══════════════╦════════════╦═══════════════╦════════════╦═══════════════╦════════════╗
║    Date    ║ Claude Tokens ║ Claude $   ║ Codex Tokens  ║  Codex $   ║ Total Tokens  ║  Total $   ║
╠════════════╬═══════════════╬════════════╬═══════════════╬════════════╬═══════════════╬════════════╣
║ 02-11      ║    88,155,247 ║ $    37.31 ║    67,371,956 ║ $    12.82 ║   155,527,203 ║ $    50.13 ║
║ 02-10      ║   368,293,666 ║ $   160.69 ║   764,117,407 ║ $   144.86 ║ 1,132,411,073 ║ $   305.55 ║
║ 02-09      ║   195,176,795 ║ $    95.18 ║ 1,902,892,432 ║ $   350.69 ║ 2,098,069,227 ║ $   445.87 ║
║ 02-08      ║   360,956,254 ║ $   178.77 ║   707,866,133 ║ $   135.88 ║ 1,068,822,387 ║ $   314.65 ║
║ 02-07      ║   154,045,981 ║ $    77.06 ║    15,776,566 ║ $     4.37 ║   169,822,547 ║ $    81.43 ║
║ 02-06      ║   166,425,314 ║ $    79.33 ║    24,518,063 ║ $     6.57 ║   190,943,377 ║ $    85.90 ║
║ 02-05      ║   164,151,306 ║ $    98.78 ║     1,854,455 ║ $     0.54 ║   166,005,761 ║ $    99.32 ║
║ 02-04      ║   252,827,149 ║ $   173.95 ║   166,021,233 ║ $    48.41 ║   418,848,382 ║ $   222.36 ║
╠════════════╬═══════════════╬════════════╬═══════════════╬════════════╬═══════════════╬════════════╣
║   TOTAL    ║ 1,750,031,712 ║ $   901.07 ║ 3,650,418,245 ║ $   704.14 ║ 5,400,449,957 ║ $ 1,605.21 ║
╚════════════╩═══════════════╩════════════╩═══════════════╩════════════╩═══════════════╩════════════╝
```

## Daily Averages

### Last 7 Complete Days (Feb 4-10)
- **Claude**: 237,410,924 tokens/day | $123.39/day
- **Codex**: 511,863,756 tokens/day | $98.76/day
- **TOTAL**: 749,274,679 tokens/day | $222.15/day

### All 8 Days Including Today (Feb 4-11)
- **Claude**: 218,753,964 tokens/day | $112.63/day
- **Codex**: 456,302,281 tokens/day | $88.02/day
- **TOTAL**: 675,056,245 tokens/day | $200.65/day

## Key Insights

### Usage Distribution
- **Codex dominates token usage**: ~67% of total tokens (3.65B vs 1.75B)
- **Claude costs more per token**: $901 for 1.75B tokens vs $704 for 3.65B tokens
- **Cost ratio**: Claude tokens are ~2.8x more expensive than Codex tokens

### Peak Usage Day
- **February 9th** had the highest usage: 2.1B tokens costing $445.87
- This was driven primarily by Codex usage (1.9B tokens)

### Cache Efficiency
- Both tools show excellent cache efficiency with 90%+ cache read rates
- Cache reads significantly reduce costs for both Claude and Codex

### Cost Analysis
- **8-day total cost**: $1,605.21
- **Average daily cost**: $200.65/day
- **Projected monthly cost**: ~$6,020 (based on current usage patterns)

## Models Used

### Claude
- claude-sonnet-4-5-20250929 (primary)
- claude-haiku-4-5-20251001 (lighter tasks)
- claude-opus-4-6 (complex tasks)
- claude-opus-4-5-20251101 (specialized tasks)

### Codex
- gpt-5.3-codex (primary)
- gpt-5.2-codex (fallback)
- gpt-5-codex (specific use cases)

## Recommendations

1. **Monitor Codex usage closely** - It accounts for 67% of token usage
2. **Cache efficiency is excellent** - Continue using context caching strategies
3. **Peak day analysis** - Investigate what caused the Feb 9 spike (1.9B Codex tokens)
4. **Budget planning** - At current rates, expect ~$6K/month in AI costs
5. **Consider usage patterns** - Evaluate if all high-volume operations are necessary

## How to Generate This Report

Run the following command:
```bash
./scripts/combined-usage-report.sh
```

Or use the Claude Code skill:
```
/combined-usage
```

---

*Report generated automatically from ccusage and ccusage-codex data*
