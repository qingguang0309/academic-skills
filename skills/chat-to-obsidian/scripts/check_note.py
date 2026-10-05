#!/usr/bin/env python3
"""Check an Obsidian note written by the chat-to-obsidian skill.

Usage:
    python3 check_note.py NOTE.md [NOTE2.md ...] [--vault /path/to/vault]

The vault root defaults to the nearest ancestor directory containing `.obsidian`,
falling back to /Users/qingguang/Documents/Obsidian. Exit code 1 if any error.
Standard library only.
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_VAULT = Path("/Users/qingguang/Documents/Obsidian")
SOURCES = {"claude-chat", "claude-code", "claude-cowork"}
BAD_FILENAME_CHARS = set('/\\:*?"<>|#^[]')
# Phrases that leak the chat format into a standalone note.
CHAT_TRACES = [
    "你问", "你刚才", "我刚才", "如上所述", "上面提到", "希望对你有帮助", "希望这能帮",
    "好问题", "总的来说", "Claude 说", "Claude说", "我来解释", "让我们", "下面我们",
    "本文将", "值得注意的是", "至关重要", "深入探讨",
]
GLOSSARY_LINE = re.compile(r"^- \*\*[^*]+\*\*.* — \S")


def find_vault(note: Path) -> Path:
    for parent in note.resolve().parents:
        if (parent / ".obsidian").is_dir():
            return parent
    return DEFAULT_VAULT


def parse_frontmatter(lines):
    if not lines or lines[0].strip() != "---":
        return None, 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], i + 1
    return None, 0


def check(note: Path, vault: Path):
    errors, warnings = [], []
    text = note.read_text(encoding="utf-8")
    lines = text.splitlines()

    bad = BAD_FILENAME_CHARS & set(note.stem)
    if bad:
        errors.append(f"文件名含非法字符 {''.join(sorted(bad))}")

    fm, body_start = parse_frontmatter(lines)
    if fm is None:
        errors.append("缺少 frontmatter（首行须为 ---，并有闭合的 ---）")
        fm = []
    fm_text = "\n".join(fm)
    if not re.search(r"^tags:", fm_text, re.M):
        errors.append("frontmatter 缺 tags")
    elif "claude总结" not in fm_text:
        errors.append("tags 里缺 claude总结")
    m = re.search(r"^created:\s*(\S+)", fm_text, re.M)
    if not m:
        errors.append("frontmatter 缺 created")
    else:
        try:
            date.fromisoformat(m.group(1))
        except ValueError:
            errors.append(f"created 不是 YYYY-MM-DD：{m.group(1)}")
    m = re.search(r"^source:\s*(.+)$", fm_text, re.M)
    if not m:
        errors.append("frontmatter 缺 source")
    else:
        unknown = [s for s in re.split(r"[,\s]+", m.group(1).strip()) if s and s not in SOURCES]
        if unknown:
            warnings.append(f"source 含 {unknown}，不在 {sorted(SOURCES)} 里")

    body = lines[body_start:]
    in_code = False
    prose = []  # (lineno, line) outside code blocks
    for i, line in enumerate(body, start=body_start + 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            prose.append((i, line))

    for i, line in prose:
        if re.match(r"^# \S", line):
            errors.append(f"L{i}: 正文不写一级标题（Obsidian 用文件名当标题）")

    if not any(l.strip() and not l.startswith("#") for _, l in prose[:15]):
        warnings.append("开头 15 行内没有导语段落")

    headings = [(i, l[3:].strip()) for i, l in prose if l.startswith("## ")]
    names = [h for _, h in headings]
    if "术语表" not in names:
        errors.append("缺少 ## 术语表")
    else:
        if names[-1] not in ("术语表", "相关"):
            warnings.append(f"术语表之后还有小节：{names[-1]}")
        start = next(i for i, h in headings if h == "术语表")
        entries = 0
        for i, line in prose:
            if i <= start:
                continue
            if line.startswith("## "):
                break
            if line.startswith("- "):
                entries += 1
                if not GLOSSARY_LINE.match(line):
                    errors.append(f"L{i}: 术语表条目格式应为 `- **术语** — 解释`")
        if entries == 0:
            errors.append("术语表是空的")
        elif entries < 3:
            warnings.append(f"术语表只有 {entries} 条")
    for empty in ("概述", "总结", "详细介绍", "简介", "引言"):
        if empty in names:
            warnings.append(f"空泛小节标题：## {empty}")

    existing = {p.stem for p in vault.rglob("*.md")} if vault.is_dir() else None
    for i, line in prose:
        for target in re.findall(r"\[\[([^\]]+)\]\]", line):
            name = target.split("|")[0].split("#")[0].strip()
            if existing is not None and name not in existing:
                errors.append(f"L{i}: 双链 [[{name}]] 在 vault 里找不到同名笔记")
        for phrase in CHAT_TRACES:
            if phrase in line:
                errors.append(f"L{i}: 对话痕迹/套话「{phrase}」")
    if existing is None:
        warnings.append(f"vault 目录不存在，跳过双链检查：{vault}")

    highlights = sum(len(re.findall(r"==[^=]+==", l)) for _, l in prose)
    if highlights > 5:
        warnings.append(f"==高亮== 用了 {highlights} 处，建议只留最关键的两三处")

    return errors, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("notes", nargs="+", type=Path)
    ap.add_argument("--vault", type=Path)
    args = ap.parse_args()

    failed = False
    for note in args.notes:
        if not note.is_file():
            print(f"✗ {note}: 文件不存在")
            failed = True
            continue
        vault = args.vault or find_vault(note)
        errors, warnings = check(note, vault)
        mark = "✗" if errors else "✓"
        print(f"{mark} {note.name}: {len(errors)} error, {len(warnings)} warning")
        for e in errors:
            print(f"  error   {e}")
        for w in warnings:
            print(f"  warning {w}")
        failed |= bool(errors)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
