# 领域配置:LLM / AI agent 会议论文

适用:NeurIPS、ICLR、ICML、ACL / EMNLP / NAACL(ARR)等会议上关于 LLM agent 的论文。
`deai_lint.py --profile agent-conf` 会自动查下表里带代码的项。

这类论文的 AI 初稿有两个特征:**一是把 agent 写成人**(understands、thinks、knows、realizes),
二是**用形容词代替实验**(novel、state-of-the-art、human-level、truly autonomous)。
审稿人读 agent 论文时最警惕的正是这两点:拟人化让机制无法检验,形容词让贡献无法比较。

## 必查清单

| 项目 | 代码 | 审稿人期待的写法 |
|---|---|---|
| 拟人化 | `claim/anthropomorphism` | 写可观测行为:`selects`、`outputs`、`is conditioned on`、`retrieves`;讨论内部表征要给探测实验 |
| 强断言 | `claim/hype` | `human-level`、`general-purpose`、`fully autonomous` 要么删,要么限定到具体基准和数字 |
| 首创断言 | `claim/priority` | `to our knowledge` + 与最接近工作的具体差异 |
| novel 泛滥 | `phrase/novel` | 新不新由审稿人判断;写清与最接近的已有方法差在哪一点 |
| 方差与重复 | `spec/variance` | 种子数、重复次数、均值 ± 标准差或置信区间;agent 评测随机性大,单次结果不够 |
| Limitations | `spec/limitations` | 单独一节或段落:评测覆盖不到的任务类型、失败模式、成本、对闭源模型的依赖。**ACL/ARR 强制,缺了直接拒稿** |
| 模型版本与解码参数 | `spec/model-version` | `gpt-4o-2024-08-06`、temperature、最大步数、工具集、每个任务的 token 与花费 |
| 贡献清单 | `phrase/pattern` | 每条是可核对的事实:"a memory module that stores failure summaries (Sec. 3.2)",不写 "a novel framework" |

## 这个领域的高频 AI 病灶

| AI 初稿 | 问题 | 改法 |
|---|---|---|
| `LLM agents have shown remarkable capabilities across diverse tasks` | 放进任何 agent 论文都成立 | 直接写本文关注的失败模式与已知数字 |
| `the agent understands / reasons about / realizes` | 拟人化,不可检验 | `the agent's next action depends on …`;要谈 reasoning 就指明是 chain-of-thought 输出 |
| `achieves state-of-the-art performance` | 没说在哪、比谁、多少 | `52.3% success on WebArena (812 tasks), vs. 41.2% for ReAct with the same backbone` |
| `significantly outperforms` | 无检验 | 给方差和检验,或给数值差 |
| `extensive experiments demonstrate` | 规模代替结论 | 直接给结果 |
| `paves the way for truly autonomous agents` | 许愿式结尾 | 写本文结果适用到哪里、还缺什么 |
| `our framework seamlessly integrates` | seamless 无信息 | 说清接口:模块之间传什么、谁调用谁 |
| `comprehensive evaluation on three benchmarks` | 三个基准算不上 comprehensive | 删掉形容词,写基准名称与任务数 |
| `robust to various perturbations` | 哪些扰动? | 列出扰动类型与性能下降幅度 |

## 会议论文的写法习惯

- **Introduction 末尾的贡献清单**是惯例,但每条要短、具体、可在正文中找到对应章节。
- **Claims 与证据对应**:NeurIPS checklist 第一项(Claims)要求摘要和引言里的断言与理论和实验结果相符。
  逐条对照:摘要里每个数字、每个"优于",正文里都要有对应的表或图。
- **消融实验**:引言里说"X 模块是关键",就要有去掉 X 的对照。
- **Related Work** 不是文献堆砌:每段按方法类别写,并说清本文与该类方法的区别。
  AI 初稿常见的问题是 "X et al. proposed …; Y et al. introduced …" 流水账,没有比较。
- **第一人称 we** 是会议论文的正常写法;被动语态只在主语不重要时用。
- **双盲**:改写时不要引入可识别作者身份的信息(机构名、"our previous work [12]" 的写法)。
- **提示注入**:ICLR / ICML 2026 对藏给审稿 LLM 的指令(白色文字、极小字号、"ignore previous instructions")直接拒稿。
  `deai_lint.py` 把这类内容报为 error。
- **写作规范的出处**:Lipton & Steinhardt,[Troubling Trends in ML Scholarship](https://arxiv.org/abs/1807.03341)
  总结的四类问题——解释与推测不分、不指明提升来自哪里(所以要消融)、堆砌数学、滥用术语与暗示性措辞——
  正好是 agent 论文 AI 初稿的高发区。
