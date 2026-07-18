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


def check_layout(fig, contain: float = 0.60) -> list[str]:
    """渲染前的程序化布局体检,返回问题清单(空列表 = 通过)。检查三类高发缺陷:

    1. 文字互撞(任意两段可见文字 bbox 相交)
    2. 文字出图(bbox 超出画布)
    3. 数据坐标文字出轴(transData 文字落在所属 axes 外或被裁剪过半——
       ax.text/annotate 默认不裁剪,超出坐标范围的标注会"飘"到面板外)

    刻度标签之间、panel 标号(axes fraction 坐标)不在第 3 类检查范围。
    出告警就调整布局重跑;体检通过后仍须出 PNG 亲眼检查(感知类问题查不出来)。
    """
    import itertools
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    # 幽灵刻度:locator 会在坐标范围外生成刻度,渲染时被裁剪(不可见),
    # 但 Text 对象仍在且带坐标,必须排除,否则全是误报
    phantom = set()
    for ax in fig.axes:
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
    for (t1, s1, b1), (t2, s2, b2) in itertools.combinations(texts, 2):
        if b1.padded(-0.6).overlaps(b2.padded(-0.6)):
            issues.append(f"文字互撞: {s1!r} × {s2!r}")
    for t, s, b in texts:
        if (b.x0 < -0.5 or b.y0 < -0.5
                or b.x1 > fig.bbox.width + 0.5 or b.y1 > fig.bbox.height + 0.5):
            issues.append(f"文字出图: {s!r}")
        ax = getattr(t, "axes", None)
        if ax is not None and t.get_transform() is ax.transData:
            ib = mpl.transforms.Bbox.intersection(b, ax.bbox)
            frac = 0.0 if ib is None else (ib.width * ib.height) / (b.width * b.height)
            if frac < contain:
                issues.append(f"数据坐标文字出轴: {s!r} (仅 {frac:.0%} 在轴内)")
    return issues


def grayscale(png_path: str) -> str:
    """生成灰度版用于黑白打印检查(定稿前用 Read 亲眼比对可分辨性)。"""
    from PIL import Image
    out = png_path[:-4] + "_gray.png" if png_path.endswith(".png") else png_path + "_gray.png"
    Image.open(png_path).convert("L").save(out)
    return out


def export(fig, stem: str, formats=("pdf", "png"), dpi: int = 600) -> list[str]:
    """按最终尺寸导出。默认 PDF（投稿矢量图）+ PNG 600 dpi（预览/检查）。
    需要 TIFF 时在 formats 里加 'tiff'。故意不用 bbox_inches='tight'。
    """
    for msg in check_layout(fig):          # 导出前自动体检,告警打印但不阻断
        print(f"[paperfig 布局告警] {msg}")
    paths = []
    for ext in formats:
        path = f"{stem}.{ext}"
        fig.savefig(path, dpi=dpi)
        paths.append(path)
    return paths
