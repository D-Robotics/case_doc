#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Docusaurus docs from S600 Word document, preserving original content."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
I18N_DOCS = ROOT / "i18n" / "en" / "docusaurus-plugin-content-docs" / "current"
DEFAULT_DOCX = Path(r"c:\Users\qinglian.li\Downloads\S600应用案例 (1).docx")

CODE_LANGS = {"Shell", "Python", "Bash", "YAML", "JSON", "SQL"}

SECTION_MARKERS = [
    ("01_usb", "1.1 USB 外设使用"),
    ("02_uart", "1.2 UART 使用"),
    ("03_object_detection", "2.1.1 目标检测"),
    ("04_speech_to_text", "2.2.1 语音转文字"),
    ("05_llm", "2.3.1 大语言模型"),
    ("06_vlm", "2.3.2 视觉语言模型"),
    ("07_vlm_voice", "3.1.1 语音对话案例（基于VLM）"),
    ("08_vla_pi0", "4.1.1 视觉-语言-动作模型"),
    ("09_resources", "5. 更多文档链接"),
    ("10_qa", "6. Q&A"),
    ("11_misc", "杂："),
    ("12_can", "CAN 使用"),
]

FILE_MAP = {
    "intro": ("intro.md", {"sidebar_position": 1, "slug": "/intro"}),
    "01_usb": (
        "01_getting_started/01_usb_peripherals.md",
        {"sidebar_position": 1, "sidebar_label": "1.1 USB 外设使用", "slug": "/01_getting_started/01_usb_peripherals"},
    ),
    "02_uart": (
        "01_getting_started/02_uart.md",
        {"sidebar_position": 2, "sidebar_label": "1.2 UART 使用", "slug": "/01_getting_started/02_uart"},
    ),
    "12_can": (
        "01_getting_started/03_can.md",
        {"sidebar_position": 3, "sidebar_label": "CAN 使用", "slug": "/01_getting_started/03_can"},
    ),
    "03_object_detection": (
        "02_basic/01_vision/01_object_detection.md",
        {"sidebar_position": 1, "sidebar_label": "2.1.1 目标检测", "slug": "/02_basic/01_vision/01_object_detection"},
    ),
    "04_speech_to_text": (
        "02_basic/02_audio/01_speech_to_text.md",
        {"sidebar_position": 1, "sidebar_label": "2.2.1 语音转文字", "slug": "/02_basic/02_audio/01_speech_to_text"},
    ),
    "05_llm": (
        "02_basic/03_llm/01_llm.md",
        {"sidebar_position": 1, "sidebar_label": "2.3.1 大语言模型", "slug": "/02_basic/03_llm/01_llm"},
    ),
    "06_vlm": (
        "02_basic/03_llm/02_vlm.md",
        {"sidebar_position": 2, "sidebar_label": "2.3.2 视觉语言模型", "slug": "/02_basic/03_llm/02_vlm"},
    ),
    "07_vlm_voice": (
        "03_intermediate/01_interactive/01_vlm_voice_dialogue.md",
        {"sidebar_position": 1, "sidebar_label": "3.1.1 语音对话案例（基于VLM）", "slug": "/03_intermediate/01_interactive/01_vlm_voice_dialogue"},
    ),
    "08_vla_pi0": (
        "04_advanced/01_embodied_ai/01_vla_pi0.md",
        {"sidebar_position": 1, "sidebar_label": "4.1.1 视觉-语言-动作模型", "slug": "/04_advanced/01_embodied_ai/01_vla_pi0"},
    ),
    "09_resources": (
        "05_resources/01_more_resources.md",
        {"sidebar_position": 1, "sidebar_label": "5. 更多文档链接", "slug": "/05_resources/01_more_resources"},
    ),
    "10_qa": (
        "06_qa/01_qa.md",
        {"sidebar_position": 1, "sidebar_label": "6. Q&A", "slug": "/06_qa/01_qa"},
    ),
    "11_misc": (
        "07_appendix/01_misc.md",
        {"sidebar_position": 1, "sidebar_label": "杂", "slug": "/07_appendix/01_misc"},
    ),
}

