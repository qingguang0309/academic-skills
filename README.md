# academic-skills

一套面向科研工作者的 Claude 学术技能（Agent Skills）合集：论文绘图、论文润色等，覆盖从数据到投稿的日常环节。目标领域以材料/化学为主（Nature、Science、JACS、Angew、Advanced Materials 等顶刊标准），多数规范对其他实验学科同样适用。

## Skill 列表

| Skill | 状态 | 说明 |
|---|---|---|
| [paper-figures](skills/paper-figures/) | ✅ 可用 | 顶刊标准论文绘图：Python/matplotlib 矢量出图，按期刊栏宽定尺寸，内置 XRD/XPS/Raman/电化学/吸附等温线等图型规范与色盲安全配色，交付可复现脚本 + PDF + PNG |
| paper-polish | 🚧 计划中 | 顶刊编辑视角论文润色：逐条修改意见 + 中文讲解 + 去 AI 味 |

## 安装

### Claude Code（推荐）

复制 skill 到个人技能目录（全局可用）：

```bash
git clone https://github.com/<你的用户名>/academic-skills.git
cp -r academic-skills/skills/paper-figures ~/.claude/skills/
```

或只装进某个项目：复制到项目的 `.claude/skills/` 下。

也可以作为插件市场安装：

```
/plugin marketplace add <你的用户名>/academic-skills
/plugin install academic-skills@academic-skills
```

### Claude.ai / Claude 桌面版

在 Settings → Capabilities 中上传 skill 文件夹（或打包的 `.skill` 文件）。

## 设计理念

- **数据图一律 Python + matplotlib，矢量输出**——物理尺寸精确、字体可嵌入、完全可复现，这是发表级图片与"屏幕好看"图表的分水岭。
- **按最终印刷尺寸出图**，字号所见即所得，从根上消灭"图印出来字太小"。
- **交付脚本而不只是图片**：返修改两行数据即可重跑，同一篇论文所有图风格天然一致。
- **中文讲解**：不只给结果，还讲清每个设计取舍，用一次学一次。

## 目录结构

```
academic-skills/
├── skills/
│   └── paper-figures/
│       ├── SKILL.md              # 技能主文件（触发条件 + 工作流程）
│       ├── references/           # 按需加载的规范文档
│       │   ├── chart-types.md    # 各类表征图型规范（XRD/XPS/电化学/…）
│       │   ├── journal-specs.md  # 期刊栏宽/字号/DPI/TOC 规格速查
│       │   └── color-and-style.md# 配色（Okabe-Ito/viridis）与风格细节
│       └── scripts/
│           └── paperfig.py       # 统一样式与导出工具（随交付复制给用户）
└── .claude-plugin/
    └── marketplace.json          # Claude Code 插件市场清单
```

## 规划中的方向

- paper-polish：迁移并完善现有润色 skill
- cover-letter / response-letter：投稿信与审稿回复
- literature-survey：文献调研与综述表格

## License

MIT
