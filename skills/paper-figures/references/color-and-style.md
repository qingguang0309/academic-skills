# 配色与风格细节

## 分类配色：Okabe-Ito（默认）

色盲安全、印刷友好，`pf.OKABE_ITO` / `pf.CYCLE` 已内置：

| 名称 | Hex | 用法建议 |
|---|---|---|
| blue | `#0072B2` | 主样品/主曲线 |
| vermilion | `#D55E00` | 对照/次要样品 |
| green | `#009E73` | 第三序列 |
| orange | `#E69F00` | 第四序列 |
| purple | `#CC79A7` | 第五序列 |
| skyblue | `#56B4E9` | 与 blue 需拉开时慎用 |
| black | `#000000` | 参考线、原始数据点 |
| yellow | `#F0E442` | 白底上太浅，仅填充用 |

原则：

- 一张图超过 5 条曲线就该考虑拆图或改用"灰色背景曲线 + 彩色重点曲线"的强调式画法。
- 同一样品在全文所有图里用同一个颜色——读者靠颜色记住样品身份。
- 红绿不要作为唯一区分手段；颜色+线型或颜色+符号双编码最稳。

## 连续/序列配色

- 连续量（温度序列、扫速序列、时间序列）：`viridis`、`cividis`、`plasma`，按序取色：
  `colors = plt.cm.viridis(np.linspace(0.1, 0.85, n))`（掐头去尾避免过暗过亮）。
- 发散量（正负、差值，如电荷密度差）：`RdBu_r`、`PuOr`，**零点必须映射到中间色**（`TwoSlopeNorm`）。
- **永远不用 jet/rainbow**：亮度不单调，会在数据里制造不存在的边界，且色盲不可读。
- mapping/热图配色要在 caption 或 colorbar 上有数值刻度，colorbar 标物理量和单位。

## 灰度测试

顶刊仍有读者黑白打印。定稿前跑一次灰度检查：

```python
from PIL import Image
Image.open("fig1.png").convert("L").save("fig1_gray.png")
```

用 Read 看灰度版：曲线仍可区分（靠线型/符号）则通过。

## 线宽与符号（paperfig 默认值的依据）

| 元素 | 值 | 说明 |
|---|---|---|
| 坐标框/刻度线宽 | 0.6 pt | 印刷下限 0.25 pt，0.5–0.75 为舒适区 |
| 数据线 | 0.8–1.2 pt | 比坐标框明显粗，层级分明 |
| 拟合线/辅助线 | 0.7 pt 虚线 | 比数据线细，灰色 `"0.3"` |
| 散点符号 | 2.5–4 pt | 原始数据用空心（`mfc="none"`）叠拟合线是标准画法 |
| 误差棒 capsize | 1.5–2.5 pt | 线宽与数据线一致 |

## 布局风格

- **全框 + 内刻度**（paperfig 默认）：材料/化学期刊主流（Origin 风格）。物理/CS 期刊偏好开框（只留左下轴），如投这类刊物再改。
- 图例：无边框（默认已设）；放数据留白处；曲线少时直接在曲线端点标文字比图例更好读。
- 不要图表标题（title）——那是 caption 的事；不要背景网格（确有读数需求例外，用 `alpha=0.3` 浅灰细线）。
- inset 小图：坐标框线宽、字号与主图一致，不要缩小字号塞进去。
- 组图对齐：共享轴就真共享（`sharex/sharey`），刻度标签只留最外侧；panel 间距用 constrained_layout 自动处理，不手拍 `subplots_adjust`。

## 中文图

学位论文/基金申请书：

```python
mpl.rcParams["font.sans-serif"] = ["Songti SC", "SimSun", "Arial"]  # macOS / Windows
mpl.rcParams["axes.unicode_minus"] = False   # 中文字体下负号显示
```

字号 9–10.5 pt，版心宽约 150 mm。中英混排时数字和单位仍用西文字体（把西文字体放在 fallback 列表首位反而更好：`["Arial", "Songti SC"]`）。
