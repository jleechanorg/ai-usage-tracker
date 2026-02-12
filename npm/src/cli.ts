#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { getClaudeUsageAsync, getCodexUsageAsync, combineData, checkDependencies } from "./tracker.js";
import type { CombinedData } from "./tracker.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pkg = JSON.parse(readFileSync(join(__dirname, "..", "package.json"), "utf-8"));
const VERSION: string = pkg.version;

function formatNumber(n: number): string {
  return n.toLocaleString("en-US");
}

function printTable(combinedData: CombinedData): Record<string, number> {
  console.log("");
  console.log("╔════════════╦═══════════════╦════════════╦═══════════════╦════════════╦═══════════════╦════════════╗");
  console.log("║    Date    ║ Claude Tokens ║ Claude $   ║ Codex Tokens  ║  Codex $   ║ Total Tokens  ║  Total $   ║");
  console.log("╠════════════╬═══════════════╬════════════╬═══════════════╬════════════╬═══════════════╬════════════╣");

  let totalClaudeTokens = 0;
  let totalCodexTokens = 0;
  let totalClaudeCost = 0;
  let totalCodexCost = 0;

  const dates = Object.keys(combinedData).sort().reverse();
  for (const date of dates) {
    const data = combinedData[date];
    const claudeTokens = data.claude_tokens;
    const claudeCost = data.claude_cost;
    const codexTokens = data.codex_tokens;
    const codexCost = data.codex_cost;

    const totalTokens = claudeTokens + codexTokens;
    const totalCost = claudeCost + codexCost;

    totalClaudeTokens += claudeTokens;
    totalCodexTokens += codexTokens;
    totalClaudeCost += claudeCost;
    totalCodexCost += codexCost;

    const dateShort = date.slice(5);
    console.log(
      `║ ${dateShort} ║ ${formatNumber(claudeTokens).padStart(13)} ║ $${claudeCost.toFixed(2).padStart(9)} ║ ${formatNumber(codexTokens).padStart(13)} ║ $${codexCost.toFixed(2).padStart(9)} ║ ${formatNumber(totalTokens).padStart(13)} ║ $${totalCost.toFixed(2).padStart(9)} ║`
    );
  }

  console.log("╠════════════╬═══════════════╬════════════╬═══════════════╬════════════╬═══════════════╬════════════╣");
  const totalAllTokens = totalClaudeTokens + totalCodexTokens;
  const totalAllCost = totalClaudeCost + totalCodexCost;

  console.log(
    `║   TOTAL    ║ ${formatNumber(totalClaudeTokens).padStart(13)} ║ $${totalClaudeCost.toFixed(2).padStart(9)} ║ ${formatNumber(totalCodexTokens).padStart(13)} ║ $${totalCodexCost.toFixed(2).padStart(9)} ║ ${formatNumber(totalAllTokens).padStart(13)} ║ $${totalAllCost.toFixed(2).padStart(9)} ║`
  );
  console.log("╚════════════╩═══════════════╩════════════╩═══════════════╩════════════╩═══════════════╩════════════╝");

  return {
    total_claude_tokens: totalClaudeTokens,
    total_codex_tokens: totalCodexTokens,
    total_claude_cost: totalClaudeCost,
    total_codex_cost: totalCodexCost,
    total_all_tokens: totalAllTokens,
    total_all_cost: totalAllCost,
  };
}

function printAverages(combinedData: CombinedData, totals: Record<string, number>): void {
  const sortedDates = Object.keys(combinedData).sort();
  const completeDays = sortedDates.length > 1 ? sortedDates.slice(0, -1) : sortedDates;

  if (completeDays.length > 0) {
    let claude7d = 0, codex7d = 0, claudeCost7d = 0, codexCost7d = 0;
    for (const d of completeDays) {
      claude7d += combinedData[d].claude_tokens;
      codex7d += combinedData[d].codex_tokens;
      claudeCost7d += combinedData[d].claude_cost;
      codexCost7d += combinedData[d].codex_cost;
    }
    const n = completeDays.length;
    console.log("");
    console.log("=".repeat(90));
    console.log(`DAILY AVERAGES (Last ${n} complete days)`);
    console.log("=".repeat(90));
    console.log(`Claude:  ${formatNumber(Math.round(claude7d / n)).padStart(15)} tokens/day  |  $${(claudeCost7d / n).toFixed(2).padStart(9)}/day`);
    console.log(`Codex:   ${formatNumber(Math.round(codex7d / n)).padStart(15)} tokens/day  |  $${(codexCost7d / n).toFixed(2).padStart(9)}/day`);
    console.log(`TOTAL:   ${formatNumber(Math.round((claude7d + codex7d) / n)).padStart(15)} tokens/day  |  $${((claudeCost7d + codexCost7d) / n).toFixed(2).padStart(9)}/day`);
  }

  const numDays = sortedDates.length;
  if (numDays > 0) {
    console.log("");
    console.log("=".repeat(90));
    console.log(`DAILY AVERAGES (All ${numDays} days including today)`);
    console.log("=".repeat(90));
    console.log(`Claude:  ${formatNumber(Math.round(totals.total_claude_tokens / numDays)).padStart(15)} tokens/day  |  $${(totals.total_claude_cost / numDays).toFixed(2).padStart(9)}/day`);
    console.log(`Codex:   ${formatNumber(Math.round(totals.total_codex_tokens / numDays)).padStart(15)} tokens/day  |  $${(totals.total_codex_cost / numDays).toFixed(2).padStart(9)}/day`);
    console.log(`TOTAL:   ${formatNumber(Math.round(totals.total_all_tokens / numDays)).padStart(15)} tokens/day  |  $${(totals.total_all_cost / numDays).toFixed(2).padStart(9)}/day`);
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

  await checkDependencies();

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

  process.stderr.write("Fetching Claude and Codex usage data in parallel...\n");
  const [claudeData, codexData] = await Promise.all([
    getClaudeUsageAsync(sinceDate),
    getCodexUsageAsync(sinceDate),
  ]);

  const combinedData = combineData(claudeData, codexData);

  if (outputJson) {
    console.log(JSON.stringify({
      combined_daily: combinedData,
      claude_totals: claudeData.totals ?? {},
      codex_totals: codexData.totals ?? {},
    }, null, 2));
  } else {
    const totals = printTable(combinedData);
    printAverages(combinedData, totals);
  }
}

main().catch((err) => {
  process.stderr.write(`${err.message}\n`);
  process.exit(1);
});
