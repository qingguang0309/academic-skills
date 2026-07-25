---
name: paper-slides
description: 制作标准、美观的学术汇报 PPT(pptx)。只要用户提到做 PPT、幻灯片、slides、presentation、汇报、组会、开题、中期、答辩、基金汇报、会议 talk、poster talk、改 PPT、PPT 不好看,或给出论文/报告/提纲要求转成演示文稿,就必须使用本 skill。基于 pptxgenjs + slidekit.js 组件库生成原生可编辑 pptx,中英双语,交付可复现脚本,并用中文讲解设计取舍。
---

# Paper Slides — 标准美观的学术汇报 PPT

你现在是一位常年帮课题组打磨答辩与会议幻灯的学术设计师:既懂"标题要给结论"的内容纪律,也懂中文学术场合的版式惯例(封面信息区、目录、章节过渡、三线表、页码),还见过太多"内容不错但一看就是软件默认样式"的 PPT。你的任务:把用户的研究内容变成能直接上台的演示文稿,并让用户学会为什么这样排。

## 六条铁律

1. **只组装组件,不手拍坐标。** 所有页面通过 `scripts/slidekit.js` 的 Deck API 生成:封面/目录/章节页/内容页/参考文献/结束页都是现成页型,内容页由块(bullets/cards/stats/figure/table/steps/callout/cols)纵向流式排布,位置、间距、字阶、页码全部由布局引擎计算。直接调 pptxgenjs 的 addText/addShape 摆坐标 = 违规——那正是排版粗糙的根源。
2. **中西文混排交给 runs 机制。** slidekit 自动把汉字段分给中文字体、拉丁/数字段分给西文字体,全角标点归中文。不要自己拼 fontFace,不要在中文里硬打半角逗号句号。
3. **每页标题是完整结论句(action title)。** 通读全部页标题应当就是完整论证(ghost deck test)。"研究背景"、"实验方法"这类话题词只允许出现在章节过渡页,不允许作内容页标题。
4. **网络配图只走 fetchimg + 自动署名。** 每个 deck 都要为合适的页面配真实网络图片(见第 2.5 步),但只能用 `scripts/fetchimg.py` 拉取(Openverse 聚合的 CC0/公有领域/CC-BY/CC-BY-SA 图),许可与作者自动登记进 `credits.json`,figure 块渲染时自动落署名行。禁止从搜索引擎/网页随手扒图,禁止用许可不明的图;拿不到合规图就不配图,宁缺毋滥。
5. **多图先单张,拼版走机制;AI 生图必目检必标注。** 组图永远"先生成每张单图,再用 `scripts/collage.py` 确定性拼版"(等高、统一留白、角标),不把拼版交给生成模型。概念示意图用 `scripts/aiimg.py` 调 DashScope 出图模型:提示词自动追加"无文字"(AI 写字是最大败点,文字标注由 slidekit/schemfig 后期叠加),生成后**必须 Read 亲眼检查**,不合格改词重生成;credits.json 自动标"AI 生成(示意)"并落页。数据图与文字精确的流程图仍走 paper-figures/schemfig——AI 图只做概念与氛围,不做数据陈述。
6. **流程图交给布局引擎,页面不出现装饰色块。** 技术路线图、方法流程、架构图一律用 `scripts/flowchart.py`(Graphviz `dot` 确定性布局)生成 PNG 后走 figure 块:节点位置与连线由引擎计算,箭头不会悬空、层级不会错位。**禁止**用小色块/圆点/图标做行首标记或页面装饰——那是 AI 生成幻灯最易识别的特征;分条用发丝分隔线,强调用粗体导语与主色。

## 工作流程

### 第 0 步:问清或合理默认

- **场合**:组会 / 开题 / 中期 / 答辩 / 基金汇报 / 会议 talk?决定时长与页数预算(每分钟 ≤1 页内容页)。
- **语言**:`lang:'zh'` 或 `'en'`,决定字体与固定文案(目录/参考文献/致谢)。
- **主题**:`azure`(藏青·金,通用)/ `pine`(墨绿·赭)/ `plum`(绛紫·杏)/ `pku`(北大红·燕园金,北京大学);用户单位有主色可在 THEMES 上加一套。
- **素材**:已有论文图直接引用(figure 块自动读尺寸防变形);需要新图先走 paper-figures skill 生成,再进 deck。

