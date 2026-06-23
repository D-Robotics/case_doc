#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Docusaurus docs from extracted PDF text, preserving original content."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACT = ROOT / "pdf_extract.txt"
DOCS = ROOT / "docs"
I18N_DOCS = ROOT / "i18n" / "en" / "docusaurus-plugin-content-docs" / "current"

# (start_line, end_line) 1-based inclusive
SECTIONS = {
    "intro": (2, 17),
    "01_usb": (19, 219),
    "02_uart": (220, 298),
    "03_object_detection": (304, 333),
    "04_speech_to_text": (335, 421),
    "05_llm": (423, 463),
    "06_vlm": (464, 511),
    "07_vlm_voice": (515, 575),
    "08_vla_pi0": (578, 948),
    "09_resources": (949, 955),
    "10_qa": (956, 973),
    "11_misc": (974, 1092),
    "12_can": (1093, 1238),
}

FILE_MAP = {
    "intro": ("intro.md", {"sidebar_position": 1, "slug": "/intro"}),
    "01_usb": ("01_getting_started/01_usb_peripherals.md", {"sidebar_position": 1, "sidebar_label": "1.1 USB 外设使用", "slug": "/01_getting_started/01_usb_peripherals"}),
    "02_uart": ("01_getting_started/02_uart.md", {"sidebar_position": 2, "sidebar_label": "1.2 UART 使用", "slug": "/01_getting_started/02_uart"}),
    "12_can": ("01_getting_started/03_can.md", {"sidebar_position": 3, "sidebar_label": "CAN 使用", "slug": "/01_getting_started/03_can"}),
    "03_object_detection": ("02_basic/01_vision/01_object_detection.md", {"sidebar_position": 1, "sidebar_label": "2.1.1 目标检测", "slug": "/02_basic/01_vision/01_object_detection"}),
    "04_speech_to_text": ("02_basic/02_audio/01_speech_to_text.md", {"sidebar_position": 1, "sidebar_label": "2.2.1 语音转文字", "slug": "/02_basic/02_audio/01_speech_to_text"}),
    "05_llm": ("02_basic/03_llm/01_llm.md", {"sidebar_position": 1, "sidebar_label": "2.3.1 大语言模型", "slug": "/02_basic/03_llm/01_llm"}),
    "06_vlm": ("02_basic/03_llm/02_vlm.md", {"sidebar_position": 2, "sidebar_label": "2.3.2 视觉语言模型", "slug": "/02_basic/03_llm/02_vlm"}),
    "07_vlm_voice": ("03_intermediate/01_interactive/01_vlm_voice_dialogue.md", {"sidebar_position": 1, "sidebar_label": "3.1.1 语音对话案例（基于VLM）", "slug": "/03_intermediate/01_interactive/01_vlm_voice_dialogue"}),
    "08_vla_pi0": ("04_advanced/01_embodied_ai/01_vla_pi0.md", {"sidebar_position": 1, "sidebar_label": "4.1.1 视觉-语言-动作模型", "slug": "/04_advanced/01_embodied_ai/01_vla_pi0"}),
    "09_resources": ("05_resources/01_more_resources.md", {"sidebar_position": 1, "sidebar_label": "5. 更多文档链接", "slug": "/05_resources/01_more_resources"}),
    "10_qa": ("06_qa/01_qa.md", {"sidebar_position": 1, "sidebar_label": "6. Q&A", "slug": "/06_qa/01_qa"}),
    "11_misc": ("07_appendix/01_misc.md", {"sidebar_position": 1, "sidebar_label": "杂", "slug": "/07_appendix/01_misc"}),
}

