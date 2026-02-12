import { execSync, execFileSync, spawnSync, spawn } from "node:child_process";
import { createInterface } from "node:readline";

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
}

export interface CombinedData {
  [date: string]: CombinedEntry;
}

const DEPS: Record<string, string> = {
  "ccusage": "ccusage",
  "ccusage-codex": "@ccusage/codex",
};

function commandExists(cmd: string): boolean {
  try {
    const whichCmd = process.platform === "win32" ? "where" : "which";
    execSync(`${whichCmd} ${cmd}`, { stdio: "pipe" });
    return true;
  } catch {
    return false;
  }
}

function askYesNo(prompt: string): Promise<boolean> {
  const rl = createInterface({ input: process.stdin, output: process.stderr });
  return new Promise((resolve) => {
    rl.question(prompt, (answer) => {
      rl.close();
      const a = answer.trim().toLowerCase();
      resolve(a === "" || a === "y" || a === "yes");
    });
  });
}

export async function checkDependencies(): Promise<void> {
  const missing: Record<string, string> = {};
  for (const [cmd, pkg] of Object.entries(DEPS)) {
    if (!commandExists(cmd)) {
      missing[cmd] = pkg;
    }
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
    const result = spawnSync("npm", ["install", "-g", ...pkgs], { stdio: "inherit" });
    if (result.status !== 0) {
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
    return ""; // unreachable, satisfies TS
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
    const child = spawn(bin, args, { stdio: ["pipe", "pipe", "pipe"] });
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

export async function getClaudeUsageAsync(sinceDate: string): Promise<UsageData> {
  const output = await runCommandAsync(["ccusage", "daily", "--since", sinceDate, "--order", "desc", "--json"]);
  return JSON.parse(output) as UsageData;
}

export async function getCodexUsageAsync(sinceDate: string): Promise<UsageData> {
  const output = await runCommandAsync(["ccusage-codex", "daily", "--since", sinceDate, "--order", "desc", "--json"]);
  return JSON.parse(output) as UsageData;
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
  // Use local date components to avoid timezone shift
  const year = dt.getFullYear();
  const month = String(dt.getMonth() + 1).padStart(2, "0");
  const day = String(dt.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function combineData(claudeData: UsageData, codexData: UsageData): CombinedData {
  const combined: CombinedData = {};

  for (const entry of claudeData.daily ?? []) {
    const date = normalizeDate(entry.date);
    combined[date] = {
      claude_tokens: entry.totalTokens ?? 0,
      claude_cost: entry.totalCost ?? 0,
      codex_tokens: 0,
      codex_cost: 0,
    };
  }

  for (const entry of codexData.daily ?? []) {
    const date = normalizeDate(entry.date);
    if (!combined[date]) {
      combined[date] = {
        claude_tokens: 0,
        claude_cost: 0,
        codex_tokens: 0,
        codex_cost: 0,
      };
    }
    combined[date].codex_tokens = entry.totalTokens ?? 0;
    combined[date].codex_cost = entry.costUSD ?? 0;
  }

  return combined;
}
