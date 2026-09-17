"""paperfig — 论文图统一样式与导出工具（materials/chemistry 顶刊标准）。

设计原则：按最终物理尺寸出图（figsize 直接等于期刊栏宽），投稿时无需缩放，
字号所见即所得。因此导出时不要用 bbox_inches="tight"（会改变最终宽度），
布局问题交给 constrained_layout 解决。

用法::

    import paperfig as pf

    pf.setup("nature")                          # 应用全局样式
    fig, ax = pf.figure(width="single", height_mm=60)
    ax.plot(x, y, color=pf.OKABE_ITO["blue"])
    ax.set_xlabel("Time (h)")
    ax.set_ylabel(r"H$_2$ evolved (mmol g$^{-1}$)")
    pf.export(fig, "fig2a_h2_evolution")        # -> .pdf + .png (600 dpi)

依赖：matplotlib、numpy。无其他依赖。
"""

from __future__ import annotations

import math
import string

import matplotlib as mpl
import matplotlib.pyplot as plt

MM_PER_IN = 25.4

# 各刊图片规格（单位 mm / pt）。详细出处与更多期刊见 references/journal-specs.md，
# 投稿前以期刊当期 author guidelines 为准。
JOURNALS = {
    "nature":   {"single": 89.0, "double": 183.0, "max_height": 247.0, "font": 6.0},
    "science":  {"single": 55.0, "double": 120.0, "full": 183.0, "font": 6.0},
    "acs":      {"single": 84.6, "double": 177.8, "font": 7.0},   # JACS, ACS Catal., Nano Lett. ...
    "wiley":    {"single": 85.0, "double": 175.0, "font": 7.0},   # Angew, AM, AFM, Small ...
    "elsevier": {"single": 90.0, "onehalf": 140.0, "double": 190.0, "font": 7.0},  # Appl. Catal. B ...
    "rsc":      {"single": 83.0, "double": 171.0, "font": 7.0},   # JMCA, EES, Chem. Sci. ...
}

# Okabe-Ito 色盲安全色板（论文分类配色首选）
OKABE_ITO = {
    "black":     "#000000",
    "orange":    "#E69F00",
    "skyblue":   "#56B4E9",
    "green":     "#009E73",
    "yellow":    "#F0E442",
    "blue":      "#0072B2",
    "vermilion": "#D55E00",
    "purple":    "#CC79A7",
}

# 多序列取色顺序（黄色在白底上太浅，排最后）
CYCLE = ["#0072B2", "#D55E00", "#009E73", "#E69F00", "#CC79A7", "#56B4E9", "#000000", "#F0E442"]

_current = {"journal": "nature"}


def mm2in(mm: float) -> float:
    return mm / MM_PER_IN


def setup(journal: str = "nature") -> None:
    """应用全局 rcParams。在任何绘图代码之前调用一次。"""
    j = JOURNALS[journal]
    f = j["font"]
    _current["journal"] = journal
    mpl.rcParams.update({
        # 字体：无衬线，嵌入 TrueType（Type 42），期刊制版必需
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "mathtext.fontset": "stixsans",       # 公式与正文字体协调
        # 字号：坐标轴标签 = 基准字号，刻度/图例略小
        "font.size": f,
        "axes.labelsize": f,
        "axes.titlesize": f,
        "xtick.labelsize": f - 0.5,
        "ytick.labelsize": f - 0.5,
        "legend.fontsize": f - 0.5,
        # 坐标框：全框 + 内刻度（材料/化学期刊主流样式）
        "axes.linewidth": 0.6,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.minor.size": 1.7,
        "ytick.minor.size": 1.7,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.minor.width": 0.5,
        "ytick.minor.width": 0.5,
        # 线与点
        "lines.linewidth": 1.0,
        "lines.markersize": 3.5,
        "axes.prop_cycle": mpl.cycler(color=CYCLE),
        # 图例：无边框
        "legend.frameon": False,
        "legend.handlelength": 1.4,
        "legend.borderaxespad": 0.3,
        # 预览与导出
        "figure.dpi": 150,
        "savefig.dpi": 600,
    })


