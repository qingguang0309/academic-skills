---
name: academic-deck
description: 生成中文学术汇报 PPT(pptx)。用户提到做 PPT、幻灯片、slides、汇报、组会、开题、中期、答辩、基金汇报、会议 talk、改 PPT、PPT 不好看,或给出论文/提纲要求转成演示文稿时使用。基于 pptxgenjs + slidekit 组件库生成原生可编辑 pptx,声明块而不摆坐标,交付可复现脚本。
---

# academic-deck —— 中文学术汇报 PPT

不手拍坐标。声明"这页放哪些块",位置、间距、字阶、页码、中西文分字体由布局引擎计算。

## 七条规矩

总原则:**少做包装,把具体问题、实际工作和证据讲清楚。** 拿不准一句话是否太空,问一句:
换到别人的课题里是否照样成立?成立就补上研究对象、方法、条件或证据。

1. **只组装组件。** 直接调 pptxgenjs 的 `addText`/`addShape` 摆坐标 = 违规,那正是排版
   粗糙的根源。所有页面走 Deck API。

2. **标题简短,只点明主题;一页一结论。** 页标题如"谱峰拟合方法""原型测试与后续验证",
   中文约 18 字以内,不带逗号句号,不喊口号。结论写进页题下的结论条 `conclusion`:具体事实和数字,
   关键数据用 `**…**` 标主色加粗;标题、结论条、正文、页底横条 `banner` 不重复同一句话。

3. **不用卡片、胶囊、圆角框和大面积色块。** 全文不用 `cards` 块;大数字、提示框、表头一律不加底色
   ——浅底色块是 AI 生成幻灯最好认的胎记。分区靠**线与留白**:大数字用顶部标尺线,提示框用左侧竖线。
   比较用三线表,过程用流程图,结果用数据图。正文 16–17.5 pt、表格 15.5 pt、结论条 18 pt;
   上下标用真的:`^{29}Si`、`R^{2}`、`δ_{cal}`。

4. **图文并茂,真实素材优先。** 每个内容页都要有图;没有合适的就检索文献把原图插进来,figure 块写
   `evidence: "literature"` 并在 `credit` 里注明引用来源;确实不需要图的页传 `noFigure: true`。
   实测谱图、系统截图、失败案例比概念架构图更有说服力;图注用 `evidence` 分清实测、模拟与示意。
   背景页再用 `fetchimg.py` 取 CC 许可实景照片,署名自动落页。`build()` 检查全篇有无真实素材,
   0 张报警;确实没有时传 `photos: false` 显式豁免。

5. **完成与计划分开写。** 条目用 `status: "done" | "prelim" | "planned"` 标出【已实现】
   【初步测试】【拟开展】;大数字的 `note` 写测试条件、样本量或适用范围。

6. **中西文交给 runs 机制。** 自动分字体,不要手拼 `fontFace`,不要在中文里打半角逗号句号。

7. **警告必须清零。** `build()` 会报:页面太空、内容放不下被自动降字号、标题过长或像句子、
   缺结论条或结论条没数字、总结框与正文重复、用了卡片、缺图或文献图没注来源、假上下标、
   大数字缺条件、图未标 evidence、答辩/结题没讲困难与局限、饼图类别过多、缺场合、缺 takeaway。
   这些是写在文档里会被跳过、写成检查才会被执行的东西。

## 用法

```bash
npm install
node deck.js
```

