import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { REPO } from "./paths";

export type TaskDef = {
  id: string;
  title: string;
  tool: string;          // 归属 skill/工作流
  desc: string;
  cwd: string;           // 仓库相对
  script: string;        // bash 脚本(白名单固定,不接受用户输入)
  produces: string[];    // 预期产物(仓库相对),完成后核对
  hint?: string;         // 依赖提示
};

/** 可运行任务白名单 —— 页面只能按 id 触发,不存在任意命令执行 */
export const TASKS: TaskDef[] = [
  {
    id: "slides",
    title: "重建 BSE–EDS 汇报 PPT",
    tool: "paper-slides",
    desc: "slidekit 组件库生成 18 页开放基金汇报(素材收集 → 生成 pptx → 转 PDF 预览)",
    cwd: "examples/bse-eds-report/slides",
    script: [
      "sh prepare_assets.sh",
      "[ -d node_modules/pptxgenjs ] || npm install pptxgenjs --no-fund --no-audit",
      "node gen_deck.js",
      "command -v soffice >/dev/null && soffice --headless --convert-to pdf bse_eds_grant_briefing.pptx --outdir . || echo '[skip] soffice 不可用,跳过 PDF 预览'",
    ].join(" && "),
    produces: [
      "examples/bse-eds-report/slides/bse_eds_grant_briefing.pptx",
      "examples/bse-eds-report/slides/bse_eds_grant_briefing.pdf",
    ],
    hint: "需要 Node.js;PDF 预览需要 LibreOffice",
  },
  {
    id: "figflow",
    title: "合成 BSE–EDS 架构大图",
    tool: "figflow",
    desc: "确定性排版引擎按 figure.json 锚点合成面板/箭头/色带/徽标",
    cwd: ".",
    script: "PYTHONPATH=figflow python3 -m figflow examples/figflow-demo/figure.json",
    produces: ["examples/figflow-demo/bse_eds_architecture.png"],
    hint: "需要 Python + numpy/matplotlib/scikit-image",
  },
  {
    id: "oer",
    title: "重画 OER 电催化组图",
    tool: "paper-figures",
    desc: "paper-figures 演示脚本:按期刊栏宽出版级四联图(PDF + PNG)",
    cwd: "examples/paper-figures-demo",
    script: "PYTHONPATH=../../skills/paper-figures/scripts python3 fig1_oer.py",
    produces: ["examples/paper-figures-demo/fig1_oer.pdf", "examples/paper-figures-demo/fig1_oer.png"],
    hint: "需要 Python + matplotlib",
  },
  {
    id: "paperflow",
    title: "生成研究计划报告(fixture 后端)",
    tool: "paperflow",
    desc: "论文流水线端到端:章节/图表/引用核验 → LaTeX → tectonic 编译 PDF",
    cwd: "paperflow",
    script: "PYTHONPATH=. python3 -m paperflow --config ../examples/bse-eds-report/paper.yaml --backend fixture",
    produces: ["examples/bse-eds-report/paper_article.pdf"],
    hint: "需要 pip install -r paperflow/requirements.txt 与 tectonic",
  },
];

export type Run = {
  id: string;
  taskId: string;
  title: string;
  status: "running" | "success" | "failed";
  startedAt: number;
  endedAt?: number;
  exitCode?: number;
  lines: string[];
  artifacts: { rel: string; mtime: number }[];
};

// dev 模式下模块可能被多实例加载,挂到 globalThis 保注册表唯一
const g = globalThis as unknown as { __runs?: Map<string, Run> };
const RUNS: Map<string, Run> = g.__runs ?? new Map();
g.__runs = RUNS;

const MAX_LINES = 4000;

export function listRuns(): Run[] {
  return [...RUNS.values()].sort((a, b) => b.startedAt - a.startedAt)
    .map((r) => ({ ...r, lines: [] })); // 列表不携带日志
}

export function getRun(id: string, after: number): (Omit<Run, "lines"> & { lines: string[]; cursor: number }) | null {
  const r = RUNS.get(id);
  if (!r) return null;
  const from = Math.max(0, Math.min(after, r.lines.length));
  return { ...r, lines: r.lines.slice(from), cursor: r.lines.length };
}

export function startRun(taskId: string): Run {
  const task = TASKS.find((t) => t.id === taskId);
  if (!task) throw new Error(`unknown task: ${taskId}`);
  if ([...RUNS.values()].some((r) => r.taskId === taskId && r.status === "running")) {
    throw new Error("该任务已在运行中");
  }
  const id = `${taskId}-${Date.now().toString(36)}`;
  const run: Run = {
    id, taskId, title: task.title, status: "running",
    startedAt: Date.now(), lines: [], artifacts: [],
  };
  RUNS.set(id, run);

  const push = (s: string) => {
    for (const ln of s.split(/\r?\n/)) {
      if (ln.trim() === "") continue;
      run.lines.push(ln);
      if (run.lines.length > MAX_LINES) run.lines.splice(0, run.lines.length - MAX_LINES);
    }
  };
  push(`$ ${task.script}`);

  // 用 zsh 登录壳并显式补 homebrew PATH:dev server 的环境里往往没有它,
  // 会静默落到系统 /usr/bin/python3 导致依赖缺失
  const child = spawn("zsh", ["-lc", task.script], {
    cwd: path.resolve(REPO, task.cwd),
    env: {
      ...process.env,
      PATH: `/opt/homebrew/bin:/usr/local/bin:${process.env.PATH ?? ""}`,
      FORCE_COLOR: "0", NO_COLOR: "1",
    },
  });
  child.stdout.on("data", (d) => push(String(d)));
  child.stderr.on("data", (d) => push(String(d)));
  child.on("error", (e) => { push(`[error] ${e.message}`); });
  child.on("close", (code) => {
    run.exitCode = code ?? -1;
    run.endedAt = Date.now();
    // 核对产物:存在且在本次运行内被更新的标绿
    run.artifacts = task.produces
      .map((rel) => {
        try {
          const st = fs.statSync(path.resolve(REPO, rel));
          return { rel, mtime: st.mtimeMs };
        } catch { return null; }
      })
      .filter((x): x is { rel: string; mtime: number } => !!x);
    const fresh = run.artifacts.some((a) => a.mtime >= run.startedAt - 2000);
    run.status = code === 0 && (task.produces.length === 0 || fresh || run.artifacts.length > 0) ? "success" : code === 0 ? "success" : "failed";
    push(code === 0 ? `[done] 完成,退出码 0,耗时 ${((run.endedAt - run.startedAt) / 1000).toFixed(1)}s` : `[fail] 退出码 ${code}`);
  });
  return run;
}
