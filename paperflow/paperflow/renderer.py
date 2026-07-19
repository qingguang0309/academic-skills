"""LaTeX 渲染与编译:把流水线状态填入标准论文模板并编译 PDF。

- article 模式:paperflow/templates/article/template.tex(标准 SCI 单栏投稿格式),
  natbib 作者-年份引注,bibtex 由 tectonic 自动跑。
- pkuthss 模式:北京大学学位论文模板(vendor 下载的 CTAN 发行版),章节映射为 chapter,
  参考文献用确定性 thebibliography(避免 biber 链路差异)。
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
_CITE_RE = re.compile(r"\[@[^\]]+\]")
_MARK = ""  # 私有区占位符,转义时保护引注


def _latex_escape(text: str) -> str:
    text = text.replace("\\", r"\textbackslash{}")
    for ch, rep in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                    ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                    ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")]:
        text = text.replace(ch, rep)
    return text


def prose_to_latex(text: str, cite_cmd: str = r"\citep") -> str:
    """散文 → LaTeX:先摘出 [@a; @b] 引注,转义正文,再回填 \\citep{a,b}。"""
    cites: list[str] = []

    def _stash(m: re.Match) -> str:
        keys = re.findall(r"@([\w][\w.-]*)", m.group(0))
        cites.append(cite_cmd + "{" + ",".join(keys) + "}")
        return f"{_MARK}{len(cites) - 1}{_MARK}"

    stashed = _CITE_RE.sub(_stash, text)
    escaped = _latex_escape(stashed)
    return re.sub(f"{_MARK}(\\d+){_MARK}", lambda m: cites[int(m.group(1))], escaped)


def _figure_env(fig: dict, index: int, width: str = "0.92\\linewidth") -> str:
    caption = _latex_escape(fig["caption"])
    return (
        "\\begin{figure}[htbp]\n\\centering\n"
        f"\\includegraphics[width={width}]{{{fig['path']}}}\n"
        f"\\caption{{{caption}}}\n\\label{{fig:{fig['label']}}}\n\\end{{figure}}\n"
    )


def _section_title(key: str) -> str:
    return key.replace("_", " ").title().replace("And", "and")


def render_article(state: dict, workdir: Path) -> Path:
    cfg, outline = state["config"], state["outline"]
    tpl = (TEMPLATES / "article" / "template.tex").read_text(encoding="utf-8")

    sections = dict(state["sections"])
    abstract = prose_to_latex(sections.pop("abstract", ""))

    body_parts: list[str] = []
    if cfg.get("disclaimer"):
        body_parts.append(
            "\\begin{center}\\fbox{\\parbox{0.9\\linewidth}{\\small\\itshape "
            + _latex_escape(cfg["disclaimer"]) + "}}\\end{center}\n"
        )
    for sec in outline["sections"]:
        key = sec["key"]
        if key not in sections:
            continue
        body_parts.append(f"\\section{{{_section_title(key)}}}\n\n{prose_to_latex(sections[key])}\n")
        if key == cfg.get("figures_after_section"):
            body_parts += [_figure_env(f, i) for i, f in enumerate(state.get("figures", []))]

    filled = (
        tpl.replace("@@TITLE@@", _latex_escape(outline.get("title", "Untitled")))
        .replace("@@AUTHOR@@", _latex_escape(cfg.get("author", "paperflow")))
        .replace("@@AFFILIATION@@", _latex_escape(cfg.get("affiliation", "")))
        .replace("@@DATE@@", "\\today")
        .replace("@@ABSTRACT@@", abstract)
        .replace("@@KEYWORDS@@", _latex_escape(", ".join(cfg.get("keywords", []))))
        .replace("@@BODY@@", "\n".join(body_parts))
        .replace("@@BIBFILE@@", "references")
    )
    out = workdir / "paper_article.tex"
    out.write_text(filled, encoding="utf-8")
    return out


def _thebibliography(entries: list[dict]) -> str:
    items = []
    for e in entries:
        authors = ", ".join(e.get("authors") or ["Unknown"])
        piece = (
            f"\\bibitem{{{e['key']}}} {_latex_escape(authors)}. "
            f"{_latex_escape(e.get('title', ''))}. "
            f"\\textit{{{_latex_escape(e.get('container', ''))}}}"
        )
        if e.get("year"):
            piece += f", {e['year']}"
        if e.get("volume"):
            piece += f", {e['volume']}"
        if e.get("pages"):
            piece += f": {_latex_escape(str(e['pages']))}"
        piece += "."
        if e.get("doi"):
            piece += f" DOI: {_latex_escape(e['doi'])}."
        items.append(piece)
    return "\\begin{thebibliography}{99}\n" + "\n\n".join(items) + "\n\\end{thebibliography}\n"


def _find_pkuthss_class_dir(pkuthss_dir: Path) -> Path:
    hits = sorted(pkuthss_dir.rglob("pkuthss.cls"))
    if not hits:
        raise FileNotFoundError(f"在 {pkuthss_dir} 下找不到 pkuthss.cls(先运行工具链下载)")
    return hits[0].parent


def render_pkuthss(state: dict, workdir: Path, pkuthss_dir: Path) -> Path:
    cfg, outline = state["config"], state["outline"]
    meta = cfg.get("pkuthss", {})
    build = workdir / "pkuthss_build"
    build.mkdir(parents=True, exist_ok=True)

    # 类文件全量复制:cls/def 之外还有封面必需的 pkulogo.pdf / pkuword.pdf
    cls_dir = _find_pkuthss_class_dir(Path(pkuthss_dir))
    for f in cls_dir.iterdir():
        if f.is_file():
            shutil.copy(f, build / f.name)
    # macOS 字体集:pkuthss 默认映射 Windows 字体,必须切到 mac(实测结论)
    fontset = meta.get("fontset", "mac")
    (build / "ctexopts.cfg").write_text(
        "\\ProvidesExplFile{\\ExplFileName}{}{}{}\n"
        f"\\keys_set:nn {{ ctex / option }} {{ fontset = {fontset} }}\n"
        "\\endinput\n",
        encoding="utf-8",
    )
    figsrc = workdir / "figures"
    if figsrc.is_dir():
        shutil.copytree(figsrc, build / "figures", dirs_exist_ok=True)

    sections = dict(state["sections"])
    abstract = prose_to_latex(sections.pop("abstract", ""), cite_cmd="\\cite")

    chapters: list[str] = []
    for sec in outline["sections"]:
        key = sec["key"]
        if key not in sections:
            continue
        chapters.append(
            f"\\chapter{{{_latex_escape(meta.get('chapter_names', {}).get(key, _section_title(key)))}}}\n\n"
            + prose_to_latex(sections[key], cite_cmd="\\cite") + "\n"
        )
        if key == cfg.get("figures_after_section"):
            chapters += [_figure_env(f, i, width="0.85\\linewidth") for i, f in enumerate(state.get("figures", []))]

    disclaimer = (
        "\\begin{center}\\fbox{\\parbox{0.85\\linewidth}{\\small\\itshape "
        + _latex_escape(cfg["disclaimer"]) + "}}\\end{center}\n"
        if cfg.get("disclaimer") else ""
    )

    # 仿宋(封面栏目字体)在 macOS 上映射到按需下载的 STFangsong,未装机器会出豆腐块;
    # 覆写为必装的 Songti SC。fontset 可经 pkuthss.fontset 配置(默认 mac)。
    fontfix = (
        "\\setCJKfamilyfont{zhfs}{Songti SC}\n"
        if meta.get("fontset", "mac") == "mac" else ""
    )
    tex = f"""\\documentclass[UTF8,openany]{{pkuthss}}
{fontfix}\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{hyperref}}
\\hypersetup{{hidelinks}}
\\newif\\ifblind\\blindfalse
\\pkuthssinfo{{
  cthesisname = {{{meta.get('cthesisname', '本科生毕业论文')}}}, ethesisname = {{{meta.get('ethesisname', 'Undergraduate Thesis')}}},
  ctitle = {{{meta.get('ctitle', outline.get('title', ''))}}}, etitle = {{{_latex_escape(outline.get('title', ''))}}},
  cauthor = {{{meta.get('cauthor', cfg.get('author', 'paperflow'))}}}, eauthor = {{{meta.get('eauthor', 'paperflow demo')}}},
  studentid = {{{meta.get('studentid', '00000000')}}}, date = {{{meta.get('date', '某年某月')}}},
  school = {{{meta.get('school', '示例学院')}}}, cmajor = {{{meta.get('cmajor', '材料化学')}}},
  emajor = {{{meta.get('emajor', 'Materials Chemistry')}}}, direction = {{{meta.get('direction', '电催化')}}},
  mentorlines = {{1}},
  cmentor = {{{meta.get('cmentor', '示例导师 教授')}}}, ementor = {{{meta.get('ementor', 'Prof.\\ Demo')}}},
  ckeywords = {{{meta.get('ckeywords', '、'.join(cfg.get('keywords', [])))}}},
  ekeywords = {{{meta.get('ekeywords', ', '.join(cfg.get('keywords', [])))}}},
  degreetype = {{1}}, blindid = {{0000000000}}, discipline = {{{meta.get('discipline', '材料科学')}}}
}}
\\begin{{document}}
\\frontmatter
\\pagestyle{{empty}}
\\maketitle
\\cleardoublepage
\\pagestyle{{plain}}
\\setcounter{{page}}{{0}}
\\pagenumbering{{Roman}}
\\begin{{cabstract}}
{disclaimer}{abstract}
\\end{{cabstract}}
\\begin{{eabstract}}
{meta.get('eabstract', '(English abstract omitted in this demo.)')}
\\end{{eabstract}}
\\tableofcontents
\\mainmatter
{"".join(chapters)}
\\appendix
{_thebibliography(state['bibliography'])}
\\end{{document}}
"""
    out = build / "thesis.tex"
    out.write_text(tex, encoding="utf-8")
    return out


def find_engine() -> list[str] | None:
    for name, args in [("tectonic", []), ("xelatex", ["-interaction=nonstopmode"])]:
        binpath = shutil.which(name)
        if binpath:
            return [binpath, *args]
    return None


def compile_pdf(tex_path: Path) -> tuple[Path | None, str]:
    """编译 tex → pdf。tectonic 自动处理多轮与 bibtex;xelatex 手动多轮。"""
    engine = find_engine()
    if engine is None:
        return None, "未找到 LaTeX 引擎(tectonic/xelatex)"
    cwd = tex_path.parent
    is_tectonic = "tectonic" in engine[0]
    runs = 1 if is_tectonic else 3
    log_tail = ""
    for i in range(runs):
        r = subprocess.run([*engine, tex_path.name], capture_output=True, text=True,
                           cwd=cwd, timeout=1200)
        log_tail = (r.stdout + r.stderr)[-2000:]
        if not is_tectonic and i == 0 and "\\bibliography{" in tex_path.read_text(encoding="utf-8"):
            subprocess.run(["bibtex", tex_path.stem], capture_output=True, text=True, cwd=cwd)
        if is_tectonic and r.returncode != 0:
            return None, log_tail
    pdf = cwd / (tex_path.stem + ".pdf")
    return (pdf, log_tail) if pdf.is_file() and pdf.stat().st_size > 5000 else (None, log_tail)
