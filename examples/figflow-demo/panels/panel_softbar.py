"""panel_softbar: 概率软标签水平堆叠条(40x10mm,满幅无边距)。
比例 C-(A)-S-H 0.52 / 熟料 0.18 / SCM 0.20 / 孔隙 0.10,颜色取 field.PHASE_COLORS。"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from field import PALETTE

W_MM, H_MM = 40.0, 10.0

# (名称, 比例, 颜色) —— 按契约给定顺序排布
SEGMENTS = [
    ("csh",     0.52, PALETTE["csh"]),      # C-(A)-S-H
    ("clinker", 0.18, PALETTE["clinker"]),  # 熟料
    ("scm",     0.20, PALETTE["scm"]),      # SCM
    ("pore",    0.10, PALETTE["pore"]),     # 孔隙
]

fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# 段矩形(满幅铺满,相邻排布)
x = 0.0
edges = []  # 段内部边界位置(用于白缝)
texts = []
spans = []  # (x0, x1) 供文字省略判断
for i, (_, frac, color) in enumerate(SEGMENTS):
    ax.axvspan(x, x + frac, color=color, lw=0)
    t = ax.text(x + frac / 2, 0.5, f"{frac * 100:.0f}%",
                ha="center", va="center", color="white",
                fontsize=7, fontweight="bold")
    texts.append(t)
    spans.append((x, x + frac))
    x += frac
    if i < len(SEGMENTS) - 1:
        edges.append(x)

# 段间细白缝(覆盖在边界上,~0.8pt)
for e in edges:
    ax.axvline(e, color="white", lw=0.8, zorder=5)

# 段太窄放不下数字则省略:用渲染器实测文字宽度与段宽比较
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
panel_w_px = fig.get_size_inches()[0] * fig.dpi
pad_px = 2.0  # 每侧最少留白(含白缝)
for t, (x0, x1) in zip(texts, spans):
    text_w_px = t.get_window_extent(renderer).width
    seg_w_px = (x1 - x0) * panel_w_px
    if text_w_px > seg_w_px - 2 * pad_px:
        t.set_visible(False)

out = "panels/panel_softbar.png"
fig.savefig(out, dpi=300)
print("saved", out)