CATEGORIES = {
    "docs/_category_.json": {"label": "S600 应用案例", "position": 1},
    "docs/01_getting_started/_category_.json": {"label": "1. 入门", "position": 2, "link": {"type": "generated-index", "slug": "/01_getting_started", "description": "基础外设使用教程"}},
    "docs/02_basic/_category_.json": {"label": "2. 低阶", "position": 3, "link": {"type": "generated-index", "slug": "/02_basic", "description": "入门级 AI 应用案例"}},
    "docs/02_basic/01_vision/_category_.json": {"label": "2.1 视觉案例", "position": 1, "link": {"type": "generated-index", "slug": "/02_basic/01_vision"}},
    "docs/02_basic/02_audio/_category_.json": {"label": "2.2 语音案例", "position": 2, "link": {"type": "generated-index", "slug": "/02_basic/02_audio"}},
    "docs/02_basic/03_llm/_category_.json": {"label": "2.3 大模型案例", "position": 3, "link": {"type": "generated-index", "slug": "/02_basic/03_llm"}},
    "docs/03_intermediate/_category_.json": {"label": "3. 进阶", "position": 4, "link": {"type": "generated-index", "slug": "/03_intermediate", "description": "交互式 AI 应用案例"}},
    "docs/03_intermediate/01_interactive/_category_.json": {"label": "3.1 交互案例", "position": 1, "link": {"type": "generated-index", "slug": "/03_intermediate/01_interactive"}},
    "docs/04_advanced/_category_.json": {"label": "4. 高阶", "position": 5, "link": {"type": "generated-index", "slug": "/04_advanced", "description": "具身智能应用案例"}},
    "docs/04_advanced/01_embodied_ai/_category_.json": {"label": "4.1 具身智能案例", "position": 1, "link": {"type": "generated-index", "slug": "/04_advanced/01_embodied_ai"}},
    "docs/05_resources/_category_.json": {"label": "5. 更多文档链接", "position": 6, "link": {"type": "generated-index", "slug": "/05_resources"}},
    "docs/06_qa/_category_.json": {"label": "6. Q&A", "position": 7, "link": {"type": "generated-index", "slug": "/06_qa"}},
    "docs/07_appendix/_category_.json": {"label": "附录", "position": 8, "link": {"type": "generated-index", "slug": "/07_appendix"}},
}

HEADING_RE = re.compile(r"^(\d+(?:\.\d+)+)\s+(.+)$|^(\d+)\.\s+(.+)$")
CODE_LINE_RE = re.compile(r"^\d+\s+")


def clean_line(line: str) -> str:
    return line.replace("\x01", "").rstrip("\r\n")


def is_page_marker(line: str) -> bool:
    return bool(re.match(r"^---PAGE\d+---$", line.strip()))


def heading_hashes(num_token: str, is_doc_h1: bool = False) -> str:
    if is_doc_h1:
        return "#"
    token = num_token.rstrip(".")
    if re.match(r"^\d+$", token):
        return "##"
    dots = token.count(".")
    return "#" * min(dots + 1, 6)


def is_code_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if CODE_LINE_RE.match(s):
        return True
    if re.match(r"^\d+$", s):
        return True
    return False


