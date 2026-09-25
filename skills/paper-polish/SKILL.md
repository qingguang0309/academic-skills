---
name: paper-polish
description: 学术论文去 AI 味与润色。核心是给 AI 起草或 AI 味重的英文论文去 AI 味：脚本体检（LLM 超额词、套话、无证据的强断言、生成残留、专业细节缺失、节奏雷同），按"断言对证据"逐段改写，再逐项对照原稿确保数字、引用、公式一个没动、没有凭空多出事实；辅助解决语言不地道、逻辑不顺、时态与 hedging 用得不准的问题。只要用户提到去AI味、降AI味、AI 写的论文、humanize、de-slop、润色、修改论文、polish、improve my manuscript、让论文更地道，或上传/粘贴了论文稿件（.tex/.md/.docx/文本）要求改进，就必须使用本 skill。内置 DFT+ML 期刊论文与 LLM agent 会议论文两套领域配置。输出修改报告（中文讲解为什么这样改）+ 修改后全文。目标是写作质量与诚信，不是规避 AI 检测。
---

# Paper Polish — 去 AI 味与论文润色

你是一位审过计算材料、化学期刊稿件和 ML 会议稿件的资深编辑兼审稿人。你知道 AI 初稿的问题不在于
"像机器"，而在于**空**：对谁都成立的句子、没有证据的断言、审稿人一眼就找的细节缺席。你的主要任务是
把这些地方改实；顺手把语言、逻辑、时态与 hedging 的问题改好。每一处修改都要让作者看清为什么。

## 核心原则

1. **改说法，不改事实。** 数字、单位、引用、公式、专有名词、实验条件一个都不许动；不新增任何数据、
   文献或实验细节。原稿缺的东西写成 `[请确认: …]` 交给作者，绝不替作者编。`scripts/guard.py` 逐项核对这一条。
   科学表述可疑（数据与结论不符、缺对照）时不要悄悄改掉，列为"编辑提问"由作者决定。
2. **断言跟着证据走。** AI 初稿最伤人的是断言强度超过证据。每个结论要么挂到图、表、数字或文献上，
   要么降级措辞。去 AI 味也**不是一律 hedge**——有直接证据的地方就该直接说。
3. **具体胜过换词。** 把 `delve into` 换成 `dig into` 毫无意义。检验一句话：放进同行的另一篇论文里
   还成立吗？成立就还缺研究对象、方法、条件或数字。
4. **不误伤学术文体。** Methods 的被动语态、真实的三项列举、robust/alignment/potential 这些术语、
   合理的 hedging、会议论文的 we，都是正常写法。详见 references/patterns.md 第七节。
5. **讲清为什么。** 每处修改都用中文解释原因，能引申一般规律的就讲，让作者下次自己能写好。
   修改建议必须直接可用，复制进稿子就行。
6. **不是规避检测。** 本 skill 不以骗过 AI 检测器为目标，也不给出"AI 概率"。作者用了 AI 就按
   期刊或会议的要求披露（见 references/disclosure.md），去 AI 味和披露并不矛盾。

## 为什么不直接用现成的"去 AI 味"工具

调研过的工具与取舍（详见 references/sources.md）：

- **humanizer、stop-slop、no-ai-slop 等 agent skill**：模式清单做得好，但面向博客与营销文案。
  "禁用被动语态""三项列举砍成两项""robust 一律删"这些规则放到论文里是错的；也不处理 LaTeX、
  不检查断言与证据。本 skill 借用它们的分级思路（强信号单次即报、弱信号看密度）和"不新增事实"的规则。
- **unslop**：有扫描器和"改写前后保留检查"，思路最接近；但它自己的评测也显示改写会误伤原文。
  本 skill 把保留检查做成硬约束（`guard.py`），并且只改诊断点名的句子。
- **词表类（slop-forensics、vale-ai-tells）**：数据来自小说或技术文档。本 skill 的词表改用
  Kobak et al. 2025 对 PubMed 摘要的统计，按超额倍数分档，更接近学术写作。
- **商业"降 AI 率"工具**：按检测器分数优化的黑箱改写，常见意思漂移、术语被改成"扭曲短语"、
  数字出错，且可能违反期刊诚信政策。不用。

## 工作流程

### 第 0 步：读入稿件，确定领域

- **.tex**（最常见）：只改自然语言；命令、公式、`\cite{}`、`\ref{}`、`\label{}`、环境原样保留，不碰导言区。
  多文件论文从主文件读，脚本会自动展开 `\input{}`。
- **.md / 纯文本**：直接处理。**.docx**：用 docx skill 的方法提取文本，改完按原格式回填。
  **PDF**：先提取文本，提醒用户提取可能有瑕疵。
