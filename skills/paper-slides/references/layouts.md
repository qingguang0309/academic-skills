# 页型版式库与块 API

Deck 的每个方法注册一页;`build()` 时统一渲染(页码、目录、章节导航需要全局信息)。

## Deck 构造

```js
new Deck({
  theme: "azure" | "pine" | "plum",
  lang: "zh" | "en",
  title: "封面主标题(可含\n断行)",
  shortTitle: "页脚短题",         // 建议 ≤12 字
  subtitle: "封面副题(可选)",
  occasion: "开题报告 / 学位论文答辩 / 开放基金汇报 / Conference talk…",
  presenter: "汇报人", advisor: "指导教师(可选)",
  org: "单位", date: "2026 年 7 月",
  hansFont: "Microsoft YaHei",    // 可选覆盖
  latinFont: "Arial",
})
```

## 页型

| 方法 | 页型 | 要点 |
|---|---|---|
| `d.cover({notes?, titleSize?})` | 深色封面 | 场合 kicker + 主标题 + 信息区(汇报人/导师/单位/日期) |
| `d.toc()` | 目录 | 由 section 调用自动生成,含各章节 note |
| `d.section(title, note?)` | 章节过渡 | 超大章节号 + 标题 + 底部全章节导航(当前高亮) |
| `d.page({...})` | 内容页 | 见下 |
| `d.refs([...], {title?})` | 参考文献 | >5 条自动双栏,自动编号 [n] |
| `d.closing({main?, sub?, contact?})` | 结束页 | 深色,默认文案"恳请各位专家批评指正"/"Thank You" |

## 内容页 d.page

```js
d.page({
  kicker: "默认为当前章节名,可覆盖;附录页写 '附录 A'",
  title: "完整结论句;两行内;\n 控制断点",
  sub: "可选的一行补充说明",
  notes: "演讲者备注",
  blocks: [ /* 块数组,纵向流式排布 */ ],
});
```

布局引擎先测量后绘制:总高超出内容区会整体降字号(至 ×0.85),仍溢出则终端警告——警告必须处理(删内容/分页/缩图)。

## 块类型

```js
// 要点列表:小方块行首标记,导语粗体。学术内容页的主力块
{ type: "bullets", items: [
    { lead: "导语:", text: "正文,自动换行" },
    { text: "无导语的条目" },
  ], size: 17, gap: 0.16 }

// 大数字卡:量化目标/核心指标专用,2-4 个一行
{ type: "stats", items: [
    { value: "+20 pp", label: "IoU 提升", note: "≤5% EDS 覆盖" },
  ] }

// 卡片网格:并列概念(风险/模块/贡献点),自动等高
{ type: "cards", cols: 3, items: [{ title: "…", text: "…" }] }

// 图:自动读 PNG/JPEG 尺寸等比缩放,永不变形;caption 自动编号"图 N"
{ type: "figure", path: "assets/fig.png", caption: "图注", credit: "来源",
  maxH: 4.2, maxW: 9, frame: true }

// 三线表:学术规范表格
{ type: "table", header: ["指标", "验证协议"],
  rows: [["…", "…"]], widths: [0.45, 0.55] }   // widths 为占比

// 技术路线/流程:圆形编号 + 连线,横向
{ type: "steps", items: [{ title: "配准", text: "残差 <1 px" }] }

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

- **背景/动机页**:bullets(3 条,带导语) + 可选 callout
- **科学问题页**:text(问题句,居中可加大) + callout(label:"关键构想")
- **数据集/方法概览**:cols[ bullets | bullets ] 或 cards×3
- **架构/路线页**:figure(大图) 或 steps(无现成图时)
- **结果页**:cols[ figure(3) | bullets(2) ],结论写进 title,图上要有标注
- **指标页**:stats(3-4 个) 或 table(指标×验证协议)
- **结论页**:bullets(2-4 条,lead 用"1."、"2."编号) + callout(联系方式/预印本链接)
- **附录页**:kicker 写"附录 A ……",其余同内容页

## 素材准备

- 图优先用 paper-figures skill 现场生成(带标注、配色与 deck 主题呼应);已有图直接引用。
- 从 PDF 抽图:`pdfimages -png -f <页> -l <页> paper.pdf assets/fig`。
- 校徽/logo:用户提供时放封面信息区右侧,自行加 addImage 之外的需求提给 slidekit 维护者,不要在生成脚本里手摆。
