"""OOXML 低层工具 —— 全库唯一允许碰 w: 标签的地方。

两条硬约束(研究实测,违反后 Word 报"文件已损坏"而 LibreOffice 照常打开
—— LO 能开不等于 Word 能开):
  1. CT_PPr / CT_RPr / CT_SectPr / CT_TblPr 的子元素**顺序固定**,必须按 schema 序插入。
  2. 写 w:rFonts 的具体字体后,必须删掉同一元素上的 *Theme 属性
     (ECMA-376 里 *Theme 优先,不删就白设)。
"""
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# schema 规定的子元素顺序(只列本库会写的)
ORDER = {
    "w:pPr": ["w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore",
              "w:numPr", "w:pBdr", "w:shd", "w:tabs", "w:snapToGrid",
              "w:spacing", "w:ind", "w:jc", "w:rPr"],
    "w:rPr": ["w:rFonts", "w:b", "w:i", "w:sz", "w:szCs", "w:color", "w:vertAlign"],
    "w:sectPr": ["w:footnotePr", "w:type", "w:pgSz", "w:pgMar", "w:pgNumType",
                 "w:cols", "w:docGrid"],
    "w:tblPr": ["w:tblStyle", "w:tblW", "w:jc", "w:tblBorders", "w:tblLayout", "w:tblLook"],
    "w:tblBorders": ["w:top", "w:left", "w:bottom", "w:right", "w:insideH", "w:insideV"],
    "w:tcBorders": ["w:top", "w:left", "w:bottom", "w:right"],
    "w:trPr": ["w:cantSplit", "w:tblHeader", "w:trHeight"],
}


def ordered_insert(parent, tag):
    """按 schema 序插入(或取回)子元素。禁止在别处直接 append。"""
    existing = parent.find(qn(tag))
    if existing is not None:
        return existing
    el = OxmlElement(tag)
    order = ORDER.get(parent.tag.split("}")[-1] and _short(parent.tag))
    if not order or tag not in order:
        parent.append(el)
        return el
    idx = order.index(tag)
    for child in parent:
        cs = _short(child.tag)
        if cs in order and order.index(cs) > idx:
            child.addprevious(el)
            return el
    parent.append(el)
    return el


def _short(clark):
    """{ns}tag → w:tag"""
    if "}" not in clark:
        return clark
    return "w:" + clark.split("}", 1)[1]


def set_fonts(rpr, latin, east):
    """写中西文字体。*Theme 属性必须删——否则显式字体被主题覆盖。"""
    rf = ordered_insert(rpr, "w:rFonts")
    rf.set(qn("w:ascii"), latin)
    rf.set(qn("w:hAnsi"), latin)
    rf.set(qn("w:eastAsia"), east)
    rf.set(qn("w:cs"), latin)
    rf.set(qn("w:hint"), "eastAsia")
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]


def set_val(parent, tag, val, attr="w:val"):
    el = ordered_insert(parent, tag)
    el.set(qn(attr), str(val))
    return el


def field(par, instr, cached=""):
    """插入 Word 域:PAGE / NUMPAGES / REF / TOC。cached 为域的缓存显示文本。"""
    r1 = par.add_run()._r
    fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), "begin"); r1.append(fc)
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = f" {instr} "
    r1.append(it)
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate"); r1.append(sep)
    if cached:
        r2 = par.add_run(cached)._r
    else:
        r2 = par.add_run()._r
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    r2.append(end)
    return r2


def bookmark(par, name, text, bid):
    """给一段文本加书签。REF 域在 LibreOffice 下会重算并读书签真实内容,
    因此**书签只能包住编号本身**(如 "图 2.1"),包上题名会让引用显示整句。"""
    st = OxmlElement("w:bookmarkStart")
    st.set(qn("w:id"), str(bid)); st.set(qn("w:name"), name)
    par._p.append(st)
    run = par.add_run(text)
    en = OxmlElement("w:bookmarkEnd"); en.set(qn("w:id"), str(bid))
    par._p.append(en)
    return run


def cell_bottom_border(cell, sz):
    """表头下线必须落到每个单元格的 tcPr/tcBorders/bottom ——
    表级 tblBorders 没有"第一行下方"这个概念,这是三线表最常见的失败点。"""
    tcpr = cell._tc.get_or_add_tcPr()
    borders = ordered_insert(tcpr, "w:tcBorders")
    b = ordered_insert(borders, "w:bottom")
    b.set(qn("w:val"), "single"); b.set(qn("w:sz"), str(sz))
    b.set(qn("w:space"), "0"); b.set(qn("w:color"), "000000")


def repeat_header(row):
    """表头跨页重复。"""
    trpr = row._tr.get_or_add_trPr()
    ordered_insert(trpr, "w:tblHeader")


def page_numbering(sectPr, fmt="decimal", start=None):
    """分段页码。w:start 的有无就是"重排 vs 续排"的唯一开关。"""
    pn = ordered_insert(sectPr, "w:pgNumType")
    pn.set(qn("w:fmt"), fmt)
    if start is not None:
        pn.set(qn("w:start"), str(start))
    elif pn.get(qn("w:start")) is not None:
        del pn.attrib[qn("w:start")]
    return pn


def update_fields_on_open(document):
    """让 Word 打开时自动更新域(目录页码、交叉引用)。"""
    settings = document.settings.element
    if settings.find(qn("w:updateFields")) is None:
        el = OxmlElement("w:updateFields")
        el.set(qn("w:val"), "true")
        settings.insert(0, el)
