import { execSync, execFileSync, spawn } from "node:child_process";
import { createInterface } from "node:readline";
import os from "node:os";
import path from "node:path";

// ccusage-codex scans all ~/.codex/sessions/**/*.jsonl regardless of --since,
// causing OOM on large session stores. Point it at a recent-only sessions dir.
const CODEX_HOME = path.join(os.homedir(), ".codex-recent");

export interface DailyEntry {
  date: string;
  totalTokens?: number;
  totalCost?: number;
  costUSD?: number;
}

export interface UsageData {
  daily: DailyEntry[];
  totals?: Record<string, unknown>;
}

export interface CombinedEntry {
  claude_tokens: number;
  claude_cost: number;
  codex_tokens: number;
  codex_cost: number;
  gemini_tokens: number;
  gemini_cost: number;
  opencode_tokens: number;
  opencode_cost: number;
}

export interface CombinedData {
  [date: string]: CombinedEntry;
}

const DEPS: Record<string, string> = {
  "ccusage": "ccusage",
  "ccusage-codex": "@ccusage/codex",
};

export function commandExists(cmd: string): boolean {
  try {
    const whichCmd = process.platform === "win32" ? "where" : "which";
    execSync(`${whichCmd} ${cmd}`, { stdio: "pipe" });
    return true;
  } catch {
    return false;
  }
}

export function hasRustCcusage(): boolean {
  try {
    const output = execSync("ccusage --help", { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] });
    return output.includes("openclaw") || output.includes("claude");
  } catch {
    return false;
  }
}

function askYesNo(prompt: string): Promise<boolean> {
  const rl = createInterface({ input: process.stdin, output: process.stderr });
  return new Promise((resolve) => {
    rl.on("close", () => {
      resolve(false);
    });
    rl.question(prompt, (answer) => {
      const a = answer.trim().toLowerCase();
      resolve(a === "" || a === "y" || a === "yes");
      rl.close();
    });
  });
}

export async function checkDependencies(isRust = false): Promise<void> {
  if (commandExists("ccusage")) {
    if (isRust) {
      return; // Self-contained!
    }
    if (commandExists("ccusage-codex")) {
      return;
    }
  }

  const missing: Record<string, string> = {};
  if (!commandExists("ccusage")) {
    missing["ccusage"] = "ccusage";
  }
  if (!isRust && !commandExists("ccusage-codex")) {
    missing["ccusage-codex"] = "@ccusage/codex";
  }
  if (Object.keys(missing).length === 0) return;

  const names = Object.keys(missing).join(", ");
  const pkgs = Object.values(missing);
  const installCmd = `npm install -g ${pkgs.join(" ")}`;

  process.stderr.write(`Error: Required commands not found: ${names}\n\n`);

  let shouldInstall = false;
  try {
    shouldInstall = await askYesNo(`Install them now? (${installCmd}) [Y/n] `);
  } catch {
    shouldInstall = false;
  }

  if (shouldInstall) {
    process.stderr.write(`Running: ${installCmd}\n`);
    try {
      execSync(installCmd, { stdio: "inherit" });
    } catch {
      process.stderr.write("Installation failed.\n");
      process.exit(1);
    }
    const stillMissing = Object.keys(missing).filter((cmd) => !commandExists(cmd));
    if (stillMissing.length > 0) {
      process.stderr.write(`Error: Commands still not found after install: ${stillMissing.join(", ")}\n`);
      process.exit(1);
    }
    process.stderr.write("Dependencies installed successfully.\n");
  } else {
    process.stderr.write(`Install manually with:\n  ${installCmd}\n`);
    process.exit(1);
  }
}

export function runCommand(cmd: string[]): string {
  try {
    const [bin, ...args] = cmd;
    return execFileSync(bin, args, { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] });
  } catch (err) {
    const error = err as Error & { code?: string };
    if (error.code === "ENOENT") {
      const pkg = DEPS[cmd[0]] ?? cmd[0];
      process.stderr.write(`Error: Command not found: ${cmd[0]}\n`);
      process.stderr.write(`  npm install -g ${pkg}\n`);
      process.exit(1);
    }
    process.stderr.write(`Error running command ${cmd.join(" ")}: ${error.message}\n`);
    process.exit(1);
    return "";
  }
}

export function getClaudeUsage(sinceDate: string): UsageData {
  const output = runCommand(["ccusage", "daily", "--since", sinceDate, "--order", "desc", "--json"]);
  return JSON.parse(output) as UsageData;
}

