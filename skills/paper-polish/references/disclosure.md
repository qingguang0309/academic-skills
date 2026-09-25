# AI 使用披露:目标刊物的要求

去 AI 味和披露 AI 使用并不矛盾:前者让文字变好,后者是诚信要求。下面是 2026 年 9 月调研时各刊物的
政策要点。**政策更新很频繁(Elsevier 2026 年 6 月、Wiley 2026 年 7 月、Springer Nature 2026 年都改过),
投稿前务必打开链接核对当期版本。**

## 期刊

| 出版社 | 披露什么、放在哪里 | 不用披露 | 禁止 |
|---|---|---|---|
| [Elsevier](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals) | 参考文献前单独一节 "Declaration of generative AI and AI-assisted technologies in the manuscript preparation process";AI 作为研究方法的用法写进 Methods | 基础的拼写语法检查 | AI 署名;用 AI 编造或篡改结果、生成或修改原始图像 |
| [ACS](https://researcher-resources.acs.org/publish/authorship_guidance_policies) | 用 AI 生成文字或图像写进 Acknowledgments;大量使用在 Methods 中完整说明 | — | AI 署名 |
| [Springer Nature / npj](https://www.nature.com/nature-portfolio/editorial-policies/ai) | 2026 年新框架按风险分级:语言润色、调整结构为低风险;大量改写、起草摘要为中风险,需核实并披露;未披露的 AI 推理、编造引用或数据属于禁止 | 语言润色(低风险档,具体放在哪一节以当期页面为准) | AI 署名;编造的引用或数据;写实风格的 AI 图像 |
| [RSC](https://www.rsc.org/publishing/journals/processes-and-policies/author-responsibilities) | cover letter 与 Experimental/Methods 中声明(**包括所用提示词**),工具信息写进 Acknowledgements;示意性 AI 图在图注中注明 | AI 辅助的文字编辑 | AI 署名;用 AI 修改图像 |
| [Wiley](https://authors.wiley.com/ethics-guidelines/index.html) | 投稿时与稿件中都要披露 | 拼写、语法与一般编辑 | AI 署名 |

## 会议

| 会议 | 披露什么、放在哪里 | 特别注意 |
|---|---|---|
| [NeurIPS](https://neurips.cc/Conferences/2025/LLM) | LLM 是方法中重要、原创或非常规的组成部分时要说明;checklist 有 "Declaration of LLM usage" 一项 | 未经核实的 LLM 生成引用不被接受 |
| [ICLR 2026](https://blog.iclr.cc/2025/08/26/policies-on-large-language-model-usage-at-iclr-2026/) | **所有** LLM 使用都要在论文和投稿表中披露;可放附录,不占页数 | 幻觉内容(包括编造的引用)由作者负责,可按学术不端处理并直接拒稿;**隐藏的提示注入直接拒稿** |
| [ICML 2026](https://icml.cc/Conferences/2026/CallForPapers) | 允许使用,鼓励在方法部分说明 | **提示注入直接拒稿**;另需 Impact Statement |
| [ACL / ARR](https://www.aclweb.org/adminwiki/index.php/ACL_Policy_on_Publication_Ethics) | 超出润色范围的使用写进 Acknowledgements,并在 Responsible NLP checklist 的 E1 项填写 | 润色自己写的文字不用披露;**Limitations 一节是强制的**,缺了直接拒稿 |

## 本 skill 对"去 AI 味"这件事的定位

- 如果初稿是 AI 起草、作者再修改,多数刊物把它归入需要披露的一档(Springer Nature 的中风险、
  ICLR 的"所有使用"、Elsevier 的写作辅助)。用本 skill 改写并不改变这一点。
- 本 skill 的产出是作者自己核对过的文字:每个断言对上证据,每个细节由作者补全,每条引用由作者核实。
  这正是各家政策要求作者承担的责任。

## 披露声明草稿(按实际情况改)

**Elsevier 格式**

> During the preparation of this work the authors used [工具名与版本,如 Claude (Anthropic)] in order to
> [draft initial versions of the Introduction and Discussion / improve the language of the manuscript].
> After using this tool, the authors reviewed and edited the content as needed and take full responsibility
> for the content of the published article.

**ACS / RSC(Acknowledgments)**

> The authors used [工具名与版本] to [draft and edit portions of the text]. All content, including data,
> citations and conclusions, was verified by the authors, who take full responsibility for the manuscript.

RSC 还要求在 Methods 或 cover letter 中给出所用提示词。

**ICLR / NeurIPS(附录或 checklist)**

> We used [LLM 名称与版本] to [assist with drafting and polishing the text of Sections 1 and 5]. The LLM was not
> used for [research ideation / experimental design / data analysis]. All claims, results and references were
> checked by the authors.

如果 LLM 本身是研究对象或实验组件(agent 论文通常如此),那部分属于方法,按实验细节完整报告
(模型版本、快照日期、解码参数、提示词),与"写作辅助"的披露分开写。
