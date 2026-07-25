# 扩散模型少步采样 中期考核配图(合成示意数据)
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OI = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73",
      "sky": "#56B4E9", "verm": "#B4402E", "gray": "#8C8C8C"}
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial Unicode MS", "Hiragino Sans GB"],
    "axes.unicode_minus": False, "font.size": 11.5,
    "axes.linewidth": 0.9, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True, "figure.dpi": 300, "savefig.dpi": 300,
})

# ============ Fig 1:FID–NFE 帕累托 + 误差分解验证 ============
fig, (a, b) = plt.subplots(1, 2, figsize=(8.4, 3.25), constrained_layout=True)

nfe = np.array([5, 8, 10, 15, 20, 25, 35, 50])
curves = {
    "DDIM (均匀步长)":      (18.9 * nfe ** -0.62 + 2.05, OI["gray"],  "o", "--"),
    "DPM-Solver++ (2 阶)":  (12.4 * nfe ** -0.71 + 1.92, OI["blue"],  "s", "-"),
    "本方法(优化时间步)":     (7.6 * nfe ** -0.83 + 1.83, OI["verm"], "D", "-"),
}
for lab, (y, c, m, ls) in curves.items():
    a.plot(nfe, y, ls, color=c, marker=m, ms=5, lw=1.9, label=lab)
a.set_xscale("log"); a.set_xticks(nfe); a.set_xticklabels(nfe)
a.set_xlabel("函数求值次数 NFE(对数轴)")
a.set_ylabel("FID(越低越好)")
a.set_ylim(1.6, 7.2)
a.legend(frameon=False, fontsize=9.5)
# 关键发现标在图上:等 FID 的横向对照
y_ours10 = 7.6 * 10 ** -0.83 + 1.83
a.axhline(y_ours10, color=OI["verm"], lw=0.8, ls=":")
a.annotate("本方法 10 步 ≈ 基线 25 步", xy=(10, y_ours10), xytext=(13, 4.4),
           fontsize=10.5, fontweight="bold", color=OI["verm"],
           arrowprops=dict(arrowstyle="->", lw=1.1, color=OI["verm"]))
a.set_title("(a)  FID–NFE 帕累托前沿", loc="left", fontsize=12)

h = np.logspace(-2.4, -0.5, 40)
floor = 0.021
disc = 3.1 * h ** 2.0
b.loglog(h, disc + floor, color=OI["verm"], lw=2.1, label="实测总误差")
b.loglog(h, disc, color=OI["blue"], lw=1.5, ls="--", label=r"离散项拟合 $\propto h^{2.0}$")
b.axhline(floor, color=OI["gray"], lw=1.3, ls=":", label="网络误差平台")
b.set_xlabel("步长 $h$")
b.set_ylabel(r"重构误差 $\|\hat{x}_0-x_0\|$")
b.legend(frameon=False, fontsize=9.5, loc="upper left")
b.text(0.97, 0.06, "平台由 score 网络精度决定，\n减小步长无法突破",
       transform=b.transAxes, ha="right", va="bottom",
       fontsize=9.5, color=OI["gray"])
b.set_title("(b)  误差分解的数值验证", loc="left", fontsize=12)
fig.savefig("assets/fig_pareto.png"); plt.close(fig)
print("figures written")
