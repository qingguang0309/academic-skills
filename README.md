# academic-skills

一套面向科研工作者的 Claude 学术技能（Agent Skills）合集：论文绘图、学术汇报 PPT、论文润色、Word 文档规范等，覆盖从数据到投稿、上台汇报再到成文交付的日常环节。目标领域以材料/化学为主（Nature、Science、JACS、Angew、Advanced Materials 等顶刊标准），多数规范对其他实验学科同样适用。

共同方法论：**把质量做成机制，而不是叮嘱**——绘图有五类几何体检 + strict 门拦截（示意图先实测文字再配框、箭头自动避障，文字溢出/箭头压字从构造上杜绝），PPT 有组件库与流式布局引擎（模型不手拍坐标），大图有锚点合成引擎，论文流水线有引用真实性核验门，润色与幻灯都有去 AI 味清单（论文查词汇、幻灯查结构：三项对称癖/导语对仗/每页同构由节拍审计拦下）；每个 skill 都交付可复现脚本/报告，返修只改声明重跑。

## Skill 列表

| Skill | 状态 | 说明 |
|---|---|---|
| [paper-figures](skills/paper-figures/) | ✅ 可用 | 顶刊标准论文绘图：Python/matplotlib 矢量出图，按期刊栏宽定尺寸，内置 XRD/XPS/Raman/电化学/吸附等温线等图型规范与色盲安全配色；方法示意图同样用 matplotlib（真实感合成 panel + 论文/汇报双风格）；流程图/技术路线图写声明式 JSON 规格，引擎按“泳道 × 列”网格排版并正交布线；导出前几何体检输出结构化诊断（code/证据/修法），按修复顺序修、两轮不降即停。交付可复现脚本 + PDF + PNG |
| [paper-slides](skills/paper-slides/) | ✅ 可用 | 标准美观的学术汇报 PPT：pptxgenjs + slidekit.js 组件库，模型只组装组件不手拍坐标；中西文混排自动分字体，封面/目录/章节过渡/三线表/页码等中文学术惯例内建，5 套配色主题（含北大红 `pku` 主题：答辩版式——红带封面、章节号页眉、章节列表页、红带结束页）、中英双语；页题下结论条（关键数据标红加粗）、真上下标、每页有图（缺图报警，文献图须注来源）、全文不用卡片、正文 16–17.5 pt；fetchimg 按题目拉取 CC 许可真实网络配图（格式嗅探/转码/压缩/署名清洗，且 build 时检查全篇是否有真实素材、0 张即报警），自绘流程图/技术路线图写声明式 JSON 规格、由 paper-figures 的 schemfig 自动排版与正交布线，formula 把 LaTeX 方程渲染进页面（自动降级 LaTeX→mathtext）、算法块排伪代码，chart 出原生可编辑图表（饼图守三条判据否则强制换水平条），wordlint 按四档判定扫 AI 词汇与口号（白名单保护正常术语），页标题只点明主题、完成与计划用 status 标出【已实现】【拟开展】、图注用 evidence 分清实测与示意，标题过长、总结框重复、卡片套分类模板、大数字缺条件、答辩没讲困难与局限都在 build 时报警，填充率低于阈值即报警，aiimg 调 DashScope 出图模型生成概念示意图（目检回炉），组图先单张再 collage 确定性拼版，全部署名由 credits.json 机制自动落页；全片默认注入克制的放映切换效果。产出原生可编辑 pptx + 可复现脚本。示例见 [examples/bse-eds-report/slides](examples/bse-eds-report/slides/) |
| [paper-polish](skills/paper-polish/) | ✅ 可用 | 顶刊编辑视角论文润色：整篇 30+ 条逐条修改意见（Major/Moderate/Minor 分级），每条用中文讲清为什么这样改；改语言不改科学，可疑科学表述单列"编辑提问"；系统性去 AI 味。内置去 AI 味特征清单、审稿维度清单、按 section 组织的顶刊句式库；产出润色报告 + 修改后全文（.tex/.docx 原格式回填） |
| [paper-word](skills/paper-word/) | ✅ 可用 | 学术 Word 文档风格规范：python-docx 脚本一键套版——页眉左侧北大校徽 + 右侧文档标题 + 北大红分隔线，页脚"第X页/共X页"页码域，全文各级标题（Title/Subtitle/Heading 1–9，所有级别）统一北大红（样式级 + 段落级双重兜底），正文宋体 + Times New Roman、标题微软雅黑 + Arial；技术文档强制参考文献 + 脚注，写作强调去 AI 味、结论先行、直接简洁。与 docx skill 配合：先生成内容再套版 |

