# PM2.5 队列研究答辩配图(合成示意数据)
# paper-figures 规范:Okabe-Ito 色盲安全、轴带单位、关键发现标在图上;
# 焦点色取 vermillion,与 pku 主题的北大红呼应(colour threading)。
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OI = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73",
      "sky": "#56B4E9", "verm": "#B4402E", "gray": "#8C8C8C", "purple": "#7B4E80"}
plt.rcParams.update({
    # Arial Unicode MS 单字体内含拉丁 + 中日韩字形:混排不依赖逐字回退(实测回退不可靠)
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial Unicode MS", "Hiragino Sans GB"],
    "axes.unicode_minus": False, "font.size": 11.5,
    "axes.linewidth": 0.9, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "figure.dpi": 300, "savefig.dpi": 300,
})
rng = np.random.default_rng(11)

# ============ Fig 1:暴露-反应关系 + 亚组森林图 ============
fig, (a, b) = plt.subplots(1, 2, figsize=(8.4, 3.3), constrained_layout=True,
                           gridspec_kw={"width_ratios": [1, 1.05]})

# (a) 限制性立方样条:HR 随年均 PM2.5 上升,高浓度段趋缓
x = np.linspace(10, 95, 300)
hr = 1 + 0.0092 * (x - 10) - 0.000030 * (x - 10) ** 2
se = 0.011 + 0.00045 * (x - 10)
a.fill_between(x, hr - 1.96 * se, hr + 1.96 * se, color=OI["verm"], alpha=0.15, lw=0)
a.plot(x, hr, color=OI["verm"], lw=2.2, zorder=3)
a.axhline(1.0, color=OI["gray"], lw=0.9, ls="--")
a.axvline(35, color=OI["gray"], lw=0.9, ls=":")
a.text(36, 1.06, "国家二级标准\n35 μg m$^{-3}$", fontsize=9, color=OI["gray"], va="center")
# 关键发现直接标在图上
a.annotate("每升高 10 μg m$^{-3}$\nHR = 1.09 (1.06–1.12)",
           xy=(70, 1 + 0.0092 * 60 - 0.000030 * 3600), xytext=(24, 1.46),
           fontsize=10.5, fontweight="bold", color=OI["verm"],
           arrowprops=dict(arrowstyle="->", lw=1.1, color=OI["verm"]))
a.set_xlabel("年均 PM$_{2.5}$ 暴露 (μg m$^{-3}$)")
a.set_ylabel("心血管疾病发病 HR (95% CI)")
a.set_xlim(10, 95); a.set_ylim(0.95, 1.62)
a.set_title("(a)  暴露–反应关系(限制性立方样条)", loc="left", fontsize=12)

# (b) 亚组森林图
groups = ["总人群", "男性", "女性", "< 60 岁", "≥ 60 岁", "非吸烟", "现吸烟", "城市", "县城/乡镇"]
est = [1.090, 1.084, 1.096, 1.061, 1.118, 1.072, 1.131, 1.079, 1.104]
lo  = [1.062, 1.048, 1.055, 1.021, 1.079, 1.038, 1.081, 1.045, 1.058]
hi  = [1.119, 1.121, 1.139, 1.103, 1.159, 1.107, 1.183, 1.114, 1.152]
y = np.arange(len(groups))[::-1]
for yi, e, l, h, g in zip(y, est, lo, hi, groups):
    focal = (g == "总人群")
    c = OI["verm"] if focal else OI["blue"]
    b.plot([l, h], [yi, yi], color=c, lw=2.0 if focal else 1.4, solid_capstyle="butt")
    b.plot(e, yi, "s" if focal else "o", color=c, ms=7.5 if focal else 5.5,
           mec="white", mew=0.8, zorder=3)
b.axvline(1.0, color=OI["gray"], lw=0.9, ls="--")
b.axhspan(y[0] - 0.45, y[0] + 0.45, color=OI["verm"], alpha=0.07)
b.set_yticks(y, groups, fontsize=10)
b.set_xlim(0.98, 1.22)
b.set_ylim(y[-1] - 1.15, y[0] + 0.6)
b.set_xlabel("HR per 10 μg m$^{-3}$ (95% CI)")
b.text(0.984, y[-1] - 0.85, "交互检验 $P$ > 0.05(吸烟状态除外)",
       fontsize=9, color=OI["gray"])
b.set_title("(b)  亚组一致性分析", loc="left", fontsize=12)
fig.savefig("assets/fig_dose_forest.png")
plt.close(fig)

# ============ Fig 2:累积发病曲线 + 情景归因 ============
fig, (a, b) = plt.subplots(1, 2, figsize=(8.4, 3.3), constrained_layout=True)

# (a) 按暴露四分位的累积发病率
t = np.linspace(0, 10, 200)
base = np.array([0.0165, 0.0192, 0.0224, 0.0271])
labs = ["Q1(最低)", "Q2", "Q3", "Q4(最高)"]
cols = [OI["sky"], OI["blue"], OI["orange"], OI["verm"]]
for r, lab, c in zip(base, labs, cols):
    cum = (1 - np.exp(-r * t)) * 100
    a.plot(t, cum, color=c, lw=2.0, label=lab)
    a.text(10.12, cum[-1], f"{cum[-1]:.1f}%", color=c, fontsize=9.5,
           va="center", fontweight="bold")
a.set_xlabel("随访时间 (年)")
a.set_ylabel("心血管疾病累积发病率 (%)")
a.set_xlim(0, 11.4); a.set_ylim(0, 27)
a.legend(frameon=False, fontsize=9.5, loc="upper left", title="PM$_{2.5}$ 暴露四分位",
         title_fontsize=9.5)
a.text(0.42, 0.055, "Q4 vs Q1:绝对风险差 +7.1 个百分点", transform=a.transAxes,
       fontsize=9.5, fontweight="bold", color=OI["verm"])
a.set_title("(a)  分暴露水平的累积发病", loc="left", fontsize=12)

# (b) 情景分析:归因病例与可避免病例
scen = ["现状\n(48 μg m$^{-3}$)", "达国家二级\n(35)", "达 WHO IT-2\n(25)", "达 WHO AQG\n(5)"]
attrib = [100, 62, 41, 8]
bars = b.bar(np.arange(4), attrib, color=[OI["gray"], OI["orange"], OI["green"], OI["blue"]],
             width=0.62)
for i, (bar, v) in enumerate(zip(bars, attrib)):
    b.text(bar.get_x() + bar.get_width() / 2, v + 2.5, f"{v}%", ha="center",
           fontsize=10.5, fontweight="bold")
    if i > 0:
        b.annotate("", xy=(i, v + 12), xytext=(0, 100 + 12),
                   arrowprops=dict(arrowstyle="->", lw=0, color="none"))
b.plot([0.35, 3], [112, 112], color=OI["verm"], lw=1.1)
b.text(1.7, 115, "达 WHO AQG 可避免 92% 归因病例", ha="center",
       fontsize=10, fontweight="bold", color=OI["verm"])
b.set_xticks(np.arange(4), scen, fontsize=9)
b.set_ylabel("归因发病例数(以现状为 100%)")
b.set_ylim(0, 132)
b.set_title("(b)  达标情景的可避免负担", loc="left", fontsize=12)
fig.savefig("assets/fig_burden.png")
plt.close(fig)
print("figures written")