```js
const { Deck } = require("./scripts/slidekit.js");

const d = new Deck({
  theme: "claude",          // azure 藏青 / pine 墨绿 / plum 绛紫 / claude 赤陶
  lang: "zh",               // zh | en
  kind: "defense",          // defense 答辩 / grant 结题 / groupmeeting 组会 / paperreading 文献汇报
  coverStyle: "split",      // split 左竖块(默认) / plate 底部色带 / ribbon 中部+底部双色带 / solid 满版
  headerStyle: "classic",   // numbered = 左上章节号块 + 黑色页题 + 通栏线;sectionStyle / closingStyle 同理可选 list / ribbon
  title: "标题(可含\n手动断行)",
  subtitle: "副标题",
  shortTitle: "页脚短题",
  occasion: "硕士学位论文答辩",   // 中文学术封面的必需项,缺了会警告
  presenter: "×××", advisor: "××× 教授",
  org: "×××大学 ×××学院", date: "2026 年 8 月",
});

d.cover({ notes: "开场白" });
d.toc();
d.section("章节名", "一句话说清这章要回答什么", [
  ["要点一", "说明"], ["要点二", "说明"], ["要点三", "说明"],
]);
d.page({ title: "原型测试与后续验证",
         conclusion: "线宽约束把残差中位数从 **7.4%** 降到 **3.1%**",   // 一页一结论,关键数据标红加粗
         blocks: [ /* 见下表;每页要有图 */ ],
         source: "本页论据的出处", notes: "演讲者备注" });
d.refs(["作者. 标题[J]. 期刊, 2024, 12(3): 45-67."]);
d.acknowledge({ advisor: [["××× 教授", "选题指导"]], funding: [["基金名", "编号"]] });
d.closing({ takeaway: "最想被记住的那句结论", contact: "a@b.edu" });
d.build("talk.pptx");
```

## 块类型

内容页的 `blocks` 数组纵向流式排布,超高自动降字号。

| type | 用途 | 主要字段 |
|---|---|---|
| `bullets` | 分条论述 | `items: [{status, lead, text}]`、`size`、`gap`;`status: done\|prelim\|planned` |
| `cards` | 真正并列、又不适合进表格的少数东西 | `items: [{status, title, text}]` |
| `stats` | 关键数字 | `items: [{status, value, label, note}]`;`note` 写测试条件/样本量,不写报警 |
| `figure` | 图片 | `path`、`caption`、`credit`、`evidence`、`maxH`;`evidence: measured\|screenshot\|photo\|literature\|simulated\|schematic` |
| `table` | 三线表,比较首选 | `header: []`、`rows: [[]]` |
| `chart` | 原生可编辑图表 | `kind: bar\|barh\|line\|pie`、`data: [{name, labels, values}]`、`height`、`evidence` |
| `steps` | 有序流程 | `items: [{title, text}]` |
| `callout` | 提示/推论 | `label`、`text` |
| `cols` | 左右分栏 | `ratio: [1,1]`、`cols: [{blocks:[]}]` |
| `formula` | 公式图 | `path`、`tag`、`where: [[符号, 释义]]` |

页级参数 `source` 是页内文献/数据来源:锚定页底、右对齐到与页码同一条右边缘。
**不要用 callout 写来源**——callout 跟着栏内流走会落在栏中部,引擎会对此报警。

## 首尾页素材(可选)

三个槽位都由作者自带,不含任何内置素材:

```js
new Deck({
  bgArt: "assets/bg.png",        // 首尾页满版极淡肌理
  bgArtBlock: "assets/blk.png",  // split 封面色块上的同源肌理
  coverMark: "assets/mark.png",  // 色块左上角的白色单色标识
  coverMarkH: 1.5,
})
```

素材的淡化要**烘焙进 PNG**,不要靠渲染器的透明度——烘进图里,PowerPoint、
LibreOffice、导出的 PDF 看到的才是同一张。参考配方:转灰阶 → 峰值不透明度约 12%
→ 竖向不透明度斜坡,自 55% 高度起显影、上半页保持纯白。

## 交付前必做

跑完脚本先看终端,**警告清零**;再渲染逐页亲眼看:

```bash
soffice --headless --convert-to pdf talk.pptx && pdftoppm -r 130 -png talk.pdf slide
```

- [ ] 文字无溢出无裁切,块间距均匀,页脚不与内容相撞
- [ ] 页标题短、只点明主题;每个内容页有结论条,关键数据标红加粗;标题、结论条、正文、横条不重复
- [ ] 每个内容页有图,文献图注明来源;上下标是真的(²⁹Si、R²),全文没有卡片
- [ ] 每句过一遍:换到别人的课题里是否照样成立?成立就补对象、方法、条件或证据
- [ ] 完成与计划用 `status` 分开;数字带条件与样本量;"全部达标"之类有逐项证据
- [ ] 图未变形、关键发现在图上有标注;图注分清实测与模拟/示意
- [ ] 答辩/结题讲了具体困难与局限
- [ ] 中西文混排无怪异断行
- [ ] 封面写明了场合;结束页有 takeaway
- [ ] LibreOffice 的字体是替身,字距以 PowerPoint 实际打开为准