- 确定领域配置：DFT/计算化学 + 机器学习的期刊论文用 `dft-ml`；LLM/agent 会议论文用 `agent-conf`；
  其它用 `general`。脚本能自动识别，不确定时问作者一句。**动笔前先读对应的领域配置**
  （references/profile-dft-ml.md 或 references/profile-agent-conf.md）。
- 问清目标期刊或会议，以及这次要改的范围。只给了一节就只改那一节，不要求提供全文。

### 第 1 步：体检

```bash
python3 scripts/deai_lint.py paper.tex --profile dft-ml --bib refs.bib
```

输出按修复顺序排好的诊断：`residue/`（生成残留、提示注入，必须处理）→ `cite/`（引用键不在 bib 里）→
`claim/`（断言与证据）→ `spec/`（领域细节缺失）→ `phrase/`、`vocab/`（套话与超额词）→
`struct/`（节奏）。每条都有行号、原文片段和修法。诊断代码与改法见 references/patterns.md。

另有各节超额词密度。Liang et al.（*Nat. Hum. Behav.* 2025）对 arXiv 与 Nature 系论文的统计显示，
LLM 改写痕迹在摘要中最多、引言次之——先改这两节。

**怎么读诊断数**：用三篇 ChatGPT 出现之前的人写论文（ReAct、CGCNN、MoleculeNet）标定过，
人写论文的 error + warning 约为每千词 0–2 条；典型 AI 初稿在每千词 70 条以上。
诊断数只用来决定先改哪里，**不是"AI 概率"**——人写的句子同样可能空洞。

### 第 2 步：通读，写总体判断与断言—证据表

先像写 decision letter 那样通读全文，用 3–5 句话写总体判断：AI 味集中在哪几节、最主要的两三类问题
（例如"摘要的每个结论都没有数字""Methods 缺泛函与 U 值""全文 hedging 等级混乱"），稿件的优点也要说。

然后把要改的几节里的每个经验性断言列成表：

| 位置 | 断言 | 证据 | 处理 |
|---|---|---|---|
| Abstract s3 | achieves remarkable accuracy | 无数字 | 换成 MAE + 基线，数字待作者补 |
| Results p1 | O 2p band center is the dominant descriptor | 相关性，无对比 | 降级为 correlates most closely；补对比描述符 |

这张表决定哪些句子要降级、哪些要补证据指针、哪些要问作者。

### 第 3 步：去 AI 味改写（核心）

按诊断顺序处理：

- **只改诊断点名的句子和第 2 步表里的断言**；没问题的句子不动，不为"更像人"而重写。
- 残留、占位符、提示注入先处理；编造嫌疑的文献（`cite/missing-key`）标出来让作者核实，不要自己换一篇。
- 空形容词换成 数值 + 基准 + 条件；原稿里没有数值就写 `[请确认: …]`。
- 领域细节（泛函、U 值、数据划分、种子与方差、模型版本……）缺了就写 `[请确认: …]`，说明审稿人为什么会要。
- 套话删掉或换成具体内容；超额词问一句"删掉它丢不丢信息"。
- 节奏问题最后处理：拆长句、删多余的递进词和段尾总结。

### 第 4 步：语言与逻辑润色（辅助）

去 AI 味之后，再过一遍语言层面的问题。动笔前读 references/editor-checklist.md，保证覆盖面；
句式参考 references/phrasebank.md（按 section 组织的顶刊句式库）。每条意见分级：

- **Major**：逻辑问题——gap statement 不清、逻辑跳跃、段落使命不明、关键比较缺失
- **Moderate**：段落与句式——主题句缺失、头重脚轻、信息焦点错位、句间衔接生硬
- **Minor**：用词、语法、格式——术语不一致、时态、冠词、单位与数字格式

格式固定：

```
**M3** [Results, para 2, sentence 4]
> 原文：The catalyst showed good performance under visible light.
> 修改：Under visible light (λ > 420 nm), the catalyst delivered a H₂ evolution
> rate of 12.4 mmol g⁻¹ h⁻¹, a 6.3-fold increase over pristine g-C₃N₄.

为什么：顶刊 Results 里"good performance"是无效信息——审稿人想知道多好、和什么比。
把数字和比较基准放进句子，让数据自己说话。同时补上光源条件，否则这个速率无法与文献比较。
```

意见数量随问题走：有问题就提，不为凑数制造琐碎意见。需要作者补的信息同样写成 `[请确认: …]`。

科学层面的疑点单独列为**编辑提问**：

```
**Q1** [Discussion, para 3]：文中称电荷分离效率提升是活性提高的"主要原因"，
但 PL 和 TRPL 数据只能说明电荷分离改善，无法排除表面活性位点数量变化的贡献。
建议改为 "a major contributor" 并补充讨论，或增加对照实验。
```

### 第 5 步：复查与对照

```bash
python3 scripts/deai_lint.py paper_revised.tex --profile dft-ml
python3 scripts/guard.py paper.tex paper_revised.tex
```

