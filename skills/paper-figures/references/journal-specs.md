# 期刊图片规格速查

数值为常年稳定的规格，但期刊偶有改版，**投稿前对着当期 author guidelines 核对一遍**。
paperfig.py 的 `JOURNALS` 字典与本表一致（键名见括号）。

## 栏宽与字号

| 期刊/出版社 | 单栏 | 1.5 栏 | 双栏/全宽 | 最大高度 | 建议字号（最终尺寸） |
|---|---|---|---|---|---|
| Nature 系（`nature`） | 89 mm | — | 183 mm | 247 mm | 标签 5–7 pt，panel 标号 8 pt 粗体小写 |
| Science（`science`） | 55 mm | 120 mm | 183 mm | — | 同上，panel 标号大写 |
| ACS 系：JACS、ACS Catal. 等（`acs`） | 3.33 in = 84.6 mm | — | 7 in = 177.8 mm | 9.5 in | 4.5–10 pt，推荐 7 pt 左右，Arial/Helvetica |
| Wiley 系：Angew、AM、AFM、Small（`wiley`） | 85 mm | — | 175 mm | — | ≥ 6 pt，推荐 7 pt |
| Elsevier 系：Appl. Catal. B 等（`elsevier`） | 90 mm | 140 mm | 190 mm | — | 最终尺寸 7–8 pt |
| RSC 系：EES、JMCA、Chem. Sci.（`rsc`） | 83 mm | — | 171 mm | — | ≥ 7 pt |

通用底线：**任何文字在最终印刷尺寸下不得小于 5 pt**，正常阅读的标签在 6–8 pt。

## 分辨率与格式

| 图类型 | 要求 |
|---|---|
| 数据图（线图、散点、柱状） | 首选矢量 PDF/EPS；如必须栅格 ≥ 1000 dpi |
| 照片/显微图（halftone） | ≥ 300 dpi，TIFF 或高质量 PNG |
| 混合图（照片+线条标注） | ≥ 500–600 dpi |

- 字体一律嵌入（paperfig 已设 `pdf.fonttype=42`）。
- 不要用 JPEG 存数据图（压缩伪影）。
- 部分期刊投稿系统只收 TIFF/EPS：先出 PDF 定稿，最后 `pf.export(..., formats=("pdf","tiff"))` 补一份即可。

## TOC / Graphical Abstract 尺寸

| 期刊 | 尺寸 | 备注 |
|---|---|---|
| ACS 系 TOC | 3.25 in × 1.75 in（8.25 cm × 4.45 cm） | 严格裁切，字要大（≥ 9 pt 视觉效果） |
| Wiley 系（Angew/AM）ToC image | 通常宽约 55 mm × 高 50 mm（frontispiece 另有规格） | 以当期 guidelines 为准 |
| Elsevier Graphical Abstract | 建议 531 × 1328 px 可读区（约 5 × 13 cm @ 300 dpi） | 横条构图 |
| RSC | 8 cm × 4 cm | 横条构图 |

TOC 图信息密度要远低于正文图：一个核心概念 + 极少文字，字号放大到在缩略图里可读。

## Panel 标号惯例

- Nature 系：小写粗体 `a b c`，无括号，8 pt，panel 左上角外侧。
- Science / ACS / Wiley 多数：大写粗体 `A B C` 或 `(a)`；同一篇稿子内统一即可，与目标刊近期文章对齐。
- `pf.panel_labels(axes)` 默认 Nature 风格，`upper=True` 切大写。

## 常用规范细节

- 单位格式：`(V vs. RHE)`、`(mmol g⁻¹ h⁻¹)`（负指数，不用斜杠链）；数字与单位间空格：`20 °C`、`5 wt%`。
- 轴标签句首大写其余小写：`Current density (mA cm⁻²)`。
- matplotlib 里上下标用 mathtext：`r"H$_2$ evolution rate (mmol g$^{-1}$ h$^{-1}$)"`。
- 同一篇论文所有图（含 SI）风格必须一致：同一套 paperfig 设置跑到底。
