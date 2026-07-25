#!/usr/bin/env python3
# ============================================================
# formula.py — 把 LaTeX 公式渲染成透明底高分辨率 PNG,供 slidekit 的
# formula 块嵌入。技术类汇报必须把关键方程/损失函数/判据摊在页面上,
# 用图片而不是文字拼装:字号、上下标、分式的排版交给排版引擎。
#
# 渲染后端(自动降级):
#   1) 系统装了 LaTeX(latex + dvipng)→ 走真 LaTeX,支持 amsmath 全部语法
#   2) 否则用 matplotlib mathtext(零额外依赖,覆盖绝大多数论文级公式)
#
# 用法:
#   python3 formula.py eqs.json -o assets/eq        # 批量,按 id 命名
#   python3 formula.py --tex "E = mc^2" -o assets/eq/e.png
#
# eqs.json:
# [ { "id": "loss", "tex": "\\mathcal{L} = \\lambda_r \\mathcal{L}_r + \\mathcal{L}_b",
#     "size": 22 } ]        // size 为公式字号(pt),默认 22
# ============================================================
import argparse
import json
import pathlib
import shutil
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DEFAULT_SIZE = 22


def render(tex: str, out: pathlib.Path, size: int, color: str, use_latex: bool):
    """把单条公式渲染成紧贴内容的透明 PNG。"""
    plt.rcParams.update({
        "text.usetex": use_latex,
        "mathtext.fontset": "cm",        # Computer Modern:与论文观感一致
        "font.family": "serif",
        "savefig.transparent": True,
    })
    if use_latex:
        plt.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}\usepackage{amssymb}"
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${tex}$", fontsize=size, color=color)
    try:
        fig.savefig(out, dpi=300, bbox_inches="tight", pad_inches=0.06)
    finally:
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="LaTeX 公式 → 透明 PNG(供 slidekit formula 块)")
    ap.add_argument("spec", nargs="?", help="eqs.json;与 --tex 二选一")
    ap.add_argument("--tex", help="单条公式(不含 $)")
    ap.add_argument("-o", "--out", required=True, help="批量时为输出目录,单条时为 .png 路径")
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE, help=f"字号,默认 {DEFAULT_SIZE}")
    ap.add_argument("--color", default="1A1A1A", help="公式颜色(十六进制,默认近黑)")
    ap.add_argument("--no-latex", action="store_true", help="强制用 mathtext,不探测系统 LaTeX")
    args = ap.parse_args()

    use_latex = (not args.no_latex) and bool(shutil.which("latex") and shutil.which("dvipng"))
    backend = "LaTeX" if use_latex else "matplotlib mathtext"
    color = "#" + args.color.lstrip("#")

    if args.tex:
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        render(args.tex, out, args.size, color, use_latex)
        print(f"[formula/{backend}] {out}")
        return

    if not args.spec:
        sys.exit("[formula] 需要 eqs.json 或 --tex")
    eqs = json.loads(pathlib.Path(args.spec).read_text())
    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    for e in eqs:
        out = outdir / f"{e['id']}.png"
        try:
            render(e["tex"], out, e.get("size", args.size), color, use_latex)
        except Exception as ex:  # noqa: BLE001 —— 单条失败不阻断其余公式
            print(f"  [fail] {e['id']}: {ex}", file=sys.stderr)
            continue
        print(f"  [{e['id']}] {out.name}")
    print(f"[formula/{backend}] {len(eqs)} 条 → {outdir}/")
    print("[formula] 请用 Read 亲眼检查:符号是否渲染正确、上下标是否清晰、有无语法回退成原文。")


if __name__ == "__main__":
    main()