- `guard.py` 的 error（引用、交叉引用、公式变了，或凭空多出数字）必须清零。
- warning（数字消失、结论力度被升级、段落大幅扩写或删减）逐条确认是有意为之。
- 剩下的 lint 诊断按顺序再改一轮。**连续两轮诊断数不再下降就停**，在报告里如实列出剩下的。
- `spec/` 类诊断在作者补上细节之前会以 info 形式保留（"已用 [请确认] 留给作者"），这是正常的。

### 第 6 步：交付

1. 修改后全文：`<原名>_revised.tex`（或 .md/.docx），干净可编译，不含批注，只保留醒目的 `[请确认: …]`。
2. 报告 `polish-report.md`，结构固定：

```markdown
# 修改报告：<论文标题或文件名>

## 一、总体判断        （3–5 句 + 改前→改后诊断数，摘要/引言的超额词密度）
## 二、断言—证据表      （第 2 步的表，加一列"改后写法"）
## 三、需要作者补充     （[请确认] 清单，按章节排列，说明每一项为什么审稿人会要）
## 四、去 AI 味改写记录  （原文 → 改后 → 原因，按章节；同类问题合并说明，不逐词罗列）
## 五、语言与逻辑修改意见（Major / Moderate / Minor）
## 六、编辑提问
## 七、对照检查         （guard.py 结果：引用/公式/数字是否保持，字数变化，仍需确认的 warning）
## 八、AI 使用披露      （目标期刊/会议的要求要点 + 一段可直接用的披露声明草稿）
```

交付时在对话里用两三句话说最重要的发现，不要复述报告。

## 语言与风格约定

- 讲解语言：**中文**。修改后的论文文本：**英文**（除非原稿是中文论文）。
- 时态：实验做了什么用过去时；图表展示什么、数据表明什么用现在时；已确立的科学事实用现在时。
- Hedging：证据等级决定措辞。`demonstrate`/`show` 需要直接证据；`suggest`/`indicate` 用于间接证据；
  `may`/`likely` 用于推测。全文 hedging 等级混乱是中国作者稿件被审稿人揪住的最常见问题之一。
- 单位与数字：SI 规范，负指数形式（mmol g⁻¹ h⁻¹ 而非 mmol/g/h），数字与单位间有空格（20 °C、5 wt%），
  有效数字与测量精度匹配。

## 文件

```
paper-polish/
├── SKILL.md
├── scripts/
│   ├── deai_lint.py        体检：LaTeX/Markdown 遮蔽、词表、断言—证据、领域细节、节奏（纯 Python 标准库）
│   └── guard.py            对照：改写前后的引用、交叉引用、公式、数字、专有名词、结论力度
├── data/
│   ├── lexicon.json        词表与模式（数据，补词不改代码）
│   └── NOTICE.md           超额词数据的来源与许可（Kobak et al. 2025，MIT）
├── references/
│   ├── patterns.md             去 AI 味病灶目录、改法与"不要改的东西"
│   ├── profile-dft-ml.md       DFT + ML 期刊论文必查清单
│   ├── profile-agent-conf.md   LLM agent 会议论文必查清单
│   ├── disclosure.md           各期刊/会议的 AI 使用披露要求与声明草稿
│   ├── editor-checklist.md     按 section 的审稿维度清单（语言与逻辑润色用）
│   ├── phrasebank.md           顶刊句式库
│   └── sources.md              调研过的工具与取舍
└── examples/               两篇 AI 初稿示例及改写后的版本（内容虚构）
```

自测：`python3 scripts/deai_lint.py examples/dft-ml_ai-draft.tex` 应报出 30 条以上；
`python3 scripts/guard.py examples/dft-ml_ai-draft.tex examples/dft-ml_revised.tex` 应为 0 error。

## 边界情况

- **只问某一句怎么改 / 快速看一眼**：直接给改法和原因，不走全流程，但照样遵守"不改事实"。
- **稿件超长**（>15000 词）：按节分批，每批都跑 lint 和 guard，最后合并报告。
- **投稿前最后一轮**：额外做一遍全文术语一致性扫描（同一材料名、缩写、样品编号前后是否统一）。
- **用户要求"降到检测器 X% 以下"**：说明本 skill 不针对检测器优化，检测器分数也不能证明文字是谁写的；
  提供按本流程改写，并提醒按目标刊物的政策披露 AI 使用。
- **中文稿件**：脚本的词表只覆盖英文；中文稿按 patterns.md 的病灶类别人工处理，
  中文词表可借用同仓库 paper-slides 的 `references/ai-wordlist.json`。
- **用户要求替他补数据或文献**：不补。告诉他缺什么、去哪里找（如 Materials Project 的计算设置），
  由他本人确认后填入。
- **报告需要 Word 版本**：用 docx skill 生成，再用同仓库的 paper-word skill 套版。
