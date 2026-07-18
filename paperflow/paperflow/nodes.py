"""LangGraph 节点实现。

写作类节点(plan/literature/draft/revise)调用 LLM 后端;
核验(verify)、图表(figures)、组装(assemble)、质检(qa)为确定性节点。
写作规范内嵌自已装 skills 的精华:scientific-writing(IMRAD、整段散文、不用列表)、
research-paper-writing(论点-证据对齐)、academic-paper(不编造、引用必须来自核验清单)。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .backends import BackendError
from .citations import to_bibtex, verify_candidates
from .state import PaperState

WRITER_SYSTEM = (
    "You are an experienced academic writer for materials chemistry journals. "
    "Write in full paragraphs of formal scientific English (never bullet points). "
    "Cite ONLY from the provided verified reference list, using pandoc syntax [@key]. "
    "Never invent data, results, or references; if evidence is missing, state the "
    "limitation explicitly instead of fabricating."
)


def _extract_json(text: str) -> dict | list:
    """从 LLM 输出中提取 JSON(容忍 ```json 围栏与前后杂文)。"""
    m = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    raw = m.group(1) if m else text
    start = min([i for i in (raw.find("{"), raw.find("[")) if i >= 0], default=0)
    return json.loads(raw[start:])


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
    return {"outline": outline, "log": state.get("log", []) + [f"[plan] 大纲就绪:{outline.get('title', '')}"]}


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
    return {
        "candidate_refs": cands,
        "log": state.get("log", []) + [f"[literature] 候选引用 {len(cands)} 条"],
    }


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
            "flowing academic prose. Output the section text only, no heading."
        )
        sections[key] = _backend(state).complete(f"section_{key}", WRITER_SYSTEM, prompt).strip()
        logs.append(f"[draft] {key}:{len(sections[key].split())} 词")
    return {"sections": sections, "log": state.get("log", []) + logs}


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
        "log": state.get("log", []) + [f"[revise] 第 {state.get('revision', 0) + 1} 轮修订完成"],
    }


# ---------------- 确定性节点 ----------------

def verify_node(state: PaperState) -> dict:
    verified, dropped, vlog = verify_candidates(state["candidate_refs"])
    if not verified:
        raise BackendError("所有候选引用都未通过核验,无法继续(检查网络或候选质量)。")
    return {
        "bibliography": verified,
        "dropped_refs": dropped,
        "log": state.get("log", [])
        + [f"[verify] 通过 {len(verified)} 条,剔除 {len(dropped)} 条"]
        + [f"  {l}" for l in vlog],
    }


def figures_node(state: PaperState) -> dict:
    wd = _workdir(state)
    figdir = wd / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    figures = []
    for i, f in enumerate(state["config"].get("figures", [])):
        src = Path(f["path"])
        if not src.is_absolute():
            src = wd / src
        dst = figdir / src.name
        if src.resolve() != dst.resolve():
            shutil.copy(src, dst)
        figures.append({"path": f"figures/{src.name}", "caption": f["caption"], "label": f.get("label", f"fig{i+1}")})
    return {"figures": figures, "log": state.get("log", []) + [f"[figures] 纳入 {len(figures)} 张图"]}


def assemble_node(state: PaperState) -> dict:
    cfg, outline, wd = state["config"], state["outline"], _workdir(state)
    bib_path = wd / "references.bib"
    bib_path.write_text(to_bibtex(state["bibliography"]), encoding="utf-8")

    lines = [
        "---",
        f'title: "{outline["title"]}"',
        f'author: "{cfg.get("author", "paperflow demo")}"',
        "bibliography: references.bib",
        "link-citations: true",
        "---",
        "",
    ]
    if cfg.get("disclaimer"):
        lines += [f"> {cfg['disclaimer']}", ""]
    for sec in outline["sections"]:
        lines += [f"# {sec['key'].replace('_', ' ').title()}", "", state["sections"][sec["key"]], ""]
        if sec["key"] == cfg.get("figures_after_section"):
            for i, f in enumerate(state.get("figures", [])):
                lines += [f"![Figure {i+1}. {f['caption']}]({f['path']}){{#fig:{f['label']}}}", ""]
    lines += ["# References", ""]

    md = wd / "paper.md"
    md.write_text("\n".join(lines), encoding="utf-8")

    outputs = [str(md)]
    pandoc = shutil.which("pandoc")
    if pandoc:
        for fmt in ("docx", "tex"):
            out = wd / f"paper.{fmt}"
            r = subprocess.run(
                [pandoc, str(md), "--citeproc", "--standalone",
                 "--resource-path", str(wd), "-o", str(out)],
                capture_output=True, text=True, cwd=wd,
            )
            if r.returncode == 0:
                outputs.append(str(out))
    note = "" if pandoc else "(未装 pandoc,只产出 markdown)"
    return {
        "draft_path": str(md),
        "outputs": outputs,
        "log": state.get("log", []) + [f"[assemble] 产出 {len(outputs)} 个文件 {note}"],
    }


def qa_node(state: PaperState) -> dict:
    """确定性质检:引用键有效、无占位符、章节齐全非空、图表被引用。"""
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

    passed = not issues
    return {
        "qa_report": {"passed": passed, "issues": issues},
        "log": state.get("log", [])
        + [f"[qa] {'通过' if passed else f'发现 {len(issues)} 个问题'}"]
        + [f"  - {i}" for i in issues],
    }
