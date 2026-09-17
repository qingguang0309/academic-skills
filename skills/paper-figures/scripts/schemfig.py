"""schemfig — 方法示意图/技术路线图组件库（数据图用 paperfig，示意图用本模块）。

所有组件画在 fig.transFigure 坐标（0–1 全图坐标）上，布局与 axes 无关；
嵌入的真实感小图用 img_axes 开窗。同一套布局代码套 STYLES 的 paper/dark
两个风格字典，一次产出论文白底版 + 汇报深色版。
完整技法与示例见 references/schematic-figures.md。

本模块内置三道防线，专治示意图两大顽疾（文字溢出框线、箭头被元素覆盖）：

1. **实测排版**：``text_box``/``badge`` 先渲染文字、实测像素宽高，再按实测尺寸
   生成外框——文字从机制上不可能溢出；给定 max_w 时自动换行/缩字号。
   不要再用"rbox + fig.text + 拍坐标"手工凑框，那是溢出的根源。
2. **箭头避障**：rbox/text_box/badge/slab/img_axes 创建时自动注册为障碍物；
   ``connect``/``arrow`` 画线前对弧线采样检测碰撞，自动微调弧度绕开。
   因此**先画完所有框，再画箭头**——箭头只会避让已注册的障碍物。
3. **导出体检**：``export`` 联动布局体检（含箭头穿越、文字跨框线复检），
   告警非零默认拒绝出图，并自动生成局部放大块供逐块肉眼检查。

流程图 / 技术路线图不要手拍坐标,写声明式规格交给引擎排版布线::

    fig, info = sf.flowchart(spec, style="paper")   # 节点进"泳道 × 列"网格,正交折线自动布线
    sf.export(fig, "roadmap")                       # 体检合并布线诊断

    # 或命令行:python3 schemfig.py flow roadmap.json -o figures/roadmap --style all

体检结果是结构化诊断 Issue(code / subject / evidence / fixes),导出失败时写进
<stem>.check.json;按 code 对症修复,连续两轮告警数不降就停下来如实报告。

用法::

    import schemfig as sf

    sf.setup_fonts()                      # 自动探测 CJK 字体
    for name, S in sf.STYLES.items():
        fig = sf.canvas(12.4, 6.4, S)
        sf.rbox(fig, 0.40, 0.06, 0.43, 0.91, S["band"], S["band_ec"],
                lw=1.2, zorder=1, solid=False)          # 底带=容器,solid=False 不算障碍
        a = sf.text_box(fig, 0.20, 0.50, "CNN 稠密分支", S, accent="blue")
        b = sf.text_box(fig, 0.62, 0.50, "跨模态融合", S, accent="purple")
        sf.connect(fig, a, b, S["blue"][1])              # 自动锚边 + 自动避障
        sf.badge(fig, 0.40, 0.06, 0.43, 0.05, "目标：IoU ↑ ≥20 pp", S, accent="amber")
        sf.export(fig, f"scheme-{name}", dpi=300)        # 体检不过不出图
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import textwrap
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

try:  # 结构化诊断与 paperfig 共用同一个类型,体检结果可以混在一起排序、写报告
    from paperfig import REPAIR_RULES, Issue, format_issue, sort_issues, write_report
except ImportError:  # 单独使用 schemfig(没带 paperfig)时的兜底,字段与 paperfig.Issue 一致
    REPAIR_RULES = ("按 code 对症修复,改完重跑体检;连续两轮告警数没有下降就停下来如实报告。"
                    "不许为了通过体检删掉物理量、单位、标注或连线标签。")

    class Issue(str):
        def __new__(cls, code, message, subject=None, evidence=None, fixes=(), severity="error"):
            obj = super().__new__(cls, message)
            obj.code, obj.subject, obj.severity = code, subject, severity
            obj.evidence, obj.fixes = dict(evidence or {}), list(fixes)
            return obj

        def to_dict(self):
            return {"code": self.code, "severity": self.severity, "message": str(self),
                    "subject": self.subject, "evidence": self.evidence, "fixes": self.fixes}

    def sort_issues(issues):
        return [i if hasattr(i, "code") else Issue("legacy", str(i)) for i in issues]

    def format_issue(item):
        head = f"[{getattr(item, 'severity', 'error')} {getattr(item, 'code', 'legacy')}] {item}"
        fixes = getattr(item, "fixes", [])
        return head + ("\n    修法: " + " / ".join(fixes) if fixes else "")

    def write_report(stem, issues):
        path = f"{stem}.check.json"
        issues = sort_issues(issues)
        if not issues:
            if os.path.exists(path):
                os.remove(path)
            return None
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"issues": [i.to_dict() for i in issues], "repair_rules": REPAIR_RULES},
                      fh, ensure_ascii=False, indent=2)
        return path

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
                                 "Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
                                 "WenQuanYi Zen Hei", "Arial Unicode MS"]
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
    fig._schem_obstacles = []            # El 列表:箭头避障 + 体检用
    fig._schem_arrows = []               # 已画箭头档案:体检复查用
    fig._schem_check = lambda f=fig: check(f)   # paperfig.check_layout 会调用
    return fig


def _aspect(fig) -> float:
    w, h = fig.get_size_inches()
    return w / h


def _renderer(fig):
    try:
        return fig.canvas.get_renderer()
    except AttributeError:               # 非 Agg 后端兜底
        fig.canvas.draw()
        return fig.canvas.get_renderer()


class El:
    """已放置元素的几何句柄：figure 坐标矩形 + 锚点计算。

    text_box/rbox/badge/slab/img_axes 都返回/携带 El；connect 用它自动求
    框沿锚点，避障用它当障碍物。"""

    def __init__(self, fig, x, y, w, h, label="", artists=()):
        self.fig, self.x, self.y, self.w, self.h = fig, x, y, w, h
        self.label, self.artists = label, tuple(artists)

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def contains(self, p, margin=0.004):
        return (self.x - margin <= p[0] <= self.x + self.w + margin
                and self.y - margin <= p[1] <= self.y + self.h + margin)

    def anchor(self, side="auto", other=None, gap=0.006):
        """框沿锚点（略微悬出 gap，箭头不扎进框身）。side="auto" 时朝 other
        （点或 El）所在的主方向取边中点。"""
        if isinstance(other, El):
            other = (other.cx, other.cy)
        if side == "auto":
            if other is None:
                side = "right"
            else:
                w_in, h_in = self.fig.get_size_inches()
                dx = (other[0] - self.cx) * w_in     # 用物理尺寸判方向,不受画布比例骗
                dy = (other[1] - self.cy) * h_in
                side = (("right" if dx > 0 else "left") if abs(dx) >= abs(dy)
                        else ("top" if dy > 0 else "bottom"))
        return {"left":   (self.x - gap, self.cy),
                "right":  (self.x + self.w + gap, self.cy),
                "top":    (self.cx, self.y + self.h + gap),
                "bottom": (self.cx, self.y - gap)}[side]


def _register(fig, el):
    if hasattr(fig, "_schem_obstacles"):
        fig._schem_obstacles.append(el)
    return el


def register_obstacle(fig, x, y, w, h, label="manual"):
    """手工把一块区域登记为障碍物（如 add_axes 直接画的内容区）。"""
    return _register(fig, El(fig, x, y, w, h, label=label))


def rbox(fig, x, y, w, h, fc, ec, lw=1.6, rs=0.014, ls="-", zorder=3,
         solid=True, label=""):
    """圆角框。mutation_aspect 抵消非方形画布的圆角变形。

    solid=True（默认）登记为障碍物，箭头会绕开、文字不许跨线；
    背景底带/阶段分区这类**容器**必须传 solid=False——元素本来就要画在它上面。
    返回 El（.patch 取图形对象）。"""
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rs}",
                       transform=fig.transFigure, fc=fc, ec=ec, lw=lw, ls=ls,
                       mutation_aspect=_aspect(fig), zorder=zorder, clip_on=False)
    p._schem_solid = solid               # paperfig 体检据此跳过容器
    fig.add_artist(p)
    el = El(fig, x, y, w, h, label=label or "rbox", artists=(p,))
    el.patch = p
    if solid:
        _register(fig, el)
    return el


def _measure(fig, t):
    """文字的 figure 坐标 bbox (x, y, w, h)。"""
    b = t.get_window_extent(_renderer(fig))
    inv = fig.transFigure.inverted()
    (x0, y0), (x1, y1) = inv.transform([(b.x0, b.y0), (b.x1, b.y1)])
    return x0, y0, x1 - x0, y1 - y0


def _shrink_to_fit(fig, t, text, max_w, fontsize):
    """max_w 内放不下时：先按行宽换行，仍超宽再逐级缩字号（下限 6 pt）。"""
    w = _measure(fig, t)[2]
    if w <= max_w:
        return
    lines = math.ceil(w / max_w)
    if lines > 1 and "\n" not in text:
        if " " in text.strip():
            t.set_text("\n".join(textwrap.wrap(text, math.ceil(len(text) / lines))))
        else:                             # CJK 无空格,按字数均分
            n = math.ceil(len(text) / lines)
            t.set_text("\n".join(text[i:i + n] for i in range(0, len(text), n)))
    size = fontsize
    while _measure(fig, t)[2] > max_w and size > 6:
        size -= 0.5
        t.set_fontsize(size)


def text_box(fig, cx, cy, text, S, accent="slate", fontsize=10, weight=600,
             pad=0.012, max_w=None, min_w=0.0, min_h=0.0, lw=1.4, rs=0.012,
             zorder=4, color=None, sub=None, label=""):
    """**先测文字、再配框**——框永远比文字大，溢出从机制上不可能。

    在 (cx, cy) 居中放文字（可含换行；sub 追加一行小字），实测渲染尺寸后按
    实测值 + pad 生成圆角框。max_w 限宽时自动换行/缩字号。返回 El，
    直接喂给 connect() 连线。这是示意图内容框的**默认画法**，
    代替"rbox + fig.text 手拍宽高"。"""
    fill, edge = S[accent]
    body = text if sub is None else f"{text}\n{sub}"
    t = fig.text(cx, cy, body, fontsize=fontsize, color=color or edge,
                 ha="center", va="center", weight=weight, zorder=zorder + 1,
                 linespacing=1.25)
    if max_w:
        _shrink_to_fit(fig, t, body, max_w - 2 * pad, fontsize)
    tx, ty, tw, th = _measure(fig, t)
    pad_y = pad * _aspect(fig)           # 视觉等距内边距
    w = max(tw + 2 * pad, min_w)
    h = max(th + 2 * pad_y, min_h)
    el = rbox(fig, cx - w / 2, cy - h / 2, w, h, fill, edge, lw=lw, rs=rs,
              zorder=zorder, label=label or text.split("\n")[0][:16])
    el.text = t
    return el


def badge(fig, x, y, w, h, text, S, accent="amber", fontsize=10, lw=1.3, zorder=4):
    """胶囊高亮框：承载关键量化承诺（目标指标、精度、约束）。
    文字实测后若比给定宽度宽，以原中心为准自动加宽（不会再溢出）。返回 El。"""
    fill, edge = S[accent]
    t = fig.text(x + w / 2, y + h / 2, text, fontsize=fontsize,
                 color=S.get(f"{accent}_txt", edge), ha="center", va="center",
                 weight=600, zorder=zorder + 1)
    tw, th = _measure(fig, t)[2:]
    pad, pad_y = 0.010, 0.010 * _aspect(fig)
    if tw + 2 * pad > w:
        x -= (tw + 2 * pad - w) / 2
        w = tw + 2 * pad
    if th + 2 * pad_y > h:
        y -= (th + 2 * pad_y - h) / 2
        h = th + 2 * pad_y
    el = rbox(fig, x, y, w, h, fill, edge, lw=lw, rs=0.011, zorder=zorder,
              label=text[:16])
    el.text = t
    return el


# ---------------------------------------------------------------- 箭头与避障

def _bezier(p1, c, p2, ts):
    p1, c, p2 = map(np.asarray, (p1, c, p2))
    return [(1 - t) ** 2 * p1 + 2 * t * (1 - t) * c + t ** 2 * p2 for t in ts]


def _arc3_samples(fig, p1, p2, rad, n=49):
    """arc3 弧线的 display 坐标采样点（与 matplotlib 控制点公式一致）。"""
    d1, d2 = fig.transFigure.transform([p1, p2])
    x12, y12 = (d1[0] + d2[0]) / 2, (d1[1] + d2[1]) / 2
    dx, dy = d2[0] - d1[0], d2[1] - d1[1]
    c = (x12 + rad * dy, y12 - rad * dx)
    return _bezier(d1, c, d2, np.linspace(0.10, 0.90, n))


def _disp_rect(fig, rect, pad_px=2.0):
    (x0, y0), (x1, y1) = fig.transFigure.transform(
        [(rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3])])
    return (x0 - pad_px, y0 - pad_px, x1 + pad_px, y1 + pad_px)


def _hits(samples, rects):
    """采样点命中的障碍物下标集合。"""
    out = set()
    for px, py in samples:
        for i, (x0, y0, x1, y1) in enumerate(rects):
            if x0 <= px <= x1 and y0 <= py <= y1:
                out.add(i)
    return out


def _live_obstacles(fig, p1, p2, ignore):
    ign = {id(e) for e in ignore}
    return [el for el in getattr(fig, "_schem_obstacles", [])
            if id(el) not in ign and not el.contains(p1) and not el.contains(p2)]


def arrow(fig, p1, p2, color, rad=0.0, lw=2.0, zorder=2, avoid=True,
          ignore=(), label=""):
    """曲线箭头。rad 为弧度弯曲（正=逆时针鼓），支路用固定颜色编码数据流。

    p1/p2 可以是坐标点或 El（自动取朝向对方的框沿锚点）。avoid=True 时对
    弧线采样检测是否穿过已注册障碍物，穿过则自动在 rad 附近搜索能绕开的
    弧度；绕不开保留告警交给 export 体检拦截。**先画框后画箭头**，
    避障只认画箭头时已注册的障碍物。"""
    ignore = list(ignore)
    if isinstance(p1, El):
        ignore.append(p1)
        p1 = p1.anchor("auto", other=p2 if not isinstance(p2, El) else (p2.cx, p2.cy))
    if isinstance(p2, El):
        ignore.append(p2)
        p2 = p2.anchor("auto", other=p1)
    used = rad
    if avoid and getattr(fig, "_schem_obstacles", None):
        obs = _live_obstacles(fig, p1, p2, ignore)
        rects = [_disp_rect(fig, el.rect) for el in obs]
        best, best_n = rad, None
        for cand in [rad] + [rad + s * d for d in (0.12, 0.22, 0.32, 0.45)
                             for s in (1, -1)]:
            n = len(_hits(_arc3_samples(fig, p1, p2, cand), rects))
            if n == 0:
                best, best_n = cand, 0
                break
            if best_n is None or n < best_n:
                best, best_n = cand, n
        used = best
        if best_n:
            blocked = ", ".join(el.label for i, el in enumerate(obs)
                                if i in _hits(_arc3_samples(fig, p1, p2, used),
                                              rects)) or "?"
            print(f"[schemfig] 箭头 {label or p1}->{p2} 自动避障失败,仍穿过: "
                  f"{blocked}(export 体检会拦截,请改布局或路径)")
        elif abs(used - rad) > 1e-9:
            print(f"[schemfig] 箭头 {label or ''} rad {rad:+.2f} -> {used:+.2f} 以绕开障碍物")
    # 短箭头自适应缩头:头长(≈0.4*mutation_scale)不得超过全长的一半,否则
    # FancyArrowPatch 会退化成一个不挨两端的悬浮三角(历史顽疾之三)。
    d_pt = float(np.hypot(*(np.asarray(fig.transFigure.transform(p2), float)
                            - fig.transFigure.transform(p1)))) / fig.dpi * 72.0
    ms = float(np.clip(1.25 * d_pt, 6.0, 15.0))
    lw_used = min(lw, 0.28 * ms)          # 短箭头同时收线宽,避免头比杆细
    a = FancyArrowPatch(p1, p2, transform=fig.transFigure,
                        connectionstyle=f"arc3,rad={used}", arrowstyle="-|>",
                        mutation_scale=ms, lw=lw_used, color=color,
                        shrinkA=0, shrinkB=0, zorder=zorder, capstyle="round")
    fig.add_artist(a)
    if hasattr(fig, "_schem_arrows"):
        fig._schem_arrows.append(dict(p1=tuple(p1), p2=tuple(p2), rad=used,
                                      ignore={id(e) for e in ignore},
                                      label=label, d_pt=d_pt))
    return a


def connect(fig, a, b, color, rad=0.0, side_a="auto", side_b="auto",
            gap=0.006, **kw):
    """框到框连线：自动取双方框沿锚点（起止点保证在框外），再走 arrow 避障。
    连内容框**一律用这个**，不要手拍箭头起止坐标。"""
    # 短距连线自动收边距:两框间隙不足 18pt 时,固定 gap 会吃掉大半空间,
    # 箭头只剩个头。按裸间距缩 gap,把空间留给箭头本体。
    if isinstance(a, El) and isinstance(b, El):
        p0a = a.anchor(side_a, other=b, gap=0.0)
        p0b = b.anchor(side_b, other=a, gap=0.0)
        d0_pt = float(np.hypot(*(np.asarray(fig.transFigure.transform(p0b), float)
                                 - fig.transFigure.transform(p0a)))) / fig.dpi * 72.0
        if d0_pt < 18.0:
            gap = gap * max(0.25, d0_pt / 36.0)
    pa = a.anchor(side_a, other=b, gap=gap) if isinstance(a, El) else tuple(a)
    pb = b.anchor(side_b, other=a, gap=gap) if isinstance(b, El) else tuple(b)
    ign = [e for e in (a, b) if isinstance(e, El)] + list(kw.pop("ignore", ()))
    lbl = kw.pop("label", "") or "->".join(e.label for e in (a, b)
                                           if isinstance(e, El))
    return arrow(fig, pa, pb, color, rad=rad, ignore=ign, label=lbl, **kw)


def _arrow_samples(fig, rec, step_px=2.0):
    """箭头在 display 坐标下的采样点:折线逐段按像素步长采样,弧线沿用 arc3 公式。"""
    if rec.get("points"):
        pts = fig.transFigure.transform(rec["points"])
        out = []
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            n = max(2, int(math.hypot(x1 - x0, y1 - y0) / step_px))
            out += [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
                    for t in np.linspace(0.0, 1.0, n, endpoint=False)]
        out.append(tuple(pts[-1]))
        return out
    return _arc3_samples(fig, rec["p1"], rec["p2"], rec["rad"], n=61)


def check(fig) -> list:
    """schemfig 几何体检:箭头是否穿过障碍物/压过文字,以及声明式流程图的布线诊断。
    export 前自动跑(paperfig.check_layout 也会调用),全部障碍物注册完之后复查,
    所以"先画箭头后画框"造成的穿越也逃不掉。返回 Issue 列表。"""
    issues = []
    r = _renderer(fig)
    texts = []
    for t in fig.findobj(matplotlib.text.Text):
        s = t.get_text().strip()
        if s and t.get_visible():
            b = t.get_window_extent(r)
            if b.width > 1 and b.height > 1:
                texts.append((t, s, (b.x0 - 1, b.y0 - 1, b.x1 + 1, b.y1 + 1)))
    inv = fig.transFigure.inverted()
    for rec in getattr(fig, "_schem_arrows", []):
        p1, p2 = rec["p1"], rec["p2"]
        name = rec["label"] or str(p1)
        if rec.get("d_pt", 99.0) < 5.0:
            issues.append(Issue(
                "arrow/too-short", f"箭头过短(全长 {rec['d_pt']:.1f}pt < 5pt),已退化: {name}",
                subject=name, evidence={"length_pt": round(rec["d_pt"], 1)},
                fixes=["拉开两元素间距", "减小 connect 的 gap"]))
        obs = [el for el in getattr(fig, "_schem_obstacles", [])
               if id(el) not in rec["ignore"]
               and not el.contains(p1) and not el.contains(p2)]
        samples = _arrow_samples(fig, rec)
        for i in sorted(_hits(samples, [_disp_rect(fig, el.rect) for el in obs])):
            issues.append(Issue(
                "arrow/through-element", f"箭头穿过元素: {name} × {obs[i].label!r}",
                subject={"arrow": name, "element": obs[i].label},
                fixes=["调整元素位置,给连线留出通道", "改 connect 的 side_a/side_b 或 rad",
                       "流程图/技术路线图改用 sf.flowchart 声明式规格,由引擎布线"]))
        excl = [el for el in getattr(fig, "_schem_obstacles", [])
                if id(el) in rec["ignore"] or el.contains(p1) or el.contains(p2)]
        own = rec.get("own_texts", set())
        for i in sorted(_hits(samples, [tb for _, _, tb in texts])):
            t, s, tb = texts[i]
            if id(t) in own:
                continue                      # 这条连线自己的标签
            c = inv.transform(((tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2))
            if any(el.contains(c) for el in excl):
                continue                      # 起止框自己的文字不算
            issues.append(Issue(
                "arrow/over-text", f"箭头压过文字: {name} × {s!r}",
                subject={"arrow": name, "text": s},
                fixes=["移动被压的文字或标签", "调整连线路径或元素位置"]))
    issues += list(getattr(fig, "_schem_flow_issues", []))
    return issues


def export(fig, stem, dpi=300, formats=("png", "pdf"), strict=True, crops=True, report=True):
    """示意图导出:体检(paperfig 全套 + schemfig 几何)→ 拦截 → 出图 → 切块。

    图要插 Word/PPT 时在 formats 里加 "svg"(文字自动转路径):Word 2016+ 原生
    支持 SVG 矢量插入,任意缩放不糊;PNG 插 Word 会被默认压缩到 220 ppi。

    有 error 级诊断时 strict=True 直接拒绝导出,诊断写进 <stem>.check.json——
    按 code 对症修复后重跑,不许带病交付。出图后自动生成 2×2 局部放大块,
    **每一块都必须用 Read 亲眼检查**:整图缩略时几像素的箭头擦边/文字压线是看不见的。"""
    try:
        import paperfig as pf
        issues = pf.check_layout(fig)     # 已含 fig._schem_check 的几何检查
    except ImportError:
        issues = check(fig)
    issues = sort_issues(issues)
    for item in issues:
        print(f"[schemfig 布局告警] {format_issue(item)}")
    if report:
        write_report(stem, issues)
    errors = [i for i in issues if getattr(i, "severity", "error") == "error"]
    if errors and strict:
        raise RuntimeError(f"布局体检 {len(errors)} 条 error,已阻断导出(诊断见 {stem}.check.json)。"
                           f"{REPAIR_RULES}确认误报才可 strict=False,并在交付说明中说明理由。")
    paths = []
    for ext in formats:
        p = f"{stem}.{ext}"
        if ext == "svg":
            # Word/PPT 用矢量:文字转路径,不依赖对方机器字体,缩放永远清晰
            with matplotlib.rc_context({"svg.fonttype": "path"}):
                fig.savefig(p, facecolor=fig.get_facecolor())
        else:
            fig.savefig(p, dpi=dpi, facecolor=fig.get_facecolor())
        paths.append(p)
    png = next((p for p in paths if p.endswith(".png")), None)
    if crops and png:
        cs = make_crops(png)
        print("[schemfig] 局部放大块已生成，请逐块 Read 检查: " + ", ".join(cs))
        paths += cs
    return paths


def make_crops(png_path, rows=2, cols=2, overlap=0.10):
    """PNG 切成 rows×cols 带重叠的局部块，供放大肉眼检查。"""
    from PIL import Image
    im = Image.open(png_path)
    W, H = im.size
    stem = png_path[:-4]
    out = []
    for i in range(rows):
        for j in range(cols):
            x0 = max(0, int((j - overlap) * W / cols))
            x1 = min(W, int((j + 1 + overlap) * W / cols))
            y0 = max(0, int((i - overlap) * H / rows))
            y1 = min(H, int((i + 1 + overlap) * H / rows))
            p = f"{stem}_crop{i * cols + j + 1}.png"
            im.crop((x0, y0, x1, y1)).save(p)
            out.append(p)
    return out


def slab(fig, cx, cy, w, h, fc, ec, dx=0.011, dy=0.020, zorder=4, label="slab"):
    """伪 3D 立板（CNN 特征图/数据块）。front/top/side 三面亮度分级产生体积感。
    自动注册为障碍物；返回 El。"""
    x0, y0 = cx - w / 2, cy - h / 2
    front = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]
    top = [(x0, y0 + h), (x0 + w, y0 + h), (x0 + w + dx, y0 + h + dy), (x0 + dx, y0 + h + dy)]
    side = [(x0 + w, y0), (x0 + w + dx, y0 + dy), (x0 + w + dx, y0 + h + dy), (x0 + w, y0 + h)]
    arts = []
    for pts, shade in [(top, 0.88), (side, 0.75), (front, 1.0)]:
        c = np.clip(np.array(matplotlib.colors.to_rgb(fc)) * shade, 0, 1)
        poly = Polygon(pts, closed=True, transform=fig.transFigure,
                       fc=c, ec=ec, lw=1.1, zorder=zorder)
        fig.add_artist(poly)
        arts.append(poly)
    return _register(fig, El(fig, x0, y0, w + dx, h + dy, label=label, artists=arts))


def img_axes(fig, rect, S, label="panel"):
    """嵌入真实感小图的开窗：无刻度、细边框，rect 为全图坐标 [x, y, w, h]。
    自动注册为障碍物（箭头不会横穿数据 panel）。"""
    ax = fig.add_axes(rect)
    ax.set_zorder(2)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(S["spine"])
        s.set_linewidth(1.2)
    ax._schem_el = _register(fig, El(fig, *rect, label=label))
    return ax


def scale_check(design_width_in: float, print_width_mm: float, *font_pts: float) -> dict:
    """核算缩印后的实际字号。示意图按放大画布设计时，交付前必须跑一次，
    确认最小字号 ≥ 5 pt（正文标签建议 ≥ 6 pt）。"""
    scale = print_width_mm / (design_width_in * 25.4)
    result = {pt: round(pt * scale, 1) for pt in font_pts}
    print(f"印刷缩放 {scale:.0%}：", ", ".join(f"{k}pt -> {v}pt" for k, v in result.items()))
    return result


# ================================================================ 声明式流程图 / 技术路线图
#
# 流程图、技术路线图这类"节点 + 连线"的图,手拍坐标最容易出问题:间距不匀、箭头绕路、
# 几条线叠在一起分不清。这里改成写规格、由引擎排版:
#
# - 节点放进"泳道 × 列"网格,同列同宽、同泳道同高,尺寸由文字实测决定;
# - 连线是正交折线,只在列间隙与泳道间隙里走,每条线占一条独立轨道,不会穿过其它节点;
# - 同一条框边上的多个端口自动等距错开,第一段与最后一段垂直于框边;
# - 标签沿线段挑不与其它连线相交的位置放,间隙按标签实测宽度自动加宽。
#
# 规格字段与完整示例见 references/schematic-figures.md「声明式流程图」。

FLOW_STYLE = dict(font=10.5, label_font=9.5, header_font=11.5, node_max_w=1.9, pad=0.1,
                  col_gap=0.55, lane_gap=0.36, track=0.14, corner=0.0, node_lw=1.4,
                  edge_lw=1.5, margin=0.2)
_FLOW_KEYS = {"direction", "lanes", "stages", "nodes", "edges", "style", "accents", "size"}
_NODE_KEYS = {"id", "label", "sub", "lane", "col", "accent", "tone", "max_w"}
_EDGE_KEYS = {"from", "to", "label", "accent", "style"}
_LANE_KEYS = {"id", "label"}
_SIZE_KEYS = {"max_width", "max_height"}
_EPS = 0.015        # 端口离框沿的距离(in),箭头尖正好顶到框线外侧
_HEAD_IN = 0.2      # 进入目标框前至少留出的直线段(in),保证箭头头部完整
_NO_BREAK = set("，。、；：！？）》」』,.;:!?)%")


class FlowSpecError(ValueError):
    """规格本身有 error 级问题,无法排版。``issues`` 是结构化诊断列表。"""

    def __init__(self, issues):
        self.issues = sort_issues(issues)
        super().__init__("流程图规格有误:\n" + "\n".join(format_issue(i) for i in self.issues))


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_flow(spec, S=None):
    """只校验规格(不排版、不出图)。返回 (规范化后的规格或 None, Issue 列表)。"""
    S = S or STYLES["paper"]
    issues = []

    def E(code, msg, subject=None, fixes=(), severity="error", **ev):
        issues.append(Issue(code, msg, subject=subject, evidence=ev, fixes=fixes, severity=severity))

    def unknown(obj, allowed, where):
        for k in obj:
            if k not in allowed:
                E("spec/unknown-field", f"{where} 里有未知字段 {k!r}", subject=f"{where}.{k}",
                  fixes=[f"删掉 {k!r}", "可用字段: " + ", ".join(sorted(allowed))])

    if not isinstance(spec, dict):
        E("spec/not-object", "规格必须是 JSON 对象",
          fixes=["照 references/schematic-figures.md 的示例改写"])
        return None, issues
    unknown(spec, _FLOW_KEYS, "规格")

    direction = spec.get("direction", "LR")
    if direction not in ("LR", "TB"):
        E("spec/bad-direction", f"direction 只能是 LR 或 TB,收到 {direction!r}",
          subject="direction", fixes=['"LR" 主线从左到右', '"TB" 主线从上到下'])
        direction = "LR"

    style = dict(FLOW_STYLE)
    st_in = spec.get("style") or {}
    if not isinstance(st_in, dict):
        E("spec/bad-value", "style 必须是对象", subject="style")
    else:
        unknown(st_in, set(FLOW_STYLE), "style")
        for k, v in st_in.items():
            if k in FLOW_STYLE:
                if _num(v) and v >= 0:
                    style[k] = float(v)
                else:
                    E("spec/bad-value", f"style.{k} 必须是非负数", subject=f"style.{k}")

    size = spec.get("size") or {}
    if not isinstance(size, dict):
        E("spec/bad-value", "size 必须是对象", subject="size")
        size = {}
    unknown(size, _SIZE_KEYS, "size")
    for k in _SIZE_KEYS & set(size):
        if not (_num(size[k]) and size[k] > 0):
            E("spec/bad-value", f"size.{k} 必须是正数(英寸)", subject=f"size.{k}")

    accents = {}
    acc_in = spec.get("accents") or {}
    if not isinstance(acc_in, dict):
        E("spec/bad-value", "accents 必须是对象", subject="accents")
        acc_in = {}
    for k, v in acc_in.items():
        if not (isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(c, str) for c in v)):
            E("spec/bad-accent", f"accents.{k} 要写成 [浅色填充, 深色描边]", subject=f"accents.{k}",
              fixes=['例如 "red": ["#FFFFFF", "#94070A"]'])
            continue
        try:
            for c in v:
                matplotlib.colors.to_rgb(c)
        except ValueError:
            E("spec/bad-accent", f"accents.{k} 里有无法识别的颜色 {v!r}", subject=f"accents.{k}")
            continue
        accents[k] = (v[0], v[1])
    palette = {k for k, v in S.items() if isinstance(v, tuple) and len(v) == 2} | set(accents)

    lanes, seen = [], set()
    lanes_in = spec.get("lanes")
    if lanes_in is not None:
        if not isinstance(lanes_in, list) or not lanes_in:
            E("spec/bad-lanes", "lanes 必须是非空数组", subject="lanes",
              fixes=["不需要泳道就删掉 lanes"])
        else:
            for i, ln in enumerate(lanes_in):
                if isinstance(ln, str):
                    ln = {"id": ln, "label": ln}
                if not isinstance(ln, dict) or not isinstance(ln.get("id"), str) or not ln["id"]:
                    E("spec/bad-lanes", f"lanes[{i}] 需要字符串 id", subject=f"lanes[{i}]")
                    continue
                unknown(ln, _LANE_KEYS, f"lanes[{i}]")
                if ln["id"] in seen:
                    E("spec/duplicate-id", f"泳道 id {ln['id']!r} 重复", subject=ln["id"])
                    continue
                seen.add(ln["id"])
                lanes.append({"id": ln["id"], "label": str(ln.get("label", ln["id"]))})
    named = bool(lanes)
    if not named:
        lanes = [{"id": None, "label": ""}]
    lane_index = {ln["id"]: i for i, ln in enumerate(lanes)}

    stages = spec.get("stages") or []
    if not isinstance(stages, list) or not all(isinstance(s, str) for s in stages):
        E("spec/bad-stages", "stages 必须是字符串数组(每列一个阶段名)", subject="stages")
        stages = []

    nodes_in = spec.get("nodes")
    if not isinstance(nodes_in, list) or not nodes_in:
        E("spec/no-nodes", "规格里没有节点", subject="nodes", fixes=["至少声明一个 nodes 项"])
        return None, issues
    nodes, ids = [], {}
    for i, n in enumerate(nodes_in):
        where = f"nodes[{i}]"
        if not isinstance(n, dict):
            E("spec/bad-node", f"{where} 必须是对象", subject=where)
            continue
        unknown(n, _NODE_KEYS, where)
        nid = n.get("id")
        if not isinstance(nid, str) or not nid:
            E("spec/missing-id", f"{where} 缺少字符串 id", subject=where)
            continue
        if nid in ids:
            E("spec/duplicate-id", f"节点 id {nid!r} 重复", subject=nid, fixes=["每个节点用唯一的 id"])
            continue
        label = n.get("label")
        if not isinstance(label, str) or not label.strip():
            E("spec/missing-label", f"节点 {nid!r} 缺少 label", subject=nid)
            continue
        col = n.get("col")
        if not isinstance(col, int) or isinstance(col, bool) or col < 0:
            E("spec/bad-col", f"节点 {nid!r} 的 col 必须是 ≥0 的整数", subject=nid,
              fixes=["col 从 0 开始,沿主线推进方向递增"])
            continue
        lane = n.get("lane")
        if named and lane not in lane_index:
            E("spec/unknown-lane", f"节点 {nid!r} 的 lane {lane!r} 没有在 lanes 里声明", subject=nid,
              fixes=["lane 写成 lanes 里已有的 id",
                     "可用泳道: " + ", ".join(ln["id"] for ln in lanes)])
            continue
        if not named and lane is not None:
            E("spec/unknown-lane", f"节点 {nid!r} 写了 lane,但规格没有声明 lanes", subject=nid,
              fixes=["在 lanes 里声明泳道", "删掉这个 lane"])
            continue
        accent = n.get("accent", "slate")
        if accent not in palette:
            E("spec/unknown-accent", f"节点 {nid!r} 的强调色 {accent!r} 不存在", subject=nid,
              fixes=["可用强调色: " + ", ".join(sorted(palette)),
                     "或在 accents 里自定义 [浅色填充, 深色描边]"])
            accent = "slate"
        tone = n.get("tone", "normal")
        if tone not in ("normal", "emphasis"):
            E("spec/bad-value", f"节点 {nid!r} 的 tone 只能是 normal 或 emphasis", subject=nid)
            tone = "normal"
        sub = n.get("sub")
        if sub is not None and not isinstance(sub, str):
            E("spec/bad-value", f"节点 {nid!r} 的 sub 必须是字符串", subject=nid)
            sub = None
        max_w = n.get("max_w", style["node_max_w"])
        if not (_num(max_w) and max_w > 0):
            E("spec/bad-value", f"节点 {nid!r} 的 max_w 必须是正数(英寸)", subject=nid)
            max_w = style["node_max_w"]
        node = dict(id=nid, label=label.strip(), sub=sub.strip() if sub else None,
                    lane=lane_index.get(lane, 0), col=col, accent=accent, tone=tone,
                    max_w=float(max_w))
        ids[nid] = node
        nodes.append(node)

    cells = {}
    for n in nodes:
        key = (n["lane"], n["col"])
        if key in cells:
            E("spec/grid-collision",
              f"节点 {n['id']!r} 与 {cells[key]['id']!r} 放在了同一格(泳道 {n['lane']},列 {n['col']})",
              subject=[cells[key]["id"], n["id"]], fixes=["换一列", "放进另一条泳道"])
        else:
            cells[key] = n

    edges, pairs = [], set()
    edges_in = spec.get("edges") or []
    if not isinstance(edges_in, list):
        E("spec/bad-edges", "edges 必须是数组", subject="edges")
        edges_in = []
    for i, e in enumerate(edges_in):
        where = f"edges[{i}]"
        if not isinstance(e, dict):
            E("spec/bad-edge", f"{where} 必须是对象", subject=where)
            continue
        unknown(e, _EDGE_KEYS, where)
        a, b = e.get("from"), e.get("to")
        missing = [x for x in (a, b) if x not in ids]
        if missing:
            E("spec/unknown-node", f"{where} 连到了不存在的节点 {missing}", subject=where,
              fixes=["from/to 写成 nodes 里已有的 id"])
            continue
        if a == b:
            E("spec/self-loop", f"{where} 从 {a!r} 连回自身", subject=where,
              fixes=["删掉自环;重复步骤用一条回到前序节点的反馈连线表达"])
            continue
        if (a, b) in pairs:
            E("spec/duplicate-edge", f"{a!r}→{b!r} 重复连线,已忽略后一条", subject=where,
              severity="warning", fixes=["合并成一条,把两个标签并成一句"])
            continue
        pairs.add((a, b))
        label = e.get("label")
        if label is not None and not isinstance(label, str):
            E("spec/bad-value", f"{where} 的 label 必须是字符串", subject=where)
            label = None
        accent = e.get("accent", "spine")
        if accent != "spine" and accent not in palette:
            E("spec/unknown-accent", f"{where} 的强调色 {accent!r} 不存在", subject=where,
              fixes=["可用: spine, " + ", ".join(sorted(palette))])
            accent = "spine"
        line = e.get("style", "solid")
        if line not in ("solid", "dashed"):
            E("spec/bad-value", f"{where} 的 style 只能是 solid 或 dashed", subject=where)
            line = "solid"
        edges.append(dict(idx=len(edges), src=ids[a], dst=ids[b], label=(label or "").strip(),
                          accent=accent, dashed=line == "dashed", name=f"{a}→{b}"))

    emph = [n["id"] for n in nodes if n["tone"] == "emphasis"]
    if len(emph) > 2:
        E("flow/too-many-emphasis", f"重心节点有 {len(emph)} 个(建议 ≤ 2)", subject=emph,
          severity="warning", fixes=["只保留全图重心,其余改回 normal"])
    ncols = max((n["col"] for n in nodes), default=0) + 1
    if stages and len(stages) != ncols:
        E("flow/stage-mismatch", f"stages 有 {len(stages)} 个,但节点用到了 {ncols} 列",
          subject="stages", severity="warning", fixes=["每一列写一个阶段名", "删掉 stages"])
    norm = dict(direction=direction, lanes=lanes, named=named, stages=stages[:ncols],
                nodes=nodes, edges=edges, style=style, accents=accents, size=size, ncols=ncols)
    return norm, issues


class _Measurer:
    """在一张临时画布上实测文字尺寸(英寸)。字体取当前 rcParams,须与出图一致。"""

    def __init__(self):
        self.fig = plt.figure(figsize=(10, 10), dpi=100)
        self.r = _renderer(self.fig)

    def size(self, text, fontsize, weight=600):
        t = self.fig.text(0, 0, text, fontsize=fontsize, weight=weight, linespacing=1.25)
        b = t.get_window_extent(self.r)
        t.remove()
        return b.width / self.fig.dpi, b.height / self.fig.dpi

    def close(self):
        plt.close(self.fig)


def _wrap(meas, text, fontsize, max_w, weight=600):
    """按实测宽度换行:中文逐字可断,拉丁词整体不拆,行首不留标点。不缩字号。
    行数定下来之后再收窄宽度重排,让各行长度均衡,避免"……位\n点"这种末行只剩一个字。"""
    lines = _wrap_greedy(meas, text, fontsize, max_w, weight)
    n = lines.count("\n")
    if n == 0:
        return lines
    w = max_w
    while w > 0.3 * max_w:
        trial = _wrap_greedy(meas, text, fontsize, w * 0.94, weight)
        if trial.count("\n") != n:
            break
        w, lines = w * 0.94, trial
    return lines


def _wrap_greedy(meas, text, fontsize, max_w, weight=600):
    out = []
    for line in text.split("\n"):
        if meas.size(line, fontsize, weight)[0] <= max_w:
            out.append(line)
            continue
        cur = ""
        for tk in re.findall(r"[A-Za-z0-9_.+\-/%°μ×()\[\]^]+\s*|\s+|.", line):
            cand = cur + tk
            if cur.strip() and tk[0] not in _NO_BREAK and meas.size(cand.rstrip(), fontsize, weight)[0] > max_w:
                out.append(cur.rstrip())
                cur = tk.lstrip()
            else:
                cur = cand
        if cur.strip():
            out.append(cur.rstrip())
    return "\n".join(out)


def _simplify(pts, tol=1e-9):
    out = []
    for p in pts:
        if out and abs(p[0] - out[-1][0]) < tol and abs(p[1] - out[-1][1]) < tol:
            continue
        out.append(p)
    i = 1
    while i < len(out) - 1:
        (x0, y0), (x1, y1), (x2, y2) = out[i - 1], out[i], out[i + 1]
        if (abs(x0 - x1) < tol and abs(x1 - x2) < tol) or (abs(y0 - y1) < tol and abs(y1 - y2) < tol):
            out.pop(i)
        else:
            i += 1
    return out


def _flow_geometry(norm, meas):
    """在抽象坐标里排版。m 沿主线推进方向(列),k 沿泳道方向;LR 时 m=x、k 自上而下,
    TB 时 m 自上而下、k=x。返回节点/连线/底带/表头的英寸坐标与布线诊断。"""
    st, nodes, edges = norm["style"], norm["nodes"], norm["edges"]
    LR, L, C = norm["direction"] == "LR", len(norm["lanes"]), norm["ncols"]
    issues = []

    def hw(w, h):              # 实测 (宽, 高) → (主线方向, 泳道方向) 尺寸
        return (w, h) if LR else (h, w)

    for n in nodes:
        text = _wrap(meas, n["label"], st["font"], n["max_w"])
        if n["sub"]:
            text += "\n" + _wrap(meas, n["sub"], st["font"], n["max_w"])
        n["text"] = text
        w, h = meas.size(text, st["font"])
        n["m_ext"], n["k_ext"] = hw(w + 2 * st["pad"] + 0.02, h + 2 * st["pad"] + 0.02)

    col_ext, lane_ext = [0.6] * C, [0.4] * L
    for n in nodes:
        col_ext[n["col"]] = max(col_ext[n["col"]], n["m_ext"])
        lane_ext[n["lane"]] = max(lane_ext[n["lane"]], n["k_ext"])
    stage_sz = [hw(*meas.size(s, st["header_font"], 700)) for s in norm["stages"]]
    for c, (sm, _) in enumerate(stage_sz):
        col_ext[c] = max(col_ext[c], sm)
    header_k = max((sk for _, sk in stage_sz), default=0.0)
    header_k = header_k + 0.18 if stage_sz else 0.0
    lane_sz = [hw(*meas.size(ln["label"], st["header_font"], 700)) if norm["named"] else (0.0, 0.0)
               for ln in norm["lanes"]]
    for l, (_, lk) in enumerate(lane_sz):
        lane_ext[l] = max(lane_ext[l], lk)
    lane_m = max((lm for lm, _ in lane_sz), default=0.0)
    lane_m = lane_m + 0.3 if norm["named"] else 0.0

    for e in edges:
        if e["label"]:
            e["lab_m"], e["lab_k"] = hw(*meas.size(e["label"], st["label_font"], 500))
        else:
            e["lab_m"] = e["lab_k"] = 0.0

    occ = {(n["lane"], n["col"]) for n in nodes}

    def lane_blocked(l, c0, c1):
        return any((l, c) in occ for c in range(min(c0, c1) + 1, max(c0, c1)))

    def col_blocked(c, l0, l1):
        return any((l, c) in occ for l in range(min(l0, l1) + 1, max(l0, l1)))

    # ---- 1. 布线拓扑:只依赖网格序号,不依赖坐标
    for e in edges:
        u, v = e["src"], e["dst"]
        lu, cu, lv, cv = u["lane"], u["col"], v["lane"], v["col"]
        if cv > cu:
            if lu == lv and lane_blocked(lu, cu, cv):
                p = dict(kind="U", sides=("hi", "hi"), h=lu + 1, host=("h", lu + 1))
            elif lu == lv or not lane_blocked(lu, cu, cv):
                p = dict(kind="Z", sides=("out", "in"), g=cv, host=("g", cv) if cv == cu + 1 else ("first",))
            elif not lane_blocked(lv, cu, cv):
                p = dict(kind="Z", sides=("out", "in"), g=cu + 1, host=("g", cu + 1))
            else:
                h = lu + 1 if lv > lu else lu
                p = dict(kind="S", sides=("out", "in"), g=cu + 1, h=h, g2=cv, host=("h", h))
        elif cv == cu:
            hi = lv > lu
            if not col_blocked(cu, lu, lv):
                h = lu + 1 if hi else lu
                p = dict(kind="V", sides=("hi", "lo") if hi else ("lo", "hi"), h=h, host=("h", h))
            else:
                p = dict(kind="Z", sides=("out", "out"), g=cu + 1, host=("g", cu + 1))
        elif lu == lv:
            p = dict(kind="U", sides=("hi", "hi"), h=lu + 1, host=("h", lu + 1))
        else:
            hi = lv > lu
            h = lu + 1 if hi else lu
            p = dict(kind="B", sides=("hi" if hi else "lo", "in"), h=h, g=cv, host=("h", h))
        e["plan"] = p

    # ---- 2. 端口:同一条框边上的端口按对端位置排序后等距错开
    groups = defaultdict(list)
    for e in edges:
        u, v = e["src"], e["dst"]
        for end, (node, other, side) in enumerate(((u, v, e["plan"]["sides"][0]),
                                                  (v, u, e["plan"]["sides"][1]))):
            key = (other["lane"], other["col"]) if side in ("out", "in") else (other["col"], other["lane"])
            groups[(node["id"], side)].append((key, e["idx"], e, end))
    for items in groups.values():
        items.sort(key=lambda t: (t[0], t[1]))
        for i, (_, _, e, end) in enumerate(items):
            e.setdefault("frac", [0.5, 0.5])[end] = (i + 1) / (len(items) + 1)
    # 对齐:同泳道相邻直连、同列上下直连,若只有一端被错开,另一端(独占框边)跟着对齐,
    # 线就是直的,不会多出一个小折角
    for e in edges:
        p = e["plan"]
        straightish = p["kind"] == "V" or (p["kind"] == "Z" and p["sides"] == ("out", "in")
                                           and e["src"]["lane"] == e["dst"]["lane"])
        if not straightish:
            continue
        n0 = len(groups[(e["src"]["id"], p["sides"][0])])
        n1 = len(groups[(e["dst"]["id"], p["sides"][1])])
        if n0 == 1 and n1 > 1:
            e["frac"][0] = e["frac"][1]
        elif n1 == 1 and n0 > 1:
            e["frac"][1] = e["frac"][0]

    # ---- 3. 通道占用:每条经过间隙的连线占一条独立轨道
    usage = defaultdict(list)
    for e in edges:
        p, fr = e["plan"], e["frac"]
        same = abs(fr[0] - fr[1]) < 1e-9
        if p["kind"] == "Z":
            if p["sides"] == ("out", "in") and e["src"]["lane"] == e["dst"]["lane"] and same:
                p["straight"] = True
            else:
                usage[("g", p["g"])].append(e)
        elif p["kind"] == "V":
            if same:
                p["straight"] = True
            else:
                usage[("h", p["h"])].append(e)
        elif p["kind"] == "U":
            usage[("h", p["h"])].append(e)
        elif p["kind"] == "B":
            usage[("h", p["h"])].append(e)
            usage[("g", p["g"])].append(e)
        else:
            usage[("g", p["g"])].append(e)
            usage[("h", p["h"])].append(e)
            usage[("g", p["g2"])].append(e)
    for ch, users in usage.items():
        for i, e in enumerate(users):
            e.setdefault("track", {})[ch] = i

    # ---- 4. 间隙尺寸:放得下标签 + 轨道 + 箭头头部
    tr = st["track"]
    label_g, label_h, vlabel_h = defaultdict(float), defaultdict(float), defaultdict(float)
    for e in edges:
        host = e["plan"]["host"]
        if e["label"] and e["plan"]["kind"] == "V":
            vlabel_h[host[1]] = max(vlabel_h[host[1]], e["lab_k"])   # 线旁标签单独占一条带
        elif e["label"] and host[0] == "g":
            label_g[host[1]] = max(label_g[host[1]], e["lab_m"])
        elif e["label"] and host[0] == "h":
            label_h[host[1]] = max(label_h[host[1]], e["lab_k"])
    g_lead, g_size = [], []
    for g in range(C + 1):
        n = len(usage[("g", g)])
        lead = max(label_g[g] + 0.2 if label_g[g] else 0.0, 0.18 if n else 0.0)
        need = lead + n * tr + (_HEAD_IN if (n or label_g[g]) else 0.0)
        base = st["col_gap"] if 0 < g < C else 0.12
        g_lead.append(lead)
        g_size.append(max(base, need))
    bp = 0.07 if norm["named"] else 0.0
    h_slot, h_size, h_band = [], [], []
    for h in range(L + 1):
        n = len(usage[("h", h)])
        slot = max(tr, label_h[h] + 0.08 if label_h[h] else 0.0)
        band = vlabel_h[h] + 0.12 if vlabel_h[h] else 0.0     # 放在轨道之前,标签不会压到轨道
        pads = (2 if 0 < h < L else 1) * bp
        need = pads + band + (n * slot + 0.08 if n else 0.0)
        base = st["lane_gap"] if 0 < h < L else 0.1
        h_slot.append(slot)
        h_band.append(band)
        h_size.append(max(base, need))

    # ---- 5. 坐标
    M0 = st["margin"]
    m = M0 + lane_m
    g_start, col_start = [], []
    for c in range(C):
        g_start.append(m)
        m += g_size[c]
        col_start.append(m)
        m += col_ext[c]
    g_start.append(m)
    total_m = m + g_size[C] + M0
    k = M0 + header_k
    h_start, lane_start = [], []
    for l in range(L):
        h_start.append(k)
        k += h_size[l]
        lane_start.append(k)
        k += lane_ext[l]
    h_start.append(k)
    total_k = k + h_size[L] + M0

    def Tg(g, i):
        return g_start[g] + g_lead[g] + (i + 0.5) * tr

    def Th(h, i):
        return h_start[h] + (bp if h > 0 else 0.0) + h_band[h] + 0.04 + (i + 0.5) * h_slot[h]

    def rect(n):
        m0, k0 = col_start[n["col"]], lane_start[n["lane"]]
        return m0, k0, m0 + col_ext[n["col"]], k0 + lane_ext[n["lane"]]

    def port(n, side, frac):
        m0, k0, m1, k1 = rect(n)
        return {"out": (m1 + _EPS, k0 + frac * (k1 - k0)), "in": (m0 - _EPS, k0 + frac * (k1 - k0)),
                "lo": (m0 + frac * (m1 - m0), k0 - _EPS), "hi": (m0 + frac * (m1 - m0), k1 + _EPS)}[side]

    for e in edges:
        p, tk = e["plan"], e.get("track", {})
        a = port(e["src"], p["sides"][0], e["frac"][0])
        b = port(e["dst"], p["sides"][1], e["frac"][1])
        if p.get("straight"):
            pts = [a, b]
        elif p["kind"] == "Z":
            x = Tg(p["g"], tk[("g", p["g"])])
            pts = [a, (x, a[1]), (x, b[1]), b]
        elif p["kind"] in ("U", "V"):
            y = Th(p["h"], tk[("h", p["h"])])
            pts = [a, (a[0], y), (b[0], y), b]
        elif p["kind"] == "B":
            y, x = Th(p["h"], tk[("h", p["h"])]), Tg(p["g"], tk[("g", p["g"])])
            pts = [a, (a[0], y), (x, y), (x, b[1]), b]
        else:
            y = Th(p["h"], tk[("h", p["h"])])
            x1, x2 = Tg(p["g"], tk[("g", p["g"])]), Tg(p["g2"], tk[("g", p["g2"])])
            pts = [a, (x1, a[1]), (x1, y), (x2, y), (x2, b[1]), b]
        e["pts"] = _simplify(pts)

    # ---- 6. 连线之间:共用通道(错误)与交叉(提示)
    def segs(e):
        return list(zip(e["pts"][:-1], e["pts"][1:]))

    def along_m(s):
        return abs(s[0][1] - s[1][1]) < 1e-9

    crossings = defaultdict(int)
    for i, e1 in enumerate(edges):
        for e2 in edges[i + 1:]:
            for s1 in segs(e1):
                for s2 in segs(e2):
                    h1, h2 = along_m(s1), along_m(s2)
                    if h1 == h2:
                        ax = 1 if h1 else 0          # 固定坐标轴
                        if abs(s1[0][ax] - s2[0][ax]) >= 0.03:
                            continue
                        lo = max(min(s1[0][1 - ax], s1[1][1 - ax]), min(s2[0][1 - ax], s2[1][1 - ax]))
                        hi = min(max(s1[0][1 - ax], s1[1][1 - ax]), max(s2[0][1 - ax], s2[1][1 - ax]))
                        if hi - lo > 0.06:
                            issues.append(Issue(
                                "edge/shared-corridor", f"连线 {e1['name']} 与 {e2['name']} 叠在同一段通道上",
                                subject=[e1["name"], e2["name"]], evidence={"overlap_in": round(hi - lo, 2)},
                                fixes=["加大 style.track", "调整节点的列或泳道,减少共用通道", "删掉低价值的连线"]))
                    else:
                        hs, vs = (s1, s2) if h1 else (s2, s1)
                        y, x = hs[0][1], vs[0][0]
                        xs, ys = sorted((hs[0][0], hs[1][0])), sorted((vs[0][1], vs[1][1]))
                        if xs[0] + 0.02 < x < xs[1] - 0.02 and ys[0] + 0.02 < y < ys[1] - 0.02:
                            crossings[(e1["name"], e2["name"])] += 1
    for (n1, n2), cnt in crossings.items():
        issues.append(Issue(
            "edge/crossing", f"连线 {n1} 与 {n2} 交叉 {cnt} 处", subject=[n1, n2], severity="warning",
            evidence={"count": cnt},
            fixes=["交换相关节点所在泳道的上下顺序", "让支路从主线上最近的节点出发", "删掉低价值的连线"]))

    # ---- 7. 标签:挑不与其它连线、节点相交的位置
    boxes = [rect(n) for n in nodes]

    def blocked(cm, ck, e):
        hm, hk = e["lab_m"] / 2 + 0.03, e["lab_k"] / 2 + 0.02
        r0 = (cm - hm, ck - hk, cm + hm, ck + hk)
        for other in edges:
            if other is e:
                continue
            for (x0, y0), (x1, y1) in segs(other):
                if (max(x0, x1) >= r0[0] and min(x0, x1) <= r0[2]
                        and max(y0, y1) >= r0[1] and min(y0, y1) <= r0[3]):
                    return True
        return any(bx[0] < r0[2] and bx[2] > r0[0] and bx[1] < r0[3] and bx[3] > r0[1] for bx in boxes)

    def seg_len(s):
        return math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1])

    for e in edges:
        if not e["label"]:
            continue
        ss = segs(e)
        host = e["plan"]["host"]
        if e["plan"]["kind"] == "V":
            # 同列上下的连线是跨泳道的短线,标签压在线上放不下,改放在线旁:
            # 泳道间隙里给它留了一条带(在轨道之前),沿主线方向偏开半个标签宽,两侧都试
            h = host[1]
            mk = h_start[h] + (bp if h > 0 else 0.0) + 0.06 + e["lab_k"] / 2
            cover = [s for s in ss if not along_m(s)
                     and min(s[0][1], s[1][1]) - 1e-9 <= mk <= max(s[0][1], s[1][1]) + 1e-9]
            seg = cover[0] if cover else max(ss, key=seg_len)
            # 优先:不压线且不出画布 > 不压线但伸出画布(下面加宽画布兜住) > 压线
            opts = []
            for side in (1, -1):
                cm = seg[0][0] + side * (e["lab_m"] / 2 + 0.08)
                outside = cm - e["lab_m"] / 2 < 0.04 or cm + e["lab_m"] / 2 > total_m - 0.04
                opts.append((blocked(cm, mk, e), outside, cm))
            _, _, cm = min(opts, key=lambda o: (o[0], o[1]))
            e["label_at"] = (cm, mk)
            continue
        main = [s for s in ss if along_m(s) and abs(s[0][0] - s[1][0]) > 1e-9]
        if host[0] in ("g", "first"):
            cand = [ss[0]] if ss[0] in main else main
        else:
            h = host[1]
            lo, hi = h_start[h], h_start[h] + h_size[h]
            cand = [s for s in main if lo <= s[0][1] <= hi] or ss
        seg = max(cand or ss, key=lambda s: math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]))
        length = math.hypot(seg[1][0] - seg[0][0], seg[1][1] - seg[0][1])
        need = (e["lab_m"] if along_m(seg) else e["lab_k"]) + 0.1
        if length < need:
            issues.append(Issue(
                "edge/label-no-room", f"连线 {e['name']} 的标签 {e['label']!r} 放不进所在线段",
                subject=e["name"], evidence={"label_in": round(need, 2), "segment_in": round(length, 2)},
                fixes=["加大 style.col_gap 或 style.lane_gap", "调整节点让这条连线变长",
                       "精简措辞——保留动作、物理量和条件"]))
        spots = [0.5, 0.35, 0.65, 0.25, 0.75]
        at = None
        for t in spots:
            cm = seg[0][0] + (seg[1][0] - seg[0][0]) * t
            ck = seg[0][1] + (seg[1][1] - seg[0][1]) * t
            if not blocked(cm, ck, e):
                at = (cm, ck)
                break
        e["label_at"] = at or ((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2)

    # 靠画布末端的线旁标签可能伸出去:把画布加宽到兜得住(只延长末端,不挪动已排好的坐标)
    reach = max((e["label_at"][0] + e["lab_m"] / 2 for e in edges if e.get("label_at")), default=0.0)
    total_m = max(total_m, reach + 0.08)

    return dict(LR=LR, col_start=col_start, col_ext=col_ext, lane_start=lane_start, lane_ext=lane_ext,
                lane_m=lane_m, header_k=header_k, bp=bp, total_m=total_m, total_k=total_k,
                issues=issues)


def _polyline_arrow(fig, pts, color, lw=1.5, dashed=False, zorder=2, ignore=(), label="",
                    own_texts=()):
    """正交折线箭头(figure 坐标点列)。登记进箭头档案,体检会逐段采样复查。"""
    from matplotlib.lines import Line2D
    from matplotlib.path import Path
    scale = 10.0
    if dashed:
        xs, ys = zip(*pts)
        fig.add_artist(Line2D(xs, ys, transform=fig.transFigure, color=color, lw=lw,
                              ls=(0, (4, 3)), zorder=zorder, solid_joinstyle="miter"))
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        d = np.hypot(*(fig.transFigure.transform((x1, y1)) - fig.transFigure.transform((x0, y0))))
        back = min(1.0, 0.14 * fig.dpi / max(d, 1e-9))
        fig.add_artist(FancyArrowPatch((x1 - (x1 - x0) * back, y1 - (y1 - y0) * back), (x1, y1),
                                       transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=scale, lw=lw, color=color,
                                       shrinkA=0, shrinkB=0, zorder=zorder))
    else:
        path = Path(pts, [Path.MOVETO] + [Path.LINETO] * (len(pts) - 1))
        fig.add_artist(FancyArrowPatch(path=path, transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=scale, lw=lw, color=color, shrinkA=0,
                                       shrinkB=0, zorder=zorder, joinstyle="miter"))
    disp = fig.transFigure.transform(pts)
    length_pt = float(sum(np.hypot(*(b - a)) for a, b in zip(disp[:-1], disp[1:]))) / fig.dpi * 72.0
    if hasattr(fig, "_schem_arrows"):
        fig._schem_arrows.append(dict(p1=tuple(pts[0]), p2=tuple(pts[-1]), rad=0.0,
                                      points=[tuple(p) for p in pts], label=label,
                                      ignore={id(e) for e in ignore}, d_pt=length_pt,
                                      own_texts={id(t) for t in own_texts}))


def _ink_for(fill):
    """实心填充上的文字色:按填充亮度选白字或深色字,深色风格里自定义强调色也不会糊。"""
    r, g, b = matplotlib.colors.to_rgb(fill)
    return "#FFFFFF" if 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.55 else "#0F172A"


def flowchart(spec, style="paper", fonts=True):
    """声明式流程图 / 技术路线图:规格(dict 或 JSON 文件读出的对象)→ 排版 → 画布。

    返回 ``(fig, info)``:``info["nodes"]`` 是 id → El(可以继续往上叠加 badge 等),
    ``info["issues"]`` 是排版阶段的诊断,``info["size_in"]`` 是画布英寸尺寸。
    规格有 error 级问题时抛 ``FlowSpecError``(``.issues`` 里是结构化诊断)。
    出图照常走 ``sf.export``:体检会把布线诊断与文字、箭头检查合在一起。"""
    if isinstance(style, str):
        if style not in STYLES:
            raise FlowSpecError([Issue("spec/unknown-style", f"没有风格 {style!r}", subject=style,
                                       fixes=["可用: " + ", ".join(STYLES)])])
        S = STYLES[style]
    else:
        S = style
    if fonts:
        setup_fonts()
    norm, issues = validate_flow(spec, S)
    if norm is None or any(i.severity == "error" for i in issues):
        raise FlowSpecError(issues)
    S2 = dict(S)
    S2.update(norm["accents"])
    for key, val in list(S2.items()):
        if isinstance(val, tuple) and len(val) == 2:
            S2[f"{key}__solid"] = (val[1], val[1])
    st = norm["style"]
    meas = _Measurer()
    try:
        geo = _flow_geometry(norm, meas)
    finally:
        meas.close()
    issues += geo["issues"]
    LR = geo["LR"]
    W, H = (geo["total_m"], geo["total_k"]) if LR else (geo["total_k"], geo["total_m"])
    size = norm["size"]
    over = {k: round(v, 2) for k, v, lim in (("width_in", W, size.get("max_width")),
                                             ("height_in", H, size.get("max_height")))
            if lim and v > lim + 1e-6}
    if over:
        issues.append(Issue(
            "flow/too-large", f"排版需要 {W:.2f}×{H:.2f} in,超出 size 限制", subject="size",
            evidence={"needed": over, "limit": {k: size[k] for k in _SIZE_KEYS & set(size)}},
            fixes=["减小 style.node_max_w,让节点文字换行", "减小 style.col_gap / lane_gap",
                   "减小 style.font", "把一条长主线拆成两行泳道"]))

    fig = canvas(W, H, S2)

    def P(m, k):
        x, y = (m, k) if LR else (k, m)
        return x / W, 1.0 - y / H

    def frac_rect(m0, k0, m1, k1):
        (xa, ya), (xb, yb) = P(m0, k0), P(m1, k1)
        return min(xa, xb), min(ya, yb), abs(xb - xa), abs(yb - ya)

    M0, cs, ce, ls_, le = st["margin"], geo["col_start"], geo["col_ext"], geo["lane_start"], geo["lane_ext"]
    if norm["named"]:
        for l, ln in enumerate(norm["lanes"]):
            x, y, w, h = frac_rect(M0, ls_[l] - geo["bp"], geo["total_m"] - M0, ls_[l] + le[l] + geo["bp"])
            rbox(fig, x, y, w, h, S2["band"], S2["band_ec"], lw=1.0, rs=st["corner"] / W, zorder=1,
                 solid=False, label=f"lane:{ln['id']}")
            if LR:
                fig.text(*P(M0 + 0.14, ls_[l] + le[l] / 2), ln["label"], ha="left", va="center",
                         fontsize=st["header_font"], weight=700, color=S2["sub"], zorder=3)
            else:
                fig.text(*P(M0 + geo["lane_m"] / 2, ls_[l] + le[l] / 2), ln["label"], ha="center",
                         va="center", fontsize=st["header_font"], weight=700, color=S2["sub"], zorder=3)
    for c, label in enumerate(norm["stages"]):
        fig.text(*P(cs[c] + ce[c] / 2, M0 + geo["header_k"] / 2), label, ha="center", va="center",
                 fontsize=st["header_font"], weight=700, color=S2["txt"], zorder=3)

    els = {}
    for n in norm["nodes"]:
        m0, k0 = cs[n["col"]], ls_[n["lane"]]
        m1, k1 = m0 + ce[n["col"]], k0 + le[n["lane"]]
        x, y, w, h = frac_rect(m0, k0, m1, k1)
        emph = n["tone"] == "emphasis"
        els[n["id"]] = text_box(
            fig, x + w / 2, y + h / 2, n["text"], S2,
            accent=f"{n['accent']}__solid" if emph else n["accent"],
            fontsize=st["font"], pad=st["pad"] / W, min_w=w, min_h=h, lw=st["node_lw"],
            rs=st["corner"] / W, color=_ink_for(S2[f"{n['accent']}__solid"][0]) if emph else None,
            label=n["id"])

    for e in norm["edges"]:
        own = []
        if e["label"]:
            own.append(fig.text(*P(*e["label_at"]), e["label"], ha="center", va="center",
                                fontsize=st["label_font"], weight=500, color=S2["sub"], zorder=6,
                                bbox=dict(boxstyle="square,pad=0.15", fc=S2["bg"], ec="none")))
        color = S2["spine"] if e["accent"] == "spine" else S2[e["accent"]][1]
        _polyline_arrow(fig, [P(*p) for p in e["pts"]], color, lw=st["edge_lw"], dashed=e["dashed"],
                        ignore=(els[e["src"]["id"]], els[e["dst"]["id"]]), label=e["name"],
                        own_texts=own)

    fig._schem_flow_issues = issues
    return fig, dict(nodes=els, issues=issues, size_in=(W, H), direction=norm["direction"])


# ================================================================ 命令行

def _collect_issues(fig):
    try:
        import paperfig as pf
        return sort_issues(pf.check_layout(fig))
    except ImportError:
        return sort_issues(check(fig))


def _emit(receipt, as_json, code):
    if as_json:
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return code
    for rec in receipt.get("styles", []):
        mark = "通过" if rec["errors"] == 0 else "未通过"
        print(f"[{rec['style']}] {mark}:{rec['size_in'][0]}×{rec['size_in'][1]} in,"
              f"{rec['errors']} error,{rec['warnings']} warning")
        for out in rec.get("outputs", []):
            print(f"  输出 {out}")
    for item in receipt.get("issues", []):
        fixes = item.get("fixes") or []
        print(f"[{item['severity']} {item['code']}] {item['message']}"
              + ("\n    修法: " + " / ".join(fixes) if fixes else ""))
    for rec in receipt.get("styles", []):
        for item in rec.get("issues", []):
            fixes = item.get("fixes") or []
            print(f"  [{item['severity']} {item['code']}] {item['message']}"
                  + ("\n      修法: " + " / ".join(fixes) if fixes else ""))
    if code:
        print(receipt.get("repair_rules", REPAIR_RULES))
    return code


def _main(argv=None):
    import argparse
    import contextlib
    ap = argparse.ArgumentParser(prog="schemfig.py", description="schemfig 命令行")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("flow", help="声明式流程图/技术路线图:规格 JSON → 排版 → 体检 → 出图")
    f.add_argument("spec", help="规格 JSON 文件")
    f.add_argument("-o", "--out", help="输出路径前缀(不含扩展名);--style all 时追加 -paper/-dark")
    f.add_argument("--style", default="paper", choices=[*STYLES, "all"])
    f.add_argument("--formats", default="png,pdf", help="逗号分隔,如 png,pdf,svg")
    f.add_argument("--dpi", type=int, default=300)
    f.add_argument("--check", action="store_true", help="只排版和体检,不写图")
    f.add_argument("--json", action="store_true", help="输出机器可读的回执")
    f.add_argument("--no-crops", action="store_true", help="不生成局部放大块")
    args = ap.parse_args(argv)
    if not args.check and not args.out:
        ap.error("出图需要 -o/--out;只体检请加 --check")
    matplotlib.use("Agg")
    receipt = {"ok": False, "repair_rules": REPAIR_RULES}
    try:
        with open(args.spec, encoding="utf-8") as fh:
            spec = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        receipt["issues"] = [Issue("spec/unreadable", f"读不了规格文件: {exc}", subject=args.spec).to_dict()]
        return _emit(receipt, args.json, 2)
    styles = list(STYLES) if args.style == "all" else [args.style]
    code, receipt["styles"] = 0, []
    quiet = contextlib.redirect_stdout(sys.stderr) if args.json else contextlib.nullcontext()
    for name in styles:
        try:
            with quiet:
                fig, info = flowchart(spec, style=name)
        except FlowSpecError as exc:
            receipt["issues"] = [i.to_dict() for i in exc.issues]
            return _emit(receipt, args.json, 2)
        with quiet:
            issues = _collect_issues(fig)
        errors = [i for i in issues if i.severity == "error"]
        rec = dict(style=name, size_in=[round(v, 2) for v in info["size_in"]], errors=len(errors),
                   warnings=len(issues) - len(errors), issues=[i.to_dict() for i in issues], outputs=[])
        if not args.check:
            stem = args.out if len(styles) == 1 else f"{args.out}-{name}"
            os.makedirs(os.path.dirname(stem) or ".", exist_ok=True)
            with quiet:
                if errors:
                    write_report(stem, issues)
                    rec["report"] = f"{stem}.check.json"
                else:
                    rec["outputs"] = export(fig, stem, dpi=args.dpi,
                                            formats=tuple(x for x in args.formats.split(",") if x),
                                            crops=not args.no_crops)
        plt.close(fig)
        code = max(code, 1 if errors else 0)
        receipt["styles"].append(rec)
    receipt["ok"] = code == 0
    return _emit(receipt, args.json, code)


if __name__ == "__main__":
    sys.exit(_main())
