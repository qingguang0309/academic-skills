"""docxkit 样式常量 —— 北大学位论文/技术报告规范落成可直接编码的表。

规范基准:北京大学《研究生学位论文写作指南》、GB/T 7714-2015(著录)。
所有数值集中在这里,渲染层只读不改;改规范只改本文件。
"""
from docx.shared import Cm, Pt

# ---------- 颜色:全文只有北大红与黑 ----------
PKU_RED = "94070A"
BLACK = "000000"
COLOR_WHITELIST = {PKU_RED, BLACK, "auto", "FFFFFF"}

# ---------- 字体族(缺失时按序回退) ----------
FONT = {
    "song":  ("SimSun", ["Songti SC", "Noto Serif CJK SC", "STSong"]),
    "hei":   ("SimHei", ["Heiti SC", "Noto Sans CJK SC", "PingFang SC"]),
    "fs":    ("FangSong", ["STFangsong", "FangSong_GB2312"]),
    "yahei": ("Microsoft YaHei", ["PingFang SC", "Heiti SC"]),
    "tnr":   ("Times New Roman", ["Times", "Liberation Serif"]),
    "arial": ("Arial", ["Helvetica", "Liberation Sans"]),
}


def cjk(key):
    """取中文字体名(第一可用即写入,回退名只作文档说明)。"""
    return FONT[key][0]


# ---------- 页面(A4) ----------
PAGE = dict(
    width=Cm(21.0), height=Cm(29.7),
    top=Cm(3.0), bottom=Cm(2.5), left=Cm(2.6), right=Cm(2.6),
    header_dist=Cm(2.0), footer_dist=Cm(1.75),
    header_rule_pt=0.75,
)
USABLE_W = Cm(21.0 - 2.6 - 2.6)      # 版心宽 15.8 cm:图片封顶与制表位的唯一依据
USABLE_W_CM = 15.8

# ---------- 段落样式表 ----------
# line: ("exact", pt) = 固定值;("single",) = 单倍
# indent_chars: 首行缩进汉字符数
S = {
    "cover.title":   dict(cjk="hei",   latin="arial", size=26, line=("single",),
                          before=0, after=0, align="center", bold=True, color=BLACK),
    "cover.subtitle":dict(cjk="hei",   latin="arial", size=16, line=("single",),
                          before=6, after=0, align="center", color=PKU_RED),
    # 场合(学位论文答辩/结题报告…):封面的必需项,不能与副题共用一个槽位
    "cover.occasion":dict(cjk="song",  latin="tnr",   size=14, line=("single",),
                          before=0, after=14, align="center", color=PKU_RED),
    "cover.info":    dict(cjk="fs",    latin="tnr",   size=16, line=("single",),
                          before=0, after=0, align="center", color=BLACK),
    "cover.date":    dict(cjk="song",  latin="tnr",   size=16, line=("single",),
                          before=0, after=0, align="center", color=BLACK),
    # 章级标题:章 / 摘要 / 目录 / 参考文献 / 附录 / 致谢 全部同格式
    "chapter":       dict(cjk="hei",   latin="arial", size=16, line=("single",),
                          before=24, after=18, align="center", bold=True, color=PKU_RED,
                          keep_next=True, page_break=True),
    "sec1":          dict(cjk="hei",   latin="arial", size=14, line=("exact", 20),
                          before=24, after=6, align="left", bold=True, color=PKU_RED,
                          keep_next=True),
    "sec2":          dict(cjk="hei",   latin="arial", size=13, line=("exact", 20),
                          before=12, after=6, align="left", bold=True, color=PKU_RED,
                          keep_next=True),
    "sec3":          dict(cjk="hei",   latin="arial", size=12, line=("exact", 20),
                          before=12, after=6, align="left", bold=True, color=PKU_RED,
                          keep_next=True),
    "body":          dict(cjk="song",  latin="tnr",   size=12, line=("exact", 20),
                          before=0, after=0, align="justify", indent_chars=2, color=BLACK),
    "abs.kw":        dict(cjk="song",  latin="tnr",   size=12, line=("exact", 20),
                          before=12, after=0, align="justify", indent_chars=2, color=BLACK),
    "abs_en.head":   dict(cjk="hei",   latin="arial", size=12, line=("exact", 20),
                          before=8, after=6, align="center", bold=True, color=PKU_RED),
    "fig.caption":   dict(cjk="song",  latin="tnr",   size=11, line=("single",),
                          before=6, after=12, align="center", color=BLACK),
    "fig.image":     dict(cjk="song",  latin="tnr",   size=12, line=("single",),
                          before=6, after=0, align="center", color=BLACK, keep_next=True),
    "tab.caption":   dict(cjk="song",  latin="tnr",   size=11, line=("single",),
                          before=12, after=6, align="center", color=BLACK, keep_next=True),
    "tab.cell":      dict(cjk="song",  latin="tnr",   size=11, line=("single",),
                          before=3, after=3, align="left", color=BLACK),
    "tab.note":      dict(cjk="song",  latin="tnr",   size=10.5, line=("single",),
                          before=6, after=12, align="left", color=BLACK),
    "formula":       dict(cjk="song",  latin="tnr",   size=12, line=("single",),
                          before=6, after=6, align="left", color=BLACK),
    "ref.entry":     dict(cjk="song",  latin="tnr",   size=10.5, line=("exact", 16),
                          before=3, after=0, align="justify", hanging_chars=2, color=BLACK),
    "header":        dict(cjk="song",  latin="tnr",   size=10.5, line=("single",),
                          before=0, after=0, align="center", color=PKU_RED),
    "footer":        dict(cjk="song",  latin="tnr",   size=10.5, line=("single",),
                          before=0, after=0, align="center", color=BLACK),
    "toc.ch":        dict(cjk="hei",   latin="arial", size=12, line=("exact", 20),
                          before=6, after=0, align="left", bold=True, color=BLACK),
    "toc.s1":        dict(cjk="song",  latin="tnr",   size=12, line=("exact", 20),
                          before=0, after=0, align="left", indent_left_chars=1, color=BLACK),
    "toc.s2":        dict(cjk="song",  latin="tnr",   size=12, line=("exact", 20),
                          before=0, after=0, align="left", indent_left_chars=2, color=BLACK),
}

# ---------- 三线表边框(w:sz 单位为 1/8 pt) ----------
TABLE_TOP_SZ = 12      # 1.5 pt
TABLE_BOTTOM_SZ = 12   # 1.5 pt
TABLE_HEAD_SZ = 6      # 0.75 pt 表头下线

# ---------- 图表编号:北大规范用点号(图 2.1),不用连字符 ----------
NUM_SEP = "."
LABEL = {"fig": "图", "tab": "表", "eq": "式"}

# ---------- 中文数字(章号) ----------
CN_NUM = "〇一二三四五六七八九十"


def cn_number(n: int) -> str:
    """1→一,10→十,11→十一,21→二十一(章号够用到 99)。"""
    if n <= 10:
        return CN_NUM[n]
    if n < 20:
        return "十" + CN_NUM[n - 10]
    tens, ones = divmod(n, 10)
    return CN_NUM[tens] + "十" + (CN_NUM[ones] if ones else "")
