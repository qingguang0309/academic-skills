# Figure-generation code (illustrative synthetic data)

Single self-contained script generating both report figures and the manifest
into `./figures/` (run from the report root). Imports are limited to numpy,
scipy, matplotlib (Agg) and skimage; fully deterministic (seed 42); no network.

```python
#!/usr/bin/env python3
"""Illustrative figures for the BSE-EDS multimodal fusion research-plan report.

Figure 1 (fig1_pipeline.png)  : synthetic BSE field, sparse EDS sampling,
                                SLIC superpixel graph, ground-truth phase map.
Figure 2 (fig2_targets.png)   : illustrative target curves (IoU vs. EDS
                                coverage) and machine-time bars.

All data are SYNTHETIC and ILLUSTRATIVE (project targets, not measurements).
Deterministic: np.random.default_rng(42). Imports: numpy / scipy / matplotlib
(Agg) / skimage only. Outputs 300-dpi PNGs + manifest.json into ./figures/.
"""

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import center_of_mass, distance_transform_edt, gaussian_filter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from skimage.segmentation import find_boundaries, slic

# ----------------------------------------------------------------------------
# Global publication style
# ----------------------------------------------------------------------------
MM = 1.0 / 25.4  # mm -> inch
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 8.0,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8.0,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "axes.linewidth": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "savefig.dpi": 300,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

# Okabe-Ito palette
OI = {
    "black": "#000000", "orange": "#E69F00", "skyblue": "#56B4E9",
    "green": "#009E73", "yellow": "#F0E442", "blue": "#0072B2",
    "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#999999",
}
# Phase order: 0 pore, 1 hydrate matrix, 2 metakaolin, 3 slag, 4 clinker
PHASE_COLORS = [OI["black"], OI["skyblue"], OI["orange"], OI["green"], OI["vermillion"]]
PHASE_NAMES = ["Pore", "Hydrate matrix", "Metakaolin", "Slag", "Clinker"]

OUT = Path("figures")
OUT.mkdir(exist_ok=True)

rng = np.random.default_rng(42)

# ----------------------------------------------------------------------------
# Synthetic blended-cement microstructure (gaussian-filtered random fields)
# ----------------------------------------------------------------------------
H, W = 360, 480


def blobs(sigma, frac):
    b = gaussian_filter(rng.standard_normal((H, W)), sigma)
    return b > np.quantile(b, 1.0 - frac)


phase = np.ones((H, W), int)          # 1: hydrate matrix everywhere
phase[blobs(11, 0.16)] = 2            # metakaolin
phase[blobs(8, 0.15)] = 3             # slag
phase[blobs(14, 0.12)] = 4            # clinker (bright)
phase[blobs(5, 0.07)] = 0             # pores on top (dark)

# BSE gray levels: metakaolin (0.56) and slag (0.62) are deliberately CLOSE
gray_levels = np.array([0.05, 0.44, 0.56, 0.62, 0.90])
bse = gray_levels[phase]
bse = bse + 0.05 * gaussian_filter(rng.standard_normal((H, W)), 2.5) \
          + 0.02 * rng.standard_normal((H, W))
bse = gaussian_filter(np.clip(bse, 0, 1), 0.6)

# Sparse EDS sampling points (<=5 % coverage, solid phases only)
ys, xs = np.where(phase > 0)
pick = rng.choice(len(xs), 60, replace=False)
dots = np.stack([xs[pick], ys[pick]], axis=1)  # (x, y)

# SLIC superpixels + region-adjacency graph on the BSE image
labels = slic(bse, n_segments=60, compactness=0.08, sigma=1.5,
              channel_axis=None, start_label=0)
sp_bounds = find_boundaries(labels, mode="thick")
ids = np.unique(labels)
cent = {i: center_of_mass(labels == i) for i in ids}   # (y, x)
adj = set()
a0, a1 = labels[:, :-1], labels[:, 1:]
adj |= {tuple(sorted(p)) for p in
        np.unique(np.stack([a0[a0 != a1], a1[a0 != a1]], 1), axis=0)}
v0, v1 = labels[:-1, :], labels[1:, :]
adj |= {tuple(sorted(p)) for p in
        np.unique(np.stack([v0[v0 != v1], v1[v0 != v1]], 1), axis=0)}
sampled = {}                                            # superpixel -> phase
for dx, dy in dots:
    sampled.setdefault(labels[dy, dx], phase[dy, dx])

gt_bounds = find_boundaries(phase, mode="thin")


def interior_point(mask, rows=slice(None), cols=slice(None)):
    """Deepest interior pixel of a mask, restricted to a subregion so that
    annotation leader lines stay short."""
    sub = np.zeros_like(mask)
    sub[rows, cols] = mask[rows, cols]
    if not sub.any():
        sub = mask
    d = distance_transform_edt(sub)
    y, x = np.unravel_index(np.argmax(d), d.shape)
    return int(x), int(y)


def style_image_axes(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_linewidth(0.8)
        s.set_color("black")


def panel_letter(ax, letter, x=-0.02, y=1.015):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=10,
            fontweight="bold", ha="left", va="bottom")


# ----------------------------------------------------------------------------
# Figure 1 -- pipeline panels (a)-(d), ~175 x 150 mm
# ----------------------------------------------------------------------------
fig = plt.figure(figsize=(175 * MM, 150 * MM))
gs = fig.add_gridspec(2, 2, left=0.045, right=0.985, top=0.925, bottom=0.095,
                      wspace=0.10, hspace=0.26)

# (a) synthetic BSE micrograph -----------------------------------------------
ax = fig.add_subplot(gs[0, 0])
ax.imshow(bse, cmap="gray", vmin=0, vmax=1, interpolation="bilinear")
style_image_axes(ax)
panel_letter(ax, "(a)")
ax.set_title("Synthetic BSE micrograph (MK ≈ slag)", pad=4)

top, bot = slice(0, H // 2), slice(H // 2, H)
lef, rig = slice(0, W // 2), slice(W // 2, W)
anno = [("Pore", interior_point(phase == 0, bot, lef), (0.08, 0.06)),
        ("Clinker", interior_point(phase == 4, slice(H // 4, H // 2), rig),
         (0.82, 0.92)),
        ("Metakaolin", interior_point(phase == 2, top, lef), (0.12, 0.92)),
        ("Slag", interior_point(phase == 3, bot, rig), (0.88, 0.08))]
for txt, (px, py), (fx, fy) in anno:
    t = ax.annotate(txt, xy=(px, py), xycoords="data",
                    xytext=(fx, fy), textcoords="axes fraction",
                    fontsize=7, color="white", fontweight="bold",
                    ha="center", va="center",
                    arrowprops=dict(arrowstyle="-", color="white", lw=0.9,
                                    shrinkA=2, shrinkB=2))
    t.set_path_effects([pe.withStroke(linewidth=1.8, foreground="black")])
    t.arrow_patch.set_path_effects(
        [pe.withStroke(linewidth=2.0, foreground="black")])

# (b) faint field + sparse EDS points ----------------------------------------
ax = fig.add_subplot(gs[0, 1])
ax.imshow(np.ones_like(bse), cmap="gray", vmin=0, vmax=1)
ax.imshow(bse, cmap="gray", vmin=0, vmax=1, alpha=0.28, interpolation="bilinear")
ax.scatter(dots[:, 0], dots[:, 1],
           c=[PHASE_COLORS[phase[y, x]] for x, y in dots],
           s=16, lw=0.4, edgecolors="white", zorder=3)
ax.set_xlim(0, W); ax.set_ylim(H, 0)
style_image_axes(ax)
panel_letter(ax, "(b)")
ax.set_title("Sparse EDS sampling (≤5% coverage)", pad=4)

# (c) SLIC superpixels + region-adjacency graph ------------------------------
ax = fig.add_subplot(gs[1, 0])
ax.imshow(bse, cmap="gray", vmin=0, vmax=1, alpha=0.45, interpolation="bilinear")
ov = np.zeros((H, W, 4))
ov[sp_bounds] = matplotlib.colors.to_rgba(OI["yellow"], 0.9)
ax.imshow(ov)
for i, j in adj:
    (y1, x1), (y2, x2) = cent[i], cent[j]
    ax.plot([x1, x2], [y1, y2], color="#444444", lw=0.6, alpha=0.55, zorder=3)
for i in ids:
    y, x = cent[i]
    if i in sampled:
        ax.scatter(x, y, s=42, c=PHASE_COLORS[sampled[i]],
                   edgecolors="white", linewidths=1.0, zorder=5)
    else:
        ax.scatter(x, y, s=9, c=OI["grey"], lw=0, zorder=4, alpha=0.95)
ax.set_xlim(0, W); ax.set_ylim(H, 0)
style_image_axes(ax)
panel_letter(ax, "(c)")
ax.set_title("SLIC superpixels + adjacency graph", pad=4)

# (d) ground-truth phase map --------------------------------------------------
ax = fig.add_subplot(gs[1, 1])
ax.imshow(phase, cmap=ListedColormap(PHASE_COLORS), interpolation="nearest")
ovb = np.zeros((H, W, 4))
ovb[gt_bounds] = matplotlib.colors.to_rgba("#FFFFFF", 0.9)
ax.imshow(ovb)
style_image_axes(ax)
panel_letter(ax, "(d)")
ax.set_title("Ground-truth phase map", pad=4)

# shared legend + illustrative note ------------------------------------------
handles = [Patch(fc=c, ec="black", lw=0.5, label=n)
           for c, n in zip(PHASE_COLORS, PHASE_NAMES)]
handles += [Line2D([], [], marker="o", ls="none", ms=4, mfc=OI["grey"],
                   mec="none", label="Unsampled node")]
fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.035, 0.005),
           ncol=6, frameon=False, handlelength=1.2, columnspacing=1.1,
           handletextpad=0.5)
fig.text(0.985, 0.022, "Synthetic illustrative data", ha="right", va="center",
         fontsize=7, style="italic", color="#666666")
fig.savefig(OUT / "fig1_pipeline.png")
plt.close(fig)
print("saved", OUT / "fig1_pipeline.png")

# ----------------------------------------------------------------------------
# Figure 2 -- illustrative targets, ~175 x 70 mm
# ----------------------------------------------------------------------------
C_BASE, C_RAND, C_ACT = "#555555", OI["blue"], OI["vermillion"]

fig = plt.figure(figsize=(175 * MM, 70 * MM))
gs = fig.add_gridspec(1, 2, left=0.075, right=0.985, top=0.90, bottom=0.21,
                      wspace=0.30, width_ratios=[1.45, 1.0])

# (a) IoU vs EDS coverage -----------------------------------------------------
ax = fig.add_subplot(gs[0, 0])
x = np.linspace(0, 8, 240)
iou_act = 0.55 + 0.27 * (1 - np.exp(-x / 1.6))
iou_rnd = 0.55 + 0.20 * (1 - np.exp(-x / 5.5))
xm = np.array([0.5, 1, 2, 3, 4, 5, 6, 7, 8])

ax.axhline(0.55, color=C_BASE, lw=1.3, ls="--", zorder=2)
ax.fill_between(x, iou_rnd - 0.018, iou_rnd + 0.018, color=C_RAND, alpha=0.15, lw=0)
ax.fill_between(x, iou_act - 0.018, iou_act + 0.018, color=C_ACT, alpha=0.15, lw=0)
ax.plot(x, iou_rnd, color=C_RAND, lw=1.6, zorder=3)
ax.plot(x, iou_act, color=C_ACT, lw=1.6, zorder=3)
ax.plot(xm, 0.55 + 0.20 * (1 - np.exp(-xm / 5.5)), "s", color=C_RAND,
        ms=3.5, zorder=4)
ax.plot(xm, 0.55 + 0.27 * (1 - np.exp(-xm / 1.6)), "o", color=C_ACT,
        ms=3.5, zorder=4)

# +20 pp @ <=5% target bracket
ax.plot([5, 5], [0.45, 0.55], color="#888888", lw=0.7, ls=":", zorder=1)
ax.annotate("", xy=(5, 0.75), xytext=(5, 0.55),
            arrowprops=dict(arrowstyle="<->", color="black", lw=1.1,
                            shrinkA=0, shrinkB=0), zorder=5)
ax.plot([4.85, 5.15], [0.75, 0.75], color="black", lw=1.0, zorder=5)
ax.plot([4.85, 5.15], [0.55, 0.55], color="black", lw=1.0, zorder=5)
ax.text(5.3, 0.61, "target:\n+20 pp @ ≤5%", fontsize=7.2,
        ha="left", va="center")

ax.set_xlim(0, 8)
ax.set_ylim(0.45, 0.95)
ax.set_xlabel("EDS coverage (% of field area)")
ax.set_ylabel("IoU, gray-overlapping phases (MK, slag)")
ax.legend([Line2D([], [], color=C_BASE, lw=1.3, ls="--"),
           Line2D([], [], color=C_RAND, lw=1.6, marker="s", ms=3.5),
           Line2D([], [], color=C_ACT, lw=1.6, marker="o", ms=3.5)],
          ["BSE-only baseline", "Fusion + random sampling",
           "Fusion + active sampling"],
          loc="upper left", frameon=False, handlelength=1.8,
          labelspacing=0.35, borderaxespad=0.3)
panel_letter(ax, "(a)", x=-0.155, y=1.02)

# (b) EDS machine time at equal accuracy -------------------------------------
ax = fig.add_subplot(gs[0, 1])
cats = ["Dense\nmapping", "Random\nsparse", "Active\nsampling"]
vals = [100, 70, 48]
cols = [OI["grey"], C_RAND, C_ACT]
bars = ax.bar(np.arange(3), vals, width=0.62, color=cols,
              edgecolor="black", linewidth=0.8, zorder=3)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v - 4, f"{v}%", ha="center",
            va="top", fontsize=7.5, color="white", fontweight="bold", zorder=4)
ax.axhline(50, color="black", lw=0.9, ls="--", zorder=2)
# dimension bracket: dense (100%) -> active (48%), i.e. the -50% target
ax.annotate("", xy=(0, 108), xytext=(2, 108),
            arrowprops=dict(arrowstyle="<->", color="black", lw=0.9,
                            shrinkA=0, shrinkB=0), zorder=4)
ax.plot([0, 0], [102, 108], color="black", lw=0.7, ls=":", zorder=4)
ax.plot([2, 2], [50, 108], color="black", lw=0.7, ls=":", zorder=4)
ax.text(1, 111, "−50% machine time (target ≤50%)", fontsize=7.2,
        ha="center", va="bottom")
ax.set_xticks(np.arange(3))
ax.set_xticklabels(cats)
ax.set_xlim(-0.55, 2.55)
ax.set_ylim(0, 124)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_ylabel("EDS machine time (% of dense)")
ax.tick_params(axis="x", length=0)
panel_letter(ax, "(b)", x=-0.20, y=1.02)

fig.text(0.985, 0.025, "Illustrative target curves and bars, not measurements",
         ha="right", va="center", fontsize=7, style="italic", color="#666666")
fig.savefig(OUT / "fig2_targets.png")
plt.close(fig)
print("saved", OUT / "fig2_targets.png")

# ----------------------------------------------------------------------------
# Manifest
# ----------------------------------------------------------------------------
manifest = [
    {
        "file": "fig1_pipeline.png",
        "caption": (
            "Illustrative overview of the multimodal BSE-EDS fusion pipeline "
            "on a synthetic blended-cement microstructure. (a) Synthetic "
            "backscattered-electron (BSE) micrograph in which metakaolin and "
            "slag occupy nearly identical gray levels, illustrating the "
            "gray-level degeneracy that defeats BSE-only segmentation; pores "
            "appear dark and clinker bright. (b) Sparse EDS sampling points "
            "(coverage of at most 5% of the field) colored by true phase. "
            "(c) SLIC superpixel tessellation of the BSE image with the "
            "region-adjacency graph used by the graph branch: superpixels "
            "containing an EDS sample appear as filled phase-colored nodes, "
            "unsampled superpixels as small gray nodes to be completed by "
            "graph propagation. (d) Ground-truth phase map of the same field "
            "in the same palette, with thin white phase boundaries. All "
            "panels show synthetic, illustrative data generated from "
            "gaussian-filtered random fields; they are not measurements."
        ),
        "label": "pipeline",
    },
    {
        "file": "fig2_targets.png",
        "caption": (
            "Illustrative quantitative targets of the project; the curves and "
            "bars are schematic targets, not measured results. (a) Intended "
            "IoU of the gray-overlapping phases (metakaolin, slag) versus EDS "
            "coverage: the BSE-only baseline stays near 0.55 regardless of "
            "architecture tuning, fusion with random sparse sampling improves "
            "slowly, and fusion with uncertainty-driven active sampling is "
            "targeted to exceed 0.75 before 5% coverage, meeting the +20 "
            "percentage-point target at no more than 5% coverage. "
            "(b) Intended EDS machine time required to reach equal target "
            "accuracy, normalized to dense full-field mapping (100%): active "
            "sampling is targeted to require at most 50% of the dense-mapping "
            "time, a reduction of at least 50%."
        ),
        "label": "targets",
    },
]
with open(OUT / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
print("saved", OUT / "manifest.json")
```
