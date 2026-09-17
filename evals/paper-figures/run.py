"""paper-figures 首次出图可用率评测。

固定 5 道题,用安装好的 skill 让模型各做一遍;第一次交付后立即冻结,不许人工修;
然后三关打分,三关都过才算"首次可用":

  关 1 内容正确  交付齐全(脚本/规格 + PDF + PNG)、在干净副本里重跑能复现,
                 且题目的内容检查项全部通过(单位、标注、尺寸、字号……)
  关 2 体检通过  重跑时由探针用被测版本的 check_layout 独立体检,0 条 error
  关 3 人工看过  有人打开 PNG 看过并判定可用(review 子命令)

用法::

    python3 run.py start --model claude-sonnet-5         # prepare + run + grade
    python3 run.py review  <run_id> --open                # 逐题看图、判定
    python3 run.py report  <run_id> --record              # 汇总,追加到 history.jsonl

分步::

    python3 run.py prepare [--skill 路径或 .skill] [--tasks t1_xrd,t5_toc]
    python3 run.py run     <run_id> [--model M] [--budget 5] [--jobs 2] [--timeout 1800]
    python3 run.py grade   <run_id>
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TASKS_DIR = os.path.join(HERE, "tasks")
RUNS_DIR = os.path.join(HERE, "runs")
PROBE_DIR = os.path.join(HERE, "probe")
HISTORY = os.path.join(HERE, "history.jsonl")
DEFAULT_SKILL = os.path.join(REPO, "skills", "paper-figures")

OUTPUT_EXT = (".png", ".pdf", ".svg", ".tif", ".tiff", ".eps")
LIB_NAMES = {"paperfig.py", "schemfig.py"}
SKIP_DIRS = {".git", ".claude", "__pycache__"}


# ------------------------------------------------------------------ 工具

def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            p = os.path.join(d, f)
            yield os.path.relpath(p, root)


def _manifest(root):
    return {rel: _sha(os.path.join(root, rel)) for rel in _walk(root)}


def _tree_hash(root):
    h = hashlib.sha256()
    for rel in _walk(root):
        if rel.endswith(".pyc"):
            continue
        h.update(rel.encode())
        h.update(_sha(os.path.join(root, rel)).encode())
    return h.hexdigest()[:16]


def _load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _dump(obj, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def _tasks(selected=None):
    names = sorted(d for d in os.listdir(TASKS_DIR) if os.path.isfile(os.path.join(TASKS_DIR, d, "task.json")))
    if selected:
        want = [s.strip() for s in selected.split(",") if s.strip()]
        bad = [w for w in want if w not in names]
        if bad:
            sys.exit(f"未知题目: {bad};可选 {names}")
        names = want
    return names


def _run_dir(run_id):
    path = os.path.join(RUNS_DIR, run_id)
    if not os.path.isdir(path):
        sys.exit(f"找不到 run: {path}")
    return path


def _git(*args):
    try:
        return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


# ------------------------------------------------------------------ prepare

def _install_skill(src, dest):
    if os.path.isdir(src):
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        return
    with zipfile.ZipFile(src) as zf, tempfile.TemporaryDirectory() as tmp:
        zf.extractall(tmp)
        hits = [os.path.dirname(os.path.join(d, "SKILL.md")) for d, _, fs in os.walk(tmp) if "SKILL.md" in fs]
        if not hits:
            sys.exit(f"{src} 里没有 SKILL.md")
        shutil.copytree(hits[0], dest)


def cmd_prepare(a):
    skill = os.path.abspath(a.skill)
    if not os.path.exists(skill):
        sys.exit(f"找不到 skill: {skill}")
    run_id = a.run_id or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    rd = os.path.join(RUNS_DIR, run_id)
    if os.path.exists(rd):
        sys.exit(f"run 已存在: {rd}")
    os.makedirs(rd)
    checker = os.path.join(rd, "checker")
    _install_skill(skill, checker)                   # 被测版本的完整副本,体检用它
    names = _tasks(a.tasks)
    for name in names:
        td = os.path.join(rd, name)
        ws = os.path.join(td, "ws")
        os.makedirs(ws)
        src_data = os.path.join(TASKS_DIR, name, "data")
        if os.path.isdir(src_data):
            shutil.copytree(src_data, os.path.join(ws, "data"))
        _install_skill(skill, os.path.join(ws, ".claude", "skills", "paper-figures"))
        # 独立 git 根:避免模型把上层仓库当成项目
        subprocess.run(["git", "init", "-q"], cwd=ws, check=False)
        _dump(_manifest(ws), os.path.join(td, "initial.json"))
    meta = {
        "run_id": run_id, "created": dt.datetime.now().isoformat(timespec="seconds"),
        "skill_source": skill, "skill_hash": _tree_hash(checker),
        "repo_commit": _git("rev-parse", "--short", "HEAD"),
        "repo_dirty": bool(_git("status", "--porcelain", "--", "skills/paper-figures")),
        "tasks_hash": _tree_hash(TASKS_DIR), "tasks": names,
    }
    _dump(meta, os.path.join(rd, "meta.json"))
    print(f"[prepare] {run_id}: {len(names)} 题,skill {meta['skill_hash']}")
    return run_id


# ------------------------------------------------------------------ run + freeze

def _agent_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDECODE", "CLAUDE_CODE_"))}
    return env


def _run_one(rd, name, a, meta):
    td = os.path.join(rd, name)
    ws = os.path.join(td, "ws")
    if os.path.exists(os.path.join(td, "frozen.json")):
        print(f"[run] {name}: 已冻结,跳过")
        return
    task = _load(os.path.join(TASKS_DIR, name, "task.json"))
    prompt_file = os.path.join(td, "prompt.txt")
    with open(prompt_file, "w", encoding="utf-8") as fh:
        fh.write(task["prompt"])
    if a.agent_cmd:
        cmd = a.agent_cmd.format(prompt_file=shlex.quote(prompt_file), ws=shlex.quote(ws))
        popen = dict(args=cmd, shell=True)
    else:
        args = ["claude", "-p", task["prompt"], "--output-format", "stream-json", "--verbose",
                "--permission-mode", "bypassPermissions", "--setting-sources", "project"]
        if a.model:
            args += ["--model", a.model]
        if a.budget:
            args += ["--max-budget-usd", str(a.budget)]
        popen = dict(args=args)
    started = dt.datetime.now()
    print(f"[run] {name}: 开始")
    with open(os.path.join(td, "transcript.jsonl"), "w") as out, open(os.path.join(td, "stderr.txt"), "w") as err:
        try:
            proc = subprocess.run(**popen, cwd=ws, stdout=out, stderr=err, env=_agent_env(), timeout=a.timeout)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    frozen = {"frozen_at": dt.datetime.now().isoformat(timespec="seconds"),
              "seconds": round((dt.datetime.now() - started).total_seconds(), 1),
              "exit": code, "model": a.model, "agent_cmd": a.agent_cmd, "files": _manifest(ws)}
    _dump(frozen, os.path.join(td, "frozen.json"))
    for rel in frozen["files"]:                      # 冻结:第一次交付之后不许再改
        p = os.path.join(ws, rel)
        os.chmod(p, os.stat(p).st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    print(f"[run] {name}: 结束(exit={code},{frozen['seconds']} s),已冻结")


def cmd_run(a):
    rd = _run_dir(a.run_id)
    meta = _load(os.path.join(rd, "meta.json"))
    meta["model"] = a.model
    _dump(meta, os.path.join(rd, "meta.json"))
    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        list(ex.map(lambda n: _run_one(rd, n, a, meta), meta["tasks"]))


# ------------------------------------------------------------------ grade

_TEX = {r"\theta": "θ", r"\Omega": "Ω", r"\eta": "η", r"\mu": "μ", r"\circ": "°", r"\degree": "°",
        r"\delta": "δ", r"\lambda": "λ", r"\alpha": "α", r"\beta": "β", r"\,": " ", r"\;": " ",
        r"\ ": " ", r"\!": "", r"\prime": "'", r"\rm": "", r"\it": "", r"\mathrm": "", r"\text": "",
        r"\mathit": "", r"\mathdefault": "", r"\mathbf": "", r"\bf": "", r"\times": "×", r"\cdot": "·", r"\%": "%", r"\/": "/"}
_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺₀₁₂₃₄₅₆₇₈₉−–", "0123456789-+0123456789--")


def _norm(s):
    s = unicodedata.normalize("NFKC", s)
    for k in sorted(_TEX, key=len, reverse=True):
        s = s.replace(k, _TEX[k])
    s = s.translate(_SUP)
    s = re.sub(r"[${}^_]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _squash(s):
    return re.sub(r"\s+", "", _norm(s))


def _fig_text(snap):
    parts = [t["s"] for t in snap["texts"]]
    for ax in snap["axes"]:
        parts += [ax["xlabel"], ax["ylabel"]]
    return "\n".join(_norm(p) for p in parts)


def _check_item(item, snap, ctx):
    t = item["type"]
    blob = _fig_text(snap)
    if t == "size_in":
        w, h = snap["size_in"]
        ok = item["w"][0] <= w <= item["w"][1] and ("h" not in item or item["h"][0] <= h <= item["h"][1])
        return ok, f"{w:.2f}×{h:.2f} in"
    if t == "axis_label":
        key = "xlabel" if item["axis"] == "x" else "ylabel"
        labels = [_norm(ax[key]) for ax in snap["axes"] if ax[key]]
        ok = any(all(re.search(p, lab, re.I) for p in item["all"]) for lab in labels)
        return ok, "; ".join(labels) or "无轴标签"
    if t == "text":
        if item.get("literal"):
            flat = _squash(blob)
            miss = [s for s in item["all"] if _squash(s) not in flat]
        else:
            miss = [p for p in item["all"] if not re.search(p, blob, re.I)]
        return not miss, ("缺: " + ", ".join(miss)) if miss else "齐全"
    if t == "n_axes_min":
        n = sum(1 for ax in snap["axes"] if ax["axis_on"])
        return n >= item["n"], f"{n} 个坐标轴"
    if t == "panel_labels":
        singles = {_norm(x["s"]).strip("() ").lower() for x in snap["texts"]}
        miss = [c for c in item["letters"] if c not in singles]
        return not miss, ("缺: " + ", ".join(miss)) if miss else "齐全"
    if t == "aspect_equal":
        hits = [ax for ax in snap["axes"] if re.search(item["xlabel"], _norm(ax["xlabel"]), re.I)
                and re.search(item["xlabel"], _norm(ax["ylabel"]), re.I)]
        if not hits:
            return False, "找不到两轴都是 Z 的坐标轴"
        ax = hits[0]
        sx = abs(ax["xlim"][1] - ax["xlim"][0]) / max(ax["px"][0], 1e-9)
        sy = abs(ax["ylim"][1] - ax["ylim"][0]) / max(ax["px"][1], 1e-9)
        r = sx / sy if sy else float("inf")
        return abs(r - 1) <= item.get("tol", 0.1), f"单位像素比 x/y = {r:.2f}"
    if t == "markers_open_and_filled":
        mk = [l for ax in snap["axes"] for l in ax["lines"] if l["marker"] not in ("None", "", " ", "none")]
        open_ = [l for l in mk if l["mfc"].lower() in ("none", "(0.0, 0.0, 0.0, 0.0)", "white", "#ffffff", "w")
                 or l["mfc"].startswith("(1.0, 1.0, 1.0")]
        filled = [l for l in mk if l not in open_]
        return bool(open_) and bool(filled), f"空心 {len(open_)} 条,实心 {len(filled)} 条"
    if t == "no_axes_title":
        titles = [s for ax in snap["axes"] for s in ax["titles"] if s.strip()]
        return not titles, ("有标题: " + "; ".join(titles)) if titles else "无"
    if t == "min_font_pt":
        sizes = [x["size"] for x in snap["texts"]]
        m = min(sizes) if sizes else 0
        small = sorted({x["s"][:12] for x in snap["texts"] if x["size"] < item["pt"]})[:4]
        return m >= item["pt"], f"最小 {m:.1f} pt" + (f"({', '.join(small)})" if small else "")
    if t == "no_cmap":
        used = sorted({c for ax in snap["axes"] for c in ax["cmaps"]})
        bad = [c for c in used if c.replace("_r", "") in item["names"]]
        return not bad, ("用了: " + ", ".join(bad)) if bad else "无彩虹色标"
    if t == "dashed_line":
        return bool(snap.get("dashed")), "有虚线" if snap.get("dashed") else "没有虚线"
    if t == "png_dpi_min":
        dpis = ctx.get("png_dpi", [])
        best = max(dpis) if dpis else 0
        return best >= item["dpi"] * 0.99, f"{best:.0f} dpi" if dpis else "没有 PNG"
    return False, f"未知检查类型 {t}"


def _deliverables(ws, initial):
    made = [rel for rel in _walk(ws) if rel not in initial]
    outs = [r for r in made if r.lower().endswith(OUTPUT_EXT)
            and not re.search(r"_crop\d+\.png$|_gray\.png$", r)]
    scripts = [r for r in made if r.endswith(".py") and os.path.basename(r) not in LIB_NAMES]
    specs = []
    for r in made:
        if r.endswith(".json") and not r.endswith(".check.json"):
            try:
                d = _load(os.path.join(ws, r))
                if isinstance(d, dict) and "nodes" in d and "edges" in d:
                    specs.append(r)
            except Exception:
                pass
    return made, outs, scripts, specs


def _probe_env(probe_out, checker_py):
    env = _agent_env()
    env["PYTHONPATH"] = PROBE_DIR + os.pathsep + env.get("PYTHONPATH", "")
    env["EVAL_PROBE_OUT"] = probe_out
    env["EVAL_CHECKER"] = checker_py
    env["MPLBACKEND"] = "Agg"
    return env


def _saves_figures(path):
    try:
        src = open(path, encoding="utf-8").read()
    except Exception:
        return False
    return bool(re.search(r"savefig|\.export\(|flowchart\(", src))


def _rerun(copy, scripts, specs, outs, env, log):
    runs = []
    for rel in scripts:
        path = os.path.join(copy, rel)
        if not _saves_figures(path):
            continue
        ok = False
        for cwd in dict.fromkeys([os.path.dirname(path), copy]):
            p = subprocess.run([sys.executable, path], cwd=cwd, env=env, capture_output=True, text=True, timeout=600)
            log.write(f"$ (cd {os.path.relpath(cwd, copy) or '.'}) python {rel}  -> {p.returncode}\n{p.stdout[-3000:]}\n{p.stderr[-3000:]}\n")
            if p.returncode == 0:
                ok = True
                break
        runs.append({"file": rel, "ok": ok})
    for rel in specs:
        stem_base = os.path.splitext(rel)[0]
        pngs = [o for o in outs if o.endswith(".png")]
        match = next((o for o in pngs if os.path.basename(stem_base) in os.path.basename(o)), pngs[0] if pngs else None)
        stem = os.path.splitext(match)[0] if match else stem_base
        style = "paper"
        if re.search(r"-(paper|dark)$", stem):
            stem, style = re.sub(r"-(paper|dark)$", "", stem), "all"
        exts = sorted({os.path.splitext(o)[1][1:] for o in outs
                       if os.path.splitext(o)[0].startswith(stem)} & {"png", "pdf", "svg"}) or ["png", "pdf"]
        sf = next((os.path.join(copy, s) for s in _walk(copy) if os.path.basename(s) == "schemfig.py"),
                  os.path.join(copy, ".claude", "skills", "paper-figures", "scripts", "schemfig.py"))
        cmd = [sys.executable, sf, "flow", os.path.join(copy, rel), "-o", os.path.join(copy, stem),
               "--style", style, "--formats", ",".join(exts)]
        p = subprocess.run(cmd, cwd=copy, env=env, capture_output=True, text=True, timeout=600)
        log.write(f"$ schemfig flow {rel} -o {stem} --style {style} -> {p.returncode}\n{p.stdout[-3000:]}\n{p.stderr[-3000:]}\n")
        runs.append({"file": rel, "ok": p.returncode == 0, "via": "schemfig flow"})
    return runs


def _transcript_info(path):
    info = {"skill_seen": "none", "cost_usd": None, "turns": None, "result_error": None}
    if not os.path.exists(path):
        return info
    seen_ws, seen_other = False, False
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if not isinstance(ev, dict):
                continue
            if ev.get("type") == "result":
                info["cost_usd"] = ev.get("total_cost_usd")
                info["turns"] = ev.get("num_turns")
                if ev.get("is_error"):
                    info["result_error"] = ev.get("subtype")
            msg = ev.get("message") or {}
            for block in msg.get("content") or [] if isinstance(msg.get("content"), list) else []:
                if block.get("type") != "tool_use":
                    continue
                blob = json.dumps(block.get("input", {}), ensure_ascii=False)
                if block.get("name") == "Skill" and "paper-figures" in blob:
                    seen_ws = seen_ws or ":" not in str(block.get("input", {}).get("skill", ""))
                    seen_other = seen_other or ":" in str(block.get("input", {}).get("skill", ""))
                if ".claude/skills/paper-figures" in blob:
                    seen_ws = True
                elif "paper-figures" in blob and "skills" in blob:
                    seen_other = True
    info["skill_seen"] = "workspace" if seen_ws else ("other" if seen_other else "none")
    return info


def _grade_one(rd, name, checker_py):
    td = os.path.join(rd, name)
    ws = os.path.join(td, "ws")
    task = _load(os.path.join(TASKS_DIR, name, "task.json"))
    frozen = _load(os.path.join(td, "frozen.json"))
    g = {"task": name, "title": task["title"], "notes": []}
    if frozen is None:
        g.update(status="未运行", gate1=False, gate2=False)
        return g
    now = _manifest(ws)
    tampered = sorted(set(now.items()) ^ set(frozen["files"].items()))
    g["tampered"] = sorted({k for k, _ in tampered})
    if g["tampered"]:
        g["notes"].append("冻结后文件被改动: " + ", ".join(g["tampered"][:5]))
    initial = _load(os.path.join(td, "initial.json"), {})
    made, outs, scripts, specs = _deliverables(ws, initial)
    g["deliverables"] = {"outputs": outs, "scripts": scripts, "specs": specs}
    has_pdf = any(o.endswith(".pdf") for o in outs)
    has_png = any(o.endswith(".png") for o in outs)
    has_src = bool(scripts or specs)

    gd = os.path.join(td, "grade")
    shutil.rmtree(gd, ignore_errors=True)
    copy = os.path.join(gd, "rerun")
    shutil.copytree(ws, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    for d, _, fs in os.walk(copy):
        for f in fs:
            os.chmod(os.path.join(d, f), 0o644)
    for rel in made:                                 # 删掉交付的图,重跑必须能再生成
        if rel.lower().endswith(OUTPUT_EXT) or rel.endswith(".check.json"):
            os.remove(os.path.join(copy, rel))
    probe_out = os.path.join(gd, "probe.jsonl")
    with open(os.path.join(gd, "rerun.log"), "w", encoding="utf-8") as log:
        runs = _rerun(copy, scripts, specs, outs, _probe_env(probe_out, checker_py), log)
    regenerated = [o for o in outs if os.path.exists(os.path.join(copy, o))]
    missing = [o for o in outs if o not in regenerated]
    g["rerun"] = {"runs": runs, "missing_outputs": missing}

    recs = []
    if os.path.exists(probe_out):
        recs = [json.loads(l) for l in open(probe_out, encoding="utf-8") if l.strip()]
    delivered_abs = {os.path.abspath(os.path.join(copy, o)) for o in outs}
    figs = {}
    for r in recs:
        k = (r["pid"], r["fig"])
        figs.setdefault(k, {"snapshot": None, "paths": []})
        if r.get("snapshot") is not None:
            figs[k]["snapshot"] = r["snapshot"]
        figs[k]["paths"].append(r.get("path"))
    deliver_figs = [f for f in figs.values() if delivered_abs & set(filter(None, f["paths"]))] or list(figs.values())

    # 关 1:交付齐全 + 可复现 + 内容检查
    png_dpi = []
    try:
        from PIL import Image
        for o in outs:
            if o.endswith(".png"):
                with Image.open(os.path.join(ws, o)) as im:
                    wpx = im.size[0]
                for f in deliver_figs:
                    snap = f["snapshot"] or {}
                    stems = {os.path.splitext(p)[0] for p in f["paths"] if p}
                    if os.path.splitext(os.path.abspath(os.path.join(copy, o)))[0] in stems and snap.get("size_in"):
                        png_dpi.append(wpx / snap["size_in"][0])
    except ImportError:
        g["notes"].append("没装 Pillow,跳过 PNG 分辨率检查")
    best = None
    for f in deliver_figs:
        snap = f["snapshot"]
        if not snap or "texts" not in snap:
            continue
        items = []
        for item in task["rubric"]:
            ok, ev = _check_item(item, snap, {"png_dpi": png_dpi})
            items.append({"type": item["type"], "why": item["why"], "ok": ok, "evidence": ev})
        score = sum(i["ok"] for i in items)
        if best is None or score > best["score"]:
            best = {"score": score, "items": items, "paths": [os.path.relpath(p, copy) for p in f["paths"] if p]}
    g["content"] = best
    delivery_ok = has_pdf and has_png and has_src
    rerun_ok = bool(runs) and all(r["ok"] for r in runs) and not missing
    content_ok = bool(best) and best["score"] == len(task["rubric"])
    if not delivery_ok:
        g["notes"].append("交付不全: " + ", ".join(n for n, ok in (("PDF", has_pdf), ("PNG", has_png), ("脚本或规格", has_src)) if not ok))
    if not rerun_ok:
        g["notes"].append("重跑失败或没有复现全部图: " + ", ".join(missing[:4]) if missing else "重跑失败,见 grade/rerun.log")
    g["gate1"] = bool(delivery_ok and rerun_ok and content_ok and not g["tampered"])

    # 关 2:独立体检
    errors, warnings, crashes = [], [], []
    for f in deliver_figs:
        snap = f["snapshot"] or {}
        if snap.get("check_error") or snap.get("snapshot_error"):
            crashes.append(snap.get("check_error") or snap.get("snapshot_error"))
        for it in snap.get("issues", []):
            (errors if it.get("severity") == "error" else warnings).append(it)
    g["check"] = {"errors": errors, "warnings": warnings, "crashes": crashes}
    g["gate2"] = bool(deliver_figs) and not errors and not crashes
    g.update(_transcript_info(os.path.join(td, "transcript.jsonl")))
    g["exit"] = frozen.get("exit")
    g["seconds"] = frozen.get("seconds")
    _dump(g, os.path.join(td, "grade.json"))
    return g


def cmd_grade(a):
    rd = _run_dir(a.run_id)
    meta = _load(os.path.join(rd, "meta.json"))
    checker_py = os.path.join(rd, "checker", "scripts", "paperfig.py")
    for name in meta["tasks"]:
        g = _grade_one(rd, name, checker_py)
        c = g.get("content") or {}
        print(f"[grade] {name}: 关1 {'✓' if g['gate1'] else '✗'}  关2 {'✓' if g['gate2'] else '✗'}"
              f"  内容 {c.get('score', 0)}/{len(_load(os.path.join(TASKS_DIR, name, 'task.json'))['rubric'])}"
              f"  体检 error {len((g.get('check') or {}).get('errors', []))}")


# ------------------------------------------------------------------ review

def cmd_review(a):
    rd = _run_dir(a.run_id)
    meta = _load(os.path.join(rd, "meta.json"))
    path = os.path.join(rd, "review.json")
    review = _load(path, {})
    for name in meta["tasks"]:
        g = _load(os.path.join(rd, name, "grade.json"))
        if not g:
            print(f"{name}: 还没 grade,跳过")
            continue
        pngs = [os.path.join(rd, name, "ws", o) for o in g["deliverables"]["outputs"] if o.endswith(".png")]
        prev = review.get(name, {}).get("verdict")
        if prev and not a.redo:
            print(f"{name}: 已判定 {prev},跳过(--redo 重判)")
            continue
        print(f"\n== {name} {g['title']} ==")
        for p in pngs:
            print("  ", p)
        if not pngs:
            review[name] = {"verdict": "fail", "note": "没有 PNG", "at": dt.date.today().isoformat()}
            continue
        if a.open and sys.platform == "darwin":
            subprocess.run(["open", *pngs], check=False)
        ans = input("可以直接用吗? [y]可用 / [n]不可用 / 回车跳过: ").strip().lower()
        if ans not in ("y", "n"):
            continue
        note = input("一句话理由(可空): ").strip()
        review[name] = {"verdict": "pass" if ans == "y" else "fail", "note": note, "at": dt.date.today().isoformat()}
        _dump(review, path)
    _dump(review, path)
    print(f"\n已写入 {path}")


# ------------------------------------------------------------------ report

def cmd_report(a):
    rd = _run_dir(a.run_id)
    meta = _load(os.path.join(rd, "meta.json"))
    review = _load(os.path.join(rd, "review.json"), {})
    rows, first_pass, pending = [], 0, 0
    print(f"run {meta['run_id']}  skill {meta['skill_hash']}  commit {meta.get('repo_commit')}"
          f"{' (有未提交改动)' if meta.get('repo_dirty') else ''}  model {meta.get('model')}\n")
    print("| 题目 | 关1 内容正确 | 关2 体检 | 关3 人工 | 首次可用 | 备注 |")
    print("|---|---|---|---|---|---|")
    for name in meta["tasks"]:
        g = _load(os.path.join(rd, name, "grade.json"))
        if not g:
            print(f"| {name} | 未评分 | | | | |")
            rows.append({"task": name, "graded": False})
            continue
        task = _load(os.path.join(TASKS_DIR, name, "task.json"))
        c = g.get("content") or {"score": 0, "items": []}
        v = review.get(name, {}).get("verdict")
        gate3 = v == "pass"
        auto = g["gate1"] and g["gate2"]
        usable = auto and gate3
        first_pass += usable
        pending += auto and v is None
        failed = [i["why"] + f"({i['evidence']})" for i in c["items"] if not i["ok"]]
        chk = g.get("check") or {}
        notes = failed + g["notes"] + [f"{e['code']}: {e['message']}" for e in chk.get("errors", [])[:3]]
        if g.get("skill_seen") != "workspace":
            notes.append(f"没看到读取工作区 skill({g.get('skill_seen')})")
        print(f"| {name} | {'✓' if g['gate1'] else '✗'} {c['score']}/{len(task['rubric'])} "
              f"| {'✓' if g['gate2'] else '✗'} E{len(chk.get('errors', []))} W{len(chk.get('warnings', []))} "
              f"| {'✓' if gate3 else ('待审' if v is None else '✗')} | {'✓' if usable else '✗'} "
              f"| {'; '.join(notes)[:300]} |")
        rows.append({"task": name, "graded": True, "gate1": g["gate1"], "content": [c["score"], len(task["rubric"])],
                     "gate2": g["gate2"], "errors": len(chk.get("errors", [])), "warnings": len(chk.get("warnings", [])),
                     "gate3": v, "usable": usable, "cost_usd": g.get("cost_usd"), "turns": g.get("turns"),
                     "seconds": g.get("seconds"), "skill_seen": g.get("skill_seen")})
    n = len(meta["tasks"])
    cost = sum(r.get("cost_usd") or 0 for r in rows)
    print(f"\n首次可用率 {first_pass}/{n}" + (f"(另有 {pending} 题自动两关已过、等人工判定)" if pending else "")
          + (f";总花费 ${cost:.2f}" if cost else ""))
    if a.record:
        if pending:
            sys.exit("还有题目等人工判定,先跑 review 再 --record")
        entry = {"run_id": meta["run_id"], "date": meta["created"][:10], "model": meta.get("model"),
                 "skill_hash": meta["skill_hash"], "repo_commit": meta.get("repo_commit"),
                 "repo_dirty": meta.get("repo_dirty"), "tasks_hash": meta["tasks_hash"],
                 "first_pass": [first_pass, n], "tasks": rows}
        with open(HISTORY, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"已追加到 {os.path.relpath(HISTORY, REPO)}")


# ------------------------------------------------------------------ CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="paper-figures 首次出图可用率评测")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def run_opts(p):
        p.add_argument("--model", help="传给 claude --model")
        p.add_argument("--budget", type=float, help="每题花费上限(美元)")
        p.add_argument("--jobs", type=int, default=1, help="并行题数")
        p.add_argument("--timeout", type=int, default=1800, help="每题超时(秒)")
        p.add_argument("--agent-cmd", help="自定义执行命令(shell 模板,可用 {prompt_file} {ws});默认 claude -p")

    p = sub.add_parser("prepare")
    p.add_argument("--skill", default=DEFAULT_SKILL, help="skill 目录或 .skill 包")
    p.add_argument("--tasks")
    p.add_argument("--run-id")
    p.set_defaults(fn=cmd_prepare)

    p = sub.add_parser("run")
    p.add_argument("run_id")
    run_opts(p)
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("grade")
    p.add_argument("run_id")
    p.set_defaults(fn=cmd_grade)

    p = sub.add_parser("review")
    p.add_argument("run_id")
    p.add_argument("--open", action="store_true", help="用系统看图工具打开 PNG")
    p.add_argument("--redo", action="store_true")
    p.set_defaults(fn=cmd_review)

    p = sub.add_parser("report")
    p.add_argument("run_id")
    p.add_argument("--record", action="store_true", help="追加到 history.jsonl")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("start", help="prepare + run + grade")
    p.add_argument("--skill", default=DEFAULT_SKILL)
    p.add_argument("--tasks")
    p.add_argument("--run-id")
    run_opts(p)
    p.set_defaults(fn=None)

    a = ap.parse_args(argv)
    if a.cmd == "start":
        a.run_id = cmd_prepare(a)
        cmd_run(a)
        cmd_grade(a)
        print(f"\n下一步: python3 run.py review {a.run_id} --open && python3 run.py report {a.run_id} --record")
        return
    a.fn(a)


if __name__ == "__main__":
    main()
