# 方法示意图 / 技术路线图的 matplotlib 画法

数据图规范见 chart-types.md；本文管**示意图**：方法流程图、技术路线图（基金本子）、
机理示意、网络结构图。组件库 `scripts/schemfig.py`（与 paperfig.py 一样，交付时复制进用户的 `figures/`）。

## 何时用 matplotlib 画示意图

| 场景 | 方案 |
|---|---|
| 流程图、技术路线图（节点 + 连线，常带泳道与阶段） | **声明式规格 + `schemfig.py flow`**（下一节），不写坐标 |
| 多阶段 pipeline、含数据 panel、需要论文+汇报双版本 | **matplotlib + schemfig**（本文） |
| 三五个框的轻量示意（能带对齐、简单流程） | 手写 SVG 也可以，字体字号规范照旧 |
| 3D 晶体结构、真实形貌渲染 | VESTA/Blender 出素材，matplotlib 只做排版标注 |

matplotlib 方案的核心优势：布局参数化可迭代（改一个坐标常量全图联动）、能嵌入**真实渲染的数据
panel**（示意图里放的是算出来的图不是画出来的框）、字体与数据图完全一致、一套代码出双风格。

## 声明式流程图（节点 + 连线的图一律用这个）

流程图、技术路线图手拍坐标最容易出问题：间距不匀、箭头绕路、几条线叠成一条分不清。
这类图改成**写规格，由引擎排版**：你只决定每个节点放在哪一格、谁连谁、连线上写什么；
坐标、框的尺寸、连线路径全部由 `schemfig` 计算。

```bash
python3 schemfig.py flow roadmap.json -o figures/roadmap --style all --json   # paper + dark 两版
python3 schemfig.py flow roadmap.json --check --json                          # 只排版体检,不写图
```

```python
fig, info = sf.flowchart(spec, style="paper")   # info["nodes"][id] 是 El,可以继续叠 badge
sf.export(fig, "figures/roadmap")               # 体检把布线诊断与文字/箭头检查合在一起
```

回执退出码:`0` 通过出图;`1` 有 error 级布线/版面诊断(写 `<stem>.check.json`,不出图);`2` 规格本身写错。

### 规格字段

| 字段 | 说明 |
|---|---|
| `direction` | `"LR"` 主线从左到右（默认）；`"TB"` 从上到下（竖版技术路线图） |
| `lanes` | `[{id, label}]`，泳道：责任方、实验线、子课题；可省略 |
| `stages` | 每列一个阶段名（年份、阶段）；可省略 |
| `nodes[]` | `id`、`label`、`sub`（第二行）、`lane`、`col`（从 0 起）、`accent`、`tone`（`"emphasis"` 实底重心，全图 ≤2 个）、`max_w`（换行宽度，英寸） |
| `edges[]` | `from`、`to`、`label`、`accent`（默认 `spine` 灰）、`style`（`"solid"` / `"dashed"`） |
| `accents` | 自定义强调色 `{"red": ["#FFFFFF", "#94070A"]}`（浅色填充，深色描边） |
| `style` | `font`、`label_font`、`header_font`、`node_max_w`、`pad`、`col_gap`、`lane_gap`、`track`、`corner`（默认 0 直角）、`node_lw`、`edge_lw`、`margin` |
| `size` | `max_width` / `max_height`（英寸），排版超出报 `flow/too-large` |

未知字段、重复 id、连到不存在的节点、两个节点放进同一格都会被拦下（`spec/*`，退出码 2）。