def figure(width="single", height_mm: float | None = None, journal: str | None = None, **kw):
    """按期刊栏宽建图。width 可为 'single'/'double' 等键名，或 mm 数值。

    height_mm 缺省取宽度的 0.75（单栏方图习惯）；组图请显式给高度。
    其余关键字参数透传给 plt.subplots（如 nrows、ncols）。
    """
    j = JOURNALS[journal or _current["journal"]]
    w_mm = j[width] if isinstance(width, str) else float(width)
    h_mm = height_mm if height_mm is not None else w_mm * 0.75
    kw.setdefault("layout", "constrained")
    return plt.subplots(figsize=(mm2in(w_mm), mm2in(h_mm)), **kw)


def panel_labels(axes, upper: bool = False, fontsize: float = 8,
                 dx_pt: float = -14.0, dy_pt: float = 4.0) -> None:
    """给组图加 panel 标号（axes 左上角外侧）。Nature 系用小写粗体 a b c（默认）；
    Science/ACS 用大写 A B C（upper=True）。dx_pt/dy_pt 为相对 axes 左上角的
    偏移（单位 pt），压到刻度数字或 y 轴标签上时微调。

    实现上必须用 annotate 挂在 axes 角点上（渲染时才结算位置），
    不能用 fig.text + get_position()：constrained_layout 在 draw 之前
    还没定稿 axes 位置，会把标号放错地方。
    """
    letters = string.ascii_uppercase if upper else string.ascii_lowercase
    for ax, letter in zip(axes.flat if hasattr(axes, "flat") else axes, letters):
        ax.annotate(letter, xy=(0, 1), xycoords="axes fraction",
                    xytext=(dx_pt, dy_pt), textcoords="offset points",
                    fontsize=fontsize, fontweight="bold",
                    ha="right", va="bottom", annotation_clip=False)


def mosaic(layout, width="double", height_mm: float | None = None,
           journal: str | None = None, **kw):
    """按期刊栏宽建组图(subplot_mosaic 版)。layout 如 [["a","b"],["c","d"]]。
    组图默认高度取宽度的 0.66,复杂布局请显式给 height_mm。"""
    j = JOURNALS[journal or _current["journal"]]
    w_mm = j[width] if isinstance(width, str) else float(width)
    h_mm = height_mm if height_mm is not None else w_mm * 0.66
    kw.setdefault("layout", "constrained")
    return plt.subplot_mosaic(layout, figsize=(mm2in(w_mm), mm2in(h_mm)), **kw)


# ---------------------------------------------------------------- 体检诊断

class Issue(str):
    """一条体检诊断。

    它本身仍是一段可打印的中文说明(旧代码把体检结果当 list[str] 用,照样能跑),
    同时带结构化字段,修复时按 code 对症下药,而不是读完句子再猜:

    - ``code``     稳定的错误代码,如 ``text/overlap``、``arrow/through-element``
    - ``subject``  出问题的对象(文字内容、元素标签、箭头标签)
    - ``evidence`` 实测数值(像素、比例、长度),修完拿来对比有没有变好
    - ``fixes``    可选修法,按推荐顺序排列
    - ``severity`` ``error`` 阻断导出;``warning`` 只提示
    """

    def __new__(cls, code, message, subject=None, evidence=None, fixes=(), severity="error"):
        obj = super().__new__(cls, message)
        obj.code, obj.subject, obj.severity = code, subject, severity
        obj.evidence = dict(evidence or {})
        obj.fixes = list(fixes)
        return obj

    def to_dict(self) -> dict:
        return {"code": self.code, "severity": self.severity, "message": str(self),
                "subject": self.subject, "evidence": self.evidence, "fixes": self.fixes}


# 修复顺序:前面的问题会连带制造后面的问题(框挤在一起,箭头和标签自然无处可放),
# 所以先修前面的,每修一轮重跑体检。
REPAIR_ORDER = [
    "spec/",                    # 声明式规格本身写错
    "flow/",                    # 画布尺寸、重心节点数量等整体约束
    "text/too-small",
    "text/out-of-figure",
    "text/out-of-axes",
    "text/overlap",
    "text/crosses-axis",
    "text/crosses-box",
    "container/",
    "inset/covers-data",
    "arrow/through-element",
    "edge/shared-corridor",
    "arrow/over-text",
    "edge/label-no-room",
    "arrow/too-short",
    "edge/crossing",
]

REPAIR_RULES = (
    "按 code 对症修复,一次只改被点名的对象,改完重跑体检;"
    "连续两轮告警数没有下降就停下来,如实报告剩下的诊断。"
    "不许为了通过体检删掉物理量、单位、峰位标注或连线标签——先挪位置,再调间距,最后才精简措辞。"
)


