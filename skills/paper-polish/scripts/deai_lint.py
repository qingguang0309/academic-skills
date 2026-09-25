#!/usr/bin/env python3
"""deai_lint — 论文 AI 味体检(LaTeX / Markdown / 纯文本,英文正文)。

它不是 AI 检测器:不输出"AI 概率",也不以骗过检测器为目标。它找的是**让文字变差的具体痕迹**
——空洞的高频词、对仗与总结的节拍、没有证据的强断言、生成残留、专业细节缺失——每条诊断都点名
位置、给出证据与修法,由人决定改不改。判据始终是:删掉它或改具体之后,句子丢不丢信息。

    python3 deai_lint.py paper.tex                          # 自动识别领域
    python3 deai_lint.py paper.tex --profile dft-ml         # DFT+ML 期刊论文
    python3 deai_lint.py main.tex --profile agent-conf      # AI agent 会议论文
    python3 deai_lint.py paper.tex --json                   # 机器可读
    python3 deai_lint.py paper.tex --bib refs.bib           # 顺带核对 \\cite 键是否都在 bib 里

诊断分三级:error(生成残留、占位符、引用键缺失——必须处理,退出码 1)、warning(建议改)、
info(提醒作者核对或补充,不一定要改)。有诊断时写 <文件名>.deai.json,清零后自动删除。

词表在 ../data/lexicon.json(数据,补词不改代码)。excess 词族来自 Kobak et al. 2025
(Sci. Adv. 11:eadt3813;数据 MIT 许可):PubMed 摘要中 2024 年相对 2021–22 外推值的超额比例。
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_lexicon():
    for c in (os.path.join(HERE, "..", "data", "lexicon.json"), os.path.join(HERE, "data", "lexicon.json"),
              os.path.join(HERE, "lexicon.json"), os.path.join(os.getcwd(), "lexicon.json")):
        if os.path.exists(c):
            return os.path.abspath(c)
    sys.exit("[deai_lint] 找不到 data/lexicon.json(脚本复制出去时把它放在同一目录)")


# ------------------------------------------------------------------ 诊断

SEV_RANK = {"error": 0, "warning": 1, "info": 2}
REPAIR_ORDER = ["residue/", "cite/", "claim/", "spec/", "phrase/", "vocab/", "hedge/", "struct/"]
REPAIR_RULES = ("按顺序处理:先删生成残留与占位符,再核对断言与证据,再补专业细节,最后才动词汇和节奏。"
                "只改诊断点名的句子;不许新增数据、文献、实验细节——缺的用 [请确认: …] 留给作者。"
                "连续两轮告警数没有下降就停下,如实报告剩下的诊断。")


class Issue(dict):
    def __init__(self, code, message, line=None, section=None, text=None, evidence=None, fixes=(),
                 severity="warning"):
        super().__init__(code=code, severity=severity, message=message, line=line, section=section,
                         text=text, evidence=evidence or {}, fixes=list(fixes))

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as exc:
            raise AttributeError(k) from exc


def _order(i):
    rank = next((n for n, p in enumerate(REPAIR_ORDER) if i["code"].startswith(p)), len(REPAIR_ORDER))
    return (SEV_RANK[i["severity"]], rank, i["line"] or 0)


# ------------------------------------------------------------------ 读入与遮蔽
# 遮蔽 = 把非正文(公式、命令、引用、注释、导言区……)替换成等长空白,位置与行号不变。

MATH_ENVS = r"equation|align|gather|multline|eqnarray|displaymath|math|flalign|alignat"
SKIP_ENVS = (r"tabular|tabularx|longtable|lstlisting|verbatim|minted|algorithmic|algorithm2e|tikzpicture|"
             r"thebibliography|filecontents|comment|lstinline")
ARG_DROP = (r"part|chapter|section|subsection|subsubsection|paragraph|title|author|date|label|ref|cref|Cref|autoref|eqref|pageref|cite|citep|citet|citeauthor|citeyear|nocite|url|"
            r"includegraphics|input|include|usepackage|documentclass|bibliography|bibliographystyle|"
            r"newcommand|renewcommand|def|setlength|hypersetup|graphicspath|vspace|hspace|begin|end|"
            r"small|footnotesize|centering|todo|color|textcolor|definecolor|affil|email|thanks|orcid|"
            r"cellcolor|rowcolor|multicolumn|multirow|resizebox|scalebox|SI|si|num|unit|qty|ce|pu")
SECTION_CMD = re.compile(r"\\(part|chapter|section|subsection|subsubsection|paragraph)\*?\s*(?:\[[^\]]*\])?\s*\{")
ABBREV = re.compile(r"\b(?:e\.g|i\.e|et al|Fig|Figs|Eq|Eqs|Ref|Refs|Sec|Tab|vs|ca|approx|cf|resp|No|Dr|Prof|etc|Suppl|Ext|Mr|Ms|St)\.$", re.I)


def _blank(s):
    return re.sub(r"[^\n]", " ", s)


def _mask_span(chars, a, b, token=""):
    seg = "".join(chars[a:b])
    rep = _blank(seg)
    if token and len(rep) >= len(token) and "\n" not in seg[:len(token)]:
        rep = token + rep[len(token):]
    chars[a:b] = list(rep)


def _match_brace(s, i):
    """s[i] == '{',返回配对 '}' 的下标(找不到返回 len-1)。"""
    depth = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == "\\":
            continue
        if c == "{" and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif c == "}" and (j == 0 or s[j - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return j
    return len(s) - 1


def mask_tex(src):
    chars = list(src)
    s = src
    # 注释
    for m in re.finditer(r"(?<!\\)%[^\n]*", s):
        _mask_span(chars, m.start(), m.end())
    s = "".join(chars)
    # 导言区与参考文献之后
    m = re.search(r"\\begin\{document\}", s)
    if m:
        _mask_span(chars, 0, m.end())
    m = re.search(r"\\end\{document\}", s)
    if m:
        _mask_span(chars, m.start(), len(s))
    s = "".join(chars)
    # 整段跳过的环境(表格、代码、算法、参考文献……)
    for m in re.finditer(r"\\begin\{(" + SKIP_ENVS + r")\*?\}.*?\\end\{\1\*?\}", s, re.S):
        _mask_span(chars, m.start(), m.end())
    # 陈列公式环境
    for m in re.finditer(r"\\begin\{(" + MATH_ENVS + r")\*?\}.*?\\end\{\1\*?\}", s, re.S):
        _mask_span(chars, m.start(), m.end(), "M")
    s = "".join(chars)
    for pat in (r"\$\$.*?\$\$", r"\\\[.*?\\\]", r"\\\(.*?\\\)", r"(?<!\\)\$(?:\\.|[^$\\])+?\$"):
        for m in re.finditer(pat, s, re.S):
            _mask_span(chars, m.start(), m.end(), "M")
        s = "".join(chars)
    # figure/table:只留 \caption{} 文字
    for m in re.finditer(r"\\begin\{(figure|table|wrapfigure|figure\*|table\*)\}(.*?)\\end\{\1\}", s, re.S):
        body_a = m.start(2)
        body = m.group(2)
        keep = []
        for c in re.finditer(r"\\caption(?:\[[^\]]*\])?\{", body):
            b = _match_brace(body, c.end() - 1)
            keep.append((body_a + c.end(), body_a + b))
        cur = m.start()
        for ka, kb in keep:
            _mask_span(chars, cur, ka)
            cur = kb
        _mask_span(chars, cur, m.end())
    s = "".join(chars)
    # 带参数但参数不是正文的命令:连参数一起遮
    for m in re.finditer(r"\\(" + ARG_DROP + r")\*?(?![a-zA-Z])", s):
        a, j = m.start(), m.end()
        name = m.group(1)
        while j < len(s) and s[j] in " \t":
            j += 1
        while j < len(s) and s[j] == "[":
            k = s.find("]", j)
            j = (k + 1) if k > 0 else j + 1
        nargs = 2 if name in ("newcommand", "renewcommand", "textcolor", "definecolor", "multicolumn",
                              "multirow", "resizebox", "scalebox", "qty") else 1
        if name in ("begin", "end", "small", "footnotesize", "centering"):
            nargs = 1 if name in ("begin", "end") else 0
        for _ in range(nargs):
            while j < len(s) and s[j] in " \t":
                j += 1
            if j < len(s) and s[j] == "{":
                j = _match_brace(s, j) + 1
        token = "[C]" if name.startswith("cite") else ("[R]" if "ref" in name else "")
        if name in ("SI", "si", "num", "qty", "unit", "ce", "pu"):
            token = "9"
        _mask_span(chars, a, j, token)
    s = "".join(chars)
    # 其余命令名、花括号、~
    for m in re.finditer(r"\\[a-zA-Z@]+\*?(?:\[[^\]\n]{0,80}\])?|\\[^a-zA-Z\s]|[{}]", s):
        tok = m.group(0)
        if tok in ("\\%", "\\&", "\\_", "\\#", "\\$"):
            chars[m.start():m.end()] = list(" " + tok[1])
            continue
        _mask_span(chars, m.start(), m.end())
    s = "".join(chars).replace("~", " ")
    return s


def mask_md(src):
    chars = list(src)
    for pat in (r"```.*?```", r"`[^`\n]+`", r"<!--.*?-->", r"\$\$.*?\$\$", r"(?<!\\)\$[^$\n]+?\$"):
        for m in re.finditer(pat, "".join(chars), re.S):
            _mask_span(chars, m.start(), m.end(), "M" if "$" in pat else "")
    s = "".join(chars)
    for m in re.finditer(r"\]\([^)]+\)", s):
        _mask_span(chars, m.start(), m.end())
    for m in re.finditer(r"\[@[^\]]+\]", "".join(chars)):
        _mask_span(chars, m.start(), m.end(), "[C]")
    return "".join(chars)


def expand_inputs(path, src, depth=0):
    """把 \\input{} / \\include{} 的子文件就地展开(多文件论文);找不到的保持原样。"""
    if depth > 5:
        return src
    base = os.path.dirname(os.path.abspath(path))

    def sub(m):
        if re.search(r"(?<!\\)%[^\n]*$", src[src.rfind("\n", 0, m.start()) + 1:m.start()]):
            return m.group(0)                      # 被注释掉的 \input
        name = m.group(2).strip()
        for cand in (name, name + ".tex"):
            f = os.path.join(base, cand)
            if os.path.isfile(f):
                inner = open(f, encoding="utf-8", errors="replace").read()
                return expand_inputs(f, inner, depth + 1)
        return m.group(0)
    return re.sub(r"\\(input|include)\s*\{([^}]+)\}", sub, src)


class Doc:
    def __init__(self, path, text=None):
        self.path = path
        self.src = text if text is not None else open(path, encoding="utf-8", errors="replace").read()
        if text is None and os.path.splitext(path)[1].lower() in (".tex", ".ltx"):
            self.src = expand_inputs(path, self.src)
        ext = os.path.splitext(path)[1].lower()
        self.kind = "tex" if ext in (".tex", ".ltx") or "\\begin{" in self.src[:5000] else (
            "md" if ext in (".md", ".markdown", ".qmd", ".rmd") else "txt")
        self.masked = mask_tex(self.src) if self.kind == "tex" else (mask_md(self.src) if self.kind == "md" else self.src)
        self.nl = [i for i, c in enumerate(self.src) if c == "\n"]
        self.sections = self._sections()
        self.paragraphs = self._paragraphs()

    def line(self, pos):
        return bisect.bisect_right(self.nl, pos - 1) + 1

    def _sections(self):
        out = [(0, "(前言)")]
        if self.kind == "tex":
            for m in SECTION_CMD.finditer(self.src):
                b = _match_brace(self.src, m.end() - 1)
                title = re.sub(r"\s+", " ", self.src[m.end():b]).strip()
                out.append((m.start(), title))
            for m in re.finditer(r"\\begin\{abstract\}", self.src):
                out.append((m.start(), "Abstract"))
            for m in re.finditer(r"\\end\{abstract\}", self.src):
                out.append((m.end(), "(摘要后)"))
        else:
            for m in re.finditer(r"(?m)^#{1,4}\s+(.+)$", self.src):
                out.append((m.start(), m.group(1).strip()))
            m = re.search(r"(?im)^\s*abstract\s*[:.]?\s*$", self.src)
            if m:
                out.append((m.start(), "Abstract"))
        return sorted(out)

    def section_at(self, pos):
        i = bisect.bisect_right([p for p, _ in self.sections], pos) - 1
        return self.sections[max(i, 0)][1]

    def _paragraphs(self):
        paras = []
        for m in re.finditer(r"(?:[^\n]*\S[^\n]*(?:\n|$))+", self.masked):
            text = m.group(0)
            if len(re.findall(r"[A-Za-z]{2,}", text)) < 8:
                continue
            paras.append(Para(self, m.start(), m.end()))
        return paras


SENT_SPLIT = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[\[(\"'A-Z0-9M])")


class Para:
    def __init__(self, doc, a, b):
        self.doc, self.a, self.b = doc, a, b
        self.text = doc.masked[a:b]
        self.raw = doc.src[a:b]
        self.section = doc.section_at(a)
        self.sentences = self._split()
        self.words = len(re.findall(r"[A-Za-z][A-Za-z'-]*", self.text))

    def _split(self):
        out, start = [], 0
        for m in SENT_SPLIT.finditer(self.text):
            head = self.text[start:m.start() + 1].rstrip()
            if ABBREV.search(head) or re.search(r"\b[A-Z]\.$", head) or re.search(r"\d\.$", head) and \
                    re.match(r"\d", self.text[m.end():m.end() + 1] or ""):
                continue
            out.append((start, m.start() + 1))
            start = m.end()
        if self.text[start:].strip():
            out.append((start, len(self.text.rstrip())))
        return [(self.a + x, self.a + y) for x, y in out if re.search(r"[A-Za-z]{2,}", self.text[x:y])]

    def sent_text(self, a, b, raw=False):
        return (self.doc.src if raw else self.doc.masked)[a:b]


# ------------------------------------------------------------------ 检查

def _snip(s, n=110):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def _wl_mask(text, whitelist):
    low = text.lower()
    for w in whitelist:
        low = re.sub(r"\b" + re.escape(w.lower()) + r"\b", lambda m: " " * len(m.group(0)), low)
    return low


class Linter:
    def __init__(self, doc, lex, profile):
        self.doc, self.lex, self.profile = doc, lex, profile
        self.issues = []
        self.forms = {}
        for fam in lex["excess"]:
            for f in fam["forms"]:
                self.forms[f] = fam
        self.word_re = re.compile(r"\b(" + "|".join(sorted(self.forms, key=len, reverse=True)) + r")\b", re.I)
        self.stats = defaultdict(lambda: {"words": 0, "markers": 0, "excess": 0})
        self._dens, self._closers, self._triads = [], [], []   # 需要跨段统计后才决定报不报
        self._dashes, self._words = 0, 0

    def add(self, *a, **k):
        issue = Issue(*a, **k)
        if issue["code"].startswith("spec/") and self._pending(issue["code"]):
            issue["message"] += "(已用 [请确认] 留给作者)"
            issue["severity"] = "info"
        self.issues.append(issue)

    def run(self):
        for p in self.doc.paragraphs:
            self.stats[p.section]["words"] += p.words
            self.residue(p)
            self.vocab(p)
            self.phrases(p)
            self.claims(p)
            self.structure(p)
        self.doc_level()
        self.residue_raw()
        if self.profile == "dft-ml":
            self.profile_dft_ml()
        elif self.profile == "agent-conf":
            self.profile_agent()
        self.issues = self._aggregate(self.issues)
        self.issues.sort(key=_order)
        return self.issues

    AGGREGATE = ("claim/significance", "claim/unsupported", "struct/para-openers", "struct/uniform-length")

    def _aggregate(self, issues):
        """info 级、同一代码超过 3 条的合并成一条(附行号清单),避免淹没真正要改的地方。"""
        out, groups = [], defaultdict(list)
        for i in issues:
            (groups[i["code"]] if i["code"] in self.AGGREGATE and i["severity"] == "info" else out).append(i)
        for code, items in groups.items():
            if len(items) <= 3:
                out += items
                continue
            first = items[0]
            out.append(Issue(code, f"{first['message'].split(',')[0].split('(')[0]}——全文 {len(items)} 处",
                             line=first["line"], section=first["section"], text=first["text"],
                             evidence={"lines": [i["line"] for i in items]}, fixes=first["fixes"], severity="info"))
        return out

    # -- 生成残留:在未遮蔽的原文上查(Markdown 标记只在 tex 里算错)
    def residue(self, p):
        for it in self.lex["residue"]:
            if it.get("tex_only"):
                continue
            last = -999
            for m in re.finditer(it["re"], p.text, re.I):
                if m.start() - last < 80:          # 同一句里的多个残留片段只报一次
                    continue
                last = m.start()
                pos = p.a + m.start()
                code = "placeholder" if "占位" in it["why"] else ("prompt-injection" if "注入" in it["why"] else "chat")
                self.add("residue/" + code, it["why"],
                         line=self.doc.line(pos), section=p.section, text=_snip(m.group(0)),
                         fixes=[it["fix"]], severity="error")

    def residue_raw(self):
        for it in self.lex["residue"]:
            if not it.get("tex_only") or self.doc.kind != "tex":
                continue
            prose = self.doc.masked
            for m in re.finditer(it["re"], self.doc.src):
                if not prose[m.start():m.end()].strip():
                    continue
                self.add("residue/markdown", it["why"], line=self.doc.line(m.start()),
                         section=self.doc.section_at(m.start()), text=_snip(m.group(0)),
                         fixes=[it["fix"]], severity="error")
        for m in re.finditer(r"\\(?:textcolor|color)\{white\}|\\fontsize\{0?\.?[0-2](?:pt)?\}|\\tiny\s*\\color", self.doc.src):
            self.add("residue/hidden-text", "白色或极小字号的隐藏文字——审稿系统会当作提示注入处理", line=self.doc.line(m.start()),
                     text=_snip(self.doc.src[m.start():m.start() + 80]), severity="error",
                     fixes=["删除隐藏文字;ICLR / ICML 2026 对提示注入直接拒稿"])
        for m in re.finditer(r"oaicite|turn\d+search\d+|contentReference\[", self.doc.src):
            if self.doc.masked[m.start():m.end()].strip():
                continue          # 已在正文检查里报过
            self.add("residue/chat", "生成工具泄漏的引用标记(在命令或注释里)", line=self.doc.line(m.start()),
                     text=_snip(self.doc.src[m.start():m.start() + 60]), severity="error",
                     fixes=["换成真实 \\cite{} 并核对文献"])

    # -- 超额词
    def vocab(self, p):
        low = _wl_mask(p.text, self.lex["whitelist"])
        hits = [(m.start(), m.group(1).lower()) for m in self.word_re.finditer(low)]
        dens = []
        for pos, w in hits:
            fam = self.forms[w]
            self.stats[p.section]["excess"] += 1
            if fam["tier"] == "marker":
                self.stats[p.section]["markers"] += 1
                self.add("vocab/marker", f"LLM 高频词「{w}」(PubMed 摘要 2024 年超额 ×{fam['ratio'] or '—'})",
                         line=self.doc.line(p.a + pos), section=p.section,
                         text=_snip(p.text[max(0, pos - 50):pos + 60]),
                         evidence={"lemma": fam["lemma"], "ratio": fam["ratio"]},
                         fixes=["删掉后句子不丢信息就删", "换成具体动作或数字:show / find / 12% lower",
                                "确属术语(如 surpass 基线)可保留"])
            else:
                dens.append((pos, w))
        if len(dens) >= 2:
            words = [w for _, w in dens]
            self.add("vocab/density", f"本段 LLM 超额词偏多({len(words)} 个): {', '.join(sorted(set(words)))}",
                     line=self.doc.line(p.a + dens[0][0]), section=p.section, text=_snip(p.text[:110]),
                     evidence={"count": len(words), "words_in_para": p.words},
                     fixes=["每个词问一次:删掉它丢不丢信息", "保留真正需要的一两个,其余换成具体说法"])

    # -- 短语模式
    def phrases(self, p):
        low = _wl_mask(p.text, self.lex["whitelist"])
        dens = []
        for it in self.lex["phrases"]:
            last = -999
            for m in re.finditer(it["re"], low, re.I):
                if m.start() - last < 40:          # 同一模式的相邻匹配(如 in today's rapidly evolving)只报一次
                    continue
                last = m.start()
                pos = p.a + m.start()
                if it["tier"] == "marker":
                    self.add("phrase/cliche", it["why"], line=self.doc.line(pos), section=p.section,
                             text=_snip(p.text[m.start():m.end() + 40]), fixes=[it["fix"]])
                else:
                    dens.append((it, pos, m))
        hs = self.lex["hedge_stack"]
        for m in re.finditer(hs["re"], low, re.I):
            self.add("hedge/stacked", hs["why"], line=self.doc.line(p.a + m.start()), section=p.section,
                     text=_snip(p.text[m.start():m.end() + 30]), fixes=[hs["fix"]])
        self._dens.extend((p, it, pos, m) for it, pos, m in dens)

    # -- 断言与证据
    def claims(self, p):
        c = self.lex["claims"]
        for a, b in p.sentences:
            s = p.sent_text(a, b)
            raw = p.sent_text(a, b, raw=True)
            has_ev = re.search(c["evidence"], raw, re.I) is not None
            sec = p.section.lower()
            hm = re.search(c["hype"], s, re.I)
            negated = hm and re.search(r"(?:\bnot|n't|\bno|\bnever)\b(?:\W+\w+){0,2}\W*$", s[:hm.start()], re.I)
            if hm and not has_ev and not negated:
                w = hm.group(0)
                self.add("claim/hype", f"「{w}」没有数字、图表或文献支撑", line=self.doc.line(a),
                         section=p.section, text=_snip(s),
                         fixes=["换成可核对的比较:数值 + 基准 + 条件", "没有证据就删掉形容词"])
            if re.search(c["significance"], s, re.I) and not re.search(c["stats"], raw, re.I) \
                    and not re.search(r"statistic", s, re.I):
                self.add("claim/significance", "用了 significant(ly),但本句没有统计检验、误差或置信区间",
                         line=self.doc.line(a), section=p.section, text=_snip(s), severity="info",
                         fixes=["做过检验就补 p 值或 CI;没做就改 substantially / markedly,或直接给数值差"])
            if re.search(c["strong_verbs"], s, re.I) and not has_ev and "method" not in sec:
                v = re.search(c["strong_verbs"], s, re.I).group(0)
                self.add("claim/unsupported", f"强断言动词「{v}」所在句没有指向证据(图、表、数字或文献)",
                         line=self.doc.line(a), section=p.section, text=_snip(s), severity="info",
                         fixes=["补证据指针:(Fig. 3b) / (Table 2) / \\cite{…}",
                                "间接证据降级为 suggest / indicate / is consistent with"])

    # -- 结构节拍
    def structure(self, p):
        sents = [p.sent_text(a, b) for a, b in p.sentences]
        lens = [len(re.findall(r"[A-Za-z][A-Za-z'-]*|M|\d+(?:\.\d+)?", s)) for s in sents]
        lens = [n for n in lens if n >= 3]
        if len(lens) >= 5:
            mean = statistics.mean(lens)
            cv = statistics.pstdev(lens) / mean if mean else 0
            if cv < 0.15 and mean > 16 and len(lens) >= 6:
                self.add("struct/uniform-length", f"本段 {len(lens)} 句长度过于均匀(平均 {mean:.0f} 词,变异系数 {cv:.2f})",
                         line=self.doc.line(p.a), section=p.section, text=_snip(sents[0]),
                         evidence={"lengths": lens, "cv": round(cv, 2)}, severity="info",
                         fixes=["把一个长复合句拆成一短一长", "删掉只起过渡作用的从句"])
        trans = [s for s in sents if re.match(r"\s*(?:Furthermore|Moreover|Additionally|In addition|Besides|Also),", s)]
        if len(trans) >= 2:
            self.add("struct/transitions", f"本段 {len(trans)} 句以递进词开头(Furthermore/Moreover/Additionally…)",
                     line=self.doc.line(p.a), section=p.section, text=_snip(trans[1]),
                     fixes=["保留逻辑真正需要的一处,其余直接删掉递进词"])
        firsts = [re.match(r"\s*(\w+)", s).group(1).lower() for s in sents if re.match(r"\s*\w", s)]
        raw_firsts = {re.match(r"\s*(\w+)", s).group(1) for s in sents if re.match(r"\s*\w", s)}
        proper = {w.lower() for w in raw_firsts if re.search(r"[A-Z].*[A-Z]|\d", w)}   # MoleculeNet、GPT4 这类专名
        rep = [w for w, n in Counter(firsts).items() if n >= 3 and w not in proper and w not in (
            "the", "we", "m", "this", "in", "table", "figure", "fig", "thanks", "eq", "for")]
        if rep:
            self.add("struct/openers", f"本段多句以同一个词开头: {', '.join(rep)}", line=self.doc.line(p.a),
                     section=p.section, text=_snip(p.text[:110]), fixes=["调整语序或合并句子"])
        if len(sents) >= 3 and re.match(r"\s*(?:Overall|In summary|In conclusion|Taken together|Collectively|"
                                        r"In essence|Ultimately|Thus|Therefore|Together),", sents[-1]):
            self._closers.append((p, sents[-1]))
        for m in re.finditer(r"\b(\w+(?:ly)?), (\w+(?:ly)?),? and (\w+(?:ly)?) (?=[a-z])", p.text):
            words = m.groups()
            if all(re.search(r"(?:ive|al|ous|ful|ble|ent|ant|ic|ing|ly)$", w) for w in words):
                self._triads.append((p, m))
        dash = len(re.findall(r"—|(?<!-)---(?!-)", p.raw))
        self._dashes += dash
        self._words += p.words

    def doc_level(self):
        # 段尾总结句:跨段统计才有意义
        if len(self._closers) >= 3:
            for p, s in self._closers:
                self.add("struct/summary-closer", "段尾又用总结句收束(全文已有 %d 处)" % len(self._closers),
                         line=self.doc.line(p.b - len(s)), section=p.section, text=_snip(s),
                         fixes=["删掉复述性的收尾;段落靠推进,不靠自我总结"])
        if len(self._triads) >= 3:
            for p, m in self._triads:
                self.add("struct/triad", "形容词三连(X, Y, and Z)偏多", line=self.doc.line(p.a + m.start()),
                         section=p.section, text=_snip(m.group(0)), severity="info",
                         fixes=["真有三点就留;为对称凑出来的那一项删掉"])
        per_k = 1000 * self._dashes / max(self._words, 1)
        if self._dashes >= 4 and per_k > 3:
            self.add("struct/em-dash", f"破折号偏多:全文 {self._dashes} 处(每千词 {per_k:.1f})",
                     evidence={"count": self._dashes, "per_1000_words": round(per_k, 1)}, severity="info",
                     fixes=["插入语改成逗号或括号,或拆成两句;保留确实需要停顿的少数几处"])
        # 密度档短语:同段 >=2 或全文 >=3 才报
        by_label = defaultdict(list)
        for p, it, pos, m in self._dens:
            by_label[it["why"]].append((p, it, pos, m))
        for why, hits in by_label.items():
            paras = Counter(id(h[0]) for h in hits)
            rate = 1000 * len(hits) / max(self._words, 1)
            if max(paras.values()) >= 2 or (len(hits) >= 3 and rate > 1.5):
                for p, it, pos, m in hits:
                    self.add("phrase/pattern", f"{why}(全文 {len(hits)} 处)", line=self.doc.line(pos),
                             section=p.section, text=_snip(p.text[m.start():m.end() + 40]),
                             fixes=[it["fix"]])
        # 开头雷同:连续段落同一开头词组
        heads = [" ".join(re.findall(r"[A-Za-z]+", p.text)[:2]).lower() for p in self.doc.paragraphs]
        for k in range(2, len(heads)):
            if heads[k] and heads[k] == heads[k - 1] == heads[k - 2] and (k + 1 == len(heads) or heads[k + 1] != heads[k]):
                p = self.doc.paragraphs[k]
                self.add("struct/para-openers", f"连续几段都以「{heads[k]}」开头", line=self.doc.line(p.a),
                         section=p.section, text=_snip(p.text[:80]), severity="info",
                         fixes=["换一个开头:从本段的具体对象或结果说起"])
        # 全文超额词率
        tot_w = sum(v["words"] for v in self.stats.values())
        tot_e = sum(v["excess"] for v in self.stats.values())
        if tot_w >= 300 and 1000 * tot_e / tot_w >= 6:
            self.add("vocab/rate", f"LLM 超额词每千词 {1000 * tot_e / tot_w:.1f} 个",
                     evidence={"per_1000_words": round(1000 * tot_e / tot_w, 1)}, severity="info",
                     fixes=["优先处理摘要与引言——超额词最集中的地方"])

    # ---------------------------------------------------------------- 领域:DFT + ML
    def _has(self, rx):
        # [请确认: …] 里的文字是待补清单,不算已经写了
        src = getattr(self, "_src_nc", None)
        if src is None:
            src = self._src_nc = re.sub(r"\[(?:请确认|待确认|CONFIRM)[:：]?[^\]]*\]", " ", self.doc.src, flags=re.I)
        return re.search(rx, src, re.I | re.S) is not None

    def _first(self, rx):
        m = re.search(rx, self.doc.masked, re.I)
        return (self.doc.line(m.start()), _snip(self.doc.masked[m.start():m.start() + 100])) if m else (None, None)

    # 作者待补的占位符里提到了这一项,就降级为 info:问题已经交给作者,不再算改写没做完
    PENDING = {"spec/dft-functional": r"泛函|functional", "spec/hubbard-u": r"U_?eff|U 值|\bU\b",
               "spec/cutoff": r"截断能|cut-?off", "spec/k-points": r"k 点|k-?point",
               "spec/convergence": r"收敛|converg", "spec/dataset-size": r"数据量|dataset|数据集",
               "spec/split": r"划分|split", "spec/metric": r"MAE|RMSE|误差", "spec/metric-unit": r"MAE|RMSE|误差",
               "spec/baseline": r"基线|baseline|比较", "spec/generalization": r"分布外|OOD|out-of-distribution",
               "spec/interpretability": r"解释|SHAP|interpret",
               "spec/variance": r"种子|seed|标准差|std|方差|variance|重复", "spec/model-version": r"快照|snapshot|temperature|版本|version",
               "spec/limitations": r"局限|limitation|失败|failure"}

    def _pending(self, code):
        rx = self.PENDING.get(code)
        return bool(rx) and any(re.search(rx, m.group(0), re.I) for m in re.finditer(
            r"\[(?:请确认|待确认|CONFIRM)[:：]?[^\]]*\]", self.doc.masked, re.I))

    def profile_dft_ml(self):
        def spec(code, msg, rx_for_line, fixes, sev="warning"):
            line, text = self._first(rx_for_line)
            self.add(code, msg, line=line, section="全文", text=text, fixes=fixes, severity=sev)
        dft = r"\bDFT\b|density[- ]functional|\bVASP\b|Quantum ESPRESSO|\bCP2K\b|\bGPAW\b|\bCASTEP\b|\bGaussian\b|\bORCA\b"
        if self._has(dft):
            if not self._has(r"\b(?:PBE(?:sol)?|PW91|RPBE|revPBE|LDA|GGA|r?2?SCAN|HSE0?6|B3LYP|PBE0|M06|ωB97|wB97|optB86b|optB88|vdW-DF\d?|BEEF)\b"):
                spec("spec/dft-functional", "提到了 DFT,但没写交换关联泛函(PBE/SCAN/HSE06…)", dft,
                     ["在方法里写明泛函与色散校正(如 PBE+D3(BJ));不知道就留 [请确认: 泛函]"])
            if self._has(r"DFT\s*\+\s*U|\+U\b|Hubbard") and not self._has(r"U(?:_\{?eff\}?)?\s*=\s*\d|U\s*values?\s+of\s+\d|\d(?:\.\d+)?\s*eV\s+for\s+(?:the\s+)?[A-Z][a-z]?\b"):
                spec("spec/hubbard-u", "用了 +U,但没有给出各元素的 U 值", r"\+U|Hubbard",
                     ["逐元素给 U_eff(如 Co 3.3 eV),并注明来源"])
            if self._has(r"\bVASP\b|plane[- ]wave|PAW|Quantum ESPRESSO"):
                if not self._has(r"cut-?off|ENCUT|kinetic energy"):
                    spec("spec/cutoff", "平面波计算没写截断能", r"plane[- ]wave|VASP",
                         ["写明截断能(如 520 eV)"])
                if not self._has(r"k-?point|Monkhorst|Γ-centered|Gamma-centered|\\Gamma"):
                    spec("spec/k-points", "没写 k 点网格或 k 点密度", r"plane[- ]wave|VASP",
                         ["写明 k 点网格(如 4×4×1 Γ-centered)或 k 点密度"])
                if not self._has(r"converge|convergence|10\^?\{?-\d|1e-\d|eV\s*/\s*Å|eV/A|eV Å"):
                    spec("spec/convergence", "没写电子步与离子步的收敛判据", r"plane[- ]wave|VASP",
                         ["写明收敛判据(如 10⁻⁵ eV,0.02 eV/Å)"], "info")
        ml = r"machine[- ]learn|neural network|graph neural|\bGNN\b|random forest|gradient boost|XGBoost|kernel ridge|Gaussian process|\bMLIP\b|interatomic potential|surrogate model|descriptor"
        if self._has(ml):
            if not self._has(r"\b\d[\d,]*\s+(?:structures|configurations|samples|data ?points|entries|compounds|materials|frames|molecules)\b"):
                spec("spec/dataset-size", "用了机器学习,但没写数据集规模", ml,
                     ["写明数据量与来源(如 12 480 structures from Materials Project v2023.11)"])
            if not self._has(r"\btrain(?:ing)?\b.{0,80}\b(?:test|validation)\b|\bsplit\b|cross[- ]validation|k-fold|held[- ]out"):
                spec("spec/split", "没写训练/验证/测试划分方式", ml,
                     ["写明划分比例与方式(随机 / 按成分 / 按结构原型),以及是否有泄漏控制"])
            if not self._has(r"\b(?:MAE|RMSE|MSE|R\^?\{?2\}?|R²|Spearman|Pearson|AUC|F1)\b"):
                spec("spec/metric", "没有报告误差指标(MAE/RMSE/R²…)", ml,
                     ["给出测试集指标及单位(如 MAE = 0.041 eV/atom)"])
            elif not self._has(r"(?:MAE|RMSE)[^.]{0,60}\d[^.]{0,20}(?:m?eV|eV/atom|meV/atom|eV/Å|kcal|kJ|GPa|%)"):
                spec("spec/metric-unit", "误差指标没带单位", r"MAE|RMSE", ["写成 MAE = 0.041 eV/atom 这样带单位的形式"], "info")
            if not self._has(r"baseline|compared (?:with|to)|benchmark(?:ed)? against|versus|\bvs\.?\b"):
                spec("spec/baseline", "没有和基线模型或已有方法比较", ml,
                     ["加一个基线(线性模型、已发表模型或 DFT 本身),否则“准确”无从判断"])
            # 只认"做过 OOD 测试"的方法性表述;正文里说一句 unseen 不算
            if self._has(r"\bgenerali[sz](?:e|es|ing)\s+(?:well|to|across|beyond)|generali[sz]ab|"
                         r"generali[sz]ation (?:ability|performance|capabilit|to)") and not self._has(
                    r"out[- ]of[- ]distribution|\bOOD\b|held[- ]out (?:set|chemistr|composition|famil|element)|"
                    r"leave-one-(?:cluster|group|element|family)-out|(?:cluster|composition|scaffold|prototype|temporal|time)[- ](?:based )?split"):
                spec("spec/generalization", "声称可泛化,但没有分布外(OOD)测试", r"generali[sz](?:e|es|ing|ab|ation)",
                     ["补 OOD / 按化学体系留出的测试,或把措辞改成“在测试集上”"])
            if self._has(r"interpretab|explainab|physical insight") and not self._has(r"SHAP|feature importance|attribution|sensitivity analysis|permutation|symbolic regression|SISSO"):
                spec("spec/interpretability", "声称可解释 / 给出物理洞见,但没有对应的分析方法", r"interpretab|explainab|physical insight",
                     ["写明解释方法(SHAP、置换重要性、SISSO…)与得到的具体结论"], "info")
        for m in re.finditer(r"\b(?:DFT|chemical|quantum|near[- ]DFT)[- ]level accuracy\b|\bchemical accuracy\b|\bhigh(?:ly)? accura(?:te|cy)\b", self.doc.masked, re.I):
            p = self._para_at(m.start())
            sent = self._sentence_at(p, m.start()) if p else ""
            if not re.search(r"\d", sent):
                self.add("claim/accuracy", "“精度高 / DFT 级精度”没有给数值", line=self.doc.line(m.start()),
                         section=self.doc.section_at(m.start()), text=_snip(sent or m.group(0)),
                         fixes=["给出误差与参照:MAE = 0.03 eV/atom vs. DFT (PBE)"])

    # ---------------------------------------------------------------- 领域:AI agent 会议论文
    def profile_agent(self):
        for m in re.finditer(r"\b(?:the |our |an? )?(?:agent|model|LLM|system|policy)s? (?:truly |really |deeply )?"
                             r"(?:understands?|thinks?|knows?|believes?|realizes?|wants?|feels?|is aware|comprehends?|"
                             r"intends?|desires?)\b", self.doc.masked, re.I):
            self.add("claim/anthropomorphism", f"拟人化表述「{_snip(m.group(0), 40)}」", line=self.doc.line(m.start()),
                     section=self.doc.section_at(m.start()), text=_snip(self._sentence_at(self._para_at(m.start()), m.start())),
                     fixes=["改成可观测行为:the agent selects / predicts / outputs / is conditioned on",
                            "确要讨论内部状态,用 represents / encodes 并给证据"])
        for m in re.finditer(r"\b(?:human[- ]level|super[- ]?human|AGI|artificial general intelligence|fully autonomous|"
                             r"general[- ]purpose agent|solves? (?:the )?(?:problem|task) completely)\b", self.doc.masked, re.I):
            p = self._para_at(m.start())
            s = self._sentence_at(p, m.start()) if p else m.group(0)
            if not re.search(r"\d|\[C\]|\[R\]", s):
                self.add("claim/hype", f"「{m.group(0)}」这类断言需要基准数字支撑", line=self.doc.line(m.start()),
                         section=self.doc.section_at(m.start()), text=_snip(s),
                         fixes=["限定到实际评测:on WebArena (812 tasks) the agent reaches 41.2% success"])
        novel = [m for m in re.finditer(r"\bnovel\b", self.doc.masked, re.I)]
        if len(novel) >= 3:
            self.add("phrase/novel", f"“novel”出现 {len(novel)} 次", line=self.doc.line(novel[0].start()),
                     evidence={"count": len(novel)},
                     fixes=["新不新由审稿人判断;说清和最接近的已有工作差在哪一点即可"])
        for m in re.finditer(r"\b(?:we are|this is) the first\b|\bfirst (?:work|study|paper|framework|method) to\b", self.doc.masked, re.I):
            s = self._sentence_at(self._para_at(m.start()), m.start())
            if not re.search(r"to (?:the best of )?our knowledge", s, re.I):
                self.add("claim/priority", "“首个”断言没有限定", line=self.doc.line(m.start()),
                         section=self.doc.section_at(m.start()), text=_snip(s),
                         fixes=["加 to our knowledge 并写清检索范围,或删掉"])
        if self._has(r"outperform|state-of-the-art|\bSOTA\b|surpass") and not self._has(
                r"±|\\pm|std|standard deviation|standard error|confidence interval|\bseeds?\b|\bruns\b|\btrials\b|bootstrap"):
            self.add("spec/variance", "报告了超过基线的结果,但全文没有方差、随机种子或重复次数",
                     line=self._first(r"outperform|state-of-the-art|surpass")[0],
                     fixes=["写明重复次数与种子,报告均值 ± 标准差或置信区间(NeurIPS checklist 的统计显著性一项)"])
        if not self._has(r"\\section\*?\{[^}]*limitation|^#+\s*limitation|\blimitations?\b[^.]{0,40}(?:include|are|:)"):
            self.add("spec/limitations", "没有找到 Limitations 小节或段落(ACL/ARR 缺这一节直接拒稿;NeurIPS checklist 也要求)", severity="warning",
                     fixes=["加一节 Limitations:评测覆盖不到的场景、成本、失败模式——具体到任务类型"])
        llm = re.finditer(r"\b(?:GPT-?[345](?:o|\.\d)?(?:-[a-z]+)?|Claude(?: \d(?:\.\d)?)?(?: (?:Opus|Sonnet|Haiku))?|Gemini(?: \d(?:\.\d)?)?(?: (?:Pro|Flash|Ultra))?|Llama[- ]?\d(?:\.\d)?|Qwen[- ]?\d(?:\.\d)?|DeepSeek[- ]?[RV]?\d?|Mistral)\b", self.doc.masked)
        if any(True for _ in llm) and not self._has(r"\b20\d\d-\d\d-\d\d\b|\bversion\b|snapshot|checkpoint|temperature|\btop[-_ ]?p\b"):
            self.add("spec/model-version", "用到了具体 LLM,但没写版本/快照日期或解码参数", severity="info",
                     line=self._first(r"GPT|Claude|Gemini|Llama|Qwen|DeepSeek|Mistral")[0],
                     fixes=["写明模型快照(如 gpt-4o-2024-08-06)、temperature、最大步数与花费"])

    def _para_at(self, pos):
        for p in self.doc.paragraphs:
            if p.a <= pos < p.b:
                return p
        return None

    def _sentence_at(self, p, pos):
        if p is None:
            return ""
        for a, b in p.sentences:
            if a <= pos < b:
                return p.sent_text(a, b)
        return p.text


def detect_profile(doc):
    s = doc.masked
    dft = len(re.findall(r"\bDFT\b|density functional|VASP|\beV\b|band gap|adsorption energ|formation energ|interatomic|"
                         r"\bcrystals?\b|\bmolecul|perovskite|catalys|\bQM9\b|materials project|electrolyte", s, re.I))
    agent = len(re.findall(r"\bLLMs?\b|language models?|\bagents?\b|tool[- ]use|prompting|in-context|WebArena|SWE-bench|"
                           r"\bGAIA\b|ReAct|ALFWorld|HotpotQA|chain-of-thought|GPT-?[34]", s, re.I))
    if max(dft, agent) < 3:
        return "general"
    return "dft-ml" if dft >= agent else "agent-conf"


def check_bib(doc, bib_path):
    keys = set()
    for p in bib_path:
        keys |= set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", open(p, encoding="utf-8", errors="replace").read()))
    out = []
    for m in re.finditer(r"\\(?:cite|citep|citet|citeauthor|nocite)\*?(?:\[[^\]]*\])*\{([^}]*)\}", doc.src):
        for k in [x.strip() for x in m.group(1).split(",") if x.strip()]:
            if k not in keys and k != "*":
                out.append(Issue("cite/missing-key", f"引用键「{k}」不在 bib 里——可能是编造或拼错的文献",
                                 line=doc.line(m.start()), section=doc.section_at(m.start()), text=k,
                                 fixes=["在 Google Scholar / Crossref 核实这篇文献确实存在,再加进 bib",
                                        "核实不了就删掉这处引用,换成你读过的文献"], severity="error"))
    return out


def lint(path, profile="auto", bib=None, text=None, lexicon=None):
    doc = Doc(path, text)
    lex = lexicon or json.load(open(_find_lexicon(), encoding="utf-8"))
    prof = detect_profile(doc) if profile == "auto" else profile
    lt = Linter(doc, lex, prof)
    issues = lt.run()
    if bib:
        issues = sorted(issues + check_bib(doc, bib), key=_order)
    words = sum(p.words for p in doc.paragraphs)
    stats = {sec: {**v, "excess_per_1000": round(1000 * v["excess"] / v["words"], 1) if v["words"] else 0}
             for sec, v in lt.stats.items() if v["words"]}
    return {"file": path, "profile": prof, "words": words, "paragraphs": len(doc.paragraphs),
            "sections": stats, "issues": issues,
            "counts": dict(Counter(i["severity"] for i in issues)), "repair_rules": REPAIR_RULES}


def write_report(path, result):
    rp = os.path.splitext(path)[0] + ".deai.json"
    if not result["issues"]:
        if os.path.exists(rp):
            os.remove(rp)
        return None
    with open(rp, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    return rp


def print_human(res, limit):
    c = res["counts"]
    print(f"[deai_lint] {os.path.basename(res['file'])}:{res['words']} 词,{res['paragraphs']} 段,领域 {res['profile']}"
          f" —— error {c.get('error', 0)} / warning {c.get('warning', 0)} / info {c.get('info', 0)}")
    if res["sections"]:
        print("  各节 LLM 超额词密度(每千词;人类学术写作通常 < 3):")
        for sec, v in res["sections"].items():
            print(f"    {sec[:40]:40s} {v['words']:6d} 词  {v['excess_per_1000']:5.1f}")
    shown = 0
    for i in res["issues"]:
        if shown >= limit:
            print(f"  … 另有 {len(res['issues']) - shown} 条,见 .deai.json 或加 --limit")
            break
        loc = f"L{i['line']}" if i["line"] else "全文"
        print(f"  [{i['severity']:7s} {i['code']}] {loc} {i['message']}")
        if i.get("text"):
            print(f"      “{i['text']}”")
        if i.get("fixes"):
            print(f"      修法: {' / '.join(i['fixes'])}")
        shown += 1
    if res["issues"]:
        print(res["repair_rules"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="论文 AI 味体检(不是 AI 检测器)")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--profile", default="auto", choices=["auto", "general", "dft-ml", "agent-conf"])
    ap.add_argument("--bib", nargs="*", help="bib 文件,核对 \\cite 键")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=60, help="终端最多显示多少条")
    ap.add_argument("--no-report", action="store_true", help="不写 .deai.json")
    a = ap.parse_args(argv)
    code = 0
    results = []
    for f in a.files:
        if not os.path.exists(f):
            print(f"[deai_lint] 找不到 {f}", file=sys.stderr)
            return 2
        res = lint(f, a.profile, a.bib)
        if not a.no_report:
            res["report"] = write_report(f, res)
        results.append(res)
        if res["counts"].get("error"):
            code = 1
        if not a.json:
            print_human(res, a.limit)
    if a.json:
        print(json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=1))
    return code


if __name__ == "__main__":
    sys.exit(main())
