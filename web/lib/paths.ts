import path from "node:path";
import fs from "node:fs";
import os from "node:os";

/** 仓库根目录:web/ 的上一级 */
export const REPO = path.resolve(process.cwd(), "..");
export const HOME_SKILLS = path.join(os.homedir(), ".claude", "skills");

/** 把用户传来的相对路径安全地解析到仓库内,越界即抛错 */
export function safeRepoPath(rel: string): string {
  const abs = path.resolve(REPO, rel);
  if (abs !== REPO && !abs.startsWith(REPO + path.sep)) {
    throw new Error("path escapes repo");
  }
  return abs;
}

export function exists(p: string): boolean {
  try { fs.accessSync(p); return true; } catch { return false; }
}

export function walk(dir: string, opts: { exts?: string[]; skip?: RegExp; maxDepth?: number } = {}): string[] {
  const { exts, skip = /node_modules|__pycache__|\.git|\.next|venv/, maxDepth = 6 } = opts;
  const out: string[] = [];
  const rec = (d: string, depth: number) => {
    if (depth > maxDepth) return;
    let entries: fs.Dirent[];
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      const p = path.join(d, e.name);
      if (skip.test(p)) continue;
      if (e.isDirectory()) rec(p, depth + 1);
      else if (!exts || exts.includes(path.extname(e.name).toLowerCase())) out.push(p);
    }
  };
  rec(dir, 0);
  return out;
}
