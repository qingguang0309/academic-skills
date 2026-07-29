# 退役 LFP 回收评估报告的配图（合成示意数据）
# Word 是单栏 15.8 cm 版心，出图宽度按 15 cm 给，字号按最终印刷尺寸设——
# 不能照搬 PPT 的图：PPT 投影距离远、字号要大，Word 是手持阅读距离。
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PKU_RED, MID, GREY = "#94070A", "#B5544F", "#6E6E6E"
GOLD = "#C9A227"
CM = 1 / 2.54
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial Unicode MS", "Hiragino Sans GB"],
    "axes.unicode_minus": False, "font.size": 9,
    "axes.linewidth": 0.8, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})

# ── 图 3-1：温度与酸浓度对锂浸出率的影响（分组柱） ──
fig, ax = plt.subplots(figsize=(15 * CM, 6.2 * CM))
temps = ["60 ℃", "75 ℃", "90 ℃"]
series = {"1.0 mol·L⁻¹": [71.2, 82.4, 88.1],
          "2.0 mol·L⁻¹": [84.6, 92.8, 95.4],
          "3.0 mol·L⁻¹": [88.3, 94.1, 95.9]}
x = np.arange(len(temps)); w = 0.26
for i, (k, v) in enumerate(series.items()):
    b = ax.bar(x + (i - 1) * w, v, w, label=k,
               color=[GREY, MID, PKU_RED][i], edgecolor="white", linewidth=0.5)
    ax.bar_label(b, fmt="%.1f", fontsize=7.5, padding=2)
ax.set_xticks(x, temps); ax.set_ylabel("锂浸出率 (%)")
ax.set_ylim(60, 104)
ax.legend(frameon=False, ncol=3, fontsize=8, loc="lower right", title="硫酸浓度",
          title_fontsize=8)
ax.grid(axis="y", color="#E0E0E0", lw=0.5); ax.set_axisbelow(True)
fig.savefig("assets/fig_leach.png"); plt.close(fig)

# ── 图 3-2：收缩核模型拟合（双子图，判定控制步骤） ──
fig, axes = plt.subplots(1, 2, figsize=(15 * CM, 5.8 * CM))
t = np.array([10, 20, 30, 45, 60, 90, 120])
for ax, (title, ys, r2) in zip(axes, [
    ("界面化学反应控制", {"60 ℃": 0.0031, "75 ℃": 0.0048, "90 ℃": 0.0067}, 0.993),
    ("内扩散控制", {"60 ℃": 0.00042, "75 ℃": 0.00071, "90 ℃": 0.00105}, 0.951),
]):
    for j, (lab, k) in enumerate(ys.items()):
        y = k * t + np.array([0, .002, -.003, .004, -.002, .003, -.001])[:len(t)]
        ax.plot(t, y, "o", ms=3.5, color=[GREY, MID, PKU_RED][j], label=lab)
        ax.plot(t, k * t, "-", lw=1.2, color=[GREY, MID, PKU_RED][j])
    ax.set_xlabel("浸出时间 (min)")
    ax.set_title(f"{title}   $R^2$ = {r2:.3f}", fontsize=9, pad=6)
    ax.grid(color="#E0E0E0", lw=0.5); ax.set_axisbelow(True)
axes[0].set_ylabel(r"$1-(1-x)^{1/3}$")
axes[1].set_ylabel(r"$1-3(1-x)^{2/3}+2(1-x)$")
axes[0].legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig("assets/fig_kinetics.png"); plt.close(fig)

# ── 图 4-1：处理成本构成（水平堆叠条，两条路线对比） ──
fig, ax = plt.subplots(figsize=(15 * CM, 4.6 * CM))
routes = ["火法回收", "本报告湿法路线"]
items = ["能耗", "试剂", "人工与折旧", "废液处理"]
vals = np.array([[4.82, 0.31, 2.10, 0.44],
                 [1.36, 2.05, 1.88, 1.12]])
cols = [PKU_RED, MID, GOLD, GREY]
left = np.zeros(2)
for i, it in enumerate(items):
    ax.barh(routes, vals[:, i], left=left, height=0.46, label=it,
            color=cols[i], edgecolor="white", linewidth=0.6)
    for r in range(2):
        if vals[r, i] > 0.6:
            ax.text(left[r] + vals[r, i] / 2, r, f"{vals[r, i]:.2f}",
                    ha="center", va="center", fontsize=7.5, color="white")
    left += vals[:, i]
for r, tot in enumerate(vals.sum(axis=1)):
    ax.text(tot + 0.12, r, f"合计 {tot:.2f}", va="center", fontsize=8.5, color="#333")
ax.set_xlabel("单位处理成本 (万元·t⁻¹)")
ax.set_xlim(0, 9.6)
ax.legend(frameon=False, ncol=4, fontsize=8, loc="lower right",
          bbox_to_anchor=(1.0, -0.42))
ax.grid(axis="x", color="#E0E0E0", lw=0.5); ax.set_axisbelow(True)
fig.savefig("assets/fig_cost.png"); plt.close(fig)

print("3 张图已生成")
