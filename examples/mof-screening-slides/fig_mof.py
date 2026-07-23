# MOF 开题 deck 配图(合成示意数据,paper-figures 规范:Okabe-Ito、带单位、图上标注关键发现)
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OI = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73",
      "sky": "#56B4E9", "verm": "#D55E00", "gray": "#8C8C8C"}
plt.rcParams.update({
    "font.family": "Arial", "font.size": 11.5,
    "axes.linewidth": 0.9, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True, "axes.grid": False,
    "figure.dpi": 300, "savefig.dpi": 300,
})
rng = np.random.default_rng(7)

# ---------------- Fig 1: 筛选漏斗 + Pareto 散点 ----------------
fig, (a, b) = plt.subplots(1, 2, figsize=(8.2, 3.15), constrained_layout=True)

stages = ["CoRE MOF 2019\n(all)", "Geometric\nfilter", "GCMC\ncoarse screen",
          "ML-guided\nrefinement", "DFT + stability\nshortlist"]
counts = [137953, 46800, 8200, 620, 50]
y = np.arange(len(stages))[::-1]
colors = [OI["gray"], OI["sky"], OI["blue"], OI["orange"], OI["verm"]]
a.barh(y, counts, color=colors, height=0.62, log=True)
for yi, c in zip(y, counts):
    a.text(c * 1.25, yi, f"{c:,}", va="center", fontsize=10.5)
a.set_yticks(y, stages, fontsize=9.5)
a.set_xlim(20, 8e5)
a.set_xlabel("Number of candidate structures (log scale)")
a.text(0.34, 0.06, "137 953 → 50:  ≈2 800× reduction", transform=a.transAxes,
       fontsize=10.5, fontweight="bold", color=OI["verm"])
a.set_title("(a)  Four-stage screening funnel", loc="left", fontsize=12)

n = 900
sel = 10 ** rng.normal(1.35, 0.42, n)
upt = np.clip(rng.normal(1.9, 0.85, n) + 0.35 * np.log10(sel), 0.05, None)
b.scatter(sel, upt, s=9, c=OI["gray"], alpha=0.35, lw=0, label="Screened MOFs")
sf = np.array(sorted(zip(sel, upt)))
pareto, best = [], -1
for s, u in sf[::-1]:
    if u > best: pareto.append((s, u)); best = u
pareto = np.array(pareto)
b.plot(pareto[:, 0], pareto[:, 1], "-o", color=OI["orange"], ms=4.5, lw=1.6,
       label="Pareto front")
b.axvspan(150, 1200, ymin=0.62, color=OI["green"], alpha=0.12)
b.text(165, 5.15, "target region\nS ≥ 150, q ≥ 4 mmol g$^{-1}$",
       fontsize=9.5, color=OI["green"], fontweight="bold")
b.set_xscale("log"); b.set_xlim(3, 1200); b.set_ylim(0, 6.2)
b.set_xlabel("CO$_2$/N$_2$ selectivity (15:85, 313 K)")
b.set_ylabel("CO$_2$ uptake (mmol g$^{-1}$, 0.15 bar)")
b.legend(frameon=False, fontsize=9.5, loc="upper left")
b.set_title("(b)  Uptake–selectivity landscape", loc="left", fontsize=12)
fig.savefig("assets/fig_screening.png")
plt.close(fig)

# ---------------- Fig 2: 等温线 + ML parity ----------------
fig, (a, b) = plt.subplots(1, 2, figsize=(8.2, 3.15), constrained_layout=True)

p = np.linspace(0, 1.0, 120)
def dsl(p, q1, b1, q2, b2):
    return q1 * b1 * p / (1 + b1 * p) + q2 * b2 * p / (1 + b2 * p)
a.plot(p, dsl(p, 3.1, 42, 2.2, 2.5), color=OI["verm"], lw=2, label="CO$_2$, candidate MOF")
a.plot(p, dsl(p, 2.2, 18, 1.8, 1.2), color=OI["verm"], lw=1.4, ls="--", label="CO$_2$, MOF-74 ref")
a.plot(p, dsl(p, 0.9, 0.35, 0.4, 0.1), color=OI["blue"], lw=2, label="N$_2$, candidate MOF")
a.axvline(0.15, color=OI["gray"], lw=0.9, ls=":")
a.annotate("flue-gas\n$p_{CO_2}$ = 0.15 bar", xy=(0.15, 2.55), xytext=(0.32, 1.6),
           fontsize=9.5, arrowprops=dict(arrowstyle="->", lw=0.9, color=OI["gray"]))
a.set_xlabel("Pressure (bar)"); a.set_ylabel("Uptake (mmol g$^{-1}$)")
a.set_xlim(0, 1); a.set_ylim(0, 4.2)
a.legend(frameon=False, fontsize=9, loc="lower right")
a.set_title("(a)  Simulated isotherms, 313 K", loc="left", fontsize=12)

m = 320
truth = np.clip(rng.gamma(2.6, 0.75, m), 0.05, 6)
pred = np.clip(truth + rng.normal(0, 0.22 + 0.05 * truth, m), 0, 6.5)
b.scatter(truth, pred, s=11, c=OI["blue"], alpha=0.45, lw=0)
b.plot([0, 6.5], [0, 6.5], color=OI["gray"], lw=1.1)
b.fill_between([0, 6.5], [-0.5, 6.0], [0.5, 7.0], color=OI["gray"], alpha=0.10)
ss = 1 - np.sum((pred - truth) ** 2) / np.sum((truth - truth.mean()) ** 2)
b.text(0.05, 0.95, f"$R^2$ = {ss:.2f}\nMAE = {np.mean(np.abs(pred-truth)):.2f} mmol g$^{{-1}}$",
       transform=b.transAxes, fontsize=10.5, fontweight="bold", color=OI["blue"],
       va="top")
b.text(0.97, 0.06, "±0.5 mmol g$^{-1}$ band", transform=b.transAxes,
       fontsize=9, color=OI["gray"], ha="right")
b.set_xlabel("GCMC uptake (mmol g$^{-1}$)")
b.set_ylabel("ML-predicted uptake (mmol g$^{-1}$)")
b.set_xlim(0, 6.5); b.set_ylim(0, 6.5)
b.set_title("(b)  Surrogate-model parity", loc="left", fontsize=12)
fig.savefig("assets/fig_isotherm.png")
plt.close(fig)
print("figures written")
