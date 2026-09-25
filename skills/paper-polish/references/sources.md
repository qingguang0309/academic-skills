# 调研来源与取舍

paper-polish 去 AI 味部分设计前调研过的工具与研究(2026 年 9 月)。借了什么、没借什么、为什么。

## Agent skill 与提示词

| 工具 | 许可 | 做什么 | 借用 | 不借用 |
|---|---|---|---|---|
| [blader/humanizer](https://github.com/blader/humanizer) | MIT | 一份 SKILL.md:25 类模式分五组(铺垫、节奏、夸大、格式、残留),强信号单次即改,弱信号要有旁证 | 分级思路;"不新增事实、名字、数字、引用";"何时不要改" | 面向通用文本,没有断言—证据检查,不处理 LaTeX |
| [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) | MIT | 8 条规则 + 五维打分 | 短语目录的组织方式 | "禁用被动语态""删副词""用 you 对读者说话"——对论文是错的 |
| [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) | MIT | 词表 + 模式表 + 自检 | 自检清单 | 把 robust、facilitate、intricate 一律禁用,误伤术语 |
| [theclaymethod/unslop](https://github.com/theclaymethod/unslop) | MIT(README) | 约 20 个 Python 扫描器,含改写前后保留检查,有精度/召回/损伤评测 | 扫描器 + 保留检查的架构 | 其评测自述尚未达到可用的精度与损伤标准——提醒我们只改被点名的句子 |
| [stephenturner/skill-deslop](https://github.com/stephenturner/skill-deslop) | MIT | stop-slop 的科学写作改编版 | — | 仍要求"三项列举改成两项",Methods 被动语态处理不一致 |

## 词表与检测数据

| 数据 | 许可 | 用法 |
|---|---|---|
| [berenslab/llm-excess-vocab](https://github.com/berenslab/llm-excess-vocab)(Kobak et al., *Sci. Adv.* 2025, 11:eadt3813) | MIT | **本 skill 词表的主数据**。取其中标注为 style 的 407 个词,用 `yearly-counts.csv.gz` 计算 2024 年频率相对 2021–22 线性外推值的倍数,按词族归并;≥ 约 3 倍且无常见术语义的进 marker 档,其余进 density 档,常见功能词和领域术语剔除 |
| [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | CC BY-SA | 只借分类思路(内容、语言、风格、残留、引用);其中"无效指标"一节提醒:语法完美、文风正式、过渡词本身都不是 AI 痕迹 |
| [sam-paech/slop-forensics](https://github.com/sam-paech/slop-forensics)、[antislop-sampler](https://github.com/sam-paech/antislop-sampler) | MIT / Apache-2.0 | 未直接使用:数据主要来自小说与随笔,学术写作误报多 |
| [tbhb/vale-ai-tells](https://github.com/tbhb/vale-ai-tells) | MIT | 参考了规则类别(对比否定、serves as、叠加 hedging);规则为本 skill 重写,面向论文调整 |

## 为什么不用商业"降 AI"工具

Undetectable.ai、StealthGPT 一类工具与国内的"降 AI 率"服务,按检测器分数优化黑箱改写。问题:

- **意思漂移与扭曲短语**:自动改写会把 "artificial intelligence" 改成 "counterfeit consciousness" 这类
  "tortured phrases",已在数百种期刊中被发现(Cabanac et al. 2021,[arXiv:2107.06751](https://arxiv.org/abs/2107.06751))。
- **数字与事实出错**:改写不区分事实与措辞。
- **诚信风险**:这类工具的卖点就是隐藏 AI 使用;Turnitin 已专门检测"AI 改写绕过"。
  期刊与会议要求的是披露,而不是隐藏。

## 本 skill 自己加的部分

- LaTeX 感知的遮蔽:公式、引用、命令、表格、注释不参与检查,行号保持不变。
- 断言—证据检查:强动词、空形容词、无检验的 significant 是否挂在证据上。
- 两个领域配置:DFT+ML 期刊论文的计算细节清单;agent 会议论文的拟人化、方差、Limitations、模型版本检查。
- `guard.py`:改写前后逐项对照引用、交叉引用、公式、数字、专有名词与结论力度。
- 待补细节统一写成 `[请确认: …]`,lint 与 guard 都识别它。