def _as_issue(item):
    return item if isinstance(item, Issue) or hasattr(item, "code") else Issue("legacy", str(item))


def _order_key(item):
    code = getattr(item, "code", "")
    for i, prefix in enumerate(REPAIR_ORDER):
        if code.startswith(prefix):
            return i
    return len(REPAIR_ORDER)


def sort_issues(issues) -> list:
    """按修复顺序排列诊断(同类保持原有顺序)。"""
    return sorted((_as_issue(i) for i in issues), key=_order_key)


def format_issue(item) -> str:
    item = _as_issue(item)
    head = f"[{item.severity} {item.code}] {item}"
    if item.fixes:
        head += "\n    修法: " + " / ".join(item.fixes)
    return head


def write_report(stem: str, issues) -> str | None:
    """把诊断写成 <stem>.check.json;没有诊断时删掉旧报告,避免读到过期结果。"""
    import json
    import os
    path = f"{stem}.check.json"
    issues = sort_issues(issues)
    if not issues:
        if os.path.exists(path):
            os.remove(path)
        return None
    errors = sum(1 for i in issues if i.severity == "error")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"passed": errors == 0, "errors": errors,
                   "warnings": len(issues) - errors, "repair_rules": REPAIR_RULES,
                   "issues": [i.to_dict() for i in issues]}, fh, ensure_ascii=False, indent=2)
    return path


# TOC / graphical abstract 的成品尺寸(英寸)。图幅命中其一就按 TOC 字号底线体检:
# 缩略图里 8 pt 以下的字读不出来。
TOC_SIZES = {
    "ACS TOC": (3.25, 1.75),
    "RSC TOC": (80 / MM_PER_IN, 40 / MM_PER_IN),
    "Wiley ToC": (55 / MM_PER_IN, 50 / MM_PER_IN),
}
MIN_FONT_PT = 5.0          # 任何文字在最终印刷尺寸下的底线
MIN_FONT_TOC_PT = 8.0


def _toc_kind(fig):
    w, h = fig.get_size_inches()
    for name, (tw, th) in TOC_SIZES.items():
        if abs(w - tw) <= 0.03 * tw and abs(h - th) <= 0.03 * th:
            return name
    return None


