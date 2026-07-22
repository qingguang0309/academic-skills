"""panel_bse: 合成 BSE 显微图(满幅灰度,无标注)。40x30 mm, 300 dpi."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from field import make_field

W_MM, H_MM = 40, 30

_, gray = make_field()

fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")
ax.imshow(gray, cmap="gray", vmin=0, vmax=1, interpolation="nearest", aspect="auto")
fig.savefig("panels/panel_bse.png", dpi=300)