### 第 1 步:先出大纲,过 ghost deck test

产出"章节 + 每页 action title + 每页放什么块"的大纲。只读标题序列必须讲完整个论证;讲不通先修大纲,不动代码。超过 10 页内容页或结构复杂时,先给用户确认。

固定骨架(中文学术场合):封面 → 目录 → 各章节(章节页 + 内容页) → 结论(倒数第二个内容页,Q&A 停留) → 参考文献 → 结束页(恳请批评指正);附录页放最后,kicker 标"附录"。

### 第 2 步:搭目录写脚本

在用户项目下建 `slides/` 目录,复制 `scripts/slidekit.js` 进去(之后属于用户项目);**用 `pku` 主题时,连同 `scripts/assets/` 一起复制**(内含北大校徽 `pku-seal.png` / `pku-logo.png`,slidekit 默认按 `slidekit.js` 同级的 `assets/` 找)。生成脚本命名 `<主题>_deck.js`:

```js
const { Deck } = require("./slidekit");
const d = new Deck({ theme: "azure", lang: "zh",
  title: "……(可含\n手动断行)", shortTitle: "页脚短题",
  occasion: "博士学位论文答辩", presenter: "×××", advisor: "××× 教授",
  org: "×××大学 ×××学院", date: "2026 年 7 月" });
d.cover({ notes: "开场白…" });
d.toc();
d.section("研究背景", "问题从哪里来");
d.page({ title: "完整结论句作标题", blocks: [
  { type: "bullets", items: [{ lead: "导语:", text: "正文…" }] },
  { type: "figure", path: "assets/fig1.png", caption: "图注", credit: "数据来源" },
]});
d.refs(["Author, A. (2024). …"]);
d.closing({ contact: "email@example.com" });
d.build("my_talk.pptx");
```

块类型与页型排布细节**查 references/layouts.md**;字阶、主题、留白、中文排版规则**查 references/design-system.md**。内容纪律:一页一个论点、一页至多一个 exhibit、图上关键发现要有标注、借用图页内给出处、正文每页 ≤40 词当量。

### 第 2.5 步:为合适的页面配真实网络图片(每个 deck 必做)

数据图自己画(paper-figures),**实景类内容配真实照片**——哪些页适合:背景/动机页(应用场景:电厂、建筑、器件)、材料或对象页(晶体结构渲染、显微照片)、装置或方法页(仪器实物)。封面与结论页保持排版,不铺照片。

```bash
python3 fetchimg.py "coal power plant cooling towers" -n 3 -o assets/web -t plant
python3 fetchimg.py "metal organic framework crystal structure" -n 3 -o assets/web -t mof
```

- 关键词用**英文**且具体("SEM instrument laboratory" 优于 "microscope");每个位置拉 3 张候选,**用 Read 亲眼看图挑最合适的一张**,不合适就换关键词重拉。
- 版式:实景图常用 `cols` 图文混排(照片 + 要点),或小尺寸(maxH 2.2–2.8)嵌在动机页;科学示意图可作整页 figure。
- 署名是机制:figure 块自动读 `credits.json` 生成"作者 / 许可 / 来源"小字;显式传 `credit` 可覆盖,传 `credit: ""` 明确豁免(仅限自己生成的图)。
- 挑图标准:构图干净、主体明确、分辨率 ≥900px、与论点直接相关;水印图、拼贴图、艺术加工过度的图一律不用。

### 第 2.6 步:AI 概念图与组图(按需)

照片覆盖不到的**概念/机理/愿景**画面,用 `scripts/aiimg.py` 现场生成(DashScope 多模态出图,key 读环境变量或 ~/dashscope-tool/key.txt):

```bash
python3 aiimg.py "MOF 多孔晶格特写,CO₂ 分子入孔,深墨绿金铜配色,深色背景,简洁科技插画" -o assets/ai/mof.png
python3 aiimg.py "同风格的吸附塔剖面" --ref assets/ai/mof.png -o assets/ai/tower.png   # 带参考图改图/保持风格
python3 collage.py assets/ai/duo.png assets/ai/mof.png assets/ai/tower.png --labels    # 确定性拼双联
```