```json
{
  "direction": "LR",
  "lanes": [{"id": "data", "label": "数据"}, {"id": "model", "label": "模型"}, {"id": "valid", "label": "验证"}],
  "stages": ["数据准备", "模型构建", "实验验证", "成果"],
  "accents": {"red": ["#FFFFFF", "#94070A"]},
  "nodes": [
    {"id": "d0", "label": "文献与数据库采集", "lane": "data", "col": 0},
    {"id": "d1", "label": "谱图预处理", "sub": "基线校正 · 去噪", "lane": "data", "col": 1},
    {"id": "m1", "label": "化学位移先验", "lane": "model", "col": 1, "accent": "blue"},
    {"id": "m2", "label": "谱峰拟合模型", "lane": "model", "col": 2, "accent": "red", "tone": "emphasis"},
    {"id": "v2", "label": "实测谱图对比", "lane": "valid", "col": 2, "accent": "green"}
  ],
  "edges": [
    {"from": "d0", "to": "d1", "label": "清洗"},
    {"from": "d1", "to": "m1", "label": "提取特征"},
    {"from": "m1", "to": "m2", "label": "约束", "accent": "red"},
    {"from": "m2", "to": "v2", "label": "预测"},
    {"from": "v2", "to": "m1", "label": "残差反馈", "style": "dashed"}
  ]
}
```

### 引擎保证什么

- **网格**：同列同宽、同泳道同高，尺寸由文字实测决定；节点文字按 `max_w` 换行，不缩字号。
- **正交布线**：连线只在列间隙和泳道间隙里走，**不会穿过其它节点**；第一段和最后一段垂直于框边。
- **独立轨道**：经过同一间隙的每条连线占一条轨道，不会叠成一条线；间隙宽度按轨道数自动加宽。
- **端口错开**：同一条框边上的多个端口按对端位置排序后等距错开；同泳道相邻直连会自动对齐成直线。
- **反馈与跳级**：回到前序节点的反馈线、跨过中间节点的跳级线，走泳道间隙绕行。
- **标签**：放在连线最长的一段上，自动避开其它连线；同列上下的短连线把标签放在线旁；间隙按标签实测宽度加宽。

### 写规格的纪律

- **一条主线**：主线沿 `col` 单调推进，支路从主线上最近的节点出发；重心节点（`emphasis`）不超过两个。
- **泳道表达责任或实验线**，不是装饰；阶段（`stages`）表达时间或阶段，列数与阶段数一致。
- **连线标签是语义数据**：写动作、物理量或条件（"预测能垒""残差反馈"），不写整句。
  修布局时先换列、换泳道、调 `style.col_gap` / `lane_gap`，**不许删标签换通过**。
- **交叉（`edge/crossing`，warning）先试交换泳道顺序**；确实避不开就保留，并在交付说明里一句话说明。
- 上屏用（PPT）时 `style.font` 取 16 左右，并用 `size.max_width` 控制在幻灯内容区宽度以内；
  进论文时按栏宽设 `size.max_width`，字号用 `scale_check` 核算。

## 核心技法（按重要性排序）

### 1. 全图坐标布局

所有框、箭头、文字画在 `fig.transFigure`（0–1 全图坐标）上，与 axes 无关；嵌入小图用
`sf.img_axes(fig, [x, y, w, h], S)` 开窗。布局坐标是设计决策，集中写成常量，不要散落在调用里。
圆角框必须传画布长宽比抵消变形——`sf.rbox` 已内置（`mutation_aspect`）。

**位置可以拍，尺寸不许拍。** 中心点坐标是设计决策，你来定；但框的宽高取决于文字渲染后的
实际尺寸，写代码时预测不了（字体度量、CJK 回退都会变）——所以：

- 内容框一律 `sf.text_box(fig, cx, cy, "文字", S, accent="blue")`：先渲染文字实测宽高，
  再按实测值+内边距配框，溢出从机制上不可能；`max_w=` 限宽时自动换行/缩字号；
- 关键指标框 `sf.badge(...)`：给定宽度装不下时以原中心自动加宽；
- 框间连线一律 `sf.connect(fig, elA, elB, color)`：自动取朝向对方的框沿锚点
  （起止点保证在框外），并对弧线采样避障，穿框时自动微调 rad 绕开；