def check_layout(fig, contain: float = 0.60) -> list:
    """渲染前的程序化布局体检,返回诊断清单(空列表 = 通过)。每条是 ``Issue``:

    1. ``text/overlap``          文字互撞(任意两段可见文字 bbox 相交)
    2. ``text/out-of-figure``    文字出图(bbox 超出画布)
    3. ``text/out-of-axes``      数据坐标文字出轴(transData 文字落在所属 axes 外或被裁剪过半——
       ax.text/annotate 默认不裁剪,超出坐标范围的标注会"飘"到面板外)
    4. ``text/crosses-box``      文字跨越图形框线(示意图高发:文字比框宽,溢出到框外)
       ``container/straddle-*``  元素骑在容器框线上(文字或实心框伸出底带/分区边线)
    5. 示意图几何检查(schemfig 注册的箭头穿过元素/压过文字、声明式流程图的布线诊断)
    6. ``text/too-small``        字号低于底线(印刷 5 pt;图幅是 TOC 尺寸时 8 pt)
    7. ``arrow/over-text``       数据图里 annotate 画的箭头/标尺线压过别的文字
    8. ``inset/covers-data``     插图(含刻度与轴标签)盖住了主图的数据线或数据点
    9. ``text/crosses-axis``     标注文字压在坐标轴框线或内向刻度上

    所有阈值按磅(pt)计,与绘图后端和屏幕像素比无关——同一张图在 macOS 与 Linux 上结论一致。

    刻度标签之间、panel 标号(axes fraction 坐标)不在第 3 类检查范围。
    出告警就按 REPAIR_ORDER 调整布局重跑;体检通过后仍须出 PNG 亲眼检查(感知类问题查不出来)。
    """
    import itertools
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    pt = 72.0 / fig.dpi          # 像素 → 磅
    # 幽灵刻度:locator 会在坐标范围外生成刻度,渲染时被裁剪(不可见),
    # 但 Text 对象仍在且带坐标,必须排除,否则全是误报
    phantom = set()
    # 插图(ax.inset_axes)不在 fig.axes 里,要用 findobj 把子坐标轴一起找出来
    for ax in fig.findobj(mpl.axes.Axes):
        for axis, lim in ((ax.xaxis, sorted(ax.get_xlim())),
                          (ax.yaxis, sorted(ax.get_ylim()))):
            lo, hi = lim
            for tick in list(axis.get_major_ticks()) + list(axis.get_minor_ticks()):
                if not (lo - 1e-12 <= tick.get_loc() <= hi + 1e-12):
                    phantom.add(tick.label1)
                    phantom.add(tick.label2)
    issues, texts = [], []
    for t in fig.findobj(mpl.text.Text):
        s = t.get_text().strip()
        if not s or not t.get_visible() or t in phantom:
            continue
        b = t.get_window_extent(r)
        if b.width <= 1 or b.height <= 1:
            continue
        texts.append((t, s, b))
    # 文字框自带行距留白,相交不足 1 pt 的看不出碰撞,不报
    for (t1, s1, b1), (t2, s2, b2) in itertools.combinations(texts, 2):
        ib = mpl.transforms.Bbox.intersection(b1, b2)
        if ib is not None and ib.width * pt > 1.0 and ib.height * pt > 1.0:
            ev = {"overlap_pt": [round(ib.width * pt, 1), round(ib.height * pt, 1)]}
            issues.append(Issue(
                "text/overlap", f"文字互撞: {s1!r} × {s2!r}", subject=[s1, s2], evidence=ev,
                fixes=["移动其中一段文字(数据标注的偏移从数据算)", "拉开所在元素的间距或加大画布",
                       "精简措辞——保留物理量、单位和标注本身"]))
    W, H = fig.bbox.width, fig.bbox.height
    for t, s, b in texts:
        over = {k: round(v * pt, 1) for k, v in (("left", -b.x0), ("bottom", -b.y0),
                                                   ("right", b.x1 - W), ("top", b.y1 - H)) if v * pt > 0.5}
        if over:
            issues.append(Issue(
                "text/out-of-figure", f"文字出图: {s!r}", subject=s, evidence={"overflow_pt": over},
                fixes=["把文字移回画布内", "加大画布或边距", "缩短文字(保留物理量与单位)"]))
        ax = getattr(t, "axes", None)
        if ax is not None and t.get_transform() is ax.transData:
            ib = mpl.transforms.Bbox.intersection(b, ax.bbox)
            frac = 0.0 if ib is None else (ib.width * ib.height) / (b.width * b.height)
            if frac < contain:
                issues.append(Issue(
                    "text/out-of-axes", f"数据坐标文字出轴: {s!r} (仅 {frac:.0%} 在轴内)",
                    subject=s, evidence={"inside_fraction": round(frac, 2)},
                    fixes=["按数据范围重新计算标注坐标并留出偏移", "放宽 set_xlim/set_ylim 给标注留白",
                           "改用 axes fraction 坐标放置"]))
    # 4) 文字跨框线:只查画在 figure 坐标上的实心图形框(示意图元素),
    #    数据图里的 bar/legend patch 不在此列。schemfig 的容器底带
    #    (_schem_solid=False)与占画布过半的背景框跳过——元素本就画在其上。
    from matplotlib.patches import FancyBboxPatch
    boxes = []
    for p in fig.findobj(FancyBboxPatch):
        if p.get_transform() is not fig.transFigure or not p.get_visible():
            continue
        if getattr(p, "_schem_solid", True) is False:
            continue
        bb = p.get_window_extent(r)
        if bb.width * bb.height > 0.55 * W * H:
            continue
        boxes.append(bb)
    for t, s, b in texts:
        for bb in boxes:
            ib = mpl.transforms.Bbox.intersection(b, bb)
            frac = 0.0 if ib is None else (ib.width * ib.height) / (b.width * b.height)
            if 0.08 < frac < 0.95:
                issues.append(Issue(
                    "text/crosses-box", f"文字跨框线: {s!r} (仅 {frac:.0%} 在框内——要么全进要么全出)",
                    subject=s, evidence={"inside_fraction": round(frac, 2)},
                    fixes=["内容框改用 sf.text_box,按文字实测尺寸生成", "把文字整体移进或移出该框"]))
    # 4b) 容器压线:容器底带(solid=False)允许元素画在其内部,但元素(文字/实心框)
    #     不许"骑"在容器框线上——要么全进,要么全出。这正是"徽章/长文字
    #     伸出底带边线"一类缺陷的检测点(容器不参与 4 的实心框检查,但
    #     它自己的边线仍是视觉硬边界)。
    containers, solid_boxes = [], []
    for p in fig.findobj(FancyBboxPatch):
        if p.get_transform() is not fig.transFigure or not p.get_visible():
            continue
        bb = p.get_window_extent(r)
        if getattr(p, "_schem_solid", True) is False:
            containers.append(bb)
        else:
            solid_boxes.append(bb)
    def _frac_in(inner, outer):
        ib = mpl.transforms.Bbox.intersection(inner, outer)
        return 0.0 if ib is None else (ib.width * ib.height) / (inner.width * inner.height)
    for cb in containers:
        for t, s, b in texts:
            frac = _frac_in(b, cb)
            if 0.08 < frac < 0.95:
                issues.append(Issue(
                    "container/straddle-text", f"文字骑在容器框线上: {s!r} (仅 {frac:.0%} 在容器内)",
                    subject=s, evidence={"inside_fraction": round(frac, 2)},
                    fixes=["把文字整体移进或移出容器底带", "加大容器底带"]))
        for bb in solid_boxes:
            frac = _frac_in(bb, cb)
            if 0.08 < frac < 0.95:
                pos = [round(bb.x0 / W, 2), round(bb.y0 / H, 2)]
                issues.append(Issue(
                    "container/straddle-box",
                    f"元素框骑在容器框线上 (仅 {frac:.0%} 在容器内,约 x={pos[0]:.2f},y={pos[1]:.2f})",
                    subject=pos, evidence={"inside_fraction": round(frac, 2), "figure_xy": pos},
                    fixes=["把元素整体移进或移出容器底带", "加大容器底带"]))
    # 6) 字号底线:图按最终尺寸建,fontsize 就是印刷磅值
    toc = _toc_kind(fig)
    floor = MIN_FONT_TOC_PT if toc else MIN_FONT_PT
    small = sorted({(round(t.get_fontsize(), 1), s) for t, s, _ in texts if t.get_fontsize() < floor - 1e-6})
    if small:
        where = f"{toc} 图幅" if toc else "印刷尺寸"
        issues.append(Issue(
            "text/too-small", f"{len(small)} 段文字小于 {floor:g} pt({where}): "
            + ", ".join(f"{s[:12]!r} {z:g} pt" for z, s in small[:5]),
            subject=[s for _, s in small], evidence={"floor_pt": floor, "sizes_pt": [z for z, _ in small]},
            fixes=["加大字号到底线以上", "删减次要文字(TOC 只留核心概念和关键数字)",
                   "拉开布局腾出空间,不要靠缩字塞内容"]))

    # 7) 数据图里的标注箭头/标尺线压字(schemfig 自己登记的箭头由第 5 项查)
    from matplotlib.patches import FancyArrowPatch
    from matplotlib.text import Annotation
    arrows = []
    for ann in fig.findobj(Annotation):
        ap = getattr(ann, "arrow_patch", None)
        if ap is not None and ap.get_visible() and ann.get_visible():
            arrows.append((ann, ap))
    own = {id(ap) for _, ap in arrows}
    for ax in fig.findobj(mpl.axes.Axes):
        for p in ax.patches:
            if isinstance(p, FancyArrowPatch) and p.get_visible() and id(p) not in own:
                arrows.append((None, p))
    for ann, ap in arrows:
        try:
            polys = ap.get_transform().transform_path(ap.get_path()).to_polygons(closed_only=False)
        except Exception:
            continue
        samples = []
        for poly in polys:
            for (x0, y0), (x1, y1) in zip(poly[:-1], poly[1:]):
                n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 1.5))
                samples += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n + 1)]
        if not samples:
            continue
        name = (ann.get_text().strip() if ann is not None else "") or "标注箭头"
        for t, s, b in texts:
            if t is ann:
                continue
            inner = b.padded(-1.0 / pt)          # 贴边不算,压进 1 pt 才算
            if inner.width <= 0 or inner.height <= 0:
                continue
            if any(inner.x0 < x < inner.x1 and inner.y0 < y < inner.y1 for x, y in samples):
                issues.append(Issue(
                    "arrow/over-text", f"标注箭头压过文字: {name!r} × {s!r}",
                    subject={"arrow": name, "text": s},
                    fixes=["把文字移到箭头一侧(偏移从数据算)", "缩短箭头或改变起止点",
                           "文字改用 annotate 自带的 xytext 放在箭头尾端"]))

    # 8) 插图盖住数据:插图不透明,主图落在它(含刻度与轴标签)下面的线和点就看不见了
    axes_all = [a for a in fig.findobj(mpl.axes.Axes) if a.get_visible()]
    for child in axes_all:
        patch = child.patch
        if not patch.get_visible() or patch.get_facecolor()[3] == 0:
            continue
        cb_area = child.bbox
        for parent in axes_all:
            pb = parent.bbox
            if parent is child or cb_area.width * cb_area.height >= pb.width * pb.height:
                continue
            if not (pb.x0 - 1 <= cb_area.x0 and cb_area.x1 <= pb.x1 + 1
                    and pb.y0 - 1 <= cb_area.y0 and cb_area.y1 <= pb.y1 + 1):
                continue
            cover = child.get_tightbbox(r)
            hidden = []
            for ln in parent.get_lines():
                if not ln.get_visible() or len(ln.get_xydata()) == 0:
                    continue
                xy = ln.get_transform().transform(ln.get_xydata())
                inside_ax = [(x, y) for x, y in xy if pb.x0 <= x <= pb.x1 and pb.y0 <= y <= pb.y1]
                marks = sum(1 for x, y in inside_ax if cover.x0 < x < cover.x1 and cover.y0 < y < cover.y1)
                length = 0.0
                if ln.get_linestyle() not in ("None", " ", ""):
                    for (x0, y0), (x1, y1) in zip(xy[:-1], xy[1:]):
                        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 1.5))
                        for k in range(n):
                            x, y = x0 + (x1 - x0) * (k + 0.5) / n, y0 + (y1 - y0) * (k + 0.5) / n
                            if (cover.x0 < x < cover.x1 and cover.y0 < y < cover.y1
                                    and pb.x0 <= x <= pb.x1 and pb.y0 <= y <= pb.y1):
                                length += math.hypot(x1 - x0, y1 - y0) / n
                has_marker = ln.get_marker() not in (None, "None", " ", "", "none")
                if (has_marker and marks) or length * pt > 3.0:
                    lab = ln.get_label()
                    if not lab or lab.startswith("_"):
                        lab = f"第 {parent.get_lines().index(ln) + 1} 条线({mpl.colors.to_hex(ln.get_color())})"
                    hidden.append((lab, marks if has_marker else 0, round(length * pt, 1)))
            for coll in parent.collections:
                offs = getattr(coll, "get_offsets", lambda: [])()
                if not coll.get_visible() or len(offs) == 0:
                    continue
                xy = coll.get_offset_transform().transform(offs)
                marks = sum(1 for x, y in xy if cover.x0 < x < cover.x1 and cover.y0 < y < cover.y1
                            and pb.x0 <= x <= pb.x1 and pb.y0 <= y <= pb.y1)
                if marks:
                    lab = coll.get_label()
                    hidden.append((lab if lab and not lab.startswith("_") else "散点", marks, 0.0))
            if hidden:
                names = [h[0] for h in hidden]
                issues.append(Issue(
                    "inset/covers-data", f"插图盖住了主图数据: {', '.join(map(str, names))}",
                    subject=names,
                    evidence={"hidden": [{"series": n, "points": m, "line_pt": l}
                                         for n, (_, m, l) in zip(names, hidden)]},
                    fixes=["把插图移到没有数据的空白区域(按数据范围算位置)",
                           "放宽主图坐标范围给插图腾出空白", "缩小插图,或改成并排的独立 panel"]))

    # 9) 标注压轴:ax.text/annotate 的文字压在坐标轴框线上,或落进内向刻度的那一条带
    for ax in axes_all:
        if not ax.axison:
            continue
        own_texts = {id(t) for t in ax.texts}
        ab = ax.bbox
        bands = []
        for side, spine in ax.spines.items():
            if not spine.get_visible() or side not in ("left", "right", "bottom", "top"):
                continue
            axis = ax.xaxis if side in ("bottom", "top") else ax.yaxis
            tick_in = 0.0
            if mpl.rcParams[f"{'x' if axis is ax.xaxis else 'y'}tick.direction"] in ("in", "inout"):
                tick_in = mpl.rcParams[f"{'x' if axis is ax.xaxis else 'y'}tick.major.size"] / pt
            lw = max(spine.get_linewidth() / pt / 2, 0.5)
            if side == "bottom":
                bands.append((side, ab.x0, ab.y0 - lw, ab.x1, ab.y0 + lw + tick_in))
            elif side == "top":
                bands.append((side, ab.x0, ab.y1 - lw - tick_in, ab.x1, ab.y1 + lw))
            elif side == "left":
                bands.append((side, ab.x0 - lw, ab.y0, ab.x0 + lw + tick_in, ab.y1))
            else:
                bands.append((side, ab.x1 - lw - tick_in, ab.y0, ab.x1 + lw, ab.y1))
        for t, s, b in texts:
            if id(t) not in own_texts or getattr(t, "axes", None) is not ax:
                continue
            inner = b.padded(-0.5 / pt)
            for side, x0, y0, x1, y1 in bands:
                if inner.x0 < x1 and inner.x1 > x0 and inner.y0 < y1 and inner.y1 > y0:
                    issues.append(Issue(
                        "text/crosses-axis", f"标注压在坐标轴{ {'bottom': '下', 'top': '上', 'left': '左', 'right': '右'}[side] }框线或刻度上: {s!r}",
                        subject=s, evidence={"side": side},
                        fixes=["把标注往坐标区内挪,离框线留出刻度长度以上的空白",
                               "放宽坐标范围给标注腾位置", "改放在数据曲线旁的空白处"]))
                    break

    # 5) 示意图几何检查:schemfig.canvas 会在 fig 上挂 _schem_check
    extra = getattr(fig, "_schem_check", None)
    if callable(extra):
        issues += [_as_issue(i) for i in extra()]
    return issues


