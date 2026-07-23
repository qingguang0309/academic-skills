# academic-skills

一套面向科研工作者的 Claude 学术技能（Agent Skills）合集：论文绘图、学术汇报 PPT、论文润色等，覆盖从数据到投稿再到上台汇报的日常环节。目标领域以材料/化学为主（Nature、Science、JACS、Angew、Advanced Materials 等顶刊标准），多数规范对其他实验学科同样适用。

共同方法论：**把质量做成机制，而不是叮嘱**——绘图有五类几何体检 + strict 门拦截（示意图先实测文字再配框、箭头自动避障，文字溢出/箭头压字从构造上杜绝），PPT 有组件库与流式布局引擎（模型不手拍坐标），大图有锚点合成引擎，论文流水线有引用真实性核验门，润色有去 AI 味特征清单与审稿维度清单；每个 skill 都交付可复现脚本/报告，返修只改声明重跑。

## Skill 列表

| Skill | 状态 | 说明 |
|---|---|---|
| [paper-figures](skills/paper-figures/) | ✅ 可用 | 顶刊标准论文绘图：Python/matplotlib 矢量出图，按期刊栏宽定尺寸，内置 XRD/XPS/Raman/电化学/吸附等温线等图型规范与色盲安全配色；方法示意图/技术路线图同样用 matplotlib（真实感合成 panel + 论文/汇报双风格）。交付可复现脚本 + PDF + PNG |
| [paper-slides](skills/paper-slides/) | ✅ 可用 | 标准美观的学术汇报 PPT：pptxgenjs + slidekit.js 组件库，模型只组装组件不手拍坐标；中西文混排自动分字体，封面/目录/章节过渡/三线表/页码等中文学术惯例内建，3 套配色主题、中英双语；产出原生可编辑 pptx + 可复现脚本。示例见 [examples/bse-eds-report/slides](examples/bse-eds-report/slides/) |
| [paper-polish](skills/paper-polish/) | ✅ 可用 | 顶刊编辑视角论文润色：整篇 30+ 条逐条修改意见（Major/Moderate/Minor 分级），每条用中文讲清为什么这样改；改语言不改科学，可疑科学表述单列"编辑提问"；系统性去 AI 味。内置去 AI 味特征清单、审稿维度清单、按 section 组织的顶刊句式库；产出润色报告 + 修改后全文（.tex/.docx 原格式回填） |

此外,仓库内置 **[paperflow](paperflow/)** —— 基于 LangGraph 的论文生成流水线:大纲之后**文献链与图表链并行**(按主题现场生成 matplotlib 图),引用经 Crossref/Semantic Scholar 真实性核验(自动剔除编造 DOI),再渲染进**标准 LaTeX 模板**(SCI 单栏投稿格式 / 北京大学 pkuthss 学位论文)并用 tectonic 编译 PDF,QA 不过自动修订。LLM 后端默认走**本机 claude CLI 登录态**(不需要 API key),端到端演示见 [examples/paperflow-demo](examples/paperflow-demo/)。

多面板大图(架构图/技术路线图)另有 **[figflow](figflow/)** 分治出图工作流:面板由并行子代理生成自检,箭头/色带/徽标由确定性排版引擎按锚点合成(模型不手拍大图坐标,连接类缺陷从机制上消除),再经对抗性审图回炉;示例见 [examples/figflow-demo](examples/figflow-demo/)。

## 安装

### Claude Code（推荐）

复制 skill 到个人技能目录（全局可用）：

```bash
git clone https://github.com/qingguang0309/academic-skills.git
cp -r academic-skills/skills/paper-figures academic-skills/skills/paper-slides academic-skills/skills/paper-polish ~/.claude/skills/
```

或只装进某个项目：复制到项目的 `.claude/skills/` 下。

运行时依赖：paper-figures 需要 Python + matplotlib；paper-slides 需要 Node.js（生成时 `npm install pptxgenjs`），视觉检查用 LibreOffice + poppler（`soffice`/`pdftoppm`，可选）。

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
| [bse-eds-report](examples/bse-eds-report/) | 真实基金申请书再生成研究计划报告；[slides/](examples/bse-eds-report/slides/) 为 paper-slides 生成的 18 页汇报 PPT |
| [figflow-demo](examples/figflow-demo/) | figflow 分治出图：BSE–EDS 四阶段架构图（并行面板 + 锚点合成） |

## 目录结构

```
academic-skills/
├── paperflow/                    # LangGraph 论文生成流水线(引用核验/组装/QA)
├── figflow/                      # 分治出图工作流(并行面板+确定性排版引擎)
├── examples/                     # 端到端演示(paper-figures-demo、paperflow-demo…)
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
│   │       └── schemfig.py       # 示意图组件库（圆角框/曲线箭头/伪3D/双风格）
│   ├── paper-slides/
│   │   ├── SKILL.md              # 触发条件 + 三条铁律 + 工作流程
│   │   ├── references/
│   │   │   ├── design-system.md  # 网格/字阶/主题/中文排版规则
│   │   │   └── layouts.md        # 页型版式库与块 API
│   │   └── scripts/
│   │       └── slidekit.js       # 学术幻灯组件库（随交付复制给用户）
│   └── paper-polish/
│       ├── SKILL.md              # 编辑视角润色流程（意见分级 + 去 AI 味 pass）
│       └── references/
│           ├── deai-style-guide.md # 去 AI 味特征清单与替换规则
│           ├── editor-checklist.md # 按 section 的审稿维度清单
│           └── phrasebank.md      # 顶刊句式库（按 section 组织）
└── .claude-plugin/
    └── marketplace.json          # Claude Code 插件市场清单
```

## 规划中的方向

- cover-letter / response-letter：投稿信与审稿回复
- literature-survey：文献调研与综述表格

## License

MIT
