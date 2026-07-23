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

import math
import textwrap

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


def check(fig) -> list[str]:
    """schemfig 几何体检：箭头是否穿过障碍物/压过文字。export 前自动跑
    （paperfig.check_layout 也会调用），全部障碍物注册完之后复查，
    所以"先画箭头后画框"造成的穿越也逃不掉。"""
    issues = []
    r = _renderer(fig)
    texts = []
    for t in fig.findobj(matplotlib.text.Text):
        s = t.get_text().strip()
        if s and t.get_visible():
            b = t.get_window_extent(r)
            if b.width > 1 and b.height > 1:
                texts.append((s, (b.x0 - 1, b.y0 - 1, b.x1 + 1, b.y1 + 1)))
    for rec in getattr(fig, "_schem_arrows", []):
        p1, p2, rad = rec["p1"], rec["p2"], rec["rad"]
        if rec.get("d_pt", 99.0) < 5.0:
            issues.append(f"箭头过短(全长 {rec['d_pt']:.1f}pt < 5pt),已退化: "
                          f"{rec['label'] or p1} —— 请拉开两元素间距或减小 connect gap")
        obs = [el for el in getattr(fig, "_schem_obstacles", [])
               if id(el) not in rec["ignore"]
               and not el.contains(p1) and not el.contains(p2)]
        samples = _arc3_samples(fig, p1, p2, rad, n=61)
        for i in _hits(samples, [_disp_rect(fig, el.rect) for el in obs]):
            issues.append(f"箭头穿过元素: {rec['label'] or p1} × {obs[i].label!r}")
        excl = [el for el in getattr(fig, "_schem_obstacles", [])
                if id(el) in rec["ignore"] or el.contains(p1) or el.contains(p2)]
        inv = fig.transFigure.inverted()
        for i in _hits(samples, [tb for _, tb in texts]):
            s, tb = texts[i]
            c = inv.transform(((tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2))
            if any(el.contains(c) for el in excl):
                continue                  # 起止框自己的文字不算
            issues.append(f"箭头压过文字: {rec['label'] or p1} × {s!r}")
    return issues


def export(fig, stem, dpi=300, formats=("png", "pdf"), strict=True, crops=True):
    """示意图导出：体检（paperfig 全套 + schemfig 几何）→ 拦截 → 出图 → 切块。

    图要插 Word/PPT 时在 formats 里加 "svg"（文字自动转路径）：Word 2016+ 原生
    支持 SVG 矢量插入，任意缩放不糊；PNG 插 Word 会被默认压缩到 220 ppi。

    告警非零时 strict=True 直接拒绝导出——修复后重跑，不许带病交付。
    出图后自动生成 2×2 局部放大块，**每一块都必须用 Read 亲眼检查**：
    整图缩略时几像素的箭头擦边/文字压线是看不见的。"""
    try:
        import paperfig as pf
        issues = pf.check_layout(fig)     # 已含 fig._schem_check 的几何检查
    except ImportError:
        issues = check(fig)
    for msg in issues:
        print(f"[schemfig 布局告警] {msg}")
    if issues and strict:
        raise RuntimeError(f"布局体检 {len(issues)} 条告警，已阻断导出；"
                           f"逐条修复后重跑（确认误报才可 strict=False，并在交付说明中说明理由）")
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