CATEGORIES = {
    "docs/_category_.json": {"label": "S600 应用案例", "position": 1},
    "docs/01_getting_started/_category_.json": {
        "label": "1. 入门",
        "position": 2,
        "link": {"type": "generated-index", "slug": "/01_getting_started", "description": "基础外设使用教程"},
    },
    "docs/02_basic/_category_.json": {
        "label": "2. 低阶",
        "position": 3,
        "link": {"type": "generated-index", "slug": "/02_basic", "description": "入门级 AI 应用案例"},
    },
    "docs/02_basic/01_vision/_category_.json": {
        "label": "2.1 视觉案例",
        "position": 1,
        "link": {"type": "generated-index", "slug": "/02_basic/01_vision"},
    },
    "docs/02_basic/02_audio/_category_.json": {
        "label": "2.2 语音案例",
        "position": 2,
        "link": {"type": "generated-index", "slug": "/02_basic/02_audio"},
    },
    "docs/02_basic/03_llm/_category_.json": {
        "label": "2.3 大模型案例",
        "position": 3,
        "link": {"type": "generated-index", "slug": "/02_basic/03_llm"},
    },
    "docs/03_intermediate/_category_.json": {
        "label": "3. 进阶",
        "position": 4,
        "link": {"type": "generated-index", "slug": "/03_intermediate", "description": "交互式 AI 应用案例"},
    },
    "docs/03_intermediate/01_interactive/_category_.json": {
        "label": "3.1 交互案例",
        "position": 1,
        "link": {"type": "generated-index", "slug": "/03_intermediate/01_interactive"},
    },
    "docs/04_advanced/_category_.json": {
        "label": "4. 高阶",
        "position": 5,
        "link": {"type": "generated-index", "slug": "/04_advanced", "description": "具身智能应用案例"},
    },
    "docs/04_advanced/01_embodied_ai/_category_.json": {
        "label": "4.1 具身智能案例",
        "position": 1,
        "link": {"type": "generated-index", "slug": "/04_advanced/01_embodied_ai"},
    },
    "docs/05_resources/_category_.json": {
        "label": "5. 更多文档链接",
        "position": 6,
        "link": {"type": "generated-index", "slug": "/05_resources"},
    },
    "docs/06_qa/_category_.json": {
        "label": "6. Q&A",
        "position": 7,
        "link": {"type": "generated-index", "slug": "/06_qa"},
    },
    "docs/07_appendix/_category_.json": {
        "label": "附录",
        "position": 8,
        "link": {"type": "generated-index", "slug": "/07_appendix"},
    },
}

NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+\S")
SINGLE_NUM_HEADING_RE = re.compile(r"^(\d+)\.\s+\S")
CAN_SUBHEADINGS = {"外设介绍", "使用方法", "示例应用", "控制报文", "反馈报文"}
USB_UART_SUBHEADINGS = {
    "USB 摄像头使用",
    "USB 语音设备使用",
    "总线舵机使用",
    "GM6020 电机使用",
    "核心特征：",
}


def iter_block_items(document: Document):
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def table_to_code_or_md(table: Table) -> str:
    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    if not rows:
        return ""

    if len(rows) == 1 and len(rows[0]) == 1 and rows[0][0]:
        content = rows[0][0].replace("\r\n", "\n").replace("\r", "\n")
        lines = content.split("\n")
        if lines and lines[0] in CODE_LANGS:
            code = "\n".join(lines[1:])
            return f"```text\n{code}\n```"
        return content

    first = rows[0][0] if rows[0] else ""
    if first in CODE_LANGS:
        code = rows[0][1] if len(rows[0]) > 1 else ""
        code = code.replace("\r\n", "\n").replace("\r", "\n")
        return f"```text\n{code}\n```"

    lines = []
    header = rows[0]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in rows[1:]:
        while len(row) < len(header):
            row.append("")
        lines.append("| " + " | ".join(row[: len(header)]) + " |")
    return "\n".join(lines)


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
                    escaped = line.replace("{", "\\{").replace("}", "\\}")
                    escaped = re.sub(r"(?<![\\])<", r"\\<", escaped)
                    fixed_lines.append(escaped)
            part = "\n".join(fixed_lines)
        out.append(part)
    return "```".join(out)


