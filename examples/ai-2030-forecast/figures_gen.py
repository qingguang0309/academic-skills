"""AI 算力外推论文的数据图。

数据来源（全部为已核实的一手来源，脚本内逐条标注）：
  [E] Epoch AI. Can AI scaling continue through 2030? 2024.
      https://epoch.ai/blog/can-ai-scaling-continue-through-2030
      · 训练算力年增约 4×；2030 年 2e29 FLOP 的训练很可能可行
      · 电力（本地园区 1–5 GW）1e28–3e29；电力（跨地域）2–45 GW → 2e28–2e30
      · 芯片产能中位 1 亿张 H100 当量 → 9e29，区间 2000 万–4 亿张 → 1e29–5e30
      · 数据 4e14–2e16 有效 token → 6e28–2e32；延迟墙 3e30–1e32
  [S] Sevilla et al. Compute Trends Across Three Eras of ML. arXiv:2202.05924.
      · 2010 年前倍增约 20 个月；深度学习期倍增约 6 个月
  [H] Hoffmann et al. Training Compute-Optimal LLMs. arXiv:2203.15556 (NeurIPS 35).
      · Chinchilla 70B / 1.4T token；N 与 D 应等比例放大
  [V] Villalobos et al. Will we run out of data? arXiv:2211.04325 (ICML 2024).
      · 公开人类文本存量约 3e14 token，2026—2032 年间用尽

图中不出现任何未列于上表的数值。
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, ACC, GREY = "#1B2733", "#B03A2E", "#7A8288"
WARM, COOL = "#C9A227", "#2F6FAE"
CM = 1 / 2.54
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial Unicode MS", "Hiragino Sans GB"],
    "axes.unicode_minus": False, "font.size": 9,
    "axes.linewidth": 0.8, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})


def sci(v, sig=1):
    """4.88e25 → '4.9×10²⁵'。图里不能出现 Python 的 e+NN 记法。"""
    SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    m, e = f"{v:.{sig}e}".split("e")
    m = m.rstrip("0").rstrip(".")
    exp = str(int(e)).translate(SUP)
    return f"{m}×10{exp}"

# ── 图 1：以已核实量为锚点构造的算力轨迹 ──────────────────────────
# 不自造起点。锚点只有两个,都取自 [E]:2030 年 2e29 FLOP、年增 4×。
# 由此反推 2024 年基准 C_2024 = 2e29 / 4^6;再按 [S] 的两段倍增期向前反推。
# 图中历史段是"按已发表倍增期反推的轨迹",不是逐模型实测点,标题已注明。
fig, ax = plt.subplots(figsize=(15 * CM, 7.4 * CM))

C_2030 = 2e29                      # [E]
G = 4.0                            # [E] 年增倍数
C_2024 = C_2030 / G ** 6           # 反推得 ≈ 4.9e25,与 [E]"逾 30 个模型达 1e25 量级"相容
C_2010 = C_2024 / G ** 14          # 深度学习期倍增 6 个月 ≈ 年增 4× [S]
G_PRE = 2 ** (12 / 20)             # 2010 年前倍增约 20 个月 [S]

t_a = np.linspace(2000, 2010, 120); c_a = C_2010 * G_PRE ** (t_a - 2010)
t_b = np.linspace(2010, 2024, 160); c_b = C_2010 * G ** (t_b - 2010)
t_c = np.linspace(2024, 2030, 120); c_c = C_2024 * G ** (t_c - 2024)

ax.plot(t_a, c_a, "-", color=GREY, lw=1.8, label="2010 年前：倍增约 20 个月")
ax.plot(t_b, c_b, "-", color=INK, lw=2.0, label="2010 年起：倍增约 6 个月（≈4×/年）")
ax.plot(t_c, c_c, "--", color=ACC, lw=2.0, label="2024—2030：维持 4×/年的外推")
ax.axvline(2024, color=GREY, lw=0.7, ls=":")

ax.plot([2030], [C_2030], "o", ms=7, color=ACC, zorder=5)
ax.annotate("锚点二：2030 年 2×10²⁹ FLOP\n（Epoch AI 判断“很可能可行”）",
            xy=(2030, C_2030), xytext=(2014.8, 3.5e28), fontsize=8.5, color=ACC,
            arrowprops=dict(arrowstyle="->", lw=0.9, color=ACC))
ax.plot([2024], [C_2024], "s", ms=6, color=INK, zorder=5)
ax.annotate(f"锚点一反推的 2024 年基准\n$C_{{2024}}$ ≈ {sci(C_2024)} FLOP",
            xy=(2024, C_2024), xytext=(2012.6, 1.2e23), fontsize=8.5, color=INK,
            arrowprops=dict(arrowstyle="->", lw=0.9, color=INK))
ax.annotate("拐点：倍增期由 20 个月缩至 6 个月",
            xy=(2010, C_2010), xytext=(2000.5, 1e19), fontsize=8.5, color=GREY,
            arrowprops=dict(arrowstyle="->", lw=0.9, color=GREY))

ax.set_yscale("log")
ax.set_xlabel("年份")
ax.set_ylabel("单次训练算力 (FLOP)")
ax.set_xlim(2000, 2031)
ax.set_ylim(1e10, 3e31)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
ax.grid(color="#E3E7EB", lw=0.5); ax.set_axisbelow(True)
fig.savefig("figures/fig_trend.pdf"); fig.savefig("figures/fig_trend.png")
plt.close(fig)

# ── 图 2：四类约束在 2030 年允许的训练规模区间 ────────────────────────
# 全部区间取自 [E]。
fig, ax = plt.subplots(figsize=(15 * CM, 6.6 * CM))
items = [
    ("延迟墙", 3e30, 1e32, COOL),
    ("数据存量（多模态有效 token）", 6e28, 2e32, WARM),
    ("芯片产能（2000 万–4 亿张 H100 当量）", 1e29, 5e30, GREY),
    ("电力·跨地域分布式（2—45 GW）", 2e28, 2e30, INK),
    ("电力·单一园区（1—5 GW）", 1e28, 3e29, ACC),
]
for i, (lab, lo, hi, c) in enumerate(items):
    ax.plot([lo, hi], [i, i], "-", lw=7, color=c, solid_capstyle="butt", alpha=0.85)
    ax.plot([lo, hi], [i, i], "|", ms=11, color=c, mew=1.4)
ax.axvline(2e29, color=ACC, lw=1.3, ls="--")
ax.text(2.4e29, 4.42, "综合结论 2×10²⁹", fontsize=8.5, color=ACC, va="center")

ax.set_yticks(range(len(items)), [x[0] for x in items], fontsize=8.5)
ax.set_xscale("log")
ax.set_xlim(3e27, 6e32)
ax.set_ylim(-0.7, 4.8)
ax.set_xlabel("2030 年该约束单独允许的训练算力上限 (FLOP)")
ax.grid(axis="x", color="#E3E7EB", lw=0.5); ax.set_axisbelow(True)
fig.savefig("figures/fig_ceilings.pdf"); fig.savefig("figures/fig_ceilings.png")
plt.close(fig)

# ── 图 3：Chinchilla 等比例配比下 N 与 D 随 C 的走向 ──────────────────
# 锚点用 [H] 报告的 Chinchilla 配置：N=7e10, D=1.4e12，C≈6ND。
fig, ax = plt.subplots(figsize=(15 * CM, 6.4 * CM))
N0, D0 = 7e10, 1.4e12
C0 = 6 * N0 * D0
C = np.logspace(np.log10(C0) - 3, np.log10(2e29), 200)
N = N0 * (C / C0) ** 0.5
D = D0 * (C / C0) ** 0.5
ax.plot(C, N, "-", color=INK, lw=2.0, label=r"参数量 $N \propto C^{1/2}$")
ax.plot(C, D, "-", color=ACC, lw=2.0, label=r"训练 token 数 $D \propto C^{1/2}$")
ax.axhline(3e14, color=WARM, lw=1.3, ls="-.")
ax.text(C0 * 1.5e-3, 3.9e14, "公开人类文本存量 ≈ 3×10¹⁴ token（Villalobos 等）",
        fontsize=8.3, color="#8A6A2E")
ax.plot([C0], [N0], "o", ms=6, color=INK)
ax.plot([C0], [D0], "o", ms=6, color=ACC)
ax.annotate("Chinchilla 锚点\n70B 参数 / 1.4T token", xy=(C0, D0),
            xytext=(C0 * 3e-3, 8e11), fontsize=8.3, color=GREY,
            arrowprops=dict(arrowstyle="->", lw=0.8, color=GREY))
C_cross_f = C0 * (3e14 / D0) ** 2
ax.plot([C_cross_f], [3e14], "o", ms=7, color=ACC, zorder=6)
ax.annotate(f"D 触及存量：C ≈ {sci(C_cross_f)} FLOP\n仅为 2×10²⁹ 的 {C_cross_f/2e29:.2f} 倍",
            xy=(C_cross_f, 3e14), xytext=(2.2e24, 2.6e9), fontsize=8.5, color=ACC,
            arrowprops=dict(arrowstyle="->", lw=0.9, color=ACC))
ax.axvline(2e29, color=GREY, lw=0.8, ls=":")
ax.text(2e29 * 0.75, 1.6e7, "2×10²⁹", fontsize=8.3, color=GREY,
        rotation=90, va="bottom", ha="right")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("训练算力 C (FLOP)")
ax.set_ylabel("参数量 N / token 数 D")
ax.set_ylim(1e7, 4e17)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
ax.grid(color="#E3E7EB", lw=0.5); ax.set_axisbelow(True)
fig.savefig("figures/fig_scaling.pdf"); fig.savefig("figures/fig_scaling.png")
plt.close(fig)

# ── 图 4：持续年增速 → 2030 年可达算力,叠加四道天花板 ─────────────
# 非循环:横轴是假设的持续年增速,纵轴由 C_2024 外推六年得到,天花板取自 [E]。
fig, ax = plt.subplots(figsize=(15 * CM, 6.8 * CM))
g = np.linspace(1.5, 6.0, 300)
C_2030_g = C_2024 * g ** 6
ax.plot(g, C_2030_g, "-", color=INK, lw=2.0)

walls = [("电力·单一园区上限 3×10²⁹", 3e29, ACC),
         ("芯片产能中位 9×10²⁹", 9e29, GREY),
         ("延迟墙下沿 3×10³⁰", 3e30, COOL)]
for lab, y, c in walls:
    ax.axhline(y, color=c, lw=1.1, ls="--")
    gx = (y / C_2024) ** (1 / 6)
    ax.plot([gx], [y], "o", ms=5.5, color=c, zorder=5)
    ax.text(1.62, y * 1.35, lab, fontsize=8, color=c, va="bottom", ha="left")
    if gx <= 5.9:                       # 交点落在坐标轴外时不标,免得标签飘到画布外
        ax.text(gx + 0.06, y * 0.34, f"g = {gx:.2f}", fontsize=8, color=c, ha="left")

ax.plot([4.0], [C_2030], "s", ms=7, color=ACC, zorder=6)
ax.annotate("维持 4×/年 → 2×10²⁹", xy=(4.0, C_2030), xytext=(4.35, 6e27),
            fontsize=8.5, color=ACC,
            arrowprops=dict(arrowstyle="->", lw=0.9, color=ACC))
ax.set_yscale("log")
ax.set_xlabel("2024—2030 年持续保持的算力年增倍数 g")
ax.set_ylabel("2030 年可达训练算力 (FLOP)")
ax.set_xlim(1.5, 6.0); ax.set_ylim(1e26, 8e31)
ax.grid(color="#E3E7EB", lw=0.5); ax.set_axisbelow(True)
fig.savefig("figures/fig_sensitivity.pdf"); fig.savefig("figures/fig_sensitivity.png")
plt.close(fig)

D_cross = 3e14
C_cross = C0 * (D_cross / D0) ** 2
print(f"4 张图已生成")
print(f"  由锚点反推的 2024 年基准 C_2024 = {C_2024:.2e} FLOP")
print(f"  Chinchilla 配比下训练 token 数触及公开文本存量 3e14 的算力 = {C_cross:.2e} FLOP")
print(f"  该值为 2e29 的 {C_cross/2e29:.3f} 倍——数据墙先于综合上限出现")
