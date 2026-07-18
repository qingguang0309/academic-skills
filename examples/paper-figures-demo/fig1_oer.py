"""Fig. 1  NiFe-LDH OER 电催化组图(Angew/wiley 双栏)。
⚠ 全部为示例数据(峰位/电位物理合理,数值为演示编造),投稿前必须替换为真实数据。
按 paper-figures skill 规范:XRD 堆叠+标准卡片 / XPS 反轴分峰 / LSV 标 η10 / Tafel 拟合。"""
import numpy as np
import matplotlib.pyplot as plt
import paperfig as pf

rng = np.random.default_rng(3)
pf.setup("wiley")

C_MAIN, C_CTRL, C_REF = pf.OKABE_ITO["blue"], pf.OKABE_ITO["vermilion"], "0.45"

fig, axd = pf.mosaic([["a", "b"], ["c", "d"]], width="double", height_mm=120)

# ---------------- (a) XRD:堆叠 + JCPDS 竖线谱 ----------------
ax = axd["a"]
tt = np.linspace(5, 80, 3000)

def peaks(centers, heights, w=0.35):
    y = np.zeros_like(tt)
    for c, h in zip(centers, heights):
        y += h / (1 + ((tt - c) / w) ** 2)          # Lorentzian
    return y

ldh_pos = [11.4, 22.9, 34.4, 38.8, 46.0, 59.9, 61.2]
ldh_hkl = ["(003)", "(006)", "(012)", "(015)", "(018)", "(110)", "(113)"]
ldh_int = [1.00, 0.45, 0.38, 0.30, 0.22, 0.25, 0.22]
noh_pos = [19.3, 33.1, 38.5, 52.1, 59.1, 62.7]
noh_int = [0.85, 0.55, 1.00, 0.35, 0.45, 0.30]

y_ldh = peaks(ldh_pos, ldh_int) + 0.05 + 0.012 * rng.standard_normal(tt.size)
y_noh = peaks(noh_pos, noh_int) + 0.05 + 0.012 * rng.standard_normal(tt.size)
off = 1.35
ax.plot(tt, y_ldh + off, lw=0.8, color=C_MAIN)
ax.plot(tt, y_noh + off * 2, lw=0.8, color=C_CTRL)
ax.text(78, off + 0.45, "NiFe-LDH", ha="right", color=C_MAIN)
ax.text(78, off * 2 + 0.45, r"Ni(OH)$_2$", ha="right", color=C_CTRL)
for p, hkl, h, dy in zip(ldh_pos[:4], ldh_hkl[:4], ldh_int[:4], [0.14, 0.14, 0.14, 0.50]):
    ax.text(p, h + off + dy, hkl, ha="center", fontsize=plt.rcParams["xtick.labelsize"])
# JCPDS 40-0215 竖线谱(灰)
ax.vlines(ldh_pos, 0, [i * 0.9 for i in ldh_int], color="0.35", lw=0.8)
ax.text(78, 0.75, "LDH JCPDS 40-0215", ha="right", color="0.35",
        fontsize=plt.rcParams["xtick.labelsize"])
ax.set_xlim(5, 80)
ax.set_ylim(0, off * 2 + 1.6)
ax.set_yticks([])
ax.set_xlabel(r"2$\theta$ (degree)")
ax.set_ylabel("Intensity (a.u.)")

# ---------------- (b) XPS Ni 2p:分峰 + 反轴 ----------------
ax = axd["b"]
be = np.linspace(848, 890, 1200)

def gauss(c, h, w):
    return h * np.exp(-((be - c) / w) ** 2)

bg = 0.12 + 0.010 * (be - 848) + 0.25 / (1 + np.exp(-(be - 866) / 2.5))   # 近似 Shirley 背景
ni2 = gauss(855.3, 1.00, 1.15) + gauss(872.9, 0.48, 1.35)                  # Ni2+ 2p3/2 + 2p1/2
ni3 = gauss(856.9, 0.55, 1.25) + gauss(874.6, 0.26, 1.45)                  # Ni3+
sat = gauss(861.4, 0.42, 2.6) + gauss(879.6, 0.24, 2.8)                    # 卫星峰
envelope = bg + ni2 + ni3 + sat
raw = envelope + 0.022 * rng.standard_normal(be.size)

ax.plot(be[::6], raw[::6], "o", ms=1.8, mfc="none", mec="0.2", mew=0.4, label="Raw")
ax.plot(be, envelope, color="0.1", lw=1.0, label="Fit")
for comp, c, lab in [(ni2, pf.CYCLE[0], r"Ni$^{2+}$"), (ni3, pf.CYCLE[1], r"Ni$^{3+}$"),
                     (sat, pf.CYCLE[3], "sat.")]:
    ax.fill_between(be, bg, comp + bg, alpha=0.35, color=c, lw=0)
