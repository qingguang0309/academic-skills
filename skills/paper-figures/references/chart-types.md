# 材料/化学常见图型规范

按测量类型组织。每节给出：坐标轴惯例、必备要素、常见错误、关键代码要点。
所有代码假定已 `import paperfig as pf; import numpy as np; import matplotlib.pyplot as plt` 且已 `pf.setup(...)`。

## 目录

- [XRD](#xrd)
- [XPS](#xps)
- [Raman / FTIR](#raman--ftir)
- [UV-Vis DRS 与 Tauc plot](#uv-vis-drs-与-tauc-plot)
- [PL / TRPL](#pl--trpl)
- [N₂ 吸附等温线与孔径分布](#n吸附等温线与孔径分布)
- [TGA / DSC](#tga--dsc)
- [电化学：CV / LSV / Tafel](#电化学cv--lsv--tafel)
- [电化学：EIS Nyquist](#电化学eis-nyquist)
- [电化学：GCD 与循环稳定性](#电化学gcd-与循环稳定性)
- [催化活性与循环测试](#催化活性与循环测试)
- [DFT：能带与态密度](#dft能带与态密度)
- [形貌图（SEM/TEM）排版](#形貌图semtem排版)
- [误差棒与统计](#误差棒与统计)

## 标注与图例布局纪律(通用)

实测中最高发的缺陷全是文字布局问题。画任何图型前先记住四条:

1. **标注坐标从数据算,不手拍**:峰/曲线归属标注的 y 值一律
   `y[np.argmin(np.abs(x - x0))] + offset` 从数据取——改数据后标注自动跟随;手拍绝对数值几乎必撞。
2. **`ax.text`/`annotate` 在数据坐标下默认不裁剪**:超出 xlim/ylim 的文字不会消失,
   会原样画到面板外"飘"在图面上。放线端/峰顶标签前先确认(或扩)轴范围。
3. **图例位置看数据形状定**:想清楚曲线峰或上升沿占哪个角,图例放对角
   (XPS 反轴后主峰在右侧 → 图例放左上)。
4. **相邻标签错开**:密集峰的指数/归属标签交错高度,或只标互不打架的主峰。

`pf.export` 导出前自动跑 `pf.check_layout(fig)`(互撞/出图/出轴三类几何体检),
**告警清零是交付门槛**;感知类问题(低对比、色彩混淆)它查不了,PNG 亲眼检查仍然必做。

## XRD

- 轴：x = `2θ (degree)`，常用范围 5–80°；y = `Intensity (a.u.)`，**y 轴不标刻度数字**（强度是相对的）。
- 多样品对比：纵向堆叠（offset），从下到上按逻辑顺序（如改性程度递增），每条曲线右端或上方标样品名。
- 底部加标准卡片（PDF/JCPDS）的竖线谱（stick pattern），并在图例或 caption 标卡号。
- 关键峰标晶面指数 `(002)`、`(101)`，字号与刻度字号一致。
- 相邻峰的晶面指数标签要错开高度,或只标互不打架的主峰(check_layout 报互撞多半就是这里)。
- 常见错误：堆叠偏移量不均匀导致基线歪斜；y 轴留着无意义的强度数字；卡片竖线用了和样品曲线抢眼的颜色（应用灰色或黑色细线）。

```python
offset = 1.2 * ymax            # 统一偏移量
for i, (name, y) in enumerate(samples):
    ax.plot(two_theta, y + i * offset, lw=0.8)
    ax.text(78, y[-1] + i * offset + 0.1 * ymax, name, ha="right")
ax.set_yticks([])              # 去掉 y 刻度
ax.vlines(ref_pos, 0, ref_int, color="0.35", lw=0.8)   # 标准卡片竖线谱(别用 stem,默认带圆点)
```

## XPS

- 轴：x = `Binding energy (eV)`，**必须从高到低**（`ax.invert_xaxis()`）；y = `Intensity (a.u.)`，不标刻度数字。
- 高分辨谱分峰：原始数据用散点（黑色小空心圆）或细线，拟合总包络用实线，各分量峰用半透明填充（`fill_between`, alpha≈0.35），背景线用灰色虚线。每个分量峰标归属（如 `Ti 2p₃/₂`、`C–O`, 元素价态）。
- 多样品同元素对比：纵向堆叠，同一元素窗口内 x 范围一致，方便峰移比较；峰移要用虚线竖线或箭头标出。
- 布局:反轴后主峰聚在图右侧(低结合能端),图例放左上;各峰归属标注的 y 坐标按包络线实际高度 + 固定偏移计算。
- 常见错误：忘了反转 x 轴（一眼假）；分量峰颜色过艳；结合能没做荷电校准说明（提醒用户在 caption 写 C 1s 284.8 eV 校准）。

```python
ax.plot(be, raw, "o", ms=1.8, mfc="none", mec="0.2", mew=0.4, label="Raw")
ax.plot(be, envelope, color="0.1", lw=1.0, label="Fit")
for comp, c in zip(components, pf.CYCLE):
    ax.fill_between(be, bg, comp + bg, alpha=0.35, color=c, lw=0)
ax.invert_xaxis()
ax.set_yticks([])
```

## Raman / FTIR

- Raman：x = `Raman shift (cm⁻¹)` 正向；多样品堆叠同 XRD；特征峰标波数或振动模式（如 D band、G band、E₂g）。碳材料记得在图上或 caption 给 I_D/I_G。
- FTIR：x = `Wavenumber (cm⁻¹)`，**惯例从高到低**（4000 → 400，`ax.invert_xaxis()`）；y = `Transmittance (%)` 或 `Absorbance (a.u.)`。特征吸收带用竖虚线跨样品对齐并标归属。
- 常见错误：FTIR 忘反轴；透射率图把曲线堆到分不清基线（改用 offset 堆叠）。

## UV-Vis DRS 与 Tauc plot

- 吸收谱：x = `Wavelength (nm)`，y = `Absorbance (a.u.)` 或 K-M 函数 `F(R)`。
- Tauc plot：x = `hν (eV)`，y = `(αhν)ⁿ (a.u.)`，直接带隙 n=2、间接带隙 n=1/2，**必须在 y 轴标签里写清指数**。外推线用与曲线同色的细虚线延到 x 轴，交点标 Eg 值。
- 常见错误：n 取错或不标；外推线画到荒腔走板的线性区外；多样品 Eg 比较时外推线互相打架（考虑拆分或用箭头标注代替画线）。

```python
ax.plot(hv, tauc, lw=1.0)
m, b = np.polyfit(hv[mask], tauc[mask], 1)      # mask 选线性区
xline = np.array([-b / m, hv[mask].max() + 0.2])
ax.plot(xline, m * xline + b, "--", lw=0.7, color="0.3")
ax.annotate(f"$E_g$ = {-b/m:.2f} eV", xy=(-b/m, 0), xytext=(-b/m + 0.15, 0.25 * tauc.max()))
ax.set_ylim(0, None)
```

## PL / TRPL

- 稳态 PL：x = `Wavelength (nm)`，y = `PL intensity (a.u.)`。多样品直接叠加（不 offset），因为要比强度高低；激发波长写进 caption 或图角。
- TRPL 衰减：x = `Time (ns)`，y = `Normalized intensity`，**y 轴对数**（`ax.set_yscale("log")`）；拟合曲线叠在数据上，τ 值（单/双指数分量与平均寿命）标在图内或列小表。
- 常见错误：TRPL 用线性 y 轴（看不出多指数行为）；比较 PL 强度但测试条件不一致未说明。

## N₂ 吸附等温线与孔径分布

- 等温线：x = `Relative pressure (P/P₀)`（0–1），y = `Quantity adsorbed (cm³ g⁻¹ STP)`。吸附支**实心符号**、脱附支**空心符号**，同色相连。BET 比表面积标图内或 caption。
- 孔径分布：x = `Pore diameter (nm)`（微孔材料常用对数轴），y = `dV/dlog(D) (cm³ g⁻¹)`；常作为等温线的 inset。
- 常见错误：吸/脱附符号不区分；多样品等温线颜色+符号都相近无法分辨（颜色和符号形状要双编码）。

```python
ax.plot(p_ads, q_ads, "o-", ms=3, lw=0.8, color=c, label=name)
ax.plot(p_des, q_des, "o-", ms=3, lw=0.8, color=c, mfc="none")
axin = ax.inset_axes([0.55, 0.15, 0.42, 0.4])   # 孔径分布 inset
```

## TGA / DSC

- TGA：x = `Temperature (°C)`，y = `Weight (%)`，从 100% 起。失重台阶用横虚线+百分数标注。气氛和升温速率写 caption。
- TGA+DTG/DSC 双轴：右轴画微分曲线，**双轴颜色与对应曲线颜色一致**，且两轴刻度都不要太密。
- 常见错误：双轴图两条曲线颜色与轴颜色不对应；失重百分数不标，读者自己量。

## 电化学：CV / LSV / Tafel

- CV：x = `Potential (V vs. RHE)`（或 vs. Ag/AgCl、SCE，**全文统一并写清**），y = `Current density (mA cm⁻²)`。扫速写 caption 或图内；多扫速图按扫速排序取色（用 viridis 取序列色）。
- LSV（HER/OER）：过电位比较是论点时，用横虚线标 10 mA cm⁻² 并标各样品 η₁₀；iR 校正与否写 caption。
- Tafel：x = `log|j| (mA cm⁻²)`，y = `Overpotential (V)`；线性区拟合线 + 斜率标注（mV dec⁻¹）。
- Tafel 斜率标签放拟合线末端外侧空白(先扩轴范围容纳),不压线;多条线的标签统一放同一端。
- 示例/占位数据要过基准值体检:碱性 OER 的 RuO₂ η₁₀ ≈ 300±30 mV(优秀 NiFe 基 200–280 mV),OER Tafel 30–70 mV dec⁻¹;酸性 HER 的 Pt/C η₁₀ ≈ 30–50 mV。数值离谱会让整套示例失去可信度。
- 常见错误：参比电极不写；电流/电流密度混用；几何面积 vs ECSA 归一化不说明。

## 电化学：EIS Nyquist

- x = `Z′ (Ω)`，y = `−Z″ (Ω)`，**两轴必须等比例**（`ax.set_aspect("equal")`），否则半圆变形误导读者。
- 拟合曲线叠加在数据点上；等效电路小图放 inset 或 caption；高频区常需局部放大 inset。
- 常见错误：不等比例坐标；只给图不给拟合参数（R_ct 等至少 caption 给表）。

```python
ax.plot(z_re, -z_im, "o", ms=3, mfc="none")
ax.plot(z_re_fit, -z_im_fit, lw=0.8)
ax.set_aspect("equal", adjustable="box")
ax.set_xlabel(r"$Z'$ ($\Omega$)"); ax.set_ylabel(r"$-Z''$ ($\Omega$)")
```

## 电化学：GCD 与循环稳定性

- GCD：x = `Time (s)` 或 `Specific capacity (mAh g⁻¹)`，y = `Potential (V)`；多倍率曲线按倍率标注。
- 循环稳定性：x = `Cycle number`，左轴容量（或保持率 %），右轴 `Coulombic efficiency (%)`（通常 90–101% 窗口）；双轴颜色对应曲线。
- 常见错误：CE 轴从 0 画到 100（把 99% 和 95% 压成一条线，窗口要收窄）；容量保持率不标最终值。

## 催化活性与循环测试

- 产量-时间：x = `Time (h)`，y = 如 `H₂ evolved (mmol g⁻¹)`；速率对比用柱状图，y = `Rate (mmol g⁻¹ h⁻¹)`，**必须带误差棒**（n ≥ 3）。柱状图同一色系即可，不必五颜六色；最优样品可用主题色突出。
- 循环测试：锯齿图（每循环清零重跑），循环间用竖虚线分隔，循环编号标顶部；或柱状图逐循环对比。
- AQE/波长依赖：左轴 AQE 数据点（柱或点），右轴叠吸收光谱，证明活性来自带隙激发。
- 常见错误：柱状图无误差棒；y 轴被截断夸大差异（从 0 画起，确需截断用断轴标记并在 caption 说明）。

## DFT：能带与态密度

- 能带：x = 高对称点路径（Γ、M、K…，刻度只标点名），y = `Energy (eV)`，费米能级置 0 并画横虚线 `E_F`。带隙值用双箭头或数值标注。
- DOS/PDOS：x = `Energy (eV)`（E−E_F），y = `DOS (states eV⁻¹)`；PDOS 各轨道填充半透明色，图例标 `Ti 3d`、`O 2p` 等。能带+DOS 常做左右双 panel 共享 y 轴。
- 常见错误：费米能级不置零；自旋极化上下谱不对称标注。

## 形貌图（SEM/TEM）排版

matplotlib 负责排版而非生成：`imshow` 显示图像，关闭坐标轴（`ax.axis("off")`）。

- **比例尺必须重画**：仪器烧录的比例尺常小到不可读。用 `matplotlib.patches.Rectangle` + 文字在角落重画白色（暗背景）或黑色（亮背景）比例尺；需要从原比例尺换算像素长度。
- 元素 mapping 组图：各元素窗口统一尺寸、统一标签位置（左上角元素名，颜色与 mapping 主色一致）。
- 常见错误：panel 之间图像被非等比缩放（imshow 保持 aspect="equal"）；标注文字颜色与背景对比不足（加细描边 `path_effects.withStroke`）。

## 误差棒与统计

- 误差棒必须说明类型（SD / SEM / 95% CI）与 n，写在 caption。
- 样本少（n=3–5）时优先把独立数据点叠画在柱/均值上（小散点 + jitter），比光秃秃的误差棒诚实。
- 显著性标记（*、**、ns）用 `ax.plot` 画横线 + `ax.text` 标星号，检验方法写 caption。
- capsize 取 1.5–2.5 pt，误差棒线宽与数据线一致。
