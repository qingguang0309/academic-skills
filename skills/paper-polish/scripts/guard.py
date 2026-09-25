#!/usr/bin/env python3
"""guard — 改写前后对照:去 AI 味只许改说法,不许改事实。

商业"降 AI"工具最大的问题是改着改着把意思改了:数字丢了、引用换了、公式动了、hedging 被悄悄
升级成断言。这个脚本把原稿和改写稿逐项对照,凡是事实层面的变化都点名报出来:

    python3 guard.py paper.tex paper_revised.tex
    python3 guard.py paper.tex paper_revised.tex --json

  error   引用键增删、\\ref/\\label 变化、公式改动、凭空多出来的数字(可能是编造)
  warning 数字消失(信息丢失)、结论力度被升级(suggest → demonstrate)、段落大幅扩写或删减
  info    专有名词/化学式/缩写消失、待作者确认的 [请确认: …] 标记清单、改写前后的 AI 味诊断对比

改写稿里新增的数字若写在 [请确认: …] 标记里,视为留给作者核对,不算编造。
退出码:0 无 error;1 有 error;2 用法错误。
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deai_lint import Doc, lint  # noqa: E402

CONFIRM = re.compile(r"\[(?:请确认|待确认|CONFIRM|TODO-author)[:：]?[^\]]*\]", re.I)
HEDGE = re.compile(r"\b(?:may|might|could|suggests?|suggested|indicat(?:e|es|ed)|likely|possibly|plausibl[ey]|"
                   r"appears?|seems?|is consistent with|tentative(?:ly)?|presumably)\b", re.I)
STRONG = re.compile(r"\b(?:demonstrat(?:e|es|ed)|prov(?:e|es|ed|en)|confirm(?:s|ed)?|establish(?:es|ed)?|"
                    r"clearly|undoubtedly|definitively|conclusively|always|guarantees?)\b", re.I)
NUM = re.compile(r"(?<![A-Za-z_\\])[-−–]?\d+(?:[.,]\d+)*(?![A-Za-z\d])(?:\s?(?:%|‰))?")  # 2p、3d 这类标签不算数字
TERM = re.compile(r"\b(?:[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+|[A-Z]{2,}[A-Za-z0-9-]*|[A-Za-z]+-\d+[A-Za-z]*)\b")


def _norm_math(s):
    return re.sub(r"\s+", "", s)


def extract(doc):
    src = doc.src
    body = src
    m = re.search(r"\\begin\{document\}", src)
    if m:
        body = src[m.end():]
    body_nc = re.sub(r"(?<!\\)%[^\n]*", "", body)
    cites = Counter(k.strip() for g in re.findall(r"\\(?:cite|citep|citet|citeauthor|citeyear|nocite)\*?(?:\[[^\]]*\])*\{([^}]*)\}", body_nc)
                    for k in g.split(",") if k.strip())
    cites += Counter(re.findall(r"\[@([\w:-]+)", body_nc))
    refs = Counter(re.findall(r"\\(?:ref|cref|Cref|autoref|eqref|pageref)\{([^}]*)\}", body_nc))
    labels = Counter(re.findall(r"\\label\{([^}]*)\}", body_nc))
    maths = Counter()
    for pat in (r"\\begin\{(equation|align|gather|multline|eqnarray)\*?\}.*?\\end\{\1\*?\}", r"\$\$.*?\$\$",
                r"\\\[.*?\\\]", r"\\\(.*?\\\)", r"(?<!\\)\$(?:\\.|[^$\\])+?\$"):
        for mm in re.finditer(pat, body_nc, re.S):
            maths[_norm_math(mm.group(0))] += 1
    graphics = Counter(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", body_nc))
    prose = CONFIRM.sub(" ", doc.masked)
    nums = Counter(n.replace("−", "-").replace("–", "-").replace(" ", "") for n in NUM.findall(prose))
    terms = Counter(TERM.findall(prose))
    confirms = [(doc.line(mm.start()), mm.group(0)) for mm in CONFIRM.finditer(doc.masked)]
    confirm_nums = Counter(n for _, c in confirms for n in NUM.findall(c))
    return dict(cites=cites, refs=refs, labels=labels, maths=maths, graphics=graphics, nums=nums,
                terms=terms, confirms=confirms, confirm_nums=confirm_nums)


def _diff(a, b):
    return sorted((a - b).elements()), sorted((b - a).elements())


def _para_strength(text):
    return len(HEDGE.findall(text)), len(STRONG.findall(text))


def align(pa, pb):
    """按段落文字相似度对齐(处理段落合并/拆分),返回 (i, j, ratio) 列表。"""
    ta = [re.sub(r"\s+", " ", p.text).strip().lower() for p in pa]
    tb = [re.sub(r"\s+", " ", p.text).strip().lower() for p in pb]
    out, used = [], set()
    for i, a in enumerate(ta):
        best, bj = 0.0, None
        for j, b in enumerate(tb):
            if j in used:
                continue
            r = difflib.SequenceMatcher(None, a.split(), b.split(), autojunk=False).ratio()
            if r > best:
                best, bj = r, j
        if bj is not None and best >= 0.25:
            used.add(bj)
            out.append((i, bj, best))
    return out


def guard(orig_path, rev_path):
    A, B = Doc(orig_path), Doc(rev_path)
    ea, eb = extract(A), extract(B)
    issues = []

    def add(code, sev, msg, **kw):
        issues.append(dict(code=code, severity=sev, message=msg, **kw))

    for key, code, label in (("cites", "fact/cite", "引用键"), ("refs", "fact/ref", "\\ref 交叉引用"),
                             ("labels", "fact/label", "\\label"), ("graphics", "fact/graphics", "插图路径")):
        gone, new = _diff(ea[key], eb[key])
        if gone:
            add(code + "-removed", "error", f"{label}被删掉: {', '.join(gone[:8])}", items=gone,
                fixes=["恢复原文的引用/交叉引用;确需删除由作者决定并在报告里说明"])
        if new:
            add(code + "-added", "error", f"改写稿新增了{label}: {', '.join(new[:8])}", items=new,
                fixes=["去 AI 味不加文献:删掉新增项;确需补文献由作者自己查证后添加"])
    gone, new = _diff(ea["maths"], eb["maths"])
    if gone or new:
        add("fact/math", "error", f"公式有改动:删 {len(gone)} 处,增 {len(new)} 处",
            items={"removed": gone[:5], "added": new[:5]}, fixes=["公式一律原样保留"])
    # 数字按"值"比较:改写时重复引用原稿已有的数字不算新增;原稿里某个值一次都不剩才算丢失
    gone = sorted(set(ea["nums"]) - set(eb["nums"]))
    new = set(eb["nums"]) - set(ea["nums"])
    new_unmarked = sorted(new - set(eb["confirm_nums"]))
    if new_unmarked:
        add("fact/number-added", "error", f"改写稿多出了原稿没有的数字: {', '.join(new_unmarked[:12])}",
            items=new_unmarked, fixes=["数字只能来自原稿或作者;来源不明的删掉,或写成 [请确认: …] 交给作者"])
    if gone:
        add("fact/number-removed", "warning", f"原稿的数字在改写稿里消失: {', '.join(gone[:12])}", items=gone,
            fixes=["确认是有意删减(重复信息)还是改丢了;数据和条件原则上保留"])
    gone_terms, _ = _diff(ea["terms"], eb["terms"])
    gone_terms = sorted(set(gone_terms) - set(eb["terms"]))
    if gone_terms:
        add("fact/term-removed", "info", f"这些专有名词/化学式/缩写在改写稿中不再出现: {', '.join(gone_terms[:15])}",
            items=gone_terms, fixes=["核对是否丢了研究对象或方法名"])

    wa = sum(p.words for p in A.paragraphs)
    wb = sum(p.words for p in B.paragraphs)
    for i, j, r in align(A.paragraphs, B.paragraphs):
        pa, pb = A.paragraphs[i], B.paragraphs[j]
        ha, sa = _para_strength(pa.text)
        hb, sb = _para_strength(pb.text)
        if sb > sa and hb <= ha:
            add("claim/escalated", "warning",
                f"段落结论力度被升级:hedging {ha}→{hb},强断言 {sa}→{sb}",
                line=B.line(pb.a), text=re.sub(r"\s+", " ", pb.text)[:120],
                fixes=["证据等级没变,措辞就不该变强;间接证据用 suggest / indicate"])
        if pa.words >= 30:
            ch = (pb.words - pa.words) / pa.words
            if ch > 0.35:
                add("length/expanded", "warning", f"段落扩写 {ch:+.0%}({pa.words}→{pb.words} 词)",
                    line=B.line(pb.a), text=re.sub(r"\s+", " ", pb.text)[:120],
                    fixes=["去 AI 味通常会让文字变短;扩出来的部分检查是不是新加的空话或新事实"])
            elif ch < -0.6:
                add("length/cut", "warning", f"段落删减 {ch:+.0%}({pa.words}→{pb.words} 词)",
                    line=B.line(pb.a), text=re.sub(r"\s+", " ", pb.text)[:120],
                    fixes=["核对删掉的是不是空话,而不是条件、对照或局限"])
    if eb["confirms"]:
        add("author/confirm", "info", f"改写稿里有 {len(eb['confirms'])} 处 [请确认] 待作者处理",
            items=[f"L{ln} {t}" for ln, t in eb["confirms"]])

    la, lb = lint(orig_path), lint(rev_path)
    groups = lambda r: Counter(i["code"].split("/")[0] for i in r["issues"])
    before, after = groups(la), groups(lb)
    rank = {"error": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda x: (rank[x["severity"]], x.get("line") or 0))
    return {"original": orig_path, "revised": rev_path, "words": [wa, wb],
            "lint_before": dict(before), "lint_after": dict(after),
            "lint_total": [len(la["issues"]), len(lb["issues"])],
            "issues": issues, "counts": dict(Counter(i["severity"] for i in issues))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="改写前后事实对照")
    ap.add_argument("original")
    ap.add_argument("revised")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    for f in (a.original, a.revised):
        if not os.path.exists(f):
            print(f"[guard] 找不到 {f}", file=sys.stderr)
            return 2
    res = guard(a.original, a.revised)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        c = res["counts"]
        wa, wb = res["words"]
        print(f"[guard] {os.path.basename(a.original)} → {os.path.basename(a.revised)}:"
              f"{wa} → {wb} 词({(wb - wa) / max(wa, 1):+.0%});"
              f"error {c.get('error', 0)} / warning {c.get('warning', 0)} / info {c.get('info', 0)}")
        la, lb = res["lint_total"]
        print(f"  AI 味诊断 {la} → {lb} 条;按类:" + ", ".join(
            f"{k} {res['lint_before'].get(k, 0)}→{res['lint_after'].get(k, 0)}"
            for k in sorted(set(res["lint_before"]) | set(res["lint_after"]))))
        for i in res["issues"]:
            loc = f"L{i['line']} " if i.get("line") else ""
            print(f"  [{i['severity']:7s} {i['code']}] {loc}{i['message']}")
            if i.get("text"):
                print(f"      “{i['text']}”")
            if i["code"] == "author/confirm":
                for it in i["items"]:
                    print(f"      {it}")
            if i.get("fixes"):
                print(f"      修法: {' / '.join(i['fixes'])}")
    return 1 if res["counts"].get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
