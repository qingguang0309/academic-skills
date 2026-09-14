# paper-slides

生成能直接上台的中文学术汇报 PPT。答辩、开题、中期、组会、基金汇报、会议 talk。

**这是一个自包含的 Claude Agent Skill**——整个 `paper-slides/` 目录可以单独打包分发，
不依赖所在仓库的其它部分。

## 它和"让模型写个 PPT"的区别

不手拍坐标。所有页面通过 `scripts/slidekit.js` 的 Deck API 声明式生成：
你只说"这页放哪些块"，位置、间距、字阶、页码、中西文分字体全部由布局引擎计算。

更关键的是，**重要的规矩被做成了会报警的构建期检查**，而不是写在文档里等人遵守：

| 检查 | 触发条件 |
|---|---|
| 真实素材 | 全篇 0 张实测图 / 截图 / 实拍（`evidence`），也没有 `credits.json` 实景照片 → 报警（`photos: false` 显式豁免） |
| 证据标注 | 自有的图和原生图表没标 `evidence`（实测 / 模拟 / 示意等）→ 报警 |
| 页面填充率 | 低于 62% → 提示这页太空，建议补真实素材或与相邻页合并，不为填版面加句子 |
| 自动降字号 | 内容放不下被引擎降了字号 → 报警（先删字，再缩字号） |
| 页标题 | 中文超过约 18 字、带逗号句号或换行 → 报警（标题只点明主题）；封面标题超三行 → 报警 |
| 重复总结 | "小结 / 总结"类提示框，或提示框与标题正文重复过半 → 报警 |
| 大数字 | `stats` 没写 `note`（测试条件、样本量、适用范围）→ 报警 |
| 结构模板 | 用了 `cards` 卡片块、四分之三的要点组恰好 3 条 → 报警 |
| 结论条 | 内容页没写 `conclusion`、结论条没数字或关键数据没用 `**…**` 标出、页底横条与结论条重复 → 报警 |
| 图文并茂 | 内容页没有图 → 报警（`noFigure: true` 豁免）；文献图没写 `credit` 引用来源 → 报警 |
| 上下标 | 写成 29Si、R2、Q3、δ_cal、CO2 → 报警（改写 `^{29}Si`、`R^{2}`、`δ_{cal}`、`CO_{2}`，渲染为真上下标） |
| 困难与局限 | 答辩 / 结题全篇没讲困难或局限 → 报警 |
| 整段加粗 | `text` 块整段加粗 → 报警 |
| 饼图选型 | 类别超过 3 类 → 报警，建议改降序水平条 |
| 图表配色 | 色板短于系列数 → 直接抛错（否则 pptxgenjs 会 `Math.random()` 取色，同一脚本跑两次颜色不一样） |
| 场合缺失 | 未写 `occasion` → 报警（中文学术封面的必需项） |
| 致谢缺失 | 答辩 / 结题场合没有致谢页 → 报警 |
| 结束页 | 经典结束页没写 `takeaway` → 报警（Q&A 全程停在这页，别只挂一句客套话；ribbon 结束页不要求） |
| AI 词汇 | `wordlint.py` 143 条词表（含口号、无证据的全称判断与水平判断）+ 37 条白名单，四级判定；可连流程图 JSON 一起扫 |

## 快速开始

```bash
npm install                        # pptxgenjs + jszip
pip install -r requirements.txt    # pillow / matplotlib / numpy
node examples/minimal/deck.js      # → minimal.pptx，6 页，零警告
```

跑通后把 `examples/minimal/deck.js` 复制一份改成自己的内容。完整规矩读 `SKILL.md`。

## 目录

```
paper-slides/
├── SKILL.md                 技能定义：十条铁律 + 五步流程
├── scripts/
│   ├── slidekit.js          组件库与布局引擎（唯一必需）
│   ├── fetchimg.py          取 CC 许可实景照片，自动登记署名
│   ├── formula.py           LaTeX → 透明底公式图
│   ├── collage.py           多图确定性拼版
│   ├── aiimg.py             概念图（DashScope，可选）
│   ├── wordlint.py          AI 词汇检查
│   └── assets/              北大主题的校徽与背景素材（仅 pku 主题用）
├── references/
│   ├── design-system.md     字阶、主题、背景层、中文排版
│   ├── layouts.md           块类型与页型参数
│   ├── charts.md            图表选型与实现坑
│   ├── content-discipline.md 去 AI 味的内容审计流程
│   └── ai-wordlist.json     词表
└── examples/minimal/        最小可运行示例
```

## 五套配色主题

`azure`（藏青·金，通用）/ `pine`（墨绿·赭）/ `plum`（绛紫·杏）/
`claude`（赤陶·暖砂，Anthropic 配色）/ `pku`（北大红·燕园金）

加自己单位的主题前先量对比度：primary 需落在 7—11∶1、accent 4.5—5.9∶1（对各自 wash 底），
否则页标题与 kicker 会比其它主题明显偏弱。

## 可选依赖

按需安装，缺了只影响对应功能，不影响出 PPT：

| 用途 | 依赖 |
|---|---|
| 流程图 / 示意图 | 同仓库的 paper-figures skill（Python + matplotlib） |
| 真 LaTeX 公式 | TeX 发行版；没有时自动降级为 matplotlib mathtext |
| 渲染 PDF 目检 | LibreOffice（`soffice`）+ poppler（`pdftoppm`） |
| AI 概念图 | DashScope API key（环境变量或 `~/dashscope-tool/key.txt`） |

## 已知限制

- 中文字体默认 Microsoft YaHei，西文 Arial；本机没有时由系统替换，
  LibreOffice 预览的字距与 PowerPoint 实际打开会有差异，拿不准的页在真机确认。
- `pku` 主题的素材是特定机构的，其它主题下自动跳过；别的单位要做同样的效果，
  用 `bgArt` / `bgArtBlock` / `coverMark` 三个槽位传自己的图。
