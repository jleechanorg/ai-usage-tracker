#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  getClaudeUsageAsync,
  getCodexUsageAsync,
  getGeminiUsageAsync,
  getOpenCodeUsageAsync,
  combineAllData,
  checkDependencies,
  hasRustCcusage,
} from "./tracker.js";
import type { CombinedData, CombinedEntry, UsageData } from "./tracker.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pkg = JSON.parse(readFileSync(join(__dirname, "..", "package.json"), "utf-8"));
const VERSION: string = pkg.version;

function formatNumber(n: number): string {
  return n.toLocaleString("en-US");
}

function printTable(combinedData: CombinedData): Record<string, number> {
  const activeAgents: string[] = [];
  for (const agent of ["claude", "codex", "gemini", "opencode"]) {
    let sumTokens = 0;
    for (const d of Object.values(combinedData)) {
      sumTokens += (d as any)[`${agent}_tokens`] || 0;
    }
    if (sumTokens > 0 || agent === "claude" || agent === "codex") {
      activeAgents.push(agent);
    }
  }

  const agentConfigs: Record<string, { key: string; headerToks: string; headerCost: string; tokWidth: number; costWidth: number }> = {
    claude: { key: "claude", headerToks: "Claude Tokens", headerCost: "Claude $", tokWidth: 15, costWidth: 12 },
    codex: { key: "codex", headerToks: "Codex Tokens", headerCost: "Codex $", tokWidth: 15, costWidth: 12 },
    gemini: { key: "gemini", headerToks: "Gemini Tokens", headerCost: "Gemini $", tokWidth: 15, costWidth: 12 },
    opencode: { key: "opencode", headerToks: "OpenCode Toks", headerCost: "OpenCode $", tokWidth: 15, costWidth: 12 },
  };

  interface ColSpec {
    header: string;
    width: number;
    align: string;
    valFn: (d: CombinedEntry, date: string) => string;
  }

  const columns: ColSpec[] = [
    {
      header: "Date",
      width: 12,
      align: "^",
      valFn: (_, date) => (date.length > 5 ? date.slice(5) : date),
    },
  ];

  for (const agent of activeAgents) {
    const cfg = agentConfigs[agent];
    columns.push({
      header: cfg.headerToks,
      width: cfg.tokWidth,
      align: ">",
      valFn: (d) => formatNumber((d as any)[`${cfg.key}_tokens`]).padStart(cfg.tokWidth),
    });
    columns.push({
      header: cfg.headerCost,
      width: cfg.costWidth,
      align: ">",
      valFn: (d) => `$${(d as any)[`${cfg.key}_cost`].toFixed(2).padStart(9)}`,
    });
  }

  columns.push({
    header: "Total Tokens",
    width: 15,
    align: ">",
    valFn: (d) => {
      let sumToks = 0;
      for (const a of activeAgents) {
        sumToks += (d as any)[`${a}_tokens`] || 0;
      }
      return formatNumber(sumToks).padStart(15);
    },
  });
  columns.push({
    header: "Total $",
    width: 12,
    align: ">",
    valFn: (d) => {
      let sumCost = 0;
      for (const a of activeAgents) {
        sumCost += (d as any)[`${a}_cost`] || 0;
      }
      return `$${sumCost.toFixed(2).padStart(9)}`;
    },
  });

  const borderLine = (left: string, mid: string, right: string) => {
    return left + columns.map((col) => "═".repeat(col.width)).join(mid) + right;
  };

  const topBorder = borderLine("╔", "╦", "╗");
  const middleBorder = borderLine("╠", "╬", "╣");
  const bottomBorder = borderLine("╚", "╩", "╝");

  const headerRow =
    "║" +
    columns
      .map((col) => {
        const padLen = col.width - col.header.length;
        const leftPad = Math.floor(padLen / 2);
        const rightPad = padLen - leftPad;
        return " ".repeat(leftPad) + col.header + " ".repeat(rightPad);
      })
      .join("║") +
    "║";

  console.log("");
  console.log(topBorder);
  console.log(headerRow);
  console.log(middleBorder);

  const totals: Record<string, number> = {};
  for (const a of activeAgents) {
    totals[`${a}_tokens`] = 0;
    totals[`${a}_cost`] = 0;
  }

  const dates = Object.keys(combinedData).sort().reverse();
  for (const date of dates) {
    const data = combinedData[date];
    for (const a of activeAgents) {
      totals[`${a}_tokens`] += (data as any)[`${a}_tokens`] || 0;
      totals[`${a}_cost`] += (data as any)[`${a}_cost`] || 0;
    }

    const rowCells = columns.map((col) => {
      const val = col.valFn(data, date);
      if (col.align === "^") {
        const padLen = col.width - val.length;
        const leftPad = Math.floor(padLen / 2);
        const rightPad = padLen - leftPad;
        return " ".repeat(leftPad) + val + " ".repeat(rightPad);
      } else if (col.align === ">") {
        return val.padStart(col.width);
      } else {
        return val.padEnd(col.width);
      }
    });
    console.log("║" + rowCells.join("║") + "║");
  }

  console.log(middleBorder);

  let totalTokensSum = 0;
  let totalCostSum = 0;
  for (const a of activeAgents) {
    totalTokensSum += totals[`${a}_tokens`];
    totalCostSum += totals[`${a}_cost`];
  }

  const totalRowCells: string[] = [];
  totalRowCells.push("   TOTAL    ");

  for (const agent of activeAgents) {
    const cfg = agentConfigs[agent];
    const tokVal = formatNumber(totals[`${agent}_tokens`]);
    const costVal = `$${totals[`${agent}_cost`].toFixed(2)}`;
    totalRowCells.push(tokVal.padStart(cfg.tokWidth));
    totalRowCells.push(costVal.padStart(cfg.costWidth));
  }

  totalRowCells.push(formatNumber(totalTokensSum).padStart(15));
  totalRowCells.push(`$${totalCostSum.toFixed(2)}`.padStart(12));

  console.log("║" + totalRowCells.join("║") + "║");
  console.log(bottomBorder);

  const compatTotals: Record<string, number> = {
    total_claude_tokens: totals["claude_tokens"] || 0,
    total_codex_tokens: totals["codex_tokens"] || 0,
    total_claude_cost: totals["claude_cost"] || 0,
    total_codex_cost: totals["codex_cost"] || 0,
    total_all_tokens: totalTokensSum,
    total_all_cost: totalCostSum,
  };
  return compatTotals;
}

