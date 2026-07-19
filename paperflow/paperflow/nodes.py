"""LangGraph 节点实现。

拓扑:plan 之后【文献链 literature→verify】与【图表链 figures】并行,在 draft 汇合;
draft → render(LaTeX 模板 + 编译)→ qa → (revise → render 循环)。
写作类节点(plan/literature/draft/revise/figures 的作图代码)调用 LLM 后端;
verify/render/qa 为确定性节点。所有节点只返回增量日志(state.log 用 reducer 合并)。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .backends import BackendError
from .citations import to_bibtex, verify_candidates
from .renderer import compile_pdf, find_engine, render_article, render_pkuthss
from .state import PaperState

WRITER_SYSTEM = (
    "You are an experienced academic writer for materials chemistry journals. "
    "Write in full paragraphs of formal scientific English (never bullet points). "
    "Cite ONLY from the provided verified reference list, using pandoc syntax [@key]. "
    "Never invent data, results, or references; if evidence is missing, state the "
    "limitation explicitly instead of fabricating."
)

FIGURE_SYSTEM = (
    "You are a scientific-figure engineer following publication conventions "
    "(Okabe-Ito colorblind-safe palette, full box frame with inward ticks, "
    "physical figure sizing in mm, 300+ dpi, no chartjunk). If a local "
    "'paper-figures' skill is available, follow it. You output a single "
    "self-contained Python script and nothing else."
)


def _extract_json(text: str) -> dict | list:
    m = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    raw = m.group(1) if m else text
    start = min([i for i in (raw.find("{"), raw.find("[")) if i >= 0], default=0)
    return json.loads(raw[start:])


def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*(.+?)```", text, re.S)
    return (m.group(1) if m else text).strip()


def _workdir(state: PaperState) -> Path:
    return Path(state["config"]["workdir"])


def _backend(state: PaperState):
    return state["config"]["_backend"]


# ---------------- 写作类节点 ----------------

def plan_node(state: PaperState) -> dict:
    cfg = state["config"]
    prompt = (
        f"Topic: {cfg['topic']}\nTarget journal: {cfg.get('journal', 'a materials chemistry journal')}\n"
        f"Core claim: {cfg.get('claim', '')}\n\n"
        "Produce a paper outline as JSON only:\n"
        '{"title": "...", "sections": [{"key": "introduction", "goal": "..."}, ...]}\n'
        f"Use exactly these section keys: {cfg['sections']}"
    )
    out = _backend(state).complete("plan", WRITER_SYSTEM, prompt)
    outline = _extract_json(out)
    return {"outline": outline, "log": [f"[plan] 大纲就绪:{outline.get('title', '')}"]}


def literature_node(state: PaperState) -> dict:
    cfg = state["config"]
    prompt = (
        f"Topic: {cfg['topic']}\n\n"
        "List the key references this paper should cite. JSON only:\n"
        '[{"key": "trotochaud2014", "title": "...", "doi": "10.xxxx/...", "why": "..."}]\n'
        "Only include references you are confident actually exist, with their real DOIs. "
        "They will be checked against Crossref; wrong DOIs will be dropped."
    )
    out = _backend(state).complete("literature", WRITER_SYSTEM, prompt)
    cands = _extract_json(out)
    return {"candidate_refs": cands, "log": [f"[literature] 候选引用 {len(cands)} 条"]}


def draft_node(state: PaperState) -> dict:
    cfg, outline = state["config"], state["outline"]
    bib_digest = "\n".join(
        f"- [@{e['key']}] {', '.join(e['authors'][:1])} et al., {e['year']}, "
        f"{e['container']}: {e['title']}"
        for e in state["bibliography"]
    )
    fig_digest = "\n".join(
        f"- Figure {i+1} ({f['label']}): {f['caption']}" for i, f in enumerate(state.get("figures", []))
    )
    sections: dict[str, str] = {}
    logs = []
    for sec in outline["sections"]:
        key, goal = sec["key"], sec.get("goal", "")
        prompt = (
            f"Paper title: {outline['title']}\nSection to write: {key}\nSection goal: {goal}\n\n"
            f"Verified references (cite with [@key], nothing else):\n{bib_digest}\n\n"
            f"Figures available (reference as 'Figure N'):\n{fig_digest or '(none)'}\n\n"
            f"Study context: {cfg.get('context', '')}\n\n"
            f"Write the {key} section in {cfg.get('words_per_section', 250)}±30% words of "
            "flowing academic prose. Plain text only (no markdown headings/bullets/LaTeX commands); "
            "output the section text only, no heading."
        )
        sections[key] = _backend(state).complete(f"section_{key}", WRITER_SYSTEM, prompt).strip()
        logs.append(f"[draft] {key}:{len(sections[key].split())} 词")
    return {"sections": sections, "log": logs}


def revise_node(state: PaperState) -> dict:
    issues = "\n".join(f"- {i}" for i in state["qa_report"]["issues"])
    fixed: dict[str, str] = {}
    for key, text in state["sections"].items():
        prompt = (
            f"QA found these issues in the manuscript:\n{issues}\n\n"
            f"Rewrite the '{key}' section fixing any issue that applies to it. "
            "Keep verified citations [@key] intact; do not add new ones.\n\n"
            f"Current text:\n{text}"
        )
        fixed[key] = _backend(state).complete(f"revise_{key}", WRITER_SYSTEM, prompt).strip()
    return {
        "sections": fixed,
        "revision": state.get("revision", 0) + 1,
        "log": [f"[revise] 第 {state.get('revision', 0) + 1} 轮修订完成"],
    }


# ---------------- 图表链(与文献链并行) ----------------

def figures_node(state: PaperState) -> dict:
    """与文献/写作并行执行:复制配置指定的现成图,并可按主题生成新图。

    生成路径:LLM(默认本机 claude CLI)产出自包含 matplotlib 脚本 → 本地执行 →
    脚本按契约把 PNG 写入 figures/ 并输出 figures/manifest.json:
    [{"file": "xxx.png", "caption": "...", "label": "..."}]
    """
    cfg, wd = state["config"], _workdir(state)
    figdir = wd / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    figures: list[dict] = []
    logs: list[str] = []

    for i, f in enumerate(cfg.get("figures", [])):
        src = Path(f["path"])
        if not src.is_absolute():
            src = wd / src
        dst = figdir / src.name
        if src.resolve() != dst.resolve():
            shutil.copy(src, dst)
        figures.append({"path": f"figures/{src.name}", "caption": f["caption"],
                        "label": f.get("label", f"fig{i+1}")})
    if figures:
        logs.append(f"[figures] 复制现成图 {len(figures)} 张")

    if cfg.get("generate_figures"):
        prompt = (
            f"Topic: {cfg['topic']}\nCore claim: {cfg.get('claim', '')}\n"
            f"Context: {cfg.get('context', '')}\n\n"
            f"Write ONE self-contained Python script that creates {cfg.get('n_generated_figures', 1)} "
            "publication-quality figure(s) ILLUSTRATING this topic with clearly synthetic example data "
            "(deterministic: np.random.default_rng(fixed seed)). Constraints:\n"
            "- imports limited to numpy / scipy / matplotlib (Agg backend, no GUI, no network)\n"
            "- save each figure as 300-dpi PNG into ./figures/\n"
            "- finally write ./figures/manifest.json: a JSON list of "
            '{"file": "name.png", "caption": "...", "label": "slug"} for every figure created\n'
            "- captions must state the data are illustrative\n"
            "Output only the Python code."
        )
        code = _extract_code(_backend(state).complete("figures_code", FIGURE_SYSTEM, prompt))
        script = wd / "figures_gen.py"
        script.write_text(code, encoding="utf-8")
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                           cwd=wd, timeout=600)
        if r.returncode != 0:
            raise BackendError(f"生成图脚本执行失败:\n{(r.stderr or r.stdout)[-800:]}")
        manifest_path = figdir / "manifest.json"
        if not manifest_path.is_file():
            raise BackendError("生成图脚本未按契约写出 figures/manifest.json")
        for m in json.loads(manifest_path.read_text(encoding="utf-8")):
            figures.append({"path": f"figures/{m['file']}", "caption": m["caption"],
                            "label": m.get("label", Path(m["file"]).stem)})
        logs.append(f"[figures] 按主题生成 {len(json.loads(manifest_path.read_text(encoding='utf-8')))} 张图(脚本已执行)")

    return {"figures": figures, "log": logs or ["[figures] 无图"]}


# ---------------- 确定性节点 ----------------

def verify_node(state: PaperState) -> dict:
    verified, dropped, vlog = verify_candidates(state["candidate_refs"])
    if not verified:
        raise BackendError("所有候选引用都未通过核验,无法继续(检查网络或候选质量)。")
    return {
        "bibliography": verified,
        "dropped_refs": dropped,
        "log": [f"[verify] 通过 {len(verified)} 条,剔除 {len(dropped)} 条"] + [f"  {l}" for l in vlog],
    }


def render_node(state: PaperState) -> dict:
    """按模板渲染标准论文格式并编译 PDF(article=SCI 投稿格式,pkuthss=北大学位论文)。"""
    cfg, wd = state["config"], _workdir(state)
    template = cfg.get("template", "article")
    (wd / "references.bib").write_text(to_bibtex(state["bibliography"]), encoding="utf-8")

    if template == "pkuthss":
        pkuthss_dir = Path(cfg.get("pkuthss_dir",
                           Path.home() / "project/paper-skills-vendor/latex-templates"))
        tex = render_pkuthss(dict(state), wd, pkuthss_dir)
    else:
        tex = render_article(dict(state), wd)

    outputs = [str(tex)]
    logs = [f"[render] 模板 {template} → {tex.name}"]
    pdf, log_tail = compile_pdf(tex)
    if pdf:
        outputs.append(str(pdf))
        logs.append(f"[render] PDF 编译成功:{pdf.name}({pdf.stat().st_size // 1024} KB)")
    else:
        logs.append(f"[render] PDF 编译失败/无引擎:{log_tail[-300:]}")
    return {"draft_path": str(tex), "outputs": outputs, "log": logs}


def qa_node(state: PaperState) -> dict:
    """确定性质检:引用键有效、无占位符、章节齐全、图被引用、PDF 编译成功。"""
    issues = []
    bib_keys = {e["key"] for e in state["bibliography"]}
    all_text = "\n".join(state["sections"].values())

    for key in set(re.findall(r"@([A-Za-z][\w-]*)", all_text)):
        if key not in bib_keys:
            issues.append(f"引用键 @{key} 不在核验通过的文献列表里")
    if len(re.findall(r"\[@", all_text)) < state["config"].get("min_citations", 3):
        issues.append("全文引用数量低于下限")
    for sec in state["outline"]["sections"]:
        text = state["sections"].get(sec["key"], "")
        if not text.strip():
            issues.append(f"章节 {sec['key']} 为空")
        if re.search(r"\bTODO\b|PLACEHOLDER|\bXXX\b", text):
            issues.append(f"章节 {sec['key']} 残留占位符")
        if re.search(r"^\s*[-*]\s", text, re.M):
            issues.append(f"章节 {sec['key']} 出现列表符号(应为整段散文)")
    for i, f in enumerate(state.get("figures", [])):
        if f"Figure {i+1}" not in all_text:
            issues.append(f"Figure {i+1}({f['label']})未在正文中被引用")
    if find_engine() and not any(o.endswith(".pdf") for o in state.get("outputs", [])):
        issues.append("LaTeX 引擎可用但未产出 PDF(编译失败)")

    passed = not issues
    return {
        "qa_report": {"passed": passed, "issues": issues},
        "log": [f"[qa] {'通过' if passed else f'发现 {len(issues)} 个问题'}"] + [f"  - {i}" for i in issues],
    }
