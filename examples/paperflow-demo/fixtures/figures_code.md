```python
"""Topic figure for the NiFe-LDH OER demo (illustrative synthetic data).
Self-contained: numpy + matplotlib only; writes figures/*.png + figures/manifest.json."""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(3)
BLUE, VERM, GRAY = "#0072B2", "#D55E00", "0.45"
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.linewidth": 0.6, "lines.linewidth": 1.0,
    "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True, "ytick.right": True,
    "legend.frameon": False, "mathtext.fontset": "stixsans",
})

fig, axd = plt.subplot_mosaic([["a", "b"], ["c", "d"]],
                              figsize=(175 / 25.4, 120 / 25.4), layout="constrained")

# (a) XRD: stacked patterns + reference sticks
ax = axd["a"]
tt = np.linspace(5, 80, 3000)
def peaks(centers, heights, w=0.35):
    y = np.zeros_like(tt)
    for c, h in zip(centers, heights):
        y += h / (1 + ((tt - c) / w) ** 2)
    return y
ldh_pos = [11.4, 22.9, 34.4, 38.8, 46.0, 59.9, 61.2]
ldh_int = [1.00, 0.45, 0.38, 0.30, 0.22, 0.25, 0.22]
noh_pos = [19.3, 33.1, 38.5, 52.1, 59.1, 62.7]
noh_int = [0.85, 0.55, 1.00, 0.35, 0.45, 0.30]
off = 1.35
ax.plot(tt, peaks(ldh_pos, ldh_int) + 0.05 + 0.012 * rng.standard_normal(tt.size) + off,
        lw=0.8, color=BLUE)
ax.plot(tt, peaks(noh_pos, noh_int) + 0.05 + 0.012 * rng.standard_normal(tt.size) + 2 * off,
        lw=0.8, color=VERM)
ax.text(78, off + 0.45, "NiFe-LDH", ha="right", color=BLUE)
ax.text(78, 2 * off + 0.45, r"Ni(OH)$_2$", ha="right", color=VERM)
for p, hkl, h, dy in zip(ldh_pos[:4], ["(003)", "(006)", "(012)", "(015)"],
                         ldh_int[:4], [0.14, 0.14, 0.14, 0.50]):
    ax.text(p, h + off + dy, hkl, ha="center", fontsize=7.5)
ax.vlines(ldh_pos, 0, [i * 0.9 for i in ldh_int], color="0.35", lw=0.8)
ax.text(78, 0.75, "LDH reference", ha="right", color="0.35", fontsize=7.5)
ax.set_xlim(5, 80); ax.set_ylim(0, 2 * off + 1.6); ax.set_yticks([])
ax.set_xlabel(r"2$\theta$ (degree)"); ax.set_ylabel("Intensity (a.u.)")

# (b) XPS Ni 2p: raw + envelope + components
ax = axd["b"]
be = np.linspace(848, 890, 1200)
g = lambda c, h, w: h * np.exp(-((be - c) / w) ** 2)
bg = 0.12 + 0.010 * (be - 848) + 0.25 / (1 + np.exp(-(be - 866) / 2.5))
ni2 = g(855.3, 1.00, 1.15) + g(872.9, 0.48, 1.35)
ni3 = g(856.9, 0.55, 1.25) + g(874.6, 0.26, 1.45)
sat = g(861.4, 0.42, 2.6) + g(879.6, 0.24, 2.8)
env = bg + ni2 + ni3 + sat
raw = env + 0.022 * rng.standard_normal(be.size)
ax.plot(be[::6], raw[::6], "o", ms=1.8, mfc="none", mec="0.2", mew=0.4, label="Raw")
ax.plot(be, env, color="0.1", lw=1.0, label="Fit")
for comp, c in [(ni2, BLUE), (ni3, VERM), (sat, "#E69F00")]:
    ax.fill_between(be, bg, comp + bg, alpha=0.35, color=c, lw=0)
ax.plot(be, bg, "--", lw=0.7, color="0.55")
yv = lambda c: env[np.argmin(np.abs(be - c))]
ax.annotate(r"Ni$^{2+}$", xy=(854.0, yv(855.3) + 0.05), ha="center", color=BLUE)
ax.annotate(r"Ni$^{3+}$", xy=(858.9, yv(856.9) + 0.10), ha="center", color=VERM)
ax.annotate("sat.", xy=(861.4, yv(861.4) + 0.06), ha="center", color="#E69F00")
ax.text(0.035, 0.92, "Ni 2p", transform=ax.transAxes, fontweight="bold")
ax.invert_xaxis(); ax.set_ylim(0, float(raw.max()) * 1.22); ax.set_yticks([])
ax.set_xlabel("Binding energy (eV)"); ax.set_ylabel("Intensity (a.u.)")
ax.legend(loc="upper left", bbox_to_anchor=(0.015, 0.86))

# (c) LSV with eta10 annotation
ax = axd["c"]
E = np.linspace(1.20, 1.75, 500)
lsv = lambda onset, b: np.clip(0.02 * np.exp(np.clip((E - onset) / b, -50, 50)), 0, 320)
j_ldh, j_ruo, j_noh = lsv(1.400, 0.0165), lsv(1.440, 0.0182), lsv(1.520, 0.0282)
eta10 = E[np.searchsorted(j_ldh, 10)] - 1.23
ax.plot(E, j_ldh, color=BLUE, label="NiFe-LDH")
ax.plot(E, j_ruo, color=GRAY, ls="-.", label=r"RuO$_2$")
ax.plot(E, j_noh, color=VERM, ls="--", label=r"Ni(OH)$_2$")
ax.axhline(10, color="0.6", lw=0.6, ls=":")
ax.text(1.213, 13, r"10 mA cm$^{-2}$", color="0.4", fontsize=7.5)
ax.annotate(rf"$\eta_{{10}}$ = {eta10 * 1000:.0f} mV", xy=(1.23 + eta10, 10),
            xytext=(1.325, 46), color=BLUE,
            arrowprops=dict(arrowstyle="-", lw=0.6, color=BLUE, shrinkB=2))
ax.set_xlim(1.20, 1.70); ax.set_ylim(0, 100)
ax.set_xlabel("Potential (V vs. RHE)"); ax.set_ylabel(r"Current density (mA cm$^{-2}$)")
ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.98))

# (d) Tafel with end-of-line slope labels
ax = axd["d"]
for j, c, ls in [(j_ldh, BLUE, "-"), (j_ruo, GRAY, "-."), (j_noh, VERM, "--")]:
    m = (j > 0.5) & (j < 50)
    lj, eta = np.log10(j[m]), (E[m] - 1.23) * 1000
    ax.plot(lj, eta, color=c, ls=ls, lw=1.0)
    fm = (lj > 0) & (lj < np.log10(20))
    k, b = np.polyfit(lj[fm], eta[fm], 1)
    xf = np.array([lj[fm].min() - 0.15, lj[fm].max() + 0.15])
    ax.plot(xf, k * xf + b, ls=":", lw=0.7, color="0.3")
    ax.text(1.82, k * 1.82 + b, rf"{k:.0f} mV dec$^{{-1}}$", color=c, va="center", fontsize=7.5)
ax.set_xlim(-0.4, 2.9); ax.set_ylim(140, 540)
ax.set_xlabel(r"log |$j$| (mA cm$^{-2}$)"); ax.set_ylabel("Overpotential (mV)")

for key, ax in axd.items():
    ax.annotate(key, xy=(0, 1), xycoords="axes fraction", xytext=(-14, 4),
                textcoords="offset points", fontsize=9, fontweight="bold",
                ha="right", va="bottom", annotation_clip=False)

outdir = Path("figures")
outdir.mkdir(exist_ok=True)
fig.savefig(outdir / "fig_oer_generated.png", dpi=300)
manifest = [{
    "file": "fig_oer_generated.png",
    "label": "oer",
    "caption": ("Structural and electrochemical characterization of NiFe-LDH "
                "(illustrative synthetic data): (a) XRD patterns with the LDH reference; "
                "(b) Ni 2p XPS with peak deconvolution; (c) OER polarization curves with "
                "the eta10 annotation; (d) Tafel analysis."),
}]
(outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("figures generated:", [m["file"] for m in manifest])
```
