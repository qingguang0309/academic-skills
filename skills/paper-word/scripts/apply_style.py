#!/usr/bin/env python3
"""为 .docx 应用北京大学风格排版：
- 页眉：左侧北大 logo（assets/pku_logo.png，0.95in × 0.22in），
  右侧文档大标题（Microsoft YaHei，北大红，右对齐 tab）
- 页眉下方：北大红 0.5pt 分隔线
- 页脚：居中 "第X页/共X页"，用 PAGE / NUMPAGES 域（自动更新）
- 全文字体：正文中文宋体 + 西文 Times New Roman；标题中文微软雅黑 + 西文 Arial
- 全文各级标题统一北大红（#94070A），不引入其他颜色
- 表格统一改为学术三线表：清除单元格底纹、去竖线与内部横线，仅保留
  顶线/表头下线/底线（黑色），表内文字统一黑色
- 全文只保留红、黑两色：去掉段落装饰性框线（含蓝色标题下划线），
  正文里非北大红的字色/框线一律归黑，非白色底纹一律清除

用法：python apply_style.py <doc.docx> --title "文档大标题" [--logo path] [-o out.docx]
依赖：pip install python-docx --break-system-packages
"""
import argparse
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement

DEFAULT_LOGO = Path(__file__).resolve().parent.parent / "assets" / "pku_logo.png"
LOGO_W_IN, LOGO_H_IN = 0.95, 0.22          # 页眉 logo 尺寸
PKU_RED = "94070A"                          # 北大红（全文唯一强调色）
PKU_RED_RGB = RGBColor(0x94, 0x07, 0x0A)    # 同上，供字体颜色使用
TITLE_FONT = "Microsoft YaHei"
TITLE_SIZE_PT = 9
BODY_LATIN, BODY_EAST = "Times New Roman", "SimSun"   # 正文：西文/中文
HEAD_LATIN, HEAD_EAST = "Arial", "Microsoft YaHei"    # 各级标题：西文/中文
# 覆盖所有级别：总标题 + 副标题 + Heading 1–9（Word 支持到 9 级），一律北大红、不逐级换色
HEADING_STYLES = ("Title", "Subtitle") + tuple(f"Heading {i}" for i in range(1, 10))


def _is_heading_style(name):
    """判断段落样式是否属于标题族（含中文本地化名 “标题 1” 及自定义 Heading*）。"""
    if not name:
        return False
    if name in ("Title", "Subtitle", "标题", "副标题"):
        return True
    return name.startswith("Heading") or name.startswith("标题 ")


def _clear(container):
    for p in list(container.paragraphs):
        p._element.getparent().remove(p._element)
    return container.add_paragraph()


def _field(par, instr):
    """在段落中插入 Word 域（如 PAGE / NUMPAGES）。"""
    run = par.add_run()
    for el, attrs, text in (
        ("w:fldChar", {"w:fldCharType": "begin"}, None),
        ("w:instrText", {"xml:space": "preserve"}, f" {instr} "),
        ("w:fldChar", {"w:fldCharType": "end"}, None),
    ):
        e = OxmlElement(el)
        for k, v in attrs.items():
            e.set(qn(k), v)
        if text:
            e.text = text
        run._r.append(e)


def _set_run_fonts(run_or_style, latin, east):
    """同时设置西文字体与中文字体（eastAsia 必须走 XML）。"""
    font = run_or_style.font
    font.name = latin
    rpr = font.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)
    rfonts.set(qn("w:eastAsia"), east)


def _bottom_border(par, color=PKU_RED, sz_eighth_pt=4):
    """段落下边框：0.5pt = sz 4（单位为 1/8 pt）。"""
    ppr = par._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(sz_eighth_pt))
    bottom.set(qn("w:space"), "3")
    bottom.set(qn("w:color"), color)
    pbdr.append(bottom)
    ppr.append(pbdr)


def _iter_all_paragraphs(doc):
    """遍历正文段落 + 所有表格单元格内的段落（标题偶尔落在表格里）。"""
    yield from doc.paragraphs
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs


