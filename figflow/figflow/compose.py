"""figflow 排版引擎:按 JSON spec 确定性合成多面板大图。

分治原则:面板(PNG)由并行代理各自生成、各自质检;本引擎负责一切"关系性"元素——
色带、箭头、徽标、伪3D块、注意力网格、图例、脚注。箭头端点由面板矩形的锚点
(id.edge:t)计算得出,模型不手拍任何大图坐标,连接类缺陷从机制上消除。

spec 结构(单位 mm,原点左下):
{
  "canvas_mm": [W, H], "dpi": 300, "font": {"cjk_first": true},
  "palette": {"name": "#hex", ...},              # 供 badge/text 以 $name 引用
  "bands":  [{"rect": [x,y,w,h], "label": "...", "color": "#..."}],
  "panels": [{"id", "file", "rect", "title", "subtitle", "border": true}],
  "items":  [{"type": "badge|text|slabs|heatgrid", ...}],
  "arrows": [{"from": "id.right", "to": "id.left:0.3", "color": "$blue", "rad": 0.2}],
  "legend": {"pos": [x,y], "entries": [["label", "$key"], ...]},
  "footnote": {"pos": [x,y], "text": "...", "size": 8}
}
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.image import imread
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

MM = 25.4


def _setup_fonts() -> None:
    avail = {f.name for f in fm.fontManager.ttflist}
    cjk = next((f for f in ["PingFang SC", "Hiragino Sans GB", "Songti SC",
                            "Microsoft YaHei", "Noto Sans CJK SC"] if f in avail), None)
    stack = ([cjk] if cjk else []) + ["Helvetica Neue", "Arial", "DejaVu Sans"]
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": stack,
                         "axes.unicode_minus": False})


class Composer:
    def __init__(self, spec: dict, workdir: Path):
        self.spec = spec
        self.wd = Path(workdir)
        self.W, self.H = spec["canvas_mm"]
        self.aspect = self.W / self.H
        self.rects: dict[str, tuple[float, float, float, float]] = {}  # id -> fig 坐标 rect
        _setup_fonts()
        self.fig = plt.figure(figsize=(self.W / MM, self.H / MM))
        self.fig.patch.set_facecolor(spec.get("background", "#FFFFFF"))

    # ---------- 坐标与颜色 ----------
    def _r(self, rect_mm) -> tuple[float, float, float, float]:
        x, y, w, h = rect_mm
        return (x / self.W, y / self.H, w / self.W, h / self.H)

    def _c(self, color: str) -> str:
        if isinstance(color, str) and color.startswith("$"):
            return self.spec.get("palette", {})[color[1:]]
        return color

    def _anchor(self, ref: str) -> tuple[float, float]:
        """解析 'id.edge[:t]' 为 fig 坐标点。edge∈left/right/top/bottom,t 为沿边比例。"""
        part, _, tstr = ref.partition(":")
        pid, _, edge = part.partition(".")
        t = float(tstr) if tstr else 0.5
        if pid not in self.rects:
            raise KeyError(f"锚点引用了未注册的元素 id:{pid!r}")
        x, y, w, h = self.rects[pid]
        return {
            "left": (x, y + h * t),
            "right": (x + w, y + h * t),
            "top": (x + w * t, y + h),
            "bottom": (x + w * t, y),
        }[edge]

    def _register(self, pid: str | None, rect_mm) -> tuple[float, float, float, float]:
        r = self._r(rect_mm)
        if pid:
            self.rects[pid] = r
        return r

    # ---------- 元素绘制 ----------
    def _rbox(self, rect, fc, ec, lw=1.4, rs=0.012, ls="-", z=2):
        x, y, w, h = rect
        rs = min(rs, w / 2, h * self.aspect / 2 * 0.9)  # 防止胶囊圆角退化
        p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rs}",
                           transform=self.fig.transFigure, fc=fc, ec=ec, lw=lw, ls=ls,
                           mutation_aspect=self.aspect, zorder=z, clip_on=False)
        self.fig.add_artist(p)

    def _draw_bands(self):
        for b in self.spec.get("bands", []):
            rect = self._register(b.get("id"), b["rect"])
            self._rbox(rect, self._c(b.get("color", "#F5F7FA")),
                       self._c(b.get("edge", "#E3E9F0")), lw=1.0, z=1)
            if b.get("label"):
                x, y, w, h = rect
                self.fig.text(x + 2.5 / self.W, y + h - 2.2 / self.H, b["label"],
                              fontsize=b.get("size", 11.5), weight=600,
                              color=self._c(b.get("label_color", "#5B6B7F")),
                              ha="left", va="top")

    def _draw_panels(self):
        for p in self.spec.get("panels", []):
            rect = self._register(p["id"], p["rect"])
            ax = self.fig.add_axes(rect)
            ax.set_zorder(3)
            img = imread(self.wd / p["file"])
            ax.imshow(img)
            ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(bool(p.get("border", True)))
                s.set_color(self._c(p.get("border_color", "#334155")))
                s.set_linewidth(1.1)
            x, y, w, h = rect
            if p.get("title"):
                self.fig.text(x + w / 2, y + h + 2.5 / self.H, p["title"],
                              fontsize=p.get("title_size", 11.5), weight=600,
                              color=self._c(p.get("title_color", "#0F172A")),
                              ha="center", va="bottom", zorder=4)
            if p.get("subtitle"):
                self.fig.text(x + w / 2, y - 2.0 / self.H, p["subtitle"],
                              fontsize=p.get("subtitle_size", 9),
                              color=self._c(p.get("subtitle_color", "#5B6B7F")),
                              ha="center", va="top", zorder=4)

    def _draw_items(self):
        rng = np.random.default_rng(7)
        for it in self.spec.get("items", []):
            kind = it["type"]
            if kind == "badge":
                rect = self._register(it.get("id"), it["rect"])
                self._rbox(rect, self._c(it.get("fill", "#FFFFFF")),
                           self._c(it.get("edge", "#334155")),
                           lw=it.get("lw", 1.3), rs=it.get("rs", 0.014), z=3)
                x, y, w, h = rect
                lines = it["lines"]
                for i, ln in enumerate(lines):
                    cy = y + h * (len(lines) - i - 0.5) / len(lines)
                    self.fig.text(x + w / 2, cy, ln.get("text", ln) if isinstance(ln, dict) else ln,
                                  fontsize=(ln.get("size", 9.5) if isinstance(ln, dict) else it.get("size", 9.5)),
                                  weight=(600 if (isinstance(ln, dict) and ln.get("bold")) else 400),
                                  color=self._c((ln.get("color") if isinstance(ln, dict) else None)
                                                or it.get("text_color", "#0F172A")),
                                  ha="center", va="center", zorder=4)
            elif kind == "text":
                x, y = it["pos"][0] / self.W, it["pos"][1] / self.H
                self.fig.text(x, y, it["text"], fontsize=it.get("size", 10),
                              weight=600 if it.get("bold") else 400,
                              color=self._c(it.get("color", "#0F172A")),
                              ha=it.get("ha", "center"), va=it.get("va", "center"), zorder=4)
            elif kind == "slabs":
                rect = self._register(it.get("id"), it["rect"])
                x, y, w, h = rect
                n = it.get("n", 4)
                colors = it.get("colors", ["#BFDBFE", "#93C5FD", "#60A5FA", "#3B82F6"])
                gap = w * 0.06
                sw = (w - gap * (n - 1)) / n * 0.72
                for i in range(n):
                    sh = h * (1.0 - 0.22 * i)
                    sx = x + i * (w - sw) / max(n - 1, 1) * 0.92
                    sy = y + (h - sh) / 2
                    dx, dy = 0.35 * sw, 0.35 * sw * self.aspect
                    front = [(sx, sy), (sx + sw, sy), (sx + sw, sy + sh), (sx, sy + sh)]
                    top = [(sx, sy + sh), (sx + sw, sy + sh), (sx + sw + dx, sy + sh + dy), (sx + dx, sy + sh + dy)]
                    side = [(sx + sw, sy), (sx + sw + dx, sy + dy), (sx + sw + dx, sy + sh + dy), (sx + sw, sy + sh)]
                    base = np.array(matplotlib.colors.to_rgb(self._c(colors[i % len(colors)])))
                    for pts, shade in [(top, 0.88), (side, 0.75), (front, 1.0)]:
                        self.fig.add_artist(Polygon(pts, closed=True, transform=self.fig.transFigure,
                                                    fc=np.clip(base * shade, 0, 1),
                                                    ec=self._c(it.get("edge", "#1E40AF")),
                                                    lw=0.9, zorder=3))
            elif kind == "heatgrid":
                rect = self._register(it.get("id"), it["rect"])
                x, y, w, h = rect
                rows, cols = it.get("shape", [6, 6])
                vals = rng.uniform(0.15, 0.95, size=(rows, cols))
                base = self._c(it.get("color", "#7C3AED"))
                cw, ch = w / cols, h / rows
                for i in range(rows):
                    for j in range(cols):
                        self.fig.add_artist(Rectangle(
                            (x + j * cw + cw * 0.08, y + i * ch + ch * 0.08),
                            cw * 0.84, ch * 0.84, transform=self.fig.transFigure,
                            fc=base, alpha=float(vals[i, j]), ec="none", zorder=3))
            else:
                raise ValueError(f"未知 item 类型:{kind}")

    def _draw_arrows(self):
        for a in self.spec.get("arrows", []):
            p1, p2 = self._anchor(a["from"]), self._anchor(a["to"])
            self.fig.add_artist(FancyArrowPatch(
                p1, p2, transform=self.fig.transFigure,
                connectionstyle=f"arc3,rad={a.get('rad', 0.0)}",
                arrowstyle="-|>", mutation_scale=a.get("head", 13),
                lw=a.get("lw", 1.8), color=self._c(a.get("color", "#475569")),
                shrinkA=a.get("shrink", 0.5), shrinkB=a.get("shrink", 0.5),
                zorder=2, capstyle="round"))

    def _draw_legend(self):
        lg = self.spec.get("legend")
        if not lg:
            return
        x = lg["pos"][0] / self.W
        y = lg["pos"][1] / self.H
        size = lg.get("size", 9)
        for label, color in lg["entries"]:
            self.fig.add_artist(Rectangle((x, y - 0.008), 3.2 / self.W, 2.6 / self.H,
                                          transform=self.fig.transFigure,
                                          fc=self._c(color), ec="#334155", lw=0.5, zorder=4))
            self.fig.text(x + 4.4 / self.W, y, label, fontsize=size,
                          color=self._c(lg.get("text_color", "#37455B")),
                          ha="left", va="center", zorder=4)
            x += (4.4 + 3.3 * len(label) + 6.0) / self.W

    def _draw_footnote(self):
        fn = self.spec.get("footnote")
        if not fn:
            return
        self.fig.text(fn["pos"][0] / self.W, fn["pos"][1] / self.H, fn["text"],
                      fontsize=fn.get("size", 8.5), color=self._c(fn.get("color", "#5B6B7F")),
                      ha=fn.get("ha", "center"), va="center", zorder=4)

    # ---------- 主流程 ----------
    def compose(self, out: Path, dpi: int | None = None) -> Path:
        # 先注册全部矩形(锚点解析需要),再按 z 序绘制
        for b in self.spec.get("bands", []):
            self._register(b.get("id"), b["rect"])
        for p in self.spec.get("panels", []):
            self._register(p["id"], p["rect"])
        for it in self.spec.get("items", []):
            if "rect" not in it:
                continue
            if it["type"] == "slabs":
                # 伪3D块的实际绘制范围窄于给定矩形,注册有效范围使锚点贴合末端棱边
                x, y, w, h = it["rect"]
                n = it.get("n", 4)
                gap = w * 0.06
                sw = (w - gap * (n - 1)) / n * 0.72
                right = x + (w - sw) * 0.92 + sw + 0.35 * sw
                self._register(it.get("id"), [x, y, right - x, h])
            else:
                self._register(it.get("id"), it["rect"])
        self._draw_bands()
        self._draw_arrows()
        self._draw_panels()
        self._draw_items()
        self._draw_legend()
        self._draw_footnote()
        out = Path(out)
        self.fig.savefig(out, dpi=dpi or self.spec.get("dpi", 300),
                         facecolor=self.fig.get_facecolor())
        plt.close(self.fig)
        return out


def compose_spec(spec_path: str | Path, out: str | Path | None = None) -> Path:
    spec_path = Path(spec_path)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    wd = spec_path.parent
    out = Path(out) if out else wd / spec.get("output", "figure_composed.png")
    return Composer(spec, wd).compose(out)