function printAverages(combinedData: CombinedData, totals: Record<string, number>): void {
  const activeAgents: string[] = [];
  for (const agent of ["claude", "codex", "gemini", "opencode"]) {
    let sumTokens = 0;
    for (const d of Object.values(combinedData)) {
      sumTokens += (d as any)[`${agent}_tokens`] || 0;
    }
    if (sumTokens > 0 || agent === "claude" || agent === "codex") {
      activeAgents.push(agent);
    }
  }

  const agentNames: Record<string, string> = {
    claude: "Claude",
    codex: "Codex",
    gemini: "Gemini",
    opencode: "OpenCode",
  };

  const sortedDates = Object.keys(combinedData).sort();
  const completeDays = sortedDates.length > 1 ? sortedDates.slice(0, -1) : sortedDates;

  if (completeDays.length > 0) {
    console.log("");
    console.log("=".repeat(90));
    console.log(`DAILY AVERAGES (Last ${completeDays.length} complete days)`);
    console.log("=".repeat(90));
    
    let totalTokensSum = 0;
    let totalCostSum = 0;
    const n = completeDays.length;

    for (const agent of activeAgents) {
      let agentTokens = 0;
      let agentCost = 0;
      for (const d of completeDays) {
        agentTokens += (combinedData[d] as any)[`${agent}_tokens`] || 0;
        agentCost += (combinedData[d] as any)[`${agent}_cost`] || 0;
      }
      totalTokensSum += agentTokens;
      totalCostSum += agentCost;
      console.log(`${agentNames[agent].padEnd(8)}: ${formatNumber(Math.round(agentTokens / n)).padStart(15)} tokens/day  |  $${(agentCost / n).toFixed(2).padStart(9)}/day`);
    }

    console.log("-".repeat(90));
    console.log(`TOTAL   : ${formatNumber(Math.round(totalTokensSum / n)).padStart(15)} tokens/day  |  $${(totalCostSum / n).toFixed(2).padStart(9)}/day`);
  }

  const numDays = sortedDates.length;
  if (numDays > 0) {
    console.log("");
    console.log("=".repeat(90));
    console.log(`DAILY AVERAGES (All ${numDays} days including today)`);
    console.log("=".repeat(90));
    
    let totalTokensSum = 0;
    let totalCostSum = 0;

    for (const agent of activeAgents) {
      let agentTokens = 0;
      let agentCost = 0;
      for (const d of sortedDates) {
        agentTokens += (combinedData[d] as any)[`${agent}_tokens`] || 0;
        agentCost += (combinedData[d] as any)[`${agent}_cost`] || 0;
      }
      totalTokensSum += agentTokens;
      totalCostSum += agentCost;
      console.log(`${agentNames[agent].padEnd(8)}: ${formatNumber(Math.round(agentTokens / numDays)).padStart(15)} tokens/day  |  $${(agentCost / numDays).toFixed(2).padStart(9)}/day`);
    }

    console.log("-".repeat(90));
    console.log(`TOTAL   : ${formatNumber(Math.round(totalTokensSum / numDays)).padStart(15)} tokens/day  |  $${(totalCostSum / numDays).toFixed(2).padStart(9)}/day`);
    console.log("=".repeat(90));
  }
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  let days = 7;
  let outputJson = false;

  if (args.includes("--version") || args.includes("-V")) {
    console.log(`ai-usage-tracker ${VERSION}`);
    process.exit(0);
  }

  if (args.includes("--help") || args.includes("-h")) {
    console.log(`
ai-usage-tracker ${VERSION} - Combined Claude + Codex Token Usage Report

Usage:
  ai-usage-tracker-js [--days DAYS] [--json]

Options:
  --days DAYS    Number of days to include in report (default: 7)
  --json         Output in JSON format
  --version      Show version number
  --help         Show this help message
`);
    process.exit(0);
  }

  const isRust = hasRustCcusage();
  await checkDependencies(isRust);

  const daysIdx = args.indexOf("--days");
  if (daysIdx !== -1 && daysIdx + 1 < args.length) {
    const parsed = parseInt(args[daysIdx + 1], 10);
    if (isNaN(parsed) || parsed < 1) {
      process.stderr.write("Error: --days must be a positive integer\n");
      process.exit(1);
    }
    days = parsed;
  }

  if (args.includes("--json")) {
    outputJson = true;
  }

  const since = new Date();
  since.setDate(since.getDate() - days);
  const year = since.getFullYear();
  const month = String(since.getMonth() + 1).padStart(2, '0');
  const day = String(since.getDate()).padStart(2, '0');
  const sinceDate = `${year}${month}${day}`;

  process.stderr.write(isRust
    ? "Fetching Claude, Codex, Gemini, and OpenCode usage data in parallel...\n"
    : "Fetching Claude and Codex usage data in parallel...\n"
  );

  let claudeData: UsageData;
  let codexData: UsageData;
  let geminiData: UsageData;
  let opencodeData: UsageData;

  if (isRust) {
    const results = await Promise.all([
      getClaudeUsageAsync(sinceDate, true),
      getCodexUsageAsync(sinceDate, true),
      getGeminiUsageAsync(sinceDate, true),
      getOpenCodeUsageAsync(sinceDate, true),
    ]);
    claudeData = results[0];
    codexData = results[1];
    geminiData = results[2];
    opencodeData = results[3];
  } else {
    const results = await Promise.all([
      getClaudeUsageAsync(sinceDate, false),
      getCodexUsageAsync(sinceDate, false),
    ]);
    claudeData = results[0];
    codexData = results[1];
    geminiData = { daily: [] };
    opencodeData = { daily: [] };
  }

  const combinedData = combineAllData(isRust ? {
    claude: claudeData,
    codex: codexData,
    gemini: geminiData,
    opencode: opencodeData,
  } : {
    claude: claudeData,
    codex: codexData,
  });

  if (outputJson) {
    const res: Record<string, any> = {
      combined_daily: combinedData,
      claude_totals: claudeData.totals ?? {},
      codex_totals: codexData.totals ?? {},
    };
    if (isRust) {
      res.gemini_totals = geminiData.totals ?? {};
      res.opencode_totals = opencodeData.totals ?? {};
    }
    console.log(JSON.stringify(res, null, 2));
  } else {
    const totals = printTable(combinedData);
    printAverages(combinedData, totals);
  }
}

main().catch((err) => {
  process.stderr.write(`${err.message}\n`);
  process.exit(1);
});