def _redden_heading_runs(par):
    """把标题段落每个 run 直接染北大红，覆盖直排式的行内颜色，
    确保样式级颜色被局部格式盖过时仍统一为北大红。"""
    for run in par.runs:
        run.font.color.rgb = PKU_RED_RGB


def _apply_document_fonts(doc):
    """正文与标题的默认字体+颜色。
    正文（含参考文献等英文内容）随 Normal 落到 Times New Roman，用默认黑色。
    各级标题（Title/Subtitle/Heading 1–9，即所有级别）统一北大红，
    全文除黑色正文外只保留这一种强调色。"""
    _set_run_fonts(doc.styles["Normal"], BODY_LATIN, BODY_EAST)
    # 1) 样式级：字体 + 颜色，覆盖所有存在的标题样式
    for name in HEADING_STYLES:
        try:
            style = doc.styles[name]
        except KeyError:
            continue
        _set_run_fonts(style, HEAD_LATIN, HEAD_EAST)
        style.font.color.rgb = PKU_RED_RGB
    # 2) 段落级兜底：任何标题族段落，逐 run 直接染红，防止局部格式盖过样式色
    for par in _iter_all_paragraphs(doc):
        if _is_heading_style(par.style.name):
            _redden_heading_runs(par)


# ---- 三线表 + 只保留红黑两色 ----

# OOXML 子元素次序（插入时须遵守，否则 Word 可能拒绝或忽略）
_TBLPR_SEQ = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
              "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd",
              "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook"]
_TCPR_SEQ = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd",
             "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"]


def _ordered_insert(parent, child, seq):
    tag = child.tag.split("}")[-1]
    idx = seq.index(tag)
    for existing in parent:
        etag = existing.tag.split("}")[-1]
        if etag in seq and seq.index(etag) > idx:
            existing.addprevious(child)
            return
    parent.append(child)


def _edge(tag, sz, val="single", color="000000"):
    """一条框线：sz 单位为 1/8 pt（12=1.5pt 粗线，6=0.75pt 细线）。"""
    e = OxmlElement("w:" + tag)
    e.set(qn("w:val"), val)
    e.set(qn("w:sz"), str(sz))
    e.set(qn("w:space"), "0")
    e.set(qn("w:color"), color)
    return e


def _three_line_table(table):
    """把一张表改成学术三线表：顶线/表头下线/底线（黑），无竖线、无其它横线，
    清除单元格底纹，表内文字统一黑色。"""
    tbl = table._tbl
    tblPr = tbl.tblPr

    # 关闭 tblStyle 的条件格式（首行/末行/隔行底纹与白字），避免它盖过下面的直接格式
    look = tblPr.find(qn("w:tblLook"))
    if look is None:
        look = OxmlElement("w:tblLook")
        _ordered_insert(tblPr, look, _TBLPR_SEQ)
    for k, v in (("firstRow", "0"), ("lastRow", "0"), ("firstColumn", "0"),
                 ("lastColumn", "0"), ("noHBand", "1"), ("noVBand", "1")):
        look.set(qn("w:" + k), v)
    look.set(qn("w:val"), "0000")

    # 表级边框：仅顶线 + 底线（1.5pt 黑），左右与内部线全部去掉
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")
    borders.append(_edge("top", 12))
    borders.append(_edge("left", 0, val="none", color="auto"))
    borders.append(_edge("bottom", 12))
    borders.append(_edge("right", 0, val="none", color="auto"))
    borders.append(_edge("insideH", 0, val="none", color="auto"))
    borders.append(_edge("insideV", 0, val="none", color="auto"))
    _ordered_insert(tblPr, borders, _TBLPR_SEQ)

    # 每个单元格：去底纹、去单元格自带边框、文字染黑
    for tc in tbl.iter(qn("w:tc")):
        tcPr = tc.find(qn("w:tcPr"))
        if tcPr is not None:
            for shd in tcPr.findall(qn("w:shd")):
                tcPr.remove(shd)
            for tcb in tcPr.findall(qn("w:tcBorders")):
                tcPr.remove(tcb)
        for run in tc.iter(qn("w:r")):
            rpr = run.find(qn("w:rPr"))
            if rpr is None:
                rpr = OxmlElement("w:rPr")
                run.insert(0, rpr)
            col = rpr.find(qn("w:color"))
            if col is None:
                col = OxmlElement("w:color")
                rpr.append(col)
            col.set(qn("w:val"), "000000")

    # 表头（首行）下加一条 0.75pt 黑细线
    if table.rows:
        for cell in table.rows[0].cells:
            tcPr = cell._tc.get_or_add_tcPr()
            for tcb in tcPr.findall(qn("w:tcBorders")):
                tcPr.remove(tcb)
            tcb = OxmlElement("w:tcBorders")
            tcb.append(_edge("bottom", 6))
            _ordered_insert(tcPr, tcb, _TCPR_SEQ)