- `rbox`/`text_box`/`badge`/`slab`/`img_axes` 会自动注册为箭头的障碍物；
  背景底带/阶段分区是容器，必须传 `solid=False`，否则箭头会莫名绕路；
  容器豁免只到这一步——**元素不许骑在容器框线上**（要么全进要么全出，
  长文字、徽章伸出底带边线都会被体检 4b 拦下）；
- **先画完所有框，再画箭头**——避障只认画箭头时已注册的障碍物
  （顺序错了 `sf.export` 的体检也能兜住，但会逼你重跑）。

### 2. 双风格一套代码

布局代码写一遍，外层循环风格字典：

```python
for name, S in sf.STYLES.items():        # paper 白底论文版 + dark 深色汇报版
    fig = sf.canvas(12.4, 6.4, S)
    ...                                   # 所有颜色只从 S 取
    sf.export(fig, f"scheme-{name}", dpi=300)   # 体检拦截 + 自动切局部放大块
```

风格字典的纪律：**布局代码里不许出现字面量颜色**。语义键（`txt/sub/band/spine/foot`）+
成对强调色（`S["blue"] = (浅填充, 深描边)`），两个风格里键名完全一致。给用户交付时，
即使只要论文版也保留这个结构——组会汇报版随时白拿。

### 3. 真实感合成 panel，且数据同源

示意图里的"输入图像/中间表示/输出结果"不要画虚线占位框，用 numpy/scipy 合成物理上合理的
数据渲染出来，而且**所有 panel 派生自同一份底层数组**，保证输入-中间-输出逐像素对应，
经得起审稿人放大看：

```python
b = gaussian_filter(rng.standard_normal((N, N)), sigma)   # 高斯滤波 + 阈值 = 相分布
phase[b > np.quantile(b, 1 - frac)] = k                   # 逐相叠加
g = gray_levels[phase] + noise                            # 相分布 -> 灰度图
# 采样点、超像素图、分割结果、统计小图……全部从同一个 phase 派生
```

合成参数（晶粒尺度、相分数、灰度对比）要向真实测量对齐，领域内的人一眼看不出假。

### 4. 颜色贯穿叙事

- 同一实体（某个相/样品/分支）在全图所有 panel 里**永远同色**，底部放色块图例收尾；
- 箭头颜色编码数据流支路（如蓝=稠密形貌流、绿=稀疏化学流、紫=融合后），
  读者不看文字就能沿颜色追踪 pipeline；
- 阶段用浅色圆角底带（`rbox`，`zorder=1`）划分，比框线轻。

### 5. 字号层级 + 缩印核算

定义一套字号常量（模块名 / 副标题 / 小注 / 阶段标题 / 脚注五级），全图只用这五个值：

```python
T_MOD, T_SUB, T_SMALL, T_STAGE, T_FOOT = 14.5, 11.5, 11, 12, 10.5
```

示意图元素多，允许按放大画布设计、印刷时等比缩小——但这与数据图"最终尺寸出图"原则的
差别必须用核算闭合：交付前跑 `sf.scale_check(12.4, 150, 14.5, 10.5)`（设计宽 12.4 in →
A4 版心 150 mm ≈ 51%，14.5 pt → 7.4 pt，10.5 pt → 5.3 pt），确认缩印后最小字号 ≥ 5 pt。
不达标就放大字号或改双栏排版，不许硬缩。

### 6. 关键量化承诺做成 badge

方法图上最值钱的信息是可考核的数字：目标指标（"IoU 较基线 ↑ ≥20 pp"）、精度约束
（"残差 < 1 px"）。用 `sf.badge` 胶囊框高亮，评审扫一眼就能抓住。放框里，不放脚注里。

### 7. 小组件武器库

- **伪 3D 立板**（`sf.slab`）：CNN 特征图/数据块的经典画法，三面亮度分级（1.0/0.88/0.75）出体积感，宽高递减排一排即是编码器；
- **mini-heatmap**：注意力/相关矩阵用 alpha 调制的小方块阵列示意（`Rectangle` + `alpha=att[i,j]`），不放假数据大图；
- **图上散点/节点**：用真实坐标画（如 EDS 采样点落在合成相图的实际位置上），采样节点大圆点白描边、未采样节点小灰点，视觉上自然分出主次；
- **竖排文字**：逐字 `fig.text` 排（如"解码器"竖排在窄框里）。

