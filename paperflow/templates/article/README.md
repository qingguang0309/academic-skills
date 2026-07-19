# article 模板 — 占位符契约

`template.tex` 是单栏 SCI 期刊投稿风格的 LaTeX 模板。paperflow 流水线通过
**Python 纯字符串替换**(`str.replace`)把内容填进 `@@NAME@@` 占位符,不做任何
模板引擎解析,因此占位符名称、大小写、`@@` 定界符都不可改动。

## 占位符一览

| 占位符 | 含义 | 填入内容要求 |
|---|---|---|
| `@@TITLE@@` | 论文标题 | 纯文本(可含内联数学 `$...$`);LaTeX 特殊字符需预先转义 |
| `@@AUTHOR@@` | 作者列表 | 如 `Zhang San, Li Si and Wang Wu`;多行作者可用 `\\` 分隔 |
| `@@AFFILIATION@@` | 作者单位 | 单行文本,渲染为标题区小号字;多个单位用 `; ` 分隔 |
| `@@DATE@@` | 日期 | 如 `July 18, 2026`;留空字符串则不显示日期 |
| `@@ABSTRACT@@` | 摘要 | 一段(或数段)纯文本段落,放入 `abstract` 环境内 |
| `@@KEYWORDS@@` | 关键词 | 以 `; ` 分隔的关键词串,如 `machine learning; optimization; benchmark` |
| `@@BODY@@` | 正文全文 | 一串 `\section{...}` 章节与 `figure` / `table` 环境,详见下文 |
| `@@BIBFILE@@` | 参考文献库 | 不带扩展名的 `.bib` 文件名,如 `references`(对应 `references.bib`) |

注意:所有占位符均为 `@@NAME@@` 形式,刻意避开 `{ } % $ # & _` 等 LaTeX
特殊字符,保证替换前的模板本身不会因占位符产生编译歧义。

## `@@BODY@@` 的期望内容

BODY 是完整正文,由流水线生成,期望形如:

```latex
\section{Introduction}
Recent advances in this field \citep{smith2024} have shown that ...
As demonstrated by \citet{lee2025}, the proposed approach ...

\section{Methods}
We formulate the problem as
\begin{equation}
  \min_{x} \; f(x) + \lambda \|x\|_1 .
\end{equation}

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{figures/framework.pdf}
  \caption{Overview of the proposed framework.}
  \label{fig:framework}
\end{figure}

\section{Results}
As shown in Figure~\ref{fig:framework} and Table~\ref{tab:main}, ...

\begin{table}[htbp]
  \centering
  \caption{Main results on the benchmark.}
  \label{tab:main}
  \begin{tabular}{lcc}
    \toprule
    Method & Accuracy & F1 \\
    \midrule
    Baseline & 87.2 & 85.9 \\
    Ours     & \textbf{91.4} & \textbf{90.3} \\
    \bottomrule
  \end{tabular}
\end{table}

\section{Conclusion}
...
```

要点:

- 章节用 `\section{...}` / `\subsection{...}`,不要出现 `\chapter`(article 类不支持)。
- 引用用 natbib 的 author-year 命令:括号引用 `\citep{key}`,行文引用 `\citet{key}`;
  引用键必须存在于 `@@BIBFILE@@.bib` 中。
- 图用标准 `figure` 环境 + `\includegraphics`,图文件路径相对于编译目录。
- 表用 `booktabs`(`\toprule` / `\midrule` / `\bottomrule`),不要用竖线表格。
- 不要在 BODY 里再引入 `\usepackage`、`\begin{document}` 或 `\bibliography`,
  这些已由模板骨架负责。

## 编译

填充后的文件(如 `template_filled.tex`)用 tectonic 编译:

```bash
tectonic template_filled.tex
```

tectonic 会自动多轮编译并处理 BibTeX,产出同名 PDF。模板只依赖 TeX Live
常见核心宏包(geometry、newtxtext/newtxmath、graphicx、booktabs、amsmath、
caption、natbib、setspace、hyperref),tectonic 默认 bundle 即可编译,
无需 `--shell-escape`,也不依赖 minted 等外部工具。

宏包顺序约束(改动模板时须保持):`amsmath` 在 `newtxmath` 之前加载,
`hyperref` 必须最后加载。