def _strip_paragraph_borders(doc):
    """删掉正文段落的装饰性框线（如蓝色标题下划线）。
    房式风格里正文不加段落框线；页眉那条红色分隔线在 header 部件里，不受影响。"""
    for par in doc.paragraphs:
        ppr = par._p.find(qn("w:pPr"))
        if ppr is None:
            continue
        for pbdr in ppr.findall(qn("w:pBdr")):
            ppr.remove(pbdr)


def _enforce_two_colors(doc):
    """兜底：正文里只允许北大红与黑。非北大红的字色/框线归黑，非白底纹清除。
    只扫正文 body，页眉页脚（含北大红分隔线与标题）由脚本单独控制、保持原样。"""
    red = PKU_RED.upper()
    body = doc.element.body
    for el in body.iter():
        val = el.get(qn("w:color"))
        if val and val != "auto" and len(val) == 6 and val.upper() != red:
            el.set(qn("w:color"), "000000")
    for shd in body.iter(qn("w:shd")):
        fill = shd.get(qn("w:fill"))
        if fill and fill.lower() not in ("auto", "ffffff"):
            shd.set(qn("w:fill"), "auto")
            shd.set(qn("w:val"), "clear")


def apply_style(doc_path, title, logo_path=DEFAULT_LOGO, out_path=None):
    doc = Document(doc_path)
    _apply_document_fonts(doc)
    for table in doc.tables:          # 表格 → 三线表
        _three_line_table(table)
    _strip_paragraph_borders(doc)     # 去掉正文装饰性框线（含蓝色标题下划线）
    _enforce_two_colors(doc)          # 兜底：正文只留红、黑两色

    for section in doc.sections:
        section.different_first_page_header_footer = False

        # --- 页眉：logo 左 + 标题右（右对齐 tab stop 到右边距处）---
        header_par = _clear(section.header)
        header_par.paragraph_format.tab_stops.clear_all()
        usable = section.page_width - section.left_margin - section.right_margin
        header_par.paragraph_format.tab_stops.add_tab_stop(usable, WD_TAB_ALIGNMENT.RIGHT)

        logo_run = header_par.add_run()
        logo_run.add_picture(str(logo_path), width=Inches(LOGO_W_IN), height=Inches(LOGO_H_IN))
        header_par.add_run("\t")
        title_run = header_par.add_run(str(title))
        _set_run_fonts(title_run, TITLE_FONT, TITLE_FONT)
        title_run.font.size = Pt(TITLE_SIZE_PT)
        title_run.font.color.rgb = PKU_RED_RGB

        # 页眉下方：北大红 0.5pt 分隔线
        _bottom_border(header_par)

        # --- 页脚：第X页/共X页，居中，用域 ---
        footer_par = _clear(section.footer)
        footer_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_par.add_run("第")
        _field(footer_par, "PAGE")
        footer_par.add_run("页/共")
        _field(footer_par, "NUMPAGES")
        footer_par.add_run("页")

    doc.save(out_path or doc_path)
    print(f"OK: {out_path or doc_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--title", required=True)
    ap.add_argument("--logo", default=str(DEFAULT_LOGO))
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    apply_style(a.docx, a.title, Path(a.logo), a.out)
