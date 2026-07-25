#!/usr/bin/env python3
# ============================================================
# wordlint.py — 扫描 deck 生成脚本里的 AI 味词汇
#
# 为什么做成脚本:去 AI 味不能靠"记得避开",要靠**每次生成后跑一遍**。
# 词表是数据(references/ai-wordlist.json),补词不用改代码。
#
# 四档判定(避免把正常术语误报成 AI 味):
#   hard    单次出现即必改(生成痕迹、未填占位符、无出处引用)
#   always  单次即报,但允许作者判断豁免
#   density 同一页命中 >=2(短文本)/>=3(长文本)才报——单个用是正常的
#   struct  句法性痕迹(三项对称、句长均质、不仅…更是),脚本查不了,交人工审计
# whitelist 优先于一切档位:鲁棒性/可持续性/数字化/深度学习 等正常术语永不报。
#
# 用法:
#   python3 wordlint.py my_deck.js
#   python3 wordlint.py my_deck.js --strict     # 有 hard/always 命中即退出码 1
#   python3 wordlint.py my_deck.js --lang paper # 论文语体:放行"进行+V"等幻灯专属规则
# ============================================================
import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
# 词表查找顺序:skill 内的 references/、脚本同级 references/、脚本同级——
# 脚本被复制进用户项目后仍能找到(把 json 一起复制即可)
def _find_wordlist():
    for c in (HERE.parent / "references" / "ai-wordlist.json",
              HERE / "references" / "ai-wordlist.json",
              HERE / "ai-wordlist.json",
              pathlib.Path.cwd() / "references" / "ai-wordlist.json",
              pathlib.Path.cwd() / "ai-wordlist.json"):
        if c.exists():
            return c
    return HERE.parent / "references" / "ai-wordlist.json"

WORDLIST = _find_wordlist()

STR_RE = re.compile(r'"((?:[^"\\]|\\.)*)"' r"|'((?:[^'\\]|\\.)*)'" r"|`((?:[^`\\]|\\.)*)`", re.S)
PAGE_RE = re.compile(r"\bd\.(page|section|cover|closing|refs)\s*\(")
# 幻灯专属规则:论文语体下放行(论文里"进行+V"是规范表达)
SLIDE_ONLY = {"进行讨论", "进行分析", "进行研究", "具有重要意义"}
DENSITY_SHORT, DENSITY_LONG = 2, 3   # 短文本(<100 字)/长文本 的密度阈值
TIER_RANK = {"hard": 0, "always": 1, "density": 2}


def load(which):
    if not WORDLIST.exists():
        sys.exit(f"[wordlint] 找不到词表 {WORDLIST}")
    d = json.loads(WORDLIST.read_text())
    wl = [w for w in d.get("whitelist", [])]
    items = []
    for grp in ("zh", "en"):
        if which in ("all", grp):
            for it in d.get(grp, []):
                if it.get("tier") == "struct":
                    continue                      # 句法档不由脚本判定
                items.append({**it, "grp": grp})
    return items, wl


def page_of(src, pos):
    """把命中位置归到它所属的 d.page(...) 块,用于按页统计密度。"""
    last, idx = 0, 0
    for i, m in enumerate(PAGE_RE.finditer(src), 1):
        if m.start() <= pos:
            last, idx = m.start(), i
        else:
            break
    return idx or 1


def scan(path, items, whitelist, lang):
    src = path.read_text()
    per_page = defaultdict(list)          # page -> [(line, item, ctx, litlen)]
    for m in STR_RE.finditer(src):
        lit = next(g for g in m.groups() if g is not None)
        if not lit.strip():
            continue
        # 先把白名单词从待检文本里挖掉:鲁棒性 不该因为含"性"而被规则命中
        probe = lit
        for w in whitelist:
            probe = probe.replace(w, " " * len(w))
        low = probe.lower()
        line = src.count("\n", 0, m.start()) + 1
        page = page_of(src, m.start())
        for it in items:
            if lang == "paper" and it["word"] in SLIDE_ONLY:
                continue
            needle = it["word"].lower()
            if "……" in needle:            # 含省略号的模式:拆成两段都要出现
                a, b = needle.split("……", 1)
                if not (a in low and b in low):
                    continue
                i = low.index(a)
            else:
                if needle not in low:
                    continue
                i = low.index(needle)
            ctx = lit[max(0, i - 16): i + len(it["word"]) + 20].replace("\n", " ")
            per_page[page].append((line, it, ctx, len(lit)))
    return per_page


def main():
    ap = argparse.ArgumentParser(description="扫描 deck 脚本中的 AI 味词汇(四档判定 + 白名单)")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--list", default="all", choices=["all", "zh", "en"])
    ap.add_argument("--lang", default="slide", choices=["slide", "paper"], help="语体档位")
    ap.add_argument("--strict", action="store_true", help="有 hard/always 命中即退出码 1")
    args = ap.parse_args()

    items, whitelist = load(args.list)
    grand = 0
    for f in args.files:
        path = pathlib.Path(f)
        if not path.exists():
            print(f"[wordlint] 跳过 {f}(不存在)", file=sys.stderr)
            continue
        per_page = scan(path, items, whitelist, args.lang)

        reported = []
        for page, hits in sorted(per_page.items()):
            dens = defaultdict(list)
            for line, it, ctx, litlen in hits:
                tier = it.get("tier", "always")
                if tier == "density":
                    dens[it["word"]].append((line, it, ctx, litlen))
                else:
                    reported.append((tier, page, line, it, ctx))
            # 密度档:按页汇总,达阈值才报
            n = sum(len(v) for v in dens.values())
            if n:
                thr = DENSITY_SHORT if max(x[3] for v in dens.values() for x in v) < 100 else DENSITY_LONG
                if n >= thr:
                    for v in dens.values():
                        for line, it, ctx, _ in v:
                            reported.append(("density", page, line, it, ctx))

        if not reported:
            print(f"[wordlint] {path.name}:干净(词表 {len(items)} 条,白名单 {len(whitelist)} 条)")
            continue

        reported.sort(key=lambda r: (TIER_RANK.get(r[0], 9), r[2]))
        hard = sum(1 for r in reported if r[0] == "hard")
        always = sum(1 for r in reported if r[0] == "always")
        dens_n = sum(1 for r in reported if r[0] == "density")
        print(f"[wordlint] {path.name}:hard {hard} / always {always} / density {dens_n}")
        for tier, page, line, it, ctx in reported:
            mark = {"hard": "!!", "always": "! ", "density": "~ "}[tier]
            print(f"  {mark} L{line:<4} P{page:<2} [{it['grp']}] 「{it['word']}」 → {it.get('replace','删或改具体')}")
            print(f"        …{ctx}…")
        grand += hard + always
        if dens_n:
            print("  ~ 密度档:单个用是正常的,同页多个才算堆砌——挑最空的删掉即可")

    if grand:
        print(f"\n[wordlint] hard/always 共 {grand} 处。逐条处理:能给数字的给数字,"
              f"给不了的删掉——不要换个同样空的说法。")
        print("[wordlint] 结构性痕迹(三项对称/句长均质/标题排比)脚本查不出,"
              "按 content-discipline.md 第五节做人工节拍审计。")
    if args.strict and grand:
        sys.exit(1)


if __name__ == "__main__":
    main()
