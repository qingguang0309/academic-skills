"""schemfig — 方法示意图/技术路线图组件库（数据图用 paperfig，示意图用本模块）。

所有组件画在 fig.transFigure 坐标（0–1 全图坐标）上，布局与 axes 无关；
嵌入的真实感小图用 img_axes 开窗。同一套布局代码套 STYLES 的 paper/dark
两个风格字典，一次产出论文白底版 + 汇报深色版。
完整技法与示例见 references/schematic-figures.md。

用法::

    import schemfig as sf

    sf.setup_fonts()                      # 自动探测 CJK 字体
    for name, S in sf.STYLES.items():
        fig = sf.canvas(12.4, 6.4, S)
        sf.rbox(fig, 0.40, 0.06, 0.43, 0.91, S["band"], S["band_ec"], lw=1.2, zorder=1)
        sf.arrow(fig, (0.36, 0.56), (0.42, 0.74), S["blue"][1], rad=0.24)
        sf.badge(fig, 0.40, 0.06, 0.43, 0.05, "目标：IoU ↑ ≥20 pp", S, accent="amber")
        fig.savefig(f"scheme-{name}.png", dpi=300, facecolor=fig.get_facecolor())
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

# 语义化风格字典：同名键在两个风格里都有，布局代码只引用键名。
# 强调色一律成对出现：(浅色填充, 深色描边/文字)。
STYLES = {
    "paper": dict(
        bg="#FFFFFF", band="#F5F7FA", band_ec="#E3E9F0",
        txt="#0F172A", sub="#5B6B7F", spine="#334155", foot="#5B6B7F",
        blue=("#EAF2FE", "#2563EB"), green=("#EAF8F1", "#059669"),
        rose=("#FDF0F0", "#DC2626"), purple=("#F3F0FD", "#7C3AED"),
        slate=("#F1F5F9", "#475569"), amber=("#FFF9EC", "#D97706"),
        rose_txt="#991B1B", amber_txt="#92400E",
        slab=["#BFDBFE", "#93C5FD", "#60A5FA"], slab_ec="#1E40AF",
    ),
    "dark": dict(
        bg="#0B1220", band="#111C33", band_ec="#22304F",
        txt="#E8EEF9", sub="#9AACC8", spine="#64748B", foot="#7C8DB5",
        blue=("#12305E", "#60A5FA"), green=("#0B3B2E", "#34D399"),
        rose=("#471523", "#FB7185"), purple=("#2A1A5E", "#A78BFA"),
        slate=("#1B2740", "#94A3B8"), amber=("#3B2A0A", "#FBBF24"),
        rose_txt="#FDA4AF", amber_txt="#FCD34D",
        slab=["#1D4ED8", "#3B82F6", "#60A5FA"], slab_ec="#93C5FD",
    ),
}


def setup_fonts(cjk: bool = True) -> str | None:
    """探测可用 CJK 字体并设置字体栈，返回选中的字体名（无则 None）。"""
    stack = ["Helvetica Neue", "Arial", "DejaVu Sans"]
    name = None
    if cjk:
        avail = {f.name for f in fm.fontManager.ttflist}
        name = next((f for f in ["PingFang SC", "Hiragino Sans GB", "Songti SC",
                                 "Microsoft YaHei", "SimHei", "Arial Unicode MS"]
                     if f in avail), None)
        if name:
            stack.insert(0, name)
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": stack,
                         "axes.unicode_minus": False, "svg.fonttype": "none"})
    return name


def canvas(width_in: float, height_in: float, S: dict):
    """建示意图画布。示意图按设计尺寸画、印刷时等比缩小，
    缩放后字号必须用 scale_check() 核算。"""
    fig = plt.figure(figsize=(width_in, height_in))
    fig.patch.set_facecolor(S["bg"])
    return fig


def _aspect(fig) -> float:
    w, h = fig.get_size_inches()
    return w / h


def rbox(fig, x, y, w, h, fc, ec, lw=1.6, rs=0.014, ls="-", zorder=3):
    """圆角框。mutation_aspect 抵消非方形画布的圆角变形。"""
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rs}",
                       transform=fig.transFigure, fc=fc, ec=ec, lw=lw, ls=ls,
                       mutation_aspect=_aspect(fig), zorder=zorder, clip_on=False)
    fig.add_artist(p)
    return p


def arrow(fig, p1, p2, color, rad=0.0, lw=2.0, zorder=2):
    """曲线箭头。rad 为弧度弯曲（正=逆时针鼓），支路用固定颜色编码数据流。"""
    a = FancyArrowPatch(p1, p2, transform=fig.transFigure,
                        connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>",
                        mutation_scale=15, lw=lw, color=color,
                        shrinkA=0, shrinkB=0, zorder=zorder, capstyle="round")
    fig.add_artist(a)
    return a


def slab(fig, cx, cy, w, h, fc, ec, dx=0.011, dy=0.020, zorder=4):
    """伪 3D 立板（CNN 特征图/数据块）。front/top/side 三面用亮度分级产生体积感。"""
    x0, y0 = cx - w / 2, cy - h / 2
    front = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]
    top = [(x0, y0 + h), (x0 + w, y0 + h), (x0 + w + dx, y0 + h + dy), (x0 + dx, y0 + h + dy)]
    side = [(x0 + w, y0), (x0 + w + dx, y0 + dy), (x0 + w + dx, y0 + h + dy), (x0 + w, y0 + h)]
    for pts, shade in [(top, 0.88), (side, 0.75), (front, 1.0)]:
        c = np.clip(np.array(matplotlib.colors.to_rgb(fc)) * shade, 0, 1)
        fig.add_artist(Polygon(pts, closed=True, transform=fig.transFigure,
                               fc=c, ec=ec, lw=1.1, zorder=zorder))


def img_axes(fig, rect, S):
    """嵌入真实感小图的开窗：无刻度、细边框，rect 为全图坐标 [x, y, w, h]。"""
    ax = fig.add_axes(rect)
    ax.set_zorder(2)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(S["spine"])
        s.set_linewidth(1.2)
    return ax


def badge(fig, x, y, w, h, text, S, accent="amber", fontsize=10, lw=1.3, zorder=4):
    """胶囊高亮框：承载关键量化承诺（目标指标、精度、约束）。"""
    fill, edge = S[accent]
    rbox(fig, x, y, w, h, fill, edge, lw=lw, rs=0.011, zorder=zorder)
    fig.text(x + w / 2, y + h / 2, text, fontsize=fontsize,
             color=S.get(f"{accent}_txt", edge), ha="center", va="center",
             weight=600, zorder=zorder + 1)


def scale_check(design_width_in: float, print_width_mm: float, *font_pts: float) -> dict:
    """核算缩印后的实际字号。示意图按放大画布设计时，交付前必须跑一次，
    确认最小字号 ≥ 5 pt（正文标签建议 ≥ 6 pt）。"""
    scale = print_width_mm / (design_width_in * 25.4)
    result = {pt: round(pt * scale, 1) for pt in font_pts}
    print(f"印刷缩放 {scale:.0%}：", ", ".join(f"{k}pt -> {v}pt" for k, v in result.items()))
    return result
