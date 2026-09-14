# 页型版式库与块 API

Deck 的每个方法注册一页;`build()` 时统一渲染(页码、目录、章节导航需要全局信息)。

## Deck 构造

```js
new Deck({
  theme: "azure" | "pine" | "plum" | "claude" | "pku",
  lang: "zh" | "en",
  kind: "defense" | "grant" | "groupmeeting" | "paperreading",
  title: "封面主标题(可含\n断行,可用 ^{29}Si 这类行内标记)",
  shortTitle: "页脚短题",         // 建议 ≤12 字
  subtitle: "封面副题(可选)",
  occasion: "开题报告 / 学位论文答辩 / 博士资格考试 / Conference talk…",
  presenter: "汇报人", advisor: "指导教师(可选)",
  org: "单位", date: "2026 年 9 月",
  // 页型变体:pku 主题的答辩/结题场合默认 ribbon / numbered / list / ribbon,其它主题默认经典版式
  coverStyle: "ribbon" | "split" | "plate" | "band" | "solid",
  headerStyle: "numbered" | "classic",
  sectionStyle: "list" | "classic",
  closingStyle: "ribbon" | "classic",
  hansFont: "Microsoft YaHei",    // 可选覆盖
  latinFont: "Arial",
})
```

## 页型

| 方法 | 页型 | 要点 |
|---|---|---|
| `d.cover({notes?, titleSize?})` | 封面 | ribbon:左上校标 + 中部色带(场合/题名/副题)+ 底部色带(汇报人/导师/单位日期);其它变体见 SKILL.md 第 1 步 |
| `d.toc()` | 目录 | 由 section 调用自动生成,含各章节 note |
| `d.section(title, note?)` | 章节过渡 | list:只留章节列表,当前章高亮;classic:超大章节号 + 标题 + note + 底部导航 |
| `d.page({...})` | 内容页 | numbered 页眉:左上章节号块 + 黑色页题 + 通栏线 + 右上校徽;结论条与页底横条见下 |
| `d.refs([...], {title?})` | 参考文献 | >5 条自动双栏,自动编号 [n] |
| `d.acknowledge({advisor, collab, funding, facility, group})` | 致谢 | 具体的人与贡献、基金全称加编号 |
| `d.closing({main?, takeaway?, contact?})` | 结束页 | ribbon:色带 + 白色校徽 + "敬请各位老师批评指正";classic:takeaway + 联系方式 + 底部细带 |

## 内容页 d.page

```js
d.page({
  kicker: "默认为当前章节名,可覆盖;附录页写 '附录 A'(numbered 页眉不显示 kicker)",
  title: "简短主题,如'原型测试与后续验证';单行,不写结论句",
  conclusion: "页题下的结论条(18 pt):具体事实和数字,关键数据用 **…** 标主色加粗;无结论的页传 false",
  banner: "可选:页底主色横条,白字,按需使用,说结论条之外的一句",
  noFigure: false,     // 确实不需要图的页传 true,否则缺图报警
  sub: "可选的一行补充说明",
  notes: "演讲者备注:这页的完整论述、怎么讲、怎么答",
  source: "本页论据的出处;传字符串或数组",
  blocks: [ /* 块数组,纵向流式排布 */ ],
});
```

### 行内标记

所有经 slidekit 渲染的文字(页题、结论条、正文、表格、图注)都支持:

| 写法 | 效果 | 例 |
|---|---|---|
| `**…**` | 主色加粗(结论条里标关键数据) | `残差降到 **3.1%**` |
| `^{…}` | 真上标 | `^{29}Si`、`Q^{n}`、`R^{2}` |
| `_{…}` | 真下标 | `δ_{cal}`、`CO_{2}` |

也可以直接用 Unicode 上标(`²⁹Si`、`R²`)。写成 `29Si`、`R2`、`Q3`、`δ_cal`、`CO2` 会报警——那是假上下标。

### source:页内文献/数据来源

来源标注属于**页面**,不属于内容流。它锚定页底(底沿固定在 6.98 in,多行向上长)、
右对齐到与页码同一条右边缘,读作页脚区的第二行;内容区高度由引擎自动扣除,正文永远压不到它。

不加"来源:"前缀、不加分隔线——拆过的两份真实汇报都没有这两样,加了等于给页面装上双层底框。
右对齐本身就是"这是注不是正文"的信号。字号 12 pt(与参考文献页同号),颜色 `muted`
而不是 `faint`:后者在白底上对比度只有 2.6:1,投影时等于没写。

**不要用 callout 块写来源**——callout 跟着栏内纵向流走,会落在栏中部。引擎会对此发警告。

三层出处 API 各管一段,不要混用:

| 场景 | 用什么 | 落在哪 |
|---|---|---|
| 整页论据的出处 | `page({ source })` | 页底,右对齐 |
| 某一张图自己的出处 | `figure` 块的 `credit` | 图注行内,跟着图走 |
| 全篇著录 | `d.refs([...])` | 参考文献页 |

一页里上下两张图来自不同文献时,用两个 `figure.credit`,不要在 `source` 里堆两条——
那会丢掉"哪条对应哪张图"。来源超过两行会警告且**不截断**:静默丢掉一条文献是署名缺失,
不是排版问题。

布局引擎先测量后绘制:总高超出内容区会整体降字号(至 ×0.85)并**报警**——放不下时先删字,再考虑缩字号;降到 ×0.85 仍溢出则报"已降字仍溢出"。两种警告都必须处理(删内容/分页/缩图)。

## 块类型

