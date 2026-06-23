#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pdfplumber
import re
import sys

pdf_path = r'c:\Users\qinglian.li\Downloads\S600应用案例.pdf'
out_path = r'd:\Awork\A_docs\samples_doc\pdf_extract.txt'

all_text = []
with pdfplumber.open(pdf_path) as pdf:
    print(f'Pages: {len(pdf.pages)}', file=sys.stderr)
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ''
        all_text.append(f'---PAGE{i+1}---\n' + text)

full = '\n'.join(all_text)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(full)

print(f'Written {len(full)} chars to {out_path}', file=sys.stderr)

# Print heading-like lines
for line in full.split('\n'):
    line = line.strip()
    if re.match(r'^(\d+\.)+\d*\s+\S', line) or re.match(r'^[1-6]\.\s', line):
        print(line[:150])
