#!/usr/bin/env python3
"""Merge all NN.md files into one HTML, then convert to PDF via WeasyPrint."""

import glob
import os
import re
import markdown
import weasyprint

# ── 1. Collect files in order ────────────────────────────────────────────────
md_files = sorted(glob.glob("[0-9][0-9].md"))
if not md_files:
    raise SystemExit("No NN.md files found.")

print(f"Found {len(md_files)} files: {md_files}")

# ── 2. Render Markdown → HTML body ───────────────────────────────────────────
md = markdown.Markdown(extensions=["toc", "tables"])
body_parts = []
for path in md_files:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # Process h3: only keep content before first space
    text = re.sub(r'^### ([^ ]+) .*$', r'### \1', text, flags=re.MULTILINE)
    # Replace [字] with <ins>字</ins> and (字) with <del>字</del>
    converted = md.convert(text)
    converted = re.sub(r'\[([^\]]+)\]', r'<ins>\1</ins>', converted)
    converted = re.sub(r'\(([^\)]+)\)', r'<del>\1</del>', converted)
    body_parts.append(converted)
    md.reset()

body = "\n".join(body_parts)

# ── 3. Wrap in full HTML with CJK-friendly CSS ───────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>集韻</title>
<style>
  @page {{
    size: A4;
    margin: 10mm;
  }}
  body {{
    font-family: "Noto Sans CJK SC", "Noto Sans SC",
                 "Plangothic P1", "遍黑体P1",
                 "Plangothic P2", "遍黑体P2",
                 sans-serif;
    font-size: 12pt;
    line-height: 1.0;
  }}
  h1 {{
    font-size: 18pt;
    font-weight: normal;
    page-break-before: always;
    border-bottom: 0.5px solid #333;
    padding-bottom: 4pt;
  }}
  h1:first-of-type {{
    page-break-before: avoid;
  }}
  h2 {{
    font-size: 14pt;
    font-weight: normal;
    padding-bottom: 0.1em;
    margin-bottom: 0.1em;
    border-bottom: 0.5px solid #333;
  }}
  h3 {{
    font-size: 8pt;
    font-weight: normal;
    display: inline-block;
    background-color: #f0f0f0;
    border: 0.5px solid #000;
    padding: 2pt;
    margin-top: 0.5em;
    margin-bottom: 0.1em;
  }}
  p {{
    margin: 0;
  }}
  del {{
    color: #bbb;
  }}
  code {{
    font-family: "Noto Sans CJK SC", "Noto Sans SC",
                 "Plangothic P1", "遍黑体P1",
                 "Plangothic P2", "遍黑体P2",
                 sans-serif;
    font-size: 8pt;
  }}
  code::before {{
    content: "（";
  }}
  code::after {{
    content: "）";
  }}
</style>
</head>
<body>
{body}
</body>
</html>
"""

# ── 4. Write HTML ─────────────────────────────────────────────────────────────
html_path = "jiyun.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML written → {html_path}")

# ── 5. Convert to PDF ─────────────────────────────────────────────────────────
pdf_path = "jiyun.pdf"
print("Converting to PDF (this may take a while)…")
weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
print(f"PDF written  → {pdf_path}")