此外,仓库内置 **[paperflow](paperflow/)** —— 基于 LangGraph 的论文生成流水线:大纲之后**文献链与图表链并行**(按主题现场生成 matplotlib 图),引用经 Crossref/Semantic Scholar 真实性核验(自动剔除编造 DOI),再渲染进**标准 LaTeX 模板**(SCI 单栏投稿格式 / 北京大学 pkuthss 学位论文)并用 tectonic 编译 PDF,QA 不过自动修订。LLM 后端默认走**本机 claude CLI 登录态**(不需要 API key),端到端演示见 [examples/paperflow-demo](examples/paperflow-demo/)。

多面板大图(架构图/技术路线图)另有 **[figflow](figflow/)** 分治出图工作流:面板由并行子代理生成自检,箭头/色带/徽标由确定性排版引擎按锚点合成(模型不手拍大图坐标,连接类缺陷从机制上消除),再经对抗性审图回炉;示例见 [examples/figflow-demo](examples/figflow-demo/)。

skill 改得好不好用数字说话:**[evals/paper-figures](evals/paper-figures/)** 固定 5 道出图题(XRD、CV+EIS、吸附等温线、技术路线图、TOC),模型第一次交付后立即冻结,按内容正确、独立体检零 error、人工看过三关打分,结果连同 skill 版本哈希记进 history.jsonl。

## 安装

### Claude Code（推荐）

复制 skill 到个人技能目录（全局可用）：

```bash
git clone https://github.com/qingguang0309/academic-skills.git
cp -r academic-skills/skills/paper-figures academic-skills/skills/paper-slides academic-skills/skills/paper-polish academic-skills/skills/paper-word ~/.claude/skills/
```

或只装进某个项目：复制到项目的 `.claude/skills/` 下。

运行时依赖：paper-figures 需要 Python + matplotlib；paper-slides 需要 Node.js（生成时 `npm install pptxgenjs`），视觉检查用 LibreOffice + poppler（`soffice`/`pdftoppm`，可选）；paper-word 需要 Python + python-docx。

也可以作为插件市场安装：

```
/plugin marketplace add qingguang0309/academic-skills
/plugin install academic-skills@academic-skills
```

### Claude.ai / Claude 桌面版

在 Settings → Capabilities 中上传 skill 文件夹（或打包的 `.skill` 文件）。

## 本地工作台（web/）

仓库自带一个 Claude 风格的本地工作台：概览统计、示例任务一键运行（实时日志与进度）、产物资源库（点击预览 PNG/PDF/PPTX）、技能管理（安装/更新到 `~/.claude/skills`、在线阅读技能文档）。

```bash
cd web && npm install && npm run dev   # → http://localhost:3620
```

详见 [web/README.md](web/README.md)。

## 设计理念

- **数据图一律 Python + matplotlib，矢量输出**——物理尺寸精确、字体可嵌入、完全可复现，这是发表级图片与"屏幕好看"图表的分水岭。
- **按最终印刷尺寸出图**，字号所见即所得，从根上消灭"图印出来字太小"。
- **版式交给组件库,模型只做内容决策**：paper-slides 的 slidekit（页型/字阶/中西文分字体/页码目录）与 paper-figures 的 paperfig/schemfig 同理——手拍坐标是排版粗糙的根源,组件化才能张张一致。
- **交付脚本而不只是成品**：返修改两行声明即可重跑，同一篇论文的图、同一份汇报的页风格天然一致。
- **中文讲解**：不只给结果，还讲清每个设计取舍，用一次学一次。

## 示例

