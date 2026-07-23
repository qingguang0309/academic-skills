import fs from "node:fs";
import path from "node:path";
import { REPO, HOME_SKILLS, exists, walk } from "./paths";

export type SkillInfo = {
  name: string;
  description: string;
  files: number;
  scripts: string[];
  references: string[];
  installed: boolean;
  updatable: boolean; // 仓库版本比已安装的新
};

export type WorkflowInfo = {
  name: string;
  description: string;
  dir: string;
};

function parseFrontmatter(md: string): Record<string, string> {
  const m = md.match(/^---\n([\s\S]*?)\n---/);
  const out: Record<string, string> = {};
  if (!m) return out;
  // 简易 YAML:key: value(value 可跨行缩进)
  const lines = m[1].split("\n");
  let key = "";
  for (const ln of lines) {
    const kv = ln.match(/^([\w-]+):\s*(.*)$/);
    if (kv) { key = kv[1]; out[key] = kv[2].replace(/^["']|["']$/g, ""); }
    else if (key && /^\s+/.test(ln)) out[key] += (out[key] ? " " : "") + ln.trim();
  }
  return out;
}

function newestMtime(dir: string): number {
  let t = 0;
  for (const f of walk(dir)) {
    const m = fs.statSync(f).mtimeMs;
    if (m > t) t = m;
  }
  return t;
}

export function listSkills(): SkillInfo[] {
  const root = path.join(REPO, "skills");
  if (!exists(root)) return [];
  return fs.readdirSync(root, { withFileTypes: true })
    .filter((e) => e.isDirectory() && exists(path.join(root, e.name, "SKILL.md")))
    .map((e) => {
      const dir = path.join(root, e.name);
      const fm = parseFrontmatter(fs.readFileSync(path.join(dir, "SKILL.md"), "utf8"));
      const scriptsDir = path.join(dir, "scripts");
      const refsDir = path.join(dir, "references");
      const installedDir = path.join(HOME_SKILLS, e.name);
      const installed = exists(installedDir);
      return {
        name: fm.name || e.name,
        description: fm.description || "",
        files: walk(dir).length,
        scripts: exists(scriptsDir) ? fs.readdirSync(scriptsDir).filter((f) => !f.startsWith("_") && !f.startsWith(".")) : [],
        references: exists(refsDir) ? fs.readdirSync(refsDir).filter((f) => !f.startsWith(".")) : [],
        installed,
        updatable: installed && newestMtime(dir) > newestMtime(installedDir) + 1000,
      };
    });
}

export function listWorkflows(): WorkflowInfo[] {
  const defs = [
    { name: "paperflow", description: "LangGraph 论文生成流水线:大纲后文献链与图表链并行,引用经 Crossref/Semantic Scholar 核验,渲染标准 LaTeX 并编译 PDF" },
    { name: "figflow", description: "多面板大图分治出图:并行子代理画面板,箭头/色带/徽标由确定性排版引擎按锚点合成" },
  ];
  return defs
    .filter((d) => exists(path.join(REPO, d.name)))
    .map((d) => ({ ...d, dir: d.name }));
}

export function installSkill(name: string): void {
  const src = path.join(REPO, "skills", name);
  if (!exists(path.join(src, "SKILL.md"))) throw new Error(`skill not found: ${name}`);
  fs.mkdirSync(HOME_SKILLS, { recursive: true });
  const dst = path.join(HOME_SKILLS, name);
  fs.rmSync(dst, { recursive: true, force: true });
  fs.cpSync(src, dst, { recursive: true });
}

export function uninstallSkill(name: string): void {
  if (!/^[\w-]+$/.test(name)) throw new Error("bad name");
  const dst = path.join(HOME_SKILLS, name);
  if (!exists(dst)) return;
  fs.rmSync(dst, { recursive: true, force: true });
}

export function readSkillDoc(name: string, file: string): string {
  if (!/^[\w-]+$/.test(name) || !/^[\w./-]+$/.test(file) || file.includes("..")) throw new Error("bad path");
  return fs.readFileSync(path.join(REPO, "skills", name, file), "utf8");
}