def is_numbered_heading(text: str) -> bool:
    return bool(NUMBERED_HEADING_RE.match(text) or SINGLE_NUM_HEADING_RE.match(text))


def is_subheading(text: str, section_key: str) -> bool:
    s = text.strip()
    if s in CAN_SUBHEADINGS or s in USB_UART_SUBHEADINGS:
        return True
    if section_key in ("01_usb", "02_uart", "12_can") and s.endswith("：") and len(s) <= 8:
        return s == "核心特征："
    return False


def heading_prefix(text: str, section_key: str, is_first: bool) -> str:
    s = text.strip()
    if is_first:
        return f"# {s}"

    m3 = re.match(r"^(\d+\.\d+\.\d+)\s+", s)
    if m3:
        return f"### {s}"

    m2 = re.match(r"^(\d+\.\d+)\s+", s)
    if m2:
        return f"### {s}"

    m1 = re.match(r"^(\d+)\.\s+", s)
    if m1:
        return f"## {s}"

    if is_subheading(s, section_key):
        if section_key == "12_can" and s in CAN_SUBHEADINGS:
            return f"## {s}"
        return f"#### {s}"

    if section_key == "12_can" and s == "CAN 使用":
        return f"# {s}"

    return s


def blocks_to_markdown(blocks: list, section_key: str) -> str:
    out: list[str] = []
    first_heading_done = False

    for kind, content in blocks:
        if kind == "para":
            text = content.strip()
            if not text:
                continue

            if is_numbered_heading(text) or is_subheading(text, section_key) or (
                section_key == "12_can" and text == "CAN 使用" and not first_heading_done
            ):
                line = heading_prefix(text, section_key, is_first=not first_heading_done)
                if line.startswith("#"):
                    first_heading_done = True
                out.append(line)
                out.append("")
            elif text.startswith("Q：") or text.startswith("A："):
                out.append(text)
                out.append("")
            else:
                out.append(text)
                out.append("")
        elif kind == "table":
            md = table_to_code_or_md(content)
            if md:
                out.append(md)
                out.append("")

    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return escape_mdx_outside_code(text)


def split_sections(document: Document) -> dict[str, list]:
    marker_map = {m: k for k, m in SECTION_MARKERS}
    current_key = None
    sections: dict[str, list] = {k: [] for k, _ in SECTION_MARKERS}

    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if not text:
                continue
            if text in marker_map:
                current_key = marker_map[text]
                sections[current_key].append(("para", text))
                continue
            if text in ("1. 入门", "2. 低阶", "2.1 视觉案例", "2.2 语音案例", "2.3 大模型案例", "3. 进阶", "3.1 交互案例", "4. 高阶", "4.1 具身智能案例"):
                continue
            if current_key:
                sections[current_key].append(("para", text))
        elif isinstance(block, Table):
            if current_key:
                sections[current_key].append(("table", block))

    return sections


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
    docx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DOCX
    if not docx_path.exists():
        print("Docx not found:", docx_path)
        sys.exit(1)

    document = Document(str(docx_path))
    sections = split_sections(document)
    write_categories()

    intro_body = "# S600 应用案例\n"
    write_doc(*FILE_MAP["intro"], intro_body)

    for key, _ in SECTION_MARKERS:
        rel, meta = FILE_MAP[key]
        body = blocks_to_markdown(sections[key], key)
        write_doc(rel, meta, body)


if __name__ == "__main__":
    main()
