# 钙钛矿湿热稳定性 deck 的静态配图（合成示意数据）
# 能用 pptxgenjs 原生图表的（柱/饼/折线）不在这里画——原生图表在 PPT 里可编辑；
# 这里只画原生图表做不了的：双轴、误差棒、对数坐标、带阴影区间的曲线。
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PKU_RED, MID, GREY = "#9A0001", "#BE2A2E", "#797069"
GOLD = "#CEAB6E"
IN = 1.0
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial Unicode MS", "Hiragino Sans GB"],
    "axes.unicode_minus": False, "font.size": 10,
    "axes.linewidth": 0.9, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.transparent": True,
})

# ── 图 1：效率涨、寿命不涨（双轴，原生图表做不了） ──
fig, ax = plt.subplots(figsize=(6.4, 3.0))
yr = np.array([2013, 2015, 2017, 2019, 2021, 2023, 2025])
pce = [14.1, 20.1, 22.1, 25.2, 25.7, 26.1, 26.7]
t80 = [50, 180, 420, 700, 1100, 1500, 1850]
ax.plot(yr, pce, "-o", color=PKU_RED, lw=1.8, ms=5, label="认证效率")
ax.set_ylabel("认证光电转换效率 (%)", color=PKU_RED)
ax.tick_params(axis="y", colors=PKU_RED)
ax.set_ylim(10, 30)
ax2 = ax.twinx()
ax2.plot(yr, t80, "--s", color=GREY, lw=1.6, ms=4.5, label="湿热 T80 寿命")
ax2.set_ylabel("湿热 85/85 下 T80 (h)", color=GREY)
ax2.tick_params(axis="y", colors=GREY)
# 门槛线留在 88% 高度，标注写在线**下方**：写上方会被顶出画布顶缘
ax2.set_ylim(0, 28500)
ax2.axhline(25000, color=GOLD, lw=1.4, ls=":")
ax2.text(2013.2, 23200, "IEC 61215 门槛 25 000 h", fontsize=8.5, color="#8A6A2E")
ax2.annotate("", xy=(2025, 1850), xytext=(2025, 24600),
             arrowprops=dict(arrowstyle="<->", lw=1.0, color=GREY))
ax2.text(2024.7, 12000, "仍差 13 倍", fontsize=8.5, color=GREY,
         ha="right", va="center")
ax.set_xlabel("年份")
ax.grid(axis="y", color="#E7DAD8", lw=0.5); ax.set_axisbelow(True)
fig.savefig("assets/fig_gap.png"); plt.close(fig)

# ── 图 2：三条降解路径的活化能（带误差棒的水平条） ──
fig, ax = plt.subplots(figsize=(6.4, 2.9))
paths = ["有机阳离子逸出", "碘化物迁移", "界面 PbI₂ 析出"]
ea = [0.42, 0.68, 0.94]
err = [0.05, 0.07, 0.06]
cols = [MID, PKU_RED, GREY]
b = ax.barh(paths, ea, xerr=err, height=0.55, color=cols,
            edgecolor="white", linewidth=0.6,
            error_kw=dict(ecolor="#4A4442", lw=1.0, capsize=3))
for bar, v in zip(b, ea):
    ax.text(v + 0.11, bar.get_y() + bar.get_height() / 2, f"{v:.2f} eV",
            va="center", fontsize=9)
ax.set_xlabel("表观活化能 $E_a$ (eV)")
ax.set_xlim(0, 1.32)
ax.grid(axis="x", color="#E7DAD8", lw=0.5); ax.set_axisbelow(True)
fig.savefig("assets/fig_ea.png"); plt.close(fig)

# ── 图 3：老化曲线 + 置信区间（阴影带，原生图表做不了） ──
fig, ax = plt.subplots(figsize=(6.4, 3.0))
t = np.linspace(0, 2400, 200)
def decay(tau, n=1.0):
    return 100 * np.exp(-(t / tau) ** n)
for lab, tau, n, c, ls in [("无封装", 260, 0.85, GREY, ":"),
                           ("单层 EVA", 780, 0.95, MID, "--"),
                           ("EVA + 原子层沉积 Al₂O₃", 1980, 1.05, PKU_RED, "-")]:
    y = decay(tau, n)
    ax.plot(t, y, ls, color=c, lw=1.9, label=lab)
    ax.fill_between(t, y * 0.975, np.minimum(y * 1.025, 100), color=c, alpha=0.14, lw=0)
ax.axhline(80, color=GOLD, lw=1.2, ls="-.")
# 标签写进画布内（x=2410 会落到轴外被裁掉），并靠右放：
# 左端 0–300 h 区间三条曲线都从 100% 陡降穿过 80% 一带，标签放那里必被压
ax.text(2340, 82.5, "T80 判据", fontsize=9, color="#8A6A2E",
        ha="right", va="bottom")
ax.set_xlabel("湿热老化时长 (h，85 ℃ / 85% RH)")
ax.set_ylabel("归一化效率 (%)")
ax.set_xlim(0, 2400); ax.set_ylim(0, 105)
ax.legend(frameon=False, fontsize=9, loc="upper right", bbox_to_anchor=(1.0, 0.93))
ax.grid(color="#E7DAD8", lw=0.5); ax.set_axisbelow(True)
fig.savefig("assets/fig_aging.png"); plt.close(fig)

print("3 张图已生成")