def grayscale(png_path: str) -> str:
    """生成灰度版用于黑白打印检查(定稿前用 Read 亲眼比对可分辨性)。"""
    from PIL import Image
    out = png_path[:-4] + "_gray.png" if png_path.endswith(".png") else png_path + "_gray.png"
    Image.open(png_path).convert("L").save(out)
    return out


def export(fig, stem: str, formats=("pdf", "png"), dpi: int = 600,
           strict: bool = True, crops="auto", report: bool = True) -> list[str]:
    """按最终尺寸导出。默认 PDF（投稿矢量图）+ PNG 600 dpi（预览/检查）。
    需要 TIFF 时在 formats 里加 'tiff'。故意不用 bbox_inches='tight'。
    图要插 Word/PPT 时在 formats 里加 'svg'（文字自动转路径,Word 2016+ 原生
    支持矢量插入,任意缩放不糊;PNG 插 Word 会被默认压缩到 220 ppi）。

    strict=True（默认）：体检有 error 级诊断直接拒绝导出——图不许带着已知缺陷
    交出去。按 REPAIR_ORDER 逐条修复后重跑；确认是误报才可 strict=False，且要在
    交付说明里写明理由。report=True：有诊断时写 <stem>.check.json（结构化诊断，
    每轮修复后对比告警数），通过后自动删除。crops="auto"：示意图（schemfig 画布）
    自动把 PNG 切成 2×2 局部放大块，逐块用 Read 亲眼检查（整图缩略看不见几像素的擦边）。
    """
    issues = sort_issues(check_layout(fig))
    for item in issues:
        print(f"[paperfig 布局告警] {format_issue(item)}")
    if report:
        write_report(stem, issues)
    errors = [i for i in issues if i.severity == "error"]
    if errors and strict:
        raise RuntimeError(
            f"布局体检 {len(errors)} 条 error，已阻断导出（诊断见 {stem}.check.json）。{REPAIR_RULES}"
            f"确认误报才可 strict=False，并在交付说明中说明理由。")
    paths = []
    for ext in formats:
        path = f"{stem}.{ext}"
        if ext == "svg":
            # Word/PPT 用矢量:文字转路径,不依赖对方机器字体,缩放永远清晰
            with mpl.rc_context({"svg.fonttype": "path"}):
                fig.savefig(path)
        else:
            fig.savefig(path, dpi=dpi)
        paths.append(path)
    if crops == "auto":
        crops = bool(getattr(fig, "_schem_obstacles", None))
    png = next((p for p in paths if p.endswith(".png")), None)
    if crops and png:
        cs = make_crops(png)
        print("[paperfig] 局部放大块已生成，请逐块 Read 检查: " + ", ".join(cs))
        paths += cs
    return paths


def make_crops(png_path: str, rows: int = 2, cols: int = 2,
               overlap: float = 0.10) -> list[str]:
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