export function getCodexUsage(sinceDate: string): UsageData {
  const output = runCommand(["ccusage-codex", "daily", "--since", sinceDate, "--order", "desc", "--json"]);
  return JSON.parse(output) as UsageData;
}

export function runCommandAsync(cmd: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const [bin, ...args] = cmd;
    const env = bin === "ccusage-codex"
      ? { ...process.env, CODEX_HOME }
      : process.env;
    const child = spawn(bin, args, { stdio: ["pipe", "pipe", "pipe"], env });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (data: Buffer) => { stdout += data.toString(); });
    child.stderr.on("data", (data: Buffer) => { stderr += data.toString(); });
    child.on("error", (err: NodeJS.ErrnoException) => {
      if (err.code === "ENOENT") {
        const pkg = DEPS[cmd[0]] ?? cmd[0];
        reject(new Error(`Command not found: ${cmd[0]}\n  npm install -g ${pkg}`));
      } else {
        reject(new Error(`Error running ${cmd.join(" ")}: ${err.message}`));
      }
    });
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`Command ${cmd.join(" ")} exited with code ${code}\n${stderr}`));
      } else {
        resolve(stdout);
      }
    });
  });
}

export async function getClaudeUsageAsync(sinceDate: string, isRust = false): Promise<UsageData> {
  const cmd = isRust
    ? ["ccusage", "claude", "daily", "--since", sinceDate, "--order", "desc", "--json"]
    : ["ccusage", "daily", "--since", sinceDate, "--order", "desc", "--json"];
  const output = await runCommandAsync(cmd);
  return JSON.parse(output) as UsageData;
}

export async function getCodexUsageAsync(sinceDate: string, isRust = false): Promise<UsageData> {
  const cmd = isRust
    ? ["ccusage", "codex", "daily", "--since", sinceDate, "--order", "desc", "--json"]
    : ["ccusage-codex", "daily", "--since", sinceDate, "--order", "desc", "--json"];
  const output = await runCommandAsync(cmd);
  return JSON.parse(output) as UsageData;
}

export async function getGeminiUsageAsync(sinceDate: string, isRust = false): Promise<UsageData> {
  if (!isRust) return { daily: [] };
  const cmd = ["ccusage", "gemini", "daily", "--since", sinceDate, "--order", "desc", "--json"];
  const output = await runCommandAsync(cmd);
  return JSON.parse(output) as UsageData;
}

export async function getOpenCodeUsageAsync(sinceDate: string, isRust = false): Promise<UsageData> {
  const cmd = isRust
    ? ["ccusage", "opencode", "daily", "--since", sinceDate, "--order", "desc", "--json"]
    : ["ccusage-opencode", "daily", "--since", sinceDate, "--order", "desc", "--json"];
  try {
    const output = await runCommandAsync(cmd);
    return JSON.parse(output) as UsageData;
  } catch {
    return { daily: [] };
  }
}

export function normalizeDate(dateStr: string): string {
  if (dateStr.includes("-")) {
    return dateStr;
  }
  // Parse "Feb 11, 2026" format
  const dt = new Date(dateStr);
  if (isNaN(dt.getTime())) {
    return dateStr;
  }
  const year = dt.getFullYear();
  const month = String(dt.getMonth() + 1).padStart(2, "0");
  const day = String(dt.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function combineData(claudeData: UsageData, codexData: UsageData): CombinedData {
  return combineAllData({ claude: claudeData, codex: codexData });
}

export function combineAllData(agentDatasets: Record<string, UsageData>): CombinedData {
  const combined: CombinedData = {};

  for (const [agentName, dataset] of Object.entries(agentDatasets)) {
    for (const entry of dataset.daily ?? []) {
      const dateVal = entry.date || (entry as any).period;
      if (!dateVal) continue;
      const date = normalizeDate(dateVal);
      if (!combined[date]) {
        combined[date] = {
          claude_tokens: 0,
          claude_cost: 0,
          codex_tokens: 0,
          codex_cost: 0,
          gemini_tokens: 0,
          gemini_cost: 0,
          opencode_tokens: 0,
          opencode_cost: 0,
        };
      }
      const tokens = entry.totalTokens ?? 0;
      const cost = entry.totalCost ?? entry.costUSD ?? 0;
      
      (combined[date] as any)[`${agentName}_tokens`] = tokens;
      (combined[date] as any)[`${agentName}_cost`] = cost;
    }
  }

  return combined;
}
