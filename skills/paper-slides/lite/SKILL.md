---
name: academic-deck
description: 生成中文学术汇报 PPT(pptx)。用户提到做 PPT、幻灯片、slides、汇报、组会、开题、中期、答辩、基金汇报、会议 talk、改 PPT、PPT 不好看,或给出论文/提纲要求转成演示文稿时使用。基于 pptxgenjs + slidekit 组件库生成原生可编辑 pptx,声明块而不摆坐标,交付可复现脚本。
---

# academic-deck —— 中文学术汇报 PPT

不手拍坐标。声明"这页放哪些块",位置、间距、字阶、页码、中西文分字体由布局引擎计算。

## 六条规矩

1. **只组装组件。** 直接调 pptxgenjs 的 `addText`/`addShape` 摆坐标 = 违规,那正是排版
   粗糙的根源。所有页面走 Deck API。

2. **每页标题是完整结论句。** 通读全部页标题应当就是完整论证。"研究背景""实验方法"
   这类话题词只允许出现在章节过渡页。

3. **不填色块。** 卡片、大数字、提示框、表头一律不加底色、不画圆角框、不用胶囊 chip
   ——浅底色块是 AI 生成幻灯最好认的胎记。分区靠**线与留白**:大数字用顶部标尺线,
   卡片用顶部细线,提示框用左侧竖线。实心色只出现在封面色块与首尾页的收尾细带。

4. **配真实照片。** 背景页、对象页、装置页配实景图才像专业汇报。用 `fetchimg.py` 取
   CC 许可图片,署名自动落页。`build()` 检查全篇是否有真实照片,0 张报警;
   确实不需要时传 `photos: false` 显式豁免——让它成为一个决定,而不是一次遗漏。

5. **中西文交给 runs 机制。** 自动分字体,不要手拼 `fontFace`,不要在中文里打半角逗号句号。

6. **警告必须清零。** `build()` 会报:页面太空(填充率 <62%)、标题超行、饼图类别过多、
   缺场合、缺 takeaway。这些是写在文档里会被跳过、写成检查才会被执行的东西。

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
  coverStyle: "split",      // split 左竖块(默认) / plate 底部色带 / solid 满版
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
d.page({ title: "完整结论句", blocks: [ /* 见下表 */ ],
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
| `bullets` | 分条论述 | `items: [{lead, text}]`、`size`、`gap` |
| `cards` | 并列的几件事 | `items: [{title, text}]` |
| `stats` | 关键数字 | `items: [{value, label, note}]` |
| `figure` | 图片 | `path`、`caption`、`credit`、`maxH` |
| `table` | 三线表 | `header: []`、`rows: [[]]` |
| `chart` | 原生可编辑图表 | `kind: bar\|barh\|line\|pie`、`data: [{name, labels, values}]`、`height` |
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
- [ ] 通读页标题 = 完整论证
- [ ] 图未变形、关键发现在图上有标注
- [ ] 中西文混排无怪异断行
- [ ] 封面写明了场合;结束页有 takeaway
- [ ] LibreOffice 的字体是替身,字距以 PowerPoint 实际打开为准
