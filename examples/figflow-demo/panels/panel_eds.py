"""panel_eds: 稀疏 EDS 采样面板 (40x30mm, 满幅无边距).

白底 + 极淡灰度场底图 (alpha=0.18) + eds_points() 彩色散点 (无描边).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from field import make_field, eds_points, PHASE_COLORS, N

W_MM, H_MM = 40.0, 30.0

phase, gray = make_field()
xs, ys, pids = eds_points()

fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

# 极淡底图: 满幅铺满面板 (aspect='auto'), 与散点共用像素坐标系
ax.imshow(
    gray,
    cmap="gray",
    vmin=0.0,
    vmax=1.0,
    alpha=0.18,
    interpolation="nearest",
    aspect="auto",
    zorder=1,
)

colors = np.asarray(PHASE_COLORS)[pids]
ax.scatter(xs, ys, s=14, c=colors, linewidths=0, zorder=2)

ax.set_xlim(-0.5, N - 0.5)
ax.set_ylim(N - 0.5, -0.5)

fig.savefig("panels/panel_eds.png", dpi=300)
