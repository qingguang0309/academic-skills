"""panel_seg —— 像素级相分割结果(40x28 mm, 满幅无边距).

ListedColormap(PHASE_COLORS) 渲染 phase, 叠加 find_boundaries(mode="thin")
细白色相界 (alpha=0.9)。相场来自共享 field.make_field(), 与其他面板同一视场。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from skimage.segmentation import find_boundaries

from field import make_field, PHASE_COLORS

W_MM, H_MM = 40.0, 28.0

phase, _ = make_field()

# 相界: thin 模式, 单像素宽
bnd = find_boundaries(phase, mode="thin")
overlay = np.zeros(phase.shape + (4,), dtype=float)
overlay[bnd] = (1.0, 1.0, 1.0, 0.9)

fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

ax.imshow(phase, cmap=ListedColormap(PHASE_COLORS), vmin=0, vmax=3,
          interpolation="nearest", aspect="auto")
ax.imshow(overlay, interpolation="nearest", aspect="auto")

fig.savefig("panels/panel_seg.png", dpi=300)