### 8. zorder 分层纪律

底带 1 → 嵌入图 2 → 箭头 2 → 内容框 3–4 → 高亮节点 5。先定层再画。箭头避障和体检能防住“箭头压字/穿框”，但 zorder 层次仍是设计语言的一部分——该在上层的东西（高亮节点、badge）要真的在上层。

## 体检诊断:按 code 修,会停

`pf.check_layout` / `sf.check` / `schemfig.py flow` 返回的每条诊断都是 `Issue`：
`code`（稳定代码）、`subject`（出问题的对象）、`evidence`（实测数值）、`fixes`（可选修法）、
`severity`（`error` 阻断导出，`warning` 只提示）。有诊断就写进 `<stem>.check.json`，全部清零时自动删除旧报告。

| code | 含义 | 常用修法 |
|---|---|---|
| `spec/*` | 规格写错：未知字段、重复 id、连到不存在的节点、同一格两个节点、未知泳道或强调色、自环 | 照诊断改规格 |
| `flow/too-large` | 排版尺寸超出 `size` 限制 | 减小 `node_max_w` 让文字换行、缩间隙或字号、长主线拆成两条泳道 |
| `flow/too-many-emphasis`（warning） | 重心节点超过 2 个 | 只保留全图重心 |
| `text/out-of-figure` | 文字出画布 | 移回画布内、加大画布或边距 |
| `text/out-of-axes` | 数据坐标标注飘出轴外 | 按数据范围重算坐标、放宽 xlim/ylim |
| `text/overlap` | 两段文字互撞 | 移动其一、拉开间距、精简措辞 |
| `text/crosses-box` | 文字一半在框内一半在框外 | 用 `sf.text_box` 按实测尺寸建框 |
| `container/straddle-*` | 文字或元素骑在底带边线上 | 整体移进或移出底带 |
| `arrow/through-element` | 箭头穿过其它元素 | 调整位置留出通道；节点—连线图改用声明式规格 |
| `edge/shared-corridor` | 两条连线叠在同一段通道上 | 加大 `style.track`、换列或换泳道、删掉低价值连线 |
| `arrow/over-text` | 箭头压过文字或其它连线的标签 | 移动文字、调整路径 |
| `edge/label-no-room` | 连线标签放不进所在线段 | 加大 `col_gap` / `lane_gap`、精简措辞 |
| `arrow/too-short` | 箭头短到退化 | 拉开两元素间距 |
| `edge/crossing`（warning） | 连线交叉 | 交换泳道顺序、让支路从最近的主线节点出发 |

修复纪律（与 SKILL.md 第 3 步一致）：按上表顺序修，每轮只改诊断点名的对象，改完重跑；
**连续两轮告警数没有下降就停下**，在交付说明里如实列出剩下的诊断；
物理量、单位、标注、连线标签不许为了通过体检删掉。

## 示意图自检清单（在 SKILL.md 通用清单之上追加）

- [ ] `scale_check` 核算过缩印字号，最小 ≥ 5 pt
- [ ] 同一实体全图同色，图例齐全；箭头支路颜色有含义且一致
- [ ] 合成 panel 之间数据同源、逐像素对应（输出真的是输入的分割/变换）
- [ ] 双风格都渲染检查过（深色版注意低对比文字）
- [ ] 流程图/技术路线图走声明式规格，回执 `ok: true`；剩下的 `edge/crossing` 已试过交换泳道，保留的在交付说明里解释
- [ ] 内容框全部出自 text_box/badge（无手拍宽高的 rbox+fig.text），连线全部出自 connect
- [ ] sf.export 体检告警为零（未用 strict=False 绕过），局部放大块逐块 Read 过
- [ ] 输出路径、随机种子固定（`default_rng(seed)`），重跑结果一致
