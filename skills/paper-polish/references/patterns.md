# 论文 AI 味:病灶目录与改法

改写时逐类对照。每一类都写了**什么时候不该改**——学术文体里有很多被博客式"去 AI 味"工具误伤的合法写法。
判据只有一条:**删掉它或换成具体说法之后,句子丢不丢信息?** 丢了就留,没丢就改。

## 目录

- [一、生成残留(必须处理)](#一生成残留必须处理)
- [二、断言与证据不匹配(最伤稿子)](#二断言与证据不匹配最伤稿子)
- [三、专业细节缺失](#三专业细节缺失)
- [四、套话与空句](#四套话与空句)
- [五、超额词](#五超额词)
- [六、节奏与结构](#六节奏与结构)
- [七、不要改的东西](#七不要改的东西)
- [八、改写示范](#八改写示范)

## 一、生成残留(必须处理)

| 痕迹 | 例子 | 处理 |
|---|---|---|
| 对话残留 | `Certainly! Here is the revised paragraph:` / `I hope this helps` | 删 |
| 知识截止声明 | `As of my last update, …` | 删,并核对该处事实是否过时 |
| 泄漏的引用标记 | `oaicite:3`、`turn0search2`、`[cite: 4]`、`utm_source=chatgpt.com` | 换成真实 `\cite{}`,**文献本身必须核实** |
| 占位符 | `[insert reference]`、`XX%`、`???` | 补真实内容,或改成 `[请确认: …]` |
| LaTeX 里的 Markdown | `**bold**`、`## Results` | 改成 `\textbf{}` / `\section{}` |
| 引用键不存在 | `\cite{zhang2023deep}` 在 bib 里找不到 | 当作编造文献处理:核实不了就删 |

**编造文献是底线问题。** 模型生成的引用常常作者、年份、期刊都像真的,但文章不存在或内容不符。
每一条由 AI 起草时加进来的引用,作者都要自己打开原文核对过:存在、内容与引用处的说法一致。

## 二、断言与证据不匹配(最伤稿子)

AI 初稿最常见、也最危险的问题不是用词,而是**断言强度超过证据**。审稿人最先抓的也是这个。

| 病灶 | 例子 | 改法 |
|---|---|---|
| 无证据的强动词 | `The trend demonstrates that X is the dominant descriptor.` | 补证据指针 `(Fig. 3b)`;间接证据降级为 `suggests` / `is consistent with` |
| 空形容词 | `remarkable accuracy`、`superior performance`、`state-of-the-art` | 换成 数值 + 基准 + 条件:`MAE of 0.041 eV/atom, vs. 0.067 eV/atom for CGCNN` |
| 无检验的 significant | `significantly outperforms` | 做过检验就给 p 值或 CI;没做就给数值差,或用 `substantially` |
| 泛化断言 | `generalizes to unseen chemistries` | 只有做过分布外测试才能这么写;否则写 `on the held-out test set` |
| 首创断言 | `we are the first to …` | `to our knowledge` + 检索范围,或删 |
| 拟人化 | `the agent understands the task` | 写可观测行为:`the agent selects`、`the policy is conditioned on` |
| 叠加 hedging | `may potentially`、`could possibly suggest` | 只留一个 |

**动词强度要跟着证据走:**

- 直接测量或对照实验 → `show`、`find`、`measure`,并把数字放进句子。
- 相关、间接或计算推断 → `suggest`、`indicate`、`is consistent with`。
- 推测 → `may`、`likely`,并说明还需要什么证据。
- 没做统计检验不写 significant;没有因果设计不写 cause / lead to。

反方向同样是病:该断言的地方处处 hedge,读起来心虚。去 AI 味**不是一律降级**。

## 三、专业细节缺失

AI 初稿"正确但空"的根源,是它不知道作者具体做了什么,只能写对谁都成立的句子。
检验句子的办法:**这句话放进同行的另一篇论文里还成立吗?** 成立,就还缺研究对象、方法、条件或数字。

专业细节只能来自作者:**缺什么就写 `[请确认: …]`,绝不替作者补。**两个领域的必查清单见
[profile-dft-ml.md](profile-dft-ml.md) 与 [profile-agent-conf.md](profile-agent-conf.md)。

## 四、套话与空句

| 套话 | 问题 | 改法 |
|---|---|---|
| `In the rapidly evolving landscape of …` / `In today's …` | 时代背景开场,放进任何论文都成立 | 开场直接写具体问题和已知数字 |
| `plays a crucial/pivotal role in` | 断言重要,不说机制 | 写出作用:`lowers the O* binding energy by 0.3 eV` |
| `It is worth noting that` / `Notably,` | 靠喊话强调 | 删掉,直接陈述 |
| `shed light on` / `pave the way for` / `open new avenues` | 许愿式结尾 | 写实际贡献,或删 |
| `in the realm/field of` | 空壳短语 | 删 |
| `provides valuable insights into` | 说有见解而不说见解 | 直接写见解本身 |
| `Extensive experiments demonstrate` | 用实验规模代替结论 | 直接给结果 |
| `Our contributions are threefold:` | 模板开场 | 直接列,每条是可核对的事实 |
| `serves as` | 回避 is | 多数改 is;`serves as a key/powerful …` 单次即提示 |
| `a wide range of` / `various` | 代替了具体数量 | 给数量或列出对象 |

**空句的四种典型:**

1. 同义反复的开场:`Catalysis is important in modern chemistry.`
2. 承诺不兑现:`This has attracted significant attention.`(谁、为什么、导向什么?)
3. 把方法当结果:`We performed XPS to analyze the surface.`(看到了什么?)
4. 循环解释:`The high activity is attributed to the excellent catalytic performance.`

## 五、超额词

`data/lexicon.json` 的 excess 词族来自 Kobak et al. 2025 对 PubMed 摘要的统计:
ChatGPT 出现后使用频率超出预期的"风格词",括号里是 2024 年相对 2021–22 外推值的倍数。

- **marker 档**(单次就提示):delve(×28)、underscore(×14)、showcase(×11)、meticulous(×10)、
  intricate(×7.7)、commendable(×6.8)、garner(×5.3)、realm(×5.0)、groundbreaking(×4.9)、
  revolutionize(×4.1)、pivotal(×3.1)、seamless(×3.1)、transformative(×3.0)、tapestry、testament……
- **density 档**(同段两个以上才提示):leverage、harness、foster、notable/notably、crucial、
  comprehensive、enhance、facilitate、utilize、additionally、insights、streamline……

**只删显眼的词没有用。** Geng & Trotta(2025)发现 delve、intricate、realm、showcasing 这些词被公开点名后
使用率开始下降,而 significant、additionally、comprehensive、enhance、capabilities、valuable、crucial、effectively
仍在上升——作者删掉了标志词,空洞的写法还在。所以本 skill 的重点放在断言、证据与细节上,词表只是入口。

超额词本身不是错,**问题在于它们通常替代了信息**。`underscores the importance of X` 删掉后什么也没少;
`surpasses the DFT baseline by 12%` 里的 surpass 就是正常用法。换词不等于改好:
把 `delve into` 换成 `dig into` 毫无意义,要换成做了什么(`we computed`、`we compared`)。

## 六、节奏与结构

| 病灶 | 症状 | 改法 |
|---|---|---|
| 句长均匀 | 一段五六句,每句 20–28 词,都是主句加从句 | 拆一个长句为一短一长;删掉只做过渡的从句 |
| 递进词堆砌 | 一段里 Furthermore、Moreover、Additionally 各一次 | 只留逻辑真正需要的一处 |
| 段尾总结 | 每段最后一句 `Overall, …` / `Taken together, …` | 删掉大部分;段落靠推进,不靠自我复述 |
| 三连形容词 | `robust, interpretable, and scalable` | 真有三点就留;为对称凑的一项删掉 |
| 对仗 | `not only … but also …` 一篇好几处 | 拆成两个陈述句 |
| 破折号多 | 插入语都用 — | 改逗号、括号或拆句,保留少数 |
| 相邻段开头雷同 | 连续几段都以 `In this work` / `The results` 开头 | 从本段的具体对象或结果说起 |

## 七、不要改的东西

博客式去 AI 味工具(humanizer、stop-slop 等)的一些规则对论文是错的:

- **被动语态**:Methods 里的被动语态是规范写法(`Samples were annealed at 500 °C`)。只在主语不明
  导致意思含糊时才改。
- **三项列举**:真实的三个样品、三个基准、三组条件就写三项,不要为了"去三连"删掉一项。
- **术语**:robust(统计与 ML 术语)、alignment(LLM 对齐)、potential(势能、化学势)、
  enhanced sampling、significant figures、interplay(确有相互作用时)都是正常术语。
- **hedging**:`suggest`、`may`、`likely` 是学术写作的精度工具,不是 AI 味。
- **we**:ML 会议论文普遍用第一人称复数;化学期刊也接受。不要为了"去 AI 味"全改成被动。
- **正式、语法无误的句子**:Wikipedia 的 AI 写作指南也明确说,语法完美、文风正式本身不是 AI 痕迹。
- **公式、引用、数字、专有名词**:一个都不许动。`guard.py` 会查。

## 八、改写示范

**DFT + ML,摘要开头**

> 原:In the rapidly evolving landscape of materials science, the discovery of efficient oxygen evolution
> catalysts plays a pivotal role in sustainable energy conversion. In this work, we delve into the intricate
> interplay between electronic structure and catalytic activity of perovskite oxides by leveraging DFT and ML.
>
> 改:Screening perovskite oxides for the oxygen evolution reaction needs an activity descriptor that is cheaper
> than computing every adsorption energy with DFT. We trained a graph neural network on DFT adsorption energies
> of oxygen intermediates [请确认: 数据量与化学空间] and used it to test which electronic-structure quantity
> tracks the predicted activity.

改了什么:删掉时代背景开场和"扮演关键角色";`delve into the intricate interplay` 换成具体做了什么;
数据量原稿没有,留给作者。

**AI agent,引言**

> 原:We argue that this failure stems from the agent's inability to understand why it failed. When the agent
> thinks about its previous trajectory, it can avoid repeating mistakes.
>
> 改:We hypothesize that these failures persist because the agent's context contains no record of why earlier
> attempts failed. When a summary of the failed trajectory is added to the context, the agent repeats the same
> invalid action less often [请确认: 对应的消融结果,如 Table 3].

改了什么:"理解""思考"改成可观测、可检验的表述;argue 改成 hypothesize(此处还没给证据);
把断言挂到证据上,证据位置留给作者。
