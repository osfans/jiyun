#!/usr/bin/env python3
"""Merge all NN.md files into one HTML, then convert to PDF via WeasyPrint."""

import glob
import os
import re
from datetime import datetime, timezone, timedelta
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
    converted = md.convert(text)
    # Replace [字] with <ins>字</ins>
    converted = re.sub(r'\[([^\]]+)\]', r'<ins>\1</ins>', converted)
    # Convert (IDS) to superscript (IDS starts with ⿰-⿻)
    converted = re.sub(r'\(([⿰-⿿〾][^\)]+)\)', r'<sup class="ids">\1</sup>', converted)
    # Other () becomes <del>
    converted = re.sub(r'\(([^\)]+)\)', r'<del>\1</del>', converted)
    body_parts.append(converted)
    md.reset()

body = "\n".join(body_parts)

# ── 3. Wrap in full HTML with CJK-friendly CSS ───────────────────────────────
tz_cst = timezone(timedelta(hours=8))
created = datetime.now(tz_cst).strftime("%Y-%m-%dT%H:%M:%S+08:00")
html = f"""<!DOCTYPE html>
<html lang="kr">
<head>
<meta charset="utf-8">
<meta name="author" content="https://github.com/osfans/jiyun">
<meta name="dcterms.created" content="{created}">
<title>集韻</title>
<style>
  @page {{
    size: A4;
    margin: 1mm;
  }}
  body {{
    font-family: "Noto Sans CJK KR",
                 "Plangothic P1", "遍黑体P1",
                 "Plangothic P2", "遍黑体P2",
                 sans-serif;
    font-weight: normal;
    font-size: 32pt;
    line-height: 1.1;
  }}
  h1, h2, h3 {{
    font-weight: normal;
    margin-top: 0.4em;
    margin-bottom: 0.1em;
    padding-bottom: 0.1em;
    border-bottom: 0.5px solid #333;
  }}
  h1 {{
    font-size: 1.2em;
    page-break-before: always;
  }}
  h1:first-of-type {{
    page-break-before: avoid;
  }}
  h2 {{
    font-size: 1em;
  }}
  h2:first-of-type::before {{
    content: "";
  }}
  h2::before {{
    content: "○";
  }}
  h3 {{
    font-size: 0.7em;
    display: inline-block;
    background-color: #f0f0f0;
    border: 0.5px solid black;
    padding: 0.1em;
  }}
  p {{
    margin: 0;
  }}
  del {{
    color: #bbb;
  }}
  code {{
    font-family: "Noto Sans CJK KR", "Noto Sans",
                 "Plangothic P1", "遍黑体P1",
                 "Plangothic P2", "遍黑体P2",
                 sans-serif;
    font-size: 0.7em;
    color: #8A511C;
  }}
  sup.ids {{
    font-size: 0.6em;
    color: #666;
    vertical-align: super;
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
