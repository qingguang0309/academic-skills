# paperflow — 论文生成流水线(LangGraph 编排)

把"选题 → 大纲 → 文献 → **引用真实性核验** → 分章起草 → 图表 → 组装 → 质检 → 修订"
编排成一条可复现的 LangGraph 流水线。写作规范取自实测筛选过的开源学术 skills
(scientific-writing、research-paper-writing、academic-paper),防编造机制借鉴
academic-research-skills 的多库交叉验证思路。

> ⚠️ 定位说明:paperflow 能产出**写作质量和格式达标的稿件骨架**,并保证引用真实;
> 它不能替你做实验。没有真实数据与科学贡献,产出只是格式上像论文的演示稿——
> 所有示例均显式标注 illustrative/DEMO。

## 架构

```
START → plan → literature → verify → figures → draft → assemble → qa ─┬→ END
         LLM       LLM     Crossref/S2  确定性    LLM     pandoc   确定性 │
                            (防编造门)                                   └→ revise ─→ assemble(循环,≤max_revisions)
```

- **verify(确定性)**:每条候选引用按 DOI 查 Crossref(兜底 Semantic Scholar),
  并做标题相似度比对;DOI 不存在或标题不符一律剔除并记录在 `dropped_refs`。
- **qa(确定性)**:引用键 ⊆ 核验通过集合、引用数量下限、章节非空、无占位符、
  无列表化散文、图表必须被正文引用;不过则进入 revise 循环。
- **assemble**:markdown + BibTeX,经 `pandoc --citeproc` 产出 docx / tex。

## 安装

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
# 可选:brew install pandoc  (缺 pandoc 时只产出 markdown)
```

## 使用

```bash
PYTHONPATH=. python -m paperflow --config ../examples/paperflow-demo/paper.yaml --backend auto
```

LLM 后端三选一(`--backend`,默认 `auto` 按下列顺序探测):

| 后端 | 条件 | 说明 |
|---|---|---|
| `anthropic` | `ANTHROPIC_API_KEY` 或 `ant auth login` 档案 | 官方 SDK,默认模型 `claude-opus-4-8`,adaptive thinking + 流式 |
| `claude-cli` | 已安装并 `claude login` | 无头调用本机 Claude Code 登录态 |
| `fixture` | workdir 有 `fixtures/` | 离线回归:各写作阶段读取预置 md,核验/组装/QA 照常真实执行 |

## 配置(paper.yaml)

见 [examples/paperflow-demo/paper.yaml](../examples/paperflow-demo/paper.yaml):
`topic/claim/context`(选题与论点)、`sections`(章节键列表)、`figures`(路径+图注,
建议由 paper-figures skill 产出)、`words_per_section`、`min_citations`、`max_revisions`。

## 演示

`examples/paperflow-demo/` 用 NiFe-LDH OER 示例(配图来自 paper-figures skill 的
端到端测试)跑通全流程:5 条真实文献全部经 Crossref 确认;候选清单里**故意埋的一条
编造 DOI 被核验门剔除**(见 `run_report.json` 的 `dropped_refs`);pandoc 产出
docx/tex,正文引注与参考文献表由 citeproc 自动生成。

## 路线图

期刊格式档案(CSL/模板)、审稿模拟节点(接 academic-paper-reviewer)、
图表节点直接驱动 paper-figures skill、LaTeX 模板对接(pkuthss 等学位论文场景)。
