#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add spaces between CJK and Latin letters/digits in Markdown prose."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET_DIRS = [
    ROOT / "docs",
    ROOT / "i18n" / "en" / "docusaurus-plugin-content-docs" / "current",
]

CJK = r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]"
LATIN = r"[A-Za-z0-9]"
CJK_TO_LATIN = re.compile(rf"({CJK})(?={LATIN})")
LATIN_TO_CJK = re.compile(rf"({LATIN})(?={CJK})")
PUNCT_TO_LATIN = re.compile(r"([】》）])(?=[A-Za-z0-9])")


def apply_spacing_rules(text: str) -> str:
    out = text
    prev = None
    while prev != out:
        prev = out
        out = CJK_TO_LATIN.sub(r"\1 ", out)
        out = LATIN_TO_CJK.sub(r"\1 ", out)
        out = PUNCT_TO_LATIN.sub(r"\1 ", out)
    out = re.sub(r" {2,}", " ", out)
    return out


def split_protected(text: str) -> list[tuple[str, bool, str]]:
    """Return (segment, is_protected, kind)."""
    pattern = re.compile(
        r"(^---\n.*?\n---\n)"  # frontmatter
        r"|(```[\s\S]*?```)"  # fenced code
        r"|(`[^`\n]+`)"  # inline code
        r"|(\[[^\]]*\]\([^)]+\))"  # markdown links
        r"|(https?://[^\s)>\]]+)",  # bare urls
        re.MULTILINE,
    )
    parts: list[tuple[str, bool, str]] = []
    last = 0
    for m in pattern.finditer(text):
        if m.start() > last:
            parts.append((text[last : m.start()], False, "prose"))
        chunk = m.group(0)
        if chunk.startswith("```"):
            parts.append((chunk, True, "fence"))
        else:
            parts.append((chunk, True, "other"))
        last = m.end()
    if last < len(text):
        parts.append((text[last:], False, "prose"))
    return parts


def fix_code_fence(block: str) -> str:
    """Fix spacing in fenced blocks: comments and CJK log/prose lines."""
    lines = block.split("\n")
    if not lines:
        return block
    opener = lines[0]
    lang = opener.replace("```", "").strip().lower()
    closer = lines[-1] if lines[-1].strip() == "```" else None
    body_end = len(lines) - 1 if closer else len(lines)
    body = lines[1:body_end]
    fix_cjk_lines = lang in ("", "text", "shell", "bash")
    fixed_body = []
    for line in body:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            prefix = line[: len(line) - len(stripped)]
            fixed_body.append(prefix + apply_spacing_rules(stripped))
        elif " #" in line or "\t#" in line:
            code, _, comment = line.partition("#")
            fixed_body.append(code + "#" + apply_spacing_rules(comment))
        elif fix_cjk_lines and re.search(CJK, line):
            fixed_body.append(apply_spacing_rules(line))
        else:
            fixed_body.append(line)
    if closer:
        return "\n".join([opener, *fixed_body, closer])
    return "\n".join([opener, *fixed_body])


def fix_markdown(text: str) -> str:
    chunks = split_protected(text)
    out = []
    for chunk, protected, kind in chunks:
        if not protected:
            out.append(apply_spacing_rules(chunk))
        elif kind == "fence":
            out.append(fix_code_fence(chunk))
        else:
            out.append(chunk)
    return "".join(out)


def main():
    changed_files = 0
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            original = path.read_text(encoding="utf-8")
            if not re.search(CJK, original):
                continue
            updated = fix_markdown(original)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                changed_files += 1
                print("Updated", path.relative_to(ROOT))
    print(f"Done. {changed_files} file(s) updated.")


if __name__ == "__main__":
    main()
