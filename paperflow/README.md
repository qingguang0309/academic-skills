# paperflow — 论文生成流水线(LangGraph 编排,标准 LaTeX 格式输出)

把"选题 → 大纲 → 【文献核验 ∥ 图表生成】→ 分章起草 → LaTeX 模板渲染 → PDF 编译 →
质检 → 修订"编排成一条可复现的流水线。写作规范取自实测筛选过的开源学术 skills,
防编造机制借鉴 academic-research-skills 的多库交叉验证思路。

> ⚠️ 定位说明:paperflow 产出**格式达标、引用真实**的稿件;它不能替你做实验。
> 没有真实数据与科学贡献,产出只是格式上像论文的演示稿——示例均显式标注 DEMO。

## 架构(图文并行)

```
            ┌─ literature ─→ verify(Crossref/S2 防编造门)─┐
plan ──┤                                                    ├─ draft → render → qa ─┬→ END
            └─ figures(按主题生成 matplotlib 图,本地执行)─┘         ↑              └→ revise ─┘
                                                                      └───────────────┘
```

- **并行分支**:plan 之后文献链与图表链同时执行(LangGraph 屏障汇合于 draft)。
  图表链让 LLM 写自包含 matplotlib 脚本 → 本地真实执行 → 按契约产出
  `figures/*.png + figures/manifest.json`(文件名/图注/标签)。
- **verify(确定性)**:每条候选引用按 DOI 查 Crossref(兜底 Semantic Scholar)+
  标题相似度比对;不通过一律剔除并记录在 `dropped_refs`。
- **render(标准论文格式)**:两套模板 →
  `article`:SCI 单栏投稿格式(Times 字体、abstract/keywords、natbib 作者-年份引注、
  plainnat 参考文献表),模板在 [templates/article/](../paperflow/templates/article/);
  `pkuthss`:北京大学学位论文(CTAN 正版模板,封面/摘要/目录/章节齐全,
  macOS 字体集实测适配)。编译引擎 tectonic(brew 安装,首跑自动拉宏包)。
- **qa(确定性)**:引用键 ⊆ 核验集合、无占位符、图必须被正文引用、PDF 必须编译成功;
  不过则 revise → render 循环。

## 后端策略:用每台电脑自己的 Claude

`--backend auto`(默认)优先级:**本机 claude CLI 登录态** → fixture 离线 → anthropic SDK。
不需要配置 ANTHROPIC_API_KEY;每台机器只要装过 Claude Code 并登录即可:

```bash
npm install -g @anthropic-ai/claude-code && claude login   # 每台机器一次
```

## 安装与使用

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
brew install tectonic          # LaTeX 引擎(编译 PDF 必需)
# 北大模板(pkuthss 模式必需;article 模式不需要):
mkdir -p ~/project/paper-skills-vendor/latex-templates && cd $_ \
  && curl -LO https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/pkuthss.zip \
  && unzip -q pkuthss.zip

# SCI 投稿格式
PYTHONPATH=. python -m paperflow --config ../examples/paperflow-demo/paper.yaml --template article
# 北大学位论文格式
PYTHONPATH=. python -m paperflow --config ../examples/paperflow-demo/paper.yaml --template pkuthss
```

配置见 [examples/paperflow-demo/paper.yaml](../examples/paperflow-demo/paper.yaml):
`topic/claim/context`、`sections`、`generate_figures`(图表链开关)、`keywords`、
`pkuthss:`(学位论文封面元数据:题目/姓名/学号/院系/导师…)。

## 演示(仓库内附产物)

- [paper_article.pdf](../examples/paperflow-demo/paper_article.pdf) — SCI 投稿格式,
  含并行生成的四联图(XRD/XPS/LSV/Tafel)与 plainnat 参考文献表
- [paper_pkuthss.pdf](../examples/paperflow-demo/paper_pkuthss.pdf) — 北大学位论文格式,
  含校徽封面、中文摘要、目录、章节与参考文献
- [run_report.json](../examples/paperflow-demo/run_report.json) — 5 条真实文献经 Crossref
  确认;候选清单里故意埋的编造 DOI 被核验门剔除(`dropped_refs`)

## 已知边界

- pkuthss 封面的仿宋字体在 macOS 上映射到按需下载的 STFangsong,渲染器已自动覆写为
  必装的 Songti SC(可经 `pkuthss.fontset` 改配);Linux/Windows 需另配 fontset。
- 期刊专用模板(elsarticle/achemso 等)与审稿模拟节点在路线图上。
