"""引用真实性核验(确定性节点,不依赖 LLM)。

思路取自 Imbad0202/academic-research-skills 的多库交叉验证:每条候选引用
按 DOI 查 Crossref(失败再查 Semantic Scholar),并做标题相似度比对——
DOI 存在但标题对不上,同样视为可疑并剔除。宁可少一条引用,不可编一条。
"""
from __future__ import annotations

import difflib
import re

import requests

UA = {"User-Agent": "paperflow/0.1 (academic-skills; mailto:paperflow@example.com)"}
TITLE_SIM_THRESHOLD = 0.55


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def _crossref(doi: str) -> dict | None:
    r = requests.get(f"https://api.crossref.org/works/{doi}", headers=UA, timeout=20)
    if r.status_code != 200:
        return None
    m = r.json()["message"]
    authors = [
        " ".join(x for x in [a.get("given"), a.get("family")] if x)
        for a in m.get("author", [])
    ]
    year = None
    for k in ("published-print", "published-online", "published", "issued"):
        parts = m.get(k, {}).get("date-parts", [[None]])
        if parts and parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    return {
        "source": "crossref",
        "title": (m.get("title") or [""])[0],
        "container": (m.get("container-title") or [""])[0],
        "authors": authors,
        "year": year,
        "volume": m.get("volume"),
        "pages": m.get("page"),
    }


def _semanticscholar(doi: str) -> dict | None:
    r = requests.get(
        f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
        params={"fields": "title,year,venue,authors"},
        headers=UA,
        timeout=20,
    )
    if r.status_code != 200:
        return None
    m = r.json()
    return {
        "source": "semanticscholar",
        "title": m.get("title") or "",
        "container": m.get("venue") or "",
        "authors": [a.get("name", "") for a in m.get("authors", [])],
        "year": m.get("year"),
        "volume": None,
        "pages": None,
    }


def verify_candidates(candidates: list[dict]) -> tuple[list[dict], list[dict], list[str]]:
    """逐条核验候选引用。返回 (verified, dropped, log)。

    candidate: {key, title, doi, why?}
    verified 条目在候选基础上并入权威题录(authors/year/container/...)。
    """
    verified, dropped, log = [], [], []
    for c in candidates:
        doi = (c.get("doi") or "").strip()
        if not doi:
            dropped.append({**c, "reason": "缺少 DOI"})
            log.append(f"✗ {c.get('key')}: 无 DOI,剔除")
            continue
        try:
            rec = _crossref(doi) or _semanticscholar(doi)
        except requests.RequestException as e:
            rec = None
            log.append(f"! {c.get('key')}: 查询异常 {e}")
        if rec is None:
            dropped.append({**c, "reason": "DOI 在 Crossref/Semantic Scholar 均未命中"})
            log.append(f"✗ {c.get('key')}: DOI {doi} 不存在,剔除(疑似编造)")
            continue
        sim = _similarity(c.get("title", ""), rec["title"])
        if sim < TITLE_SIM_THRESHOLD:
            dropped.append({**c, "reason": f"标题与权威记录不符(相似度 {sim:.2f}):{rec['title']!r}"})
            log.append(f"✗ {c.get('key')}: DOI 存在但标题不符(sim={sim:.2f}),剔除")
            continue
        verified.append({**c, **rec, "title": rec["title"], "similarity": round(sim, 2)})
        log.append(f"✓ {c.get('key')}: {rec['source']} 确认 [{rec['year']}] {rec['title'][:60]}")
    return verified, dropped, log


def to_bibtex(entries: list[dict]) -> str:
    """把核验后的题录写成 BibTeX(pandoc --citeproc 直接可用)。"""
    out = []
    for e in entries:
        authors = " and ".join(e.get("authors") or ["Unknown"])
        fields = {
            "title": e.get("title", ""),
            "author": authors,
            "journal": e.get("container", ""),
            "year": str(e.get("year") or ""),
            "volume": e.get("volume") or "",
            "pages": e.get("pages") or "",
            "doi": e.get("doi", ""),
        }
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items() if v)
        out.append(f"@article{{{e['key']},\n{body}\n}}")
    return "\n\n".join(out) + "\n"
