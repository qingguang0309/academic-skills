"""AI 算力报告 PPT 的配图 —— 与论文同源数据，按投影尺寸重排。

数据来源与 ../ai-2030-forecast/figures_gen.py 完全一致（四份已核实的一手来源），
此处只改呈现：论文版按 15 cm 印刷宽度、9 pt 字排；投影距离远，字号要给到 12—13 pt，
且单图信息量要减（论文可以让读者停下来看，幻灯不能）。
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, ACC, GREY = "#1F3A5F", "#C0504D", "#6E7681"      # 与 slidekit azure 主题同调
WARM, COOL = "#C9A227", "#2F6FAE"
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial Unicode MS", "Hiragino Sans GB"],
    "axes.unicode_minus": False, "font.size": 12.5,
    "axes.linewidth": 1.0, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "figure.dpi": 220, "savefig.dpi": 220, "savefig.bbox": "tight",
})

SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
def sci(v, sig=1):
    m, e = f"{v:.{sig}e}".split("e")
    return f"{m.rstrip('0').rstrip('.')}×10{str(int(e)).translate(SUP)}"

C_2030, G = 2e29, 4.0
C_2024 = C_2030 / G ** 6
C_2010 = C_2024 / G ** 14
G_PRE = 2 ** (12 / 20)
N0, D0 = 7e10, 1.4e12
C0 = 6 * N0 * D0

# ── 图 1：算力轨迹 ──
fig, ax = plt.subplots(figsize=(9.2, 4.5))
for t0, t1, c0, g, c, ls, lab in [
    (2000, 2010, C_2010 * G_PRE ** -10, G_PRE, GREY, "-", "2010 年前｜倍增约 20 个月"),
    (2010, 2024, C_2010, G, INK, "-", "2010 年起｜倍增约 6 个月（≈4×/年）"),
    (2024, 2030, C_2024, G, ACC, "--", "2024—2030｜维持 4×/年的外推"),
]:
    t = np.linspace(t0, t1, 150)
    ax.plot(t, c0 * g ** (t - t0), ls, color=c, lw=3.0, label=lab)
ax.plot([2030], [C_2030], "o", ms=11, color=ACC, zorder=5)
ax.annotate(f"2030 年 {sci(C_2030)} FLOP", xy=(2030, C_2030), xytext=(2013.4, 8e28),
            fontsize=12.5, color=ACC, fontweight="bold",
            arrowprops=dict(arrowstyle="->", lw=1.4, color=ACC))
ax.plot([2024], [C_2024], "s", ms=9, color=INK, zorder=5)
ax.annotate(f"反推的 2024 年基准 {sci(C_2024)}", xy=(2024, C_2024), xytext=(2007.6, 2e23),
            fontsize=12, color=INK,
            arrowprops=dict(arrowstyle="->", lw=1.3, color=INK))
ax.set_yscale("log"); ax.set_xlim(2000, 2031); ax.set_ylim(1e10, 4e31)
ax.set_xlabel("年份"); ax.set_ylabel("单次训练算力 (FLOP)")
ax.legend(frameon=False, fontsize=11.5, loc="upper left")
ax.grid(color="#E1E8F0", lw=0.7); ax.set_axisbelow(True)
fig.savefig("assets/fig_trend.png"); plt.close(fig)

# ── 图 2：四类约束天花板 ──
fig, ax = plt.subplots(figsize=(9.2, 4.2))
items = [("延迟墙", 3e30, 1e32, COOL),
         ("数据存量（多模态）", 6e28, 2e32, WARM),
         ("芯片产能", 1e29, 5e30, GREY),
         ("电力·跨地域", 2e28, 2e30, INK),
         ("电力·单一园区", 1e28, 3e29, ACC)]
for i, (lab, lo, hi, c) in enumerate(items):
    ax.plot([lo, hi], [i, i], "-", lw=12, color=c, solid_capstyle="butt", alpha=0.9)
ax.axvline(2e29, color=ACC, lw=2.0, ls="--")
ax.text(2.6e29, 4.45, "综合结论 2×10²⁹", fontsize=12.5, color=ACC,
        va="center", fontweight="bold")
ax.set_yticks(range(len(items)), [x[0] for x in items], fontsize=12.5)
ax.set_xscale("log"); ax.set_xlim(3e27, 6e32); ax.set_ylim(-0.7, 4.9)
ax.set_xlabel("2030 年该约束单独允许的训练算力上限 (FLOP)")
ax.grid(axis="x", color="#E1E8F0", lw=0.7); ax.set_axisbelow(True)
fig.savefig("assets/fig_ceilings.png"); plt.close(fig)

# ── 图 3：数据墙 ──
fig, ax = plt.subplots(figsize=(9.2, 4.4))
C = np.logspace(np.log10(C0) - 2, np.log10(2e29), 200)
ax.plot(C, D0 * (C / C0) ** 0.5, "-", color=ACC, lw=3.0, label=r"训练 token 数 $D \propto C^{1/2}$")
ax.plot(C, N0 * (C / C0) ** 0.5, "-", color=INK, lw=3.0, label=r"参数量 $N \propto C^{1/2}$")
ax.axhline(3e14, color=WARM, lw=2.0, ls="-.")
ax.text(C0 * 3e-2, 4.6e14, "公开人类文本存量 ≈ 3×10¹⁴ token", fontsize=12, color="#8A6A2E")
C_cross = C0 * (3e14 / D0) ** 2
ax.plot([C_cross], [3e14], "o", ms=12, color=ACC, zorder=6)
ax.annotate(f"D 触及存量\nC ≈ {sci(C_cross)} FLOP", xy=(C_cross, 3e14),
            xytext=(6e24, 3.4e9), fontsize=12.5, color=ACC, fontweight="bold",
            arrowprops=dict(arrowstyle="->", lw=1.4, color=ACC))
ax.axvline(2e29, color=GREY, lw=1.2, ls=":")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(1e8, 6e16)
ax.set_xlabel("训练算力 C (FLOP)"); ax.set_ylabel("参数量 N / token 数 D")
ax.legend(frameon=False, fontsize=11.5, loc="upper left")
ax.grid(color="#E1E8F0", lw=0.7); ax.set_axisbelow(True)
fig.savefig("assets/fig_scaling.png"); plt.close(fig)

# ── 图 4：增速敏感性 ──
fig, ax = plt.subplots(figsize=(9.2, 4.2))
g = np.linspace(1.5, 6.0, 300)
ax.plot(g, C_2024 * g ** 6, "-", color=INK, lw=3.0)
for lab, y, c in [("电力·单一园区 3×10²⁹", 3e29, ACC),
                  ("芯片产能中位 9×10²⁹", 9e29, GREY),
                  ("延迟墙下沿 3×10³⁰", 3e30, COOL)]:
    ax.axhline(y, color=c, lw=1.6, ls="--")
    ax.text(1.62, y * 1.4, lab, fontsize=11.5, color=c, va="bottom")
ax.plot([4.0], [C_2030], "s", ms=11, color=ACC, zorder=6)
ax.annotate("4×/年 → 2×10²⁹", xy=(4.0, C_2030), xytext=(4.3, 5e27),
            fontsize=12.5, color=ACC, fontweight="bold",
            arrowprops=dict(arrowstyle="->", lw=1.4, color=ACC))
ax.set_yscale("log"); ax.set_xlim(1.5, 6.0); ax.set_ylim(1e26, 1e32)
ax.set_xlabel("2024—2030 年持续保持的算力年增倍数 g")
ax.set_ylabel("2030 年可达算力 (FLOP)")
ax.grid(color="#E1E8F0", lw=0.7); ax.set_axisbelow(True)
fig.savefig("assets/fig_sensitivity.png"); plt.close(fig)

print(f"4 张投影版图已生成；C_2024={sci(C_2024)}，数据墙 C={sci(C_cross)}"
      f"（为 2e29 的 {C_cross/2e29:.2f} 倍）")
