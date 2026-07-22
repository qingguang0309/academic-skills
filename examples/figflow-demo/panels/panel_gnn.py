"""panel_gnn: 超像素区域邻接图(GNN 输入结构)。44x34mm,满幅无边距。

底图 BSE 灰度(alpha 0.4)+ SLIC 超像素边界 + 区域邻接图;
含 EDS 采样点的区域质心为相色大节点,其余为小灰点。
只用 numpy/scipy/matplotlib/skimage + field.py,确定性。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 找到 field.py

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from skimage.measure import regionprops
from skimage.segmentation import find_boundaries, slic

from field import PHASE_COLORS, eds_points, make_field

W_MM, H_MM = 44.0, 34.0
BOUND_COLOR = "#8A9B4C"   # 超像素边界:灰绿
EDGE_COLOR = "#75845A"    # 邻接边:偏暗灰绿
SMALL_NODE = "#9AA5B1"    # 未采样区域质心

phase, gray = make_field()
n = gray.shape[0]

# ---- 超像素分割 ----
segments = slic(gray, n_segments=40, compactness=0.08,
                channel_axis=None, start_label=1)
labels = np.unique(segments)

# 质心(row, col)
centroids = {p.label: p.centroid for p in regionprops(segments)}

# ---- 区域邻接(4 邻域) ----
adj = set()
h_pairs = np.stack([segments[:, :-1].ravel(), segments[:, 1:].ravel()], axis=1)
v_pairs = np.stack([segments[:-1, :].ravel(), segments[1:, :].ravel()], axis=1)
for a, b in np.unique(np.vstack([h_pairs, v_pairs]), axis=0):
    if a != b:
        adj.add((min(a, b), max(a, b)))

# ---- EDS 采样点落入的超像素 → 节点相色(多点取多数,先到先得破平) ----
xs, ys, pids = eds_points()
region_phase = {}
for x, y, pid in zip(xs, ys, pids):
    region_phase.setdefault(segments[y, x], []).append(int(pid))
sampled_color = {}
for lab, plist in region_phase.items():
    counts = np.bincount(plist, minlength=4)
    sampled_color[lab] = PHASE_COLORS[int(np.argmax(counts))]

# ---- 画布 ----
fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

# 底图:淡化 BSE 灰度
ax.imshow(gray, cmap="gray", vmin=0, vmax=1, alpha=0.4,
          interpolation="nearest", aspect="auto", zorder=0)

# 超像素边界:灰绿细线(用 RGBA 覆盖层,mode='inner' 保持 1px 细)
bounds = find_boundaries(segments, mode="inner")
rgba = np.zeros((n, n, 4))
rgba[bounds] = list(matplotlib.colors.to_rgb(BOUND_COLOR)) + [0.8]
ax.imshow(rgba, interpolation="nearest", aspect="auto", zorder=1)

# 邻接边:相邻区域质心连线
for a, b in sorted(adj):
    (r1, c1), (r2, c2) = centroids[a], centroids[b]
    ax.plot([c1, c2], [r1, r2], color=EDGE_COLOR, lw=0.55,
            alpha=0.5, solid_capstyle="round", zorder=2)

# 节点
for lab in labels:
    r, c = centroids[lab]
    if lab in sampled_color:
        ax.scatter(c, r, s=30, c=sampled_color[lab], edgecolors="white",
                   linewidths=0.7, zorder=4)
    else:
        ax.scatter(c, r, s=7, c=SMALL_NODE, edgecolors="none", zorder=3)

ax.set_xlim(-0.5, n - 0.5)
ax.set_ylim(n - 0.5, -0.5)

fig.savefig("panels/panel_gnn.png", dpi=300)