ax.plot(be, bg, "--", lw=0.7, color="0.55")
yv = lambda c: envelope[np.argmin(np.abs(be - c))]
ax.annotate(r"Ni$^{2+}$", xy=(854.0, yv(855.3) + 0.05), ha="center", color=pf.CYCLE[0])
ax.annotate(r"Ni$^{3+}$", xy=(858.9, yv(856.9) + 0.10), ha="center", color=pf.CYCLE[1])
ax.annotate("sat.", xy=(861.4, yv(861.4) + 0.06), ha="center", color=pf.CYCLE[3])
ax.annotate(r"Ni 2p$_{1/2}$", xy=(874.2, yv(873.2) + 0.10), ha="center", color="0.25")
ax.text(0.035, 0.92, "Ni 2p", transform=ax.transAxes, fontweight="bold")
ax.invert_xaxis()
ax.set_ylim(0, float(raw.max()) * 1.22)
ax.set_yticks([])
ax.set_xlabel("Binding energy (eV)")
ax.set_ylabel("Intensity (a.u.)")
ax.legend(loc="upper left", bbox_to_anchor=(0.015, 0.86))

# ---------------- (c) LSV:η10 标注 ----------------
ax = axd["c"]
E = np.linspace(1.20, 1.75, 500)

def lsv(onset, tafel_v):                       # 简化 BV 指数支
    j = 0.02 * np.exp(np.clip((E - onset) / tafel_v, -50, 50))
    return np.clip(j, 0, 320)

j_ldh = lsv(1.400, 0.0165)
j_noh = lsv(1.520, 0.0282)
j_ruo = lsv(1.440, 0.0182)
eta10 = {}
for name, j in [("NiFe-LDH", j_ldh), (r"Ni(OH)$_2$", j_noh), (r"RuO$_2$", j_ruo)]:
    eta10[name] = E[np.searchsorted(j, 10)] - 1.23
ax.plot(E, j_ldh, color=C_MAIN, label="NiFe-LDH")
ax.plot(E, j_ruo, color=C_REF, ls="-.", label=r"RuO$_2$")
ax.plot(E, j_noh, color=C_CTRL, ls="--", label=r"Ni(OH)$_2$")
ax.axhline(10, color="0.6", lw=0.6, ls=":")
ax.text(1.213, 13, r"10 mA cm$^{-2}$", color="0.4", fontsize=plt.rcParams["xtick.labelsize"])
ax.annotate(rf"$\eta_{{10}}$ = {eta10['NiFe-LDH']*1000:.0f} mV", xy=(1.23 + eta10["NiFe-LDH"], 10),
            xytext=(1.30, 68), color=C_MAIN,
            arrowprops=dict(arrowstyle="-", lw=0.6, color=C_MAIN, shrinkB=2))
ax.set_xlim(1.20, 1.70)
ax.set_ylim(0, 100)
ax.set_xlabel("Potential (V vs. RHE)")
ax.set_ylabel(r"Current density (mA cm$^{-2}$)")
ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.98))

# ---------------- (d) Tafel ----------------
ax = axd["d"]
for name, j, c, ls in [("NiFe-LDH", j_ldh, C_MAIN, "-"), (r"RuO$_2$", j_ruo, C_REF, "-."),
                       (r"Ni(OH)$_2$", j_noh, C_CTRL, "--")]:
    m = (j > 0.5) & (j < 50)
    lj, eta = np.log10(j[m]), (E[m] - 1.23) * 1000
    ax.plot(lj, eta, color=c, ls=ls, lw=1.0)
    fm_ = (lj > np.log10(1)) & (lj < np.log10(20))
    k, b = np.polyfit(lj[fm_], eta[fm_], 1)
    xf = np.array([lj[fm_].min() - 0.15, lj[fm_].max() + 0.15])
    ax.plot(xf, k * xf + b, ls=":", lw=0.7, color="0.3")
    ax.text(1.82, k * 1.82 + b, rf"{k:.0f} mV dec$^{{-1}}$", color=c, va="center",
            fontsize=plt.rcParams["legend.fontsize"])
ax.set_xlim(-0.4, 2.9)
ax.set_ylim(140, 540)
ax.set_xlabel(r"log |$j$| (mA cm$^{-2}$)")
ax.set_ylabel("Overpotential (mV)")

pf.panel_labels([axd[k] for k in "abcd"])
pf.export(fig, "fig1_oer")
print("η10 (mV):", {k: round(v * 1000) for k, v in eta10.items()})
