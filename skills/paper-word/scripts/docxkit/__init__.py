"""docxkit —— 声明式 Word 生成层(北大风格学术文档)。

与 apply_style.py 的关系:apply_style 是后处理器,只看得见 XML、看不见语义,
所以"表头该不该染黑""哪个段落是题注""哪个 Title 是封面"这类判断它做不了。
docxkit 走生成期路线:作者只声明块,编号/交叉引用/样式/检查全由引擎负责。
外来的 docx(pandoc、他人交来)仍然用 apply_style.py 抢救。

用法见 SKILL.md;最小示例:

    from docxkit import Doc
    d = Doc(title="…", author="…", school="…", advisor="…")
    d.cover(); d.abstract_zh("…", keywords=[...]); d.toc()
    d.chapter("引言"); d.para("正文,引用见 {@fig:route} 与 {[wang2023]}。")
    d.figure("assets/route.png", "技术路线", label="fig:route")
    d.refs([...]); d.acknowledge("…"); d.build("out.docx")
"""
from .doc import Doc, Warn  # noqa: F401

__all__ = ["Doc", "Warn"]