def is_code_continuation(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if is_code_line(s):
        return True
    if s.startswith("beijing.") or s.startswith("http") or ".com/" in s or s.endswith("-"):
        return True
    if re.match(r"^[A-Za-z_./\\|+\-[\](){}:;,=<>%$'\"`~!@#&*°]+$", s):
        return True
    if re.match(r"^\d+\s+\S", s):
        return True
    if "{" in s or "}" in s or "f\"" in s or "print(" in s:
        return True
    if s.startswith('"') or s.startswith("'") or s.endswith('"') or "°)" in s:
        return True
    return False


def escape_mdx_outside_code(text: str) -> str:
    parts = text.split("```")
    out = []
    for idx, part in enumerate(parts):
        if idx % 2 == 0:
            fixed_lines = []
            for line in part.split("\n"):
                s = line.strip()
                if s.startswith("export ") or s.startswith("import "):
                    fixed_lines.append(f"`{s}`")
                else:
                    fixed_lines.append(line.replace("{", "\\{").replace("}", "\\}"))
            part = "\n".join(fixed_lines)
        out.append(part)
    return "```".join(out)


def is_code_label(line: str) -> bool:
    s = line.strip()
    return s == "代码块" or s.startswith("代码块") or s.startswith("代1 码块")


def is_prose_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if is_code_label(s):
        return True
    if HEADING_RE.match(s):
        return True
    if s.startswith("• ") or s.startswith("◦ "):
        return True
    if s in ("---",):
        return True
    if CODE_LINE_RE.match(s):
        return False
    # table-ish / param lines stay prose unless inside code
    return True


def format_section(raw_lines: list[str], doc_h1: str | None = None) -> str:
    lines = [clean_line(x) for x in raw_lines if x.strip() and not is_page_marker(x)]
    out: list[str] = []
    i = 0
    h1_written = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "---":
            out.append("---")
            out.append("")
            i += 1
            continue

        # code block label
        if is_code_label(stripped):
            label = stripped.replace("代1 码块", "代码块")
            if label != "代码块":
                # e.g. 代码块#配置... keep suffix as text
                suffix = label[3:].strip()
                if suffix:
                    out.append(suffix)
                    out.append("")
            else:
                out.append("代码块")
                out.append("")
            i += 1
            code_lines = []
            while i < len(lines):
                cur = lines[i].rstrip()
                cur_s = cur.strip()
                if not cur_s:
                    i += 1
                    if code_lines:
                        break
                    continue
                if is_code_label(cur_s):
                    break
                if HEADING_RE.match(cur_s) and not is_code_line(cur_s):
                    break
                if cur_s.startswith("Q：") or cur_s.startswith("A：") or cur_s.startswith("杂："):
                    break
                if not is_code_continuation(cur_s) and code_lines:
                    break
                code_lines.append(cur)
                i += 1
            if code_lines:
                out.append("```text")
                out.extend(code_lines)
                out.append("```")
                out.append("")
            continue

        hm = HEADING_RE.match(stripped)
        if hm:
            full = stripped
            num = (hm.group(1) or hm.group(3) or "").rstrip(".")
            num_part = re.match(r"^([\d.]+)", stripped)
            num_token = num_part.group(1) if num_part else num
            if doc_h1 and not h1_written and stripped.startswith(doc_h1.rstrip(".")):
                out.append(f"# {full}")
                h1_written = True
            else:
                is_h1 = doc_h1 and not h1_written and stripped.startswith(doc_h1.rstrip("."))
                out.append(f"{heading_hashes(num_token, is_doc_h1=is_h1)} {full}")
            out.append("")
            i += 1
            continue

        if stripped.startswith("• ") or stripped.startswith("◦ "):
            out.append(stripped)
            i += 1
            continue

        # plain paragraph line(s)
        out.append(stripped)
        out.append("")
        i += 1

    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return escape_mdx_outside_code(text)


def frontmatter(meta: dict) -> str:
    rows = ["---"]
    for k, v in meta.items():
        rows.append(f"{k}: {v}")
    rows.append("---")
    return "\n".join(rows)


def write_doc(rel: str, meta: dict, body: str):
    content = frontmatter(meta) + "\n\n" + body
    for base in (DOCS, I18N_DOCS):
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print("Wrote", p)


def write_categories():
    en_labels = {
        "S600 应用案例": "S600 Application Cases",
        "1. 入门": "1. Getting Started",
        "2. 低阶": "2. Basic Cases",
        "2.1 视觉案例": "2.1 Vision Cases",
        "2.2 语音案例": "2.2 Audio Cases",
        "2.3 大模型案例": "2.3 LLM Cases",
        "3. 进阶": "3. Intermediate Cases",
        "3.1 交互案例": "3.1 Interactive Cases",
        "4. 高阶": "4. Advanced Cases",
        "4.1 具身智能案例": "4.1 Embodied AI Cases",
        "5. 更多文档链接": "5. More Resources",
        "6. Q&A": "6. Q&A",
        "附录": "Appendix",
    }
    for rel, data in CATEGORIES.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        en = dict(data)
        if en.get("label") in en_labels:
            en["label"] = en_labels[en["label"]]
        ep = I18N_DOCS / rel.replace("docs/", "")
        ep.parent.mkdir(parents=True, exist_ok=True)
        ep.write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    all_lines = EXTRACT.read_text(encoding="utf-8").splitlines()
    write_categories()

    h1_map = {
        "intro": None,
        "01_usb": "1.1",
        "02_uart": "1.2",
        "03_object_detection": "2.1.1",
        "04_speech_to_text": "2.2.1",
        "05_llm": "2.3.1",
        "06_vlm": "2.3.2",
        "07_vlm_voice": "3.1.1",
        "08_vla_pi0": "4.1.1",
        "09_resources": "5.",
        "10_qa": "6.",
        "12_can": None,
    }

    for key, (start, end) in SECTIONS.items():
        rel, meta = FILE_MAP[key]
        chunk = all_lines[start - 1 : end]
        body = format_section(chunk, doc_h1=h1_map.get(key))
        if key == "intro":
            body = re.sub(r"^(# S600应⽤案例\s*\n+)(S600应⽤案例\s*\n+)+", r"\1", body)
            if not body.startswith("#"):
                body = "# S600应⽤案例\n\n" + body
        if key == "12_can":
            body = re.sub(r"^(# CAN使⽤\s*\n+)(CAN使⽤\s*\n+)+", r"\1", body)
            if not body.startswith("#"):
                body = "# CAN使⽤\n\n" + body
        write_doc(rel, meta, body)


if __name__ == "__main__":
    main()