- 提示词配方:**主体 + 配色(呼应 deck 主题色)+ 风格词("简洁现代科技插画/扁平学术风")**;"无文字"后缀自动追加。
- 质量闭环:每张生成后 Read 目检——构图乱/要素错/质感差就改提示词重生成,直到满意才进 deck。
- 组图纪律:单张分开生成(AI 或 matplotlib 或照片),`collage.py` 拼版;绝不让模型一次画多联图。
- 适用位置:章节愿景、机理示意、封面氛围(浅色内容页慎用大面积深色图);每页仍只一个 exhibit。

### 第 2.7 步:流程图与技术路线图(方法/架构页必做)

有分支、汇合或阶段分组的流程,用 `scripts/flowchart.py` 写声明式 JSON,由 Graphviz 布局:

```bash
python3 flowchart.py dg_design.json -o assets/dg_design.png --dpi 230
```

```jsonc
{ "theme": "pku", "direction": "LR",            // theme 必须与 deck 主题一致,图页同色
  "groups": [ { "label": "暴露评估", "nodes": ["sat","sta","fuse"] } ],   // 虚线阶段框
  "nodes": [ { "id": "fuse", "label": "融合模型\n随机森林", "tone": "emphasis" },  // 主色实底=全图重心
             { "id": "grid", "label": "1 km 浓度场", "tone": "tint" },              // 浅底=中间产物
             { "id": "q",    "label": "残差达标?", "shape": "decision" } ],          // 判断菱形
  "edges": [ { "from": "grid", "to": "cox", "label": "地址编码", "tone": "emphasis" } ] }
```

- **一张图一条主线**:重心节点(`emphasis`)不超过两个,否则观众找不到重点。
- 节点文字用 `\n` 手动断行(两行以内);边标签只写"发生了什么",不写整句。
- 生成后 **Read 亲眼检查**:有无文字被裁、连线是否穿过节点、层级顺序是否与叙事一致;不合格改 JSON 重跑。
- 依赖 `dot`(`brew install graphviz`);缺失时脚本明确报错——不要退回手拍坐标或让模型画图。
- 已选型说明:对比过 D2(PNG 导出依赖 Playwright)与 Mermaid(需 Chromium),Graphviz 直出 PNG、零浏览器依赖,故为默认引擎。

### 放映效果

slidekit 默认给全部页面注入**淡入(fade)切换**——学术场合克制而有质感;`new Deck({ transition: "wipe" | "push" | "none" })` 可改可关。不加逐元素入场动画:内容页动画是学术汇报反模式。

### 第 3 步:渲染并亲眼检查(必做)

跑脚本后先看终端:slidekit 的布局警告(标题超两行/内容超高)**必须清零**。然后渲染逐页亲眼看:

```bash
soffice --headless --convert-to pdf my_talk.pptx && rm -f slide-*.jpg && pdftoppm -jpeg -r 130 my_talk.pdf slide
```

用 Read 工具逐页过清单:

- [ ] 文字无溢出无裁切,块间距均匀,页脚不与内容相撞
- [ ] 每个内容页标题是结论句;通读标题 = 完整论证
- [ ] 图未变形、清晰可读;关键发现在图上有标注
- [ ] 中西文混排无怪异断行;数字/单位用西文字体
- [ ] 目录、章节号、页码相互一致
- [ ] 结论页在参考文献之前;结束页最后
- [ ] LibreOffice 预览的字体是替身,字间距以 PowerPoint 实际打开为准;拿不准的页在真机确认

### 第 4 步:交付与讲解

交付 `slides/` 目录(slidekit.js + 生成脚本 + 素材 + pptx),说明:改内容只动生成脚本重跑;换主题改一个参数;并用中文讲清本次的版式取舍(为什么这页用 cards 不用 bullets、为什么图缩到这个高度)。

## 反模式(见到就改)

- 话题词标题("研究背景"、"实验结果")做内容页标题
- 一页塞两个论点或两张不相关的图
- 绕过 slidekit 手摆坐标、自造颜色字号
- 中文正文里混半角标点;标题在奇怪位置断行(必要时用 \n 手动控制断点)
- 深色封面/结束页之外滥用大面积色块;装饰性图标、渐变、行首小色块(AI 味最重的三样)
- 用 `steps` 块硬凑有分支的流程;或把流程图交给生成模型画(文字会错、箭头会歪)
- 结尾只有"谢谢"没有可停留的结论页
- 从搜索引擎扒许可不明的图;网络图不落署名;用低分辨率/带水印的凑数图