| 示例 | 演示内容 |
|---|---|
| [paper-figures-demo](examples/paper-figures-demo/) | OER 电催化组图：paper-figures 按期刊栏宽出版级绘图 |
| [paperflow-demo](examples/paperflow-demo/) | paperflow 端到端：大纲 → 并行文献/图表链 → 引用核验 → LaTeX/PDF |
| [tcm-flavonoid-slides](examples/tcm-flavonoid-slides/) | paper-slides 原生图表（柱/环/条/折线）+ 填充率治理：陈皮黄酮答辩 17 页 |
| [diffusion-midterm-slides](examples/diffusion-midterm-slides/) | paper-slides 无色块版式 + LaTeX 公式/算法块：扩散模型少步采样中期考核 18 页 |
| [pm25-defense-slides](examples/pm25-defense-slides/) | paper-slides 北大模板：PM2.5 队列研究答辩 19 页（Graphviz 技术路线图 + CC 实景照片 + 数据图） |
| [bse-eds-report](examples/bse-eds-report/) | 真实基金申请书再生成研究计划报告；[slides/](examples/bse-eds-report/slides/) 为 paper-slides 生成的 18 页汇报 PPT |
| [figflow-demo](examples/figflow-demo/) | figflow 分治出图：BSE–EDS 四阶段架构图（并行面板 + 锚点合成） |

## 目录结构

```
academic-skills/
├── paperflow/                    # LangGraph 论文生成流水线(引用核验/组装/QA)
├── figflow/                      # 分治出图工作流(并行面板+确定性排版引擎)
├── examples/                     # 端到端演示(paper-figures-demo、paperflow-demo…)
├── evals/paper-figures/          # 首次出图可用率评测(5 道固定题,冻结交付后三关打分)
├── web/                          # 本地工作台(Next.js:运行/资源预览/技能管理)
├── skills/
│   ├── paper-figures/
│   │   ├── SKILL.md              # 技能主文件（触发条件 + 工作流程）
│   │   ├── references/           # 按需加载的规范文档
│   │   │   ├── chart-types.md    # 各类表征图型规范（XRD/XPS/电化学/…）
│   │   │   ├── journal-specs.md  # 期刊栏宽/字号/DPI/TOC 规格速查
│   │   │   ├── color-and-style.md# 配色（Okabe-Ito/viridis）与风格细节
│   │   │   └── schematic-figures.md # 方法示意图/技术路线图技法
│   │   └── scripts/
│   │       ├── paperfig.py       # 数据图统一样式与导出工具（随交付复制给用户）
│   │       └── schemfig.py       # 示意图组件库（测字配框/避障箭头/声明式流程图引擎/双风格）
│   ├── paper-slides/
│   │   ├── SKILL.md              # 触发条件 + 十条铁律 + 工作流程
│   │   ├── references/
│   │   │   ├── design-system.md  # 网格/字阶/主题（含 pku 北大主题）/中文排版规则
│   │   │   └── layouts.md        # 页型版式库与块 API
│   │   └── scripts/
│   │       ├── slidekit.js       # 学术幻灯组件库（随交付复制给用户）
│   │       ├── fetchimg.py       # 按题目拉取 CC 许可网络配图 + 自动署名
│   │       ├── aiimg.py          # DashScope 出图模型生成概念示意图
│   │       ├── collage.py        # 组图确定性拼版
│   │       └── assets/           # 北大校徽（pku-seal.png / pku-logo.png，pku 主题用）
│   ├── paper-polish/
│   │   ├── SKILL.md              # 编辑视角润色流程（意见分级 + 去 AI 味 pass）
│   │   └── references/
│   │       ├── deai-style-guide.md # 去 AI 味特征清单与替换规则
│   │       ├── editor-checklist.md # 按 section 的审稿维度清单
│   │       └── phrasebank.md      # 顶刊句式库（按 section 组织）
│   └── paper-word/
│       ├── SKILL.md              # Word 文档风格规范（版式 + 文风）
│       ├── scripts/
│       │   └── apply_style.py    # python-docx 套版：页眉页脚 + 各级标题北大红
│       └── assets/
│           └── pku_logo.png      # 页眉北大校徽
└── .claude-plugin/
    └── marketplace.json          # Claude Code 插件市场清单
```

## 规划中的方向

- cover-letter / response-letter：投稿信与审稿回复
- literature-survey：文献调研与综述表格

## License

MIT