```js
// 要点列表:条目间发丝分隔线,粗体导语作强调(无行首色块)。学术内容页的主力块
// rule:false 可关分隔线(条目极短或本身已成表格感时)
// status:"done"|"prelim"|"planned" → 导语前加【已实现】【初步测试】【拟开展】,完成与计划分开写
{ type: "bullets", items: [
    { status: "done", lead: "谱峰拟合:", text: "12 张实测 ¹H 谱,残差中位数 3.1%" },
    { status: "planned", lead: "外部验证:", text: "拟在 2 台不同场强的仪器上复测" },
    { text: "无导语的条目" },
  ], size: 17, gap: 0.16 }

// 大数字卡:核心指标专用,2-4 个一行。note 必写测试条件/样本量/范围,缺了报警;
// 目标值加 status:"planned"(标签落在 note 前)
{ type: "stats", items: [
    { value: "+20 pp", label: "IoU 提升", note: "≤5% EDS 覆盖,n = 48" },
  ] }

// 卡片网格:全文不用——用了就报警。比较改 table,并列要点改 bullets,过程改流程图;
// API 仅为兼容旧脚本保留
{ type: "cards", cols: 3, items: [{ title: "…", text: "…" }] }

// 图:自动读 PNG/JPEG 尺寸等比缩放,永不变形;caption 自动编号"图 N"
// evidence 分清证据类型,图注自动带标签:measured 实测 / screenshot 截图 / photo 实拍 /
// literature 文献数据 / simulated 模拟 / schematic 示意。自有的图不标会报警
// (fetchimg / aiimg 取来的图由署名行交代来源,不报)。chart 块同样支持 evidence
{ type: "figure", path: "assets/fig.png", caption: "图注", credit: "来源",
  evidence: "measured", maxH: 4.2, maxW: 9, frame: true }

// 三线表:学术规范表格
{ type: "table", header: ["指标", "验证协议"],
  rows: [["…", "…"]], widths: [0.45, 0.55] }   // widths 为占比

// 技术路线/流程:圆形编号 + 连线,横向
{ type: "steps", items: [{ title: "配准", text: "残差 <1 px" }] }
// ↑ 仅限简单线性步骤。有分支/汇合/分组阶段的流程图用 paper-figures skill 绘制 PNG 后走 figure 块(evidence:"schematic")

// 提示框:声明、结论强调;tone:'warn' 用于"数值为目标非结果"类声明
{ type: "callout", label: "说明", text: "…", tone: "accent" | "warn" }

// 双栏/多栏:图文并排的标准方式(图左文右)
{ type: "cols", ratio: [3, 2], cols: [
    { blocks: [{ type: "figure", ... }] },
    { blocks: [{ type: "bullets", ... }] },
  ] }

{ type: "text", text: "自由段落", size, color, bold, align }
{ type: "spacer", h: 0.2 }
```

## 常用页配方

先按内容选 exhibit,再选块:

| 这页要呈现 | 用什么 |
|---|---|
| 几个方案/条件/样品的比较 | `table`(三线表) |
| 过程、流程、技术路线 | paper-figures skill 绘制的流程图走 `figure`(`evidence: "schematic"`);3–5 步、无分支的线性时间条才用 `steps` |
| 结果 | 数据图:`chart` 或 paper-figures 出图走 `figure`,标 `evidence` |
| 真实工作的样子 | 实测谱图、系统截图、失败案例走 `figure`(`evidence: "measured"` / `"screenshot"`) |
| 这页没有合适的自有图 | 检索文献原图走 `figure`(`evidence: "literature"`,`credit` 写引用来源) |
| 并列要点 | `bullets`(全文不用 `cards`) |

页标题一律只点明主题;下面说的"结论"指页题下的结论条 `conclusion`。

- **问题页**:text(问题句,可加大) + 一张说明问题的实测图或实景图;条数、配图由内容定
- **方法页**:流程图 + bullets(关键参数与约束,给出数值)
- **结果页**:cols[ figure(3) | bullets(2) ],bullets 第一条写结论并带条件与样本量,图上要有标注
- **原型测试与后续验证页**:bullets 用 `status` 分开【已实现】【初步测试】【拟开展】,测试条目写清条件与样本量
- **指标页**:table(指标 × 实测值 × 测试条件);stats 只放 2–4 个最关键的数,`note` 写条件
- **局限与下一步页**(答辩/结题必有):bullets 写具体困难——哪一步没做通、原因、打算怎么试;失败案例配图
- **结论页**:bullets(2–4 条,lead 用"1."、"2."编号);不再加总结提示框
- **附录页**:kicker 写"附录 A ……",其余同内容页

## 素材准备

- 数据图优先用 paper-figures skill 现场生成(带标注、配色与 deck 主题呼应);已有图直接引用。
- **真实网络图**:`python3 fetchimg.py "<英文关键词>" -n 3 -o assets/web -t <前缀>`,只回 CC0/公有领域/CC-BY/CC-BY-SA;逐张 Read 挑选;figure 块自动从 `assets/web/credits.json` 落署名(显式 `credit` 覆盖之)。适合背景/应用场景/材料结构/仪器实物页;不适合封面与结论页。
- 从 PDF 抽图:`pdfimages -png -f <页> -l <页> paper.pdf assets/fig`。
- 校徽/logo:用户提供时放封面信息区右侧,自行加 addImage 之外的需求提给 slidekit 维护者,不要在生成脚本里手摆。

```js
// 实景图 + 要点的标准配方(动机/应用页)
{ type: "cols", ratio: [2, 3], cols: [
    { blocks: [{ type: "figure", path: "assets/web/plant_1.jpg", maxH: 3.0 }] },  // 署名自动
    { blocks: [{ type: "bullets", items: [ … ] }] },
  ] }
```
