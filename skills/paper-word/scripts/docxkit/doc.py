"""docxkit 主引擎:块声明 → 带编号与交叉引用的 docx。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import style as ST
from .oxml_util import (bookmark, cell_bottom_border, field, ordered_insert,
                        page_numbering, repeat_header, set_fonts, set_val,
                        update_fields_on_open)

ALIGN = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
         "right": WD_ALIGN_PARAGRAPH.RIGHT, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY}
ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"

# 正文内联标记:{@fig:x} 交叉引用、{[key]} 文献引用、{^text} 脚注
INLINE = re.compile(r"\{@([\w:.-]+)\}|\{\[([\w,\s.-]+)\]\}|\{\^([^}]+)\}")


@dataclass
class Warn:
    code: str
    level: str      # error | warn | info
    msg: str


class Doc:
    def __init__(self, title, author="", school="", major="", advisor="",
                 student_id="", date="", subtitle="", level="report",
                 header_text=None, logo=True, allow=(), photos_required=False):
        self.meta = dict(title=title, subtitle=subtitle, author=author, school=school,
                         major=major, advisor=advisor, student_id=student_id, date=date,
                         level=level)
        self.header_text = header_text or title
        self.logo = (ASSETS / "pku_logo.png") if logo is True else (Path(logo) if logo else None)
        self.allow = set(allow)
        self.photos_required = photos_required
        self.d = Document()
        self._init_page()
        self._init_base_style()
        # 编号与引用状态
        self.ch = 0                    # 当前章序;附录时为字母
        self.appendix = None
        self.counters = {"fig": 0, "tab": 0, "eq": 0}   # 章内计数,每章清零
        self.totals = {"fig": 0, "tab": 0, "eq": 0}     # 全篇累计,只增不清
        self.sec_no = [0, 0, 0]
        self.marks = {}                # label -> (显示文本, bookmark 名)
        self.pending = []              # 前向引用:(缓存文本 run, instrText, label)
        self.cited = []                # 正文引用过的文献 key(首次出现序)
        self.refs_keys = []
        self.warns: list[Warn] = []
        self._bid = 1000
        self._toc_entries = []
        self._body_started = False
        self._photos = 0
        self._fignotes = []            # 声明过 label 的图/表/式
        self._used = set()             # 被 {@…} 引用过的 label

    # ---------------- 基础设置 ----------------
    def _init_page(self):
        s = self.d.sections[0]
        s.page_width, s.page_height = ST.PAGE["width"], ST.PAGE["height"]
        s.top_margin, s.bottom_margin = ST.PAGE["top"], ST.PAGE["bottom"]
        s.left_margin, s.right_margin = ST.PAGE["left"], ST.PAGE["right"]
        s.header_distance, s.footer_distance = ST.PAGE["header_dist"], ST.PAGE["footer_dist"]

    def _init_base_style(self):
        """Normal 样式设成正文规格:整篇的兜底。"""
        n = self.d.styles["Normal"]
        n.font.size = Pt(ST.S["body"]["size"])
        set_fonts(n.element.get_or_add_rPr(), ST.FONT["tnr"][0], ST.cjk("song"))

    # ---------------- 段落工厂 ----------------
    def _p(self, key, text="", parent=None):
        """按样式表建段落。样式直接写进段落属性(不依赖 Word 内建样式名)。"""
        cfg = ST.S[key]
        par = (parent or self.d).add_paragraph()
        pf, ppr = par.paragraph_format, par._p.get_or_add_pPr()
        if cfg.get("page_break"):
            ordered_insert(ppr, "w:pageBreakBefore")
        if cfg.get("keep_next"):
            ordered_insert(ppr, "w:keepNext")
        par.alignment = ALIGN[cfg["align"]]
        pf.space_before, pf.space_after = Pt(cfg["before"]), Pt(cfg["after"])
        line = cfg["line"]
        if line[0] == "exact":
            sp = ordered_insert(ppr, "w:spacing")
            sp.set(qn("w:line"), str(int(line[1] * 20)))
            sp.set(qn("w:lineRule"), "exact")
            set_val(ppr, "w:snapToGrid", "0")     # 不设会被文档网格吸附,固定行距失效
        if cfg.get("indent_chars"):
            ind = ordered_insert(ppr, "w:ind")
            ind.set(qn("w:firstLineChars"), str(cfg["indent_chars"] * 100))
            ind.set(qn("w:firstLine"), str(cfg["indent_chars"] * cfg["size"] * 20))
        if cfg.get("indent_left_chars"):
            ind = ordered_insert(ppr, "w:ind")
            ind.set(qn("w:leftChars"), str(cfg["indent_left_chars"] * 100))
        if cfg.get("hanging_chars"):
            ind = ordered_insert(ppr, "w:ind")
            ind.set(qn("w:leftChars"), str(cfg["hanging_chars"] * 100))
            ind.set(qn("w:hangingChars"), str(cfg["hanging_chars"] * 100))
        if text:
            self._run(par, text, key)
        return par

    def _run(self, par, text, key, bold=None):
        cfg = ST.S[key]
        run = par.add_run(text)
        run.font.size = Pt(cfg["size"])
        run.bold = cfg.get("bold", False) if bold is None else bold
        run.font.color.rgb = RGBColor.from_string(cfg.get("color", ST.BLACK))
        set_fonts(run._r.get_or_add_rPr(), ST.FONT[cfg["latin"]][0], ST.cjk(cfg["cjk"]))
        return run

    # ---------------- 前置部分 ----------------
    def cover(self, occasion=None):
        """封面:校徽 → 场合 → 题名 → 信息表 → 日期。

        信息区必须走无框表格。整行居中的写法(每行一个 "作者：李明")在中文封面里
        永远对不齐——姓名两字与"指导教师"四字的行宽不同,居中后冒号呈锯齿状。
        标签右对齐、值左对齐加下划线,才是学位论文封面的标准做法。
        """
        m = self.meta
        if self.logo and self.logo.exists():
            p = self._p("cover.info")
            p.add_run().add_picture(str(self.logo), width=Cm(4.8), height=Cm(1.12))
        # 留白按内容多少收缩:题名每多一行、有副题,都要从底部留白里扣回来,
        # 否则长题名会把日期挤到第二页——封面翻页是硬伤。
        title_lines = max(1, -(-len(m["title"]) // 14))
        bottom_gap = 11 - (2 if m["subtitle"] else 0) - 2 * (title_lines - 1)
        self._gap(4)
        if occasion:
            self._p("cover.occasion", occasion)
        self._p("cover.title", m["title"])
        if m["subtitle"]:
            self._p("cover.subtitle", m["subtitle"])
        self._gap(7)

        rows = [("作　　者", m["author"]), ("学　　号", m["student_id"]),
                ("院　　系", m["school"]), ("专　　业", m["major"]),
                ("指导教师", m["advisor"])]
        rows = [(k, v) for k, v in rows if v]
        if rows:
            t = self.d.add_table(rows=len(rows), cols=2)
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            # 必须关自适应并写死表宽:autofit 下 Word 会按内容重算列宽,
            # 单元格上设的 width 被忽略,居中也就跟着偏。
            t.autofit = False
            tw = ordered_insert(t._tbl.tblPr, "w:tblW")
            tw.set(qn("w:w"), str(int(10.8 * 567))); tw.set(qn("w:type"), "dxa")
            set_val(t._tbl.tblPr, "w:tblLayout", "fixed", attr="w:type")
            self._no_borders(t)
            for i, (k, v) in enumerate(rows):
                lc, vc = t.rows[i].cells
                lc.width, vc.width = Cm(4.0), Cm(6.8)
                self._cell_text(lc, f"{k}：", "cover.info", align="right")
                self._cell_text(vc, v, "cover.info", align="center")
                cell_bottom_border(vc, 6)              # 值下方的实线
        self._gap(max(3, bottom_gap))
        if m["date"]:
            self._p("cover.date", m["date"])
        self._new_section(fmt=None)                    # 封面无页码

    def _gap(self, n):
        for _ in range(n):
            self._p("cover.info")

    def _no_borders(self, table):
        borders = ordered_insert(table._tbl.tblPr, "w:tblBorders")
        for tag in ("w:top", "w:left", "w:bottom", "w:right", "w:insideH", "w:insideV"):
            b = ordered_insert(borders, tag)
            b.set(qn("w:val"), "none"); b.set(qn("w:sz"), "0")
            b.set(qn("w:space"), "0"); b.set(qn("w:color"), "auto")

    def _cell_text(self, cell, text, key, align=None, bold=None):
        """写单元格。必须复用第一个空段落,另起新段会在格内多出一行空白。"""
        par = cell.paragraphs[0]
        cfg = ST.S[key]
        par.alignment = ALIGN[align or cfg["align"]]
        par.paragraph_format.space_before = Pt(cfg["before"])
        par.paragraph_format.space_after = Pt(cfg["after"])
        if text:
            self._run(par, text, key, bold=bold)
        return par

    def abstract_zh(self, text, keywords=()):
        self._chapter_like("摘要")
        for para in _paras(text):
            self._p("body", para)
        if keywords:
            p = self._p("abs.kw")
            self._run(p, "关键词：", "abs.kw", bold=True)
            self._run(p, "，".join(keywords), "abs.kw")
        self._start_front_numbering()

    def abstract_en(self, text, keywords=()):
        self._chapter_like("ABSTRACT")
        for para in _paras(text):
            self._p("body", para)
        if keywords:
            p = self._p("abs.kw")
            self._run(p, "KEY WORDS: ", "abs.kw", bold=True)
            self._run(p, ", ".join(keywords), "abs.kw")

    def toc(self, depth=2):
        """插入 TOC 域。生成时目录是空的——Word 打开会按 updateFields 自动刷新;
        LibreOffice 需手动 Tools → Update → Indexes。这是 Word 域的固有行为。"""
        self._chapter_like("目录")
        p = self._p("toc.ch")
        field(p, f'TOC \\o "1-{depth}" \\h \\z \\u', cached="【目录：在 Word 中按 Ctrl+A 后 F9 更新】")

    # ---------------- 章节 ----------------
    def chapter(self, title, appendix=None):
        """新章。appendix 传字母(如 'A')时切到附录编号体系。"""
        if not self._body_started:
            self._start_body_numbering()
            self._body_started = True
        if appendix:
            self.appendix = appendix
            heading = f"附录 {appendix}　{title}"
            self.ch = appendix
        else:
            self.ch += 1 if isinstance(self.ch, int) else 0
            if not isinstance(self.ch, int):
                self.ch = 1
            heading = f"第{ST.cn_number(self.ch)}章　{title}"
        self.counters = {k: 0 for k in self.counters}
        self.sec_no = [0, 0, 0]
        self._p("chapter", heading)
        self._toc_entries.append(("ch", heading))
        return heading

    def section(self, title, level=1):
        self.sec_no[level - 1] += 1
        for i in range(level, 3):
            self.sec_no[i] = 0
        parts = [str(self.ch)] + [str(x) for x in self.sec_no[:level]]
        no = ".".join(parts)
        self._p(f"sec{level}", f"{no}　{title}")
        self._toc_entries.append((f"s{level}", f"{no} {title}"))
        if level >= 3:
            self.warns.append(Warn("W7", "info",
                f"节标题「{title}」已到第 {level} 级(1.1.1.x)——层级过深多半说明该拆章"))
        return no

    def para(self, text, indent=True):
        par = self._p("body")
        self._inline(par, text, "body")
        if not indent:
            ind = par._p.get_or_add_pPr().find(qn("w:ind"))
            if ind is not None:
                par._p.get_or_add_pPr().remove(ind)
        return par

    # ---------------- 图 / 表 / 公式 ----------------
    def figure(self, path, caption, label=None, width_cm=None, credit=None):
        self.counters["fig"] += 1; self.totals["fig"] += 1
        num = f"{self.ch}{ST.NUM_SEP}{self.counters['fig']}"
        disp = f"{ST.LABEL['fig']} {num}"
        p_img = self._p("fig.image")
        w = Cm(min(width_cm or ST.USABLE_W_CM, ST.USABLE_W_CM))
        p_img.add_run().add_picture(str(path), width=w)
        cap = self._p("fig.caption")
        if label:
            self._bookmark_num(cap, label, disp)
        else:
            self._run(cap, disp, "fig.caption")
        tail = f"　{caption}" + (f"（{credit}）" if credit else "")
        self._run(cap, tail, "fig.caption")
        if _is_photo(path):
            self._photos += 1
        self._fignotes.append(label)
        return disp

    def table(self, rows, caption, label=None, header_rows=1, note=None, widths=None):
        self.counters["tab"] += 1; self.totals["tab"] += 1
        num = f"{self.ch}{ST.NUM_SEP}{self.counters['tab']}"
        disp = f"{ST.LABEL['tab']} {num}"
        cap = self._p("tab.caption")
        if label:
            self._bookmark_num(cap, label, disp)
        else:
            self._run(cap, disp, "tab.caption")
        self._run(cap, f"　{caption}", "tab.caption")

        t = self.d.add_table(rows=len(rows), cols=len(rows[0]))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        self._three_line(t, header_rows)
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                cell = t.cell(ri, ci)
                cell.text = ""
                par = cell.paragraphs[0]
                cfg = ST.S["tab.cell"]
                par.alignment = ALIGN["center"] if ri < header_rows else ALIGN[cfg["align"]]
                pf = par.paragraph_format
                pf.space_before, pf.space_after = Pt(cfg["before"]), Pt(cfg["after"])
                self._run(par, str(val), "tab.cell", bold=(ri < header_rows))
        if widths:
            for ci, frac in enumerate(widths):
                for row in t.rows:
                    row.cells[ci].width = Cm(ST.USABLE_W_CM * frac)
        if note:
            self._p("tab.note", note)
        self._fignotes.append(label)
        return disp

    def formula(self, image_path, label=None):
        """公式图片居中 + 右端编号(制表位方案)。公式段必须无首行缩进,否则居中制表位被推偏。"""
        self.counters["eq"] += 1; self.totals["eq"] += 1
        num = f"{self.ch}{ST.NUM_SEP}{self.counters['eq']}"
        disp = f"（{num}）"
        par = self._p("formula")
        pf = par.paragraph_format
        pf.tab_stops.add_tab_stop(Cm(ST.USABLE_W_CM / 2), WD_TAB_ALIGNMENT.CENTER)
        pf.tab_stops.add_tab_stop(Cm(ST.USABLE_W_CM), WD_TAB_ALIGNMENT.RIGHT)
        par.add_run("\t")
        img = par.add_run()
        h = Pt(ST.S["formula"]["size"] * 1.5)
        img.add_picture(str(image_path), height=h)
        par.add_run("\t")
        if label:
            self._bookmark_num(par, label, disp, prefix_space=False)
        else:
            self._run(par, disp, "formula")
        self._fignotes.append(label)
        return disp

    # ---------------- 后置部分 ----------------
    def refs(self, entries):
        self._chapter_like("参考文献")
        self.refs_keys = [e["key"] for e in entries]
        by_key = {e["key"]: e for e in entries}
        # 顺序编码制:按正文首次引用顺序排;未被引用的排在后面并报警
        ordered = [by_key[k] for k in self.cited if k in by_key]
        rest = [e for e in entries if e["key"] not in self.cited]
        for i, e in enumerate(ordered + rest, 1):
            self._p("ref.entry", f"[{i}] " + _gbt7714(e))

    def acknowledge(self, text, funding=()):
        """致谢。中文学位论文的致谢是散文,不做成条目表——列表化是汇报 PPT 的写法。
        funding 传 [(基金名, 编号)],按规范单起一段标注在末尾。"""
        self._chapter_like("致谢")
        for para in _paras(text):
            self._p("body", para)
        if funding:
            items = "；".join(f"{n}（{no}）" if no else n for n, no in funding)
            self._p("body", f"本工作得到{items}的资助，谨此致谢。")
        if len(text) > 1200:
            self.warns.append(Warn("W9", "info", "致谢超过 1200 字,通常一页以内即可"))

    # ---------------- 内部:章级标题 / 分节 / 页码 ----------------
    def _chapter_like(self, name):
        self._p("chapter", name)
        self._toc_entries.append(("ch", name))
        self.counters = {k: 0 for k in self.counters}

    def _new_section(self, fmt="upperRoman", start=1):
        sec = self.d.add_section(WD_SECTION.NEW_PAGE)
        sec.page_width, sec.page_height = ST.PAGE["width"], ST.PAGE["height"]
        sec.top_margin, sec.bottom_margin = ST.PAGE["top"], ST.PAGE["bottom"]
        sec.left_margin, sec.right_margin = ST.PAGE["left"], ST.PAGE["right"]
        sec.header_distance, sec.footer_distance = ST.PAGE["header_dist"], ST.PAGE["footer_dist"]
        if fmt:
            page_numbering(sec._sectPr, fmt=fmt, start=start)
        return sec

    def _start_front_numbering(self):
        self._front_sec = self.d.sections[-1]
        page_numbering(self._front_sec._sectPr, fmt="upperRoman", start=1)

    def _start_body_numbering(self):
        sec = self._new_section(fmt="decimal", start=1)
        self._body_sec = sec

    def _bookmark_num(self, par, label, disp, prefix_space=True):
        """把编号包进 bookmark。只包编号,不包题名——REF 在 LO 下会重算并读书签内容。"""
        self._bid += 1
        name = f"_Ref{re.sub(r'[^A-Za-z0-9]', '', label)}{self._bid}"
        run = bookmark(par, name, disp, self._bid)
        cfg = ST.S["fig.caption"]
        run.font.size = Pt(cfg["size"])
        run.font.color.rgb = RGBColor.from_string(ST.BLACK)
        set_fonts(run._r.get_or_add_rPr(), ST.FONT[cfg["latin"]][0], ST.cjk(cfg["cjk"]))
        self.marks[label] = (disp, name)
        return run

    # ---------------- 内联标记解析 ----------------
    def _inline(self, par, text, key):
        pos = 0
        for m in INLINE.finditer(text):
            if m.start() > pos:
                self._run(par, text[pos:m.start()], key)
            ref, cites, foot = m.group(1), m.group(2), m.group(3)
            if ref:
                self._xref(par, ref, key)
            elif cites:
                keys = [k.strip() for k in cites.split(",") if k.strip()]
                nums = []
                for k in keys:
                    if k not in self.cited:
                        self.cited.append(k)
                    nums.append(str(self.cited.index(k) + 1))
                sup = self._run(par, f"[{','.join(nums)}]", key)
                sup.font.superscript = True
            elif foot:
                # 真脚注需要新建 footnotes.xml 部件,代价高;此处降级为句内小字夹注,
                # 并明确告知——见 SKILL.md 已知限制
                note = self._run(par, f"（注：{foot}）", key)
                note.font.size = Pt(ST.S["ref.entry"]["size"])
            pos = m.end()
        if pos < len(text):
            self._run(par, text[pos:], key)

    def _xref(self, par, label, key):
        """交叉引用:REF 域 + 缓存文本。前向引用在 build 时回填。"""
        self._used.add(label)
        disp, name = self.marks.get(label, (None, None))
        if name:
            field(par, f"REF {name} \\h", cached=disp)
        else:
            r = field(par, "REF _PENDING \\h", cached="【??】")
            # 必须记下**这一个**域的 instrText:同一段里可能有多个待回填的引用,
            # 只按段落找占位符会让先回填的那个把后面的也改掉(引用全指向同一张图)。
            instr = list(par._p.iter(qn("w:instrText")))[-1]
            self.pending.append((r, instr, label))

    # ---------------- 三线表 ----------------
    def _three_line(self, table, header_rows):
        tblpr = table._tbl.tblPr
        borders = ordered_insert(tblpr, "w:tblBorders")
        for tag, sz in (("w:top", ST.TABLE_TOP_SZ), ("w:bottom", ST.TABLE_BOTTOM_SZ)):
            b = ordered_insert(borders, tag)
            b.set(qn("w:val"), "single"); b.set(qn("w:sz"), str(sz))
            b.set(qn("w:space"), "0"); b.set(qn("w:color"), "000000")
        for tag in ("w:left", "w:right", "w:insideH", "w:insideV"):
            b = ordered_insert(borders, tag)
            b.set(qn("w:val"), "none"); b.set(qn("w:sz"), "0")
            b.set(qn("w:space"), "0"); b.set(qn("w:color"), "auto")
        for ri in range(header_rows):
            repeat_header(table.rows[ri])
            for cell in table.rows[ri].cells:
                cell_bottom_border(cell, ST.TABLE_HEAD_SZ)

    # ---------------- 页眉页脚 ----------------
    def _decorate(self):
        for i, sec in enumerate(self.d.sections):
            if i == 0:                              # 封面节无页眉页脚
                sec.different_first_page_header_footer = False
                continue
            sec.header.is_linked_to_previous = False
            sec.footer.is_linked_to_previous = False
            hp = sec.header.paragraphs[0]
            # 校徽居左、书名居中。制表位必须显式声明:清空段落制表位并不会
            # 移除 Header 样式自带的那两个,不写就会撞上样式里的默认位置。
            hp.paragraph_format.tab_stops.clear_all()
            hp.paragraph_format.tab_stops.add_tab_stop(
                Cm(ST.USABLE_W_CM / 2), WD_TAB_ALIGNMENT.CENTER)
            hp.paragraph_format.tab_stops.add_tab_stop(ST.USABLE_W, WD_TAB_ALIGNMENT.RIGHT)
            if self.logo and self.logo.exists():
                hp.add_run().add_picture(str(self.logo), width=Cm(2.4), height=Cm(0.56))
            hp.add_run("\t")
            self._run(hp, self.header_text, "header")
            ppr = hp._p.get_or_add_pPr()
            pbdr = ordered_insert(ppr, "w:pBdr")
            bt = ordered_insert(pbdr, "w:bottom")
            bt.set(qn("w:val"), "single")
            bt.set(qn("w:sz"), str(int(ST.PAGE["header_rule_pt"] * 8)))
            bt.set(qn("w:space"), "1"); bt.set(qn("w:color"), ST.PKU_RED)

            fp = sec.footer.paragraphs[0]
            fp.alignment = ALIGN["center"]
            pn = sec._sectPr.find(qn("w:pgNumType"))
            roman = pn is not None and (pn.get(qn("w:fmt")) or "").endswith("Roman")
            if roman:
                # 前置部分只给罗马页码。写"共 N 页"会连 NUMPAGES 一起被本节的
                # 罗马格式渲染成"共 VIII 页"——那是全文页数,却按前置格式显示,是错的。
                field(fp, "PAGE", cached="I")
            else:
                self._run(fp, "第 ", "footer")
                field(fp, "PAGE", cached="1")
                self._run(fp, " 页 / 共 ", "footer")
                field(fp, r"NUMPAGES \* ARABIC", cached="1")
                self._run(fp, " 页", "footer")

    # ---------------- 检查 ----------------
    def _check(self):
        W = self.warns.append
        if not self.refs_keys:
            W(Warn("W1", "error", "参考文献一节缺失或为空。技术文档与学位论文必须著录参考文献;"
                                  "找不到可靠来源时留空报错,禁止虚构条目补数"))
        else:
            miss = [k for k in self.cited if k not in self.refs_keys]
            unused = [k for k in self.refs_keys if k not in self.cited]
            if miss:
                W(Warn("W2", "error", f"正文引用了未著录的文献:{miss}。顺序编码制要求引用过的必须著录"))
            if unused:
                W(Warn("W2", "warn", f"文献表中 {unused} 从未被正文引用——未引用的条目不应出现在文献表"))
        if self.pending:
            W(Warn("W3", "error", f"悬空交叉引用:{[t[-1] for t in self.pending]} 指向不存在的图表/公式"
                                  "(在 LibreOffice 里会渲染成 Error: Reference source not found)"))
        unref = [l for l in self._fignotes if l and l not in self._used]
        if unref:
            W(Warn("W3", "warn", f"{unref} 在正文中从未被引用。规范要求每张图表都在正文被提及并说明作用"))
        if self.photos_required and self._photos == 0:
            W(Warn("W6", "warn", "全篇没有实景照片。技术报告的对象/装置/现场应配真实照片"
                                 "(用 paper-slides 的 fetchimg.py 取 CC 许可图);"
                                 "确实不需要时传 photos_required=False"))

    def _scan_colors(self):
        """颜色越界检查:扫正文,以及**正文真正引用到的**样式定义。

        不能整份扫 styles.xml —— python-docx 默认模板里带着 Word 全套内建样式
        (Heading 1 的 365F91、各种表格样式…),它们一次也没被引用,全扫会报出
        六十多个假阳性,把这条检查淹掉。只有被 pStyle/rStyle/tblStyle 指名的
        样式(以及 docDefaults)才真正影响渲染。
        """
        bad = set()
        used = {"Normal"}
        for el in self.d.element.body.iter():
            if el.tag in (qn("w:pStyle"), qn("w:rStyle"), qn("w:tblStyle")):
                v = el.get(qn("w:val"))
                if v:
                    used.add(v)
        parts = [self.d.element.body]
        styles_el = self.d.styles.element
        dd = styles_el.find(qn("w:docDefaults"))
        if dd is not None:
            parts.append(dd)
        for st in styles_el.findall(qn("w:style")):
            if st.get(qn("w:styleId")) in used:
                parts.append(st)
        for part in parts:
            for el in part.iter():
                if el.tag == qn("w:color"):
                    v = (el.get(qn("w:val")) or "").upper()
                    if v and v not in {c.upper() for c in ST.COLOR_WHITELIST}:
                        bad.add(v)
                if el.tag == qn("w:shd"):
                    f = (el.get(qn("w:fill")) or "").upper()
                    if f and f not in {c.upper() for c in ST.COLOR_WHITELIST}:
                        bad.add(f)
        if bad:
            self.warns.append(Warn("W4", "warn",
                f"全文出现越界排版色 {sorted(bad)}(白名单:北大红 {ST.PKU_RED} 与黑)。图片内部用色不计"))

    # ---------------- 构建 ----------------
    def build(self, out_path):
        # 回填前向引用:声明在引用之后的图表,此时 marks 已齐
        for item in list(self.pending):
            run, instr, label = item
            if label in self.marks:
                disp, name = self.marks[label]
                _retarget(run, instr, name, disp)
                self.pending.remove(item)
        self._decorate()
        self._check()
        self._scan_colors()
        update_fields_on_open(self.d)
        self.d.save(out_path)

        errs = [w for w in self.warns if w.level == "error" and w.code not in self.allow]
        shown = [w for w in self.warns if w.code not in self.allow]
        if shown:
            print("docxkit 检查:")
            for w in shown:
                mark = {"error": "!!", "warn": "! ", "info": "~ "}[w.level]
                print(f"  {mark} [{w.code}] {w.msg}")
        for code in sorted(self.allow):
            print(f"  -- [{code}] 已显式豁免")
        stats = (f"{self.totals['fig']} 图 / {self.totals['tab']} 表 / "
                 f"{self.totals['eq']} 式 / {len(self.refs_keys)} 条文献")
        print(f"written: {out_path}（{stats}）")
        print("提示:目录与页码为 Word 域,在 Word 中打开会自动更新;"
              "若未刷新请 Ctrl+A 后按 F9。")
        if errs:
            raise SystemExit(f"docxkit: {len(errs)} 处 error 级问题,必须修正后重生成")


def _retarget(run, instr, name, disp):
    """把某一个占位 REF 域指向真实 bookmark 并写入缓存文本。
    只动传进来的 instr 与 run,不扫段落——同段多引用时扫段落会串号。"""
    instr.text = f" REF {name} \\h "
    for t in run.iter(qn("w:t")):
        if t.text == "【??】":
            t.text = disp


def _paras(text):
    return [p.strip() for p in text.strip().split("\n\n") if p.strip()]


def _is_photo(path):
    """带 credits.json 登记的图算实景照片(与 paper-slides 的判据一致)。"""
    import json
    p = Path(path)
    reg = p.parent / "credits.json"
    if not reg.exists():
        return False
    try:
        d = json.loads(reg.read_text())
    except Exception:
        return False
    hit = d.get(p.name)
    return bool(hit and hit.get("license") and "AI" not in str(hit["license"]))


def _gbt7714(e):
    """GB/T 7714-2015 顺序编码制。type: M 专著 J 期刊 D 学位论文 R 报告 S 标准 EB 电子."""
    a = e.get("authors", [])
    authors = ", ".join(a[:3]) + (", 等" if len(a) > 3 else "")
    t, title, year = e.get("type", "J"), e.get("title", ""), e.get("year", "")
    if t == "J":
        s = f"{authors}. {title}[J]. {e.get('journal','')}"
        if e.get("year"):
            s += f", {year}"
        if e.get("volume"):
            s += f", {e['volume']}"
        if e.get("issue"):
            s += f"({e['issue']})"
        if e.get("pages"):
            s += f": {e['pages']}"
        return s + "."
    if t in ("M", "R", "S"):
        return (f"{authors}. {title}[{t}]. {e.get('place','')}: "
                f"{e.get('publisher','')}, {year}.")
    if t == "D":
        return f"{authors}. {title}[D]. {e.get('place','')}: {e.get('publisher','')}, {year}."
    if t == "EB":
        return (f"{authors}. {title}[EB/OL]. {e.get('url','')}"
                f"({year})[{e.get('accessed','')}].")
    return f"{authors}. {title}. {year}."
