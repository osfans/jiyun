#!/usr/bin/env python3
"""
gen_search.py — Generate a static search HTML page for 集韻 (Jiyun).

The page embeds all data as JSON and can be published to GitHub Pages.
Users can search by:
  - 韻 (yun / rhyme group)
  - 反切 (fanqie / spelling)
  - 字頭 (headword / character)
  - 解釋 (gloss / explanation)
"""

import glob
import json
import re
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Parse Markdown files into structured records
# ─────────────────────────────────────────────────────────────────────────────

def parse_md_files(pattern: str = "[0-9][0-9].md") -> list[dict]:
    """
    Return a flat list of entry dicts:
      {
        "yun":     "東第一",          # rhyme group name (h2 without backtick)
        "fanqie":  "都籠切",          # fanqie spelling (h3 first token)
        "chars":   "東",             # all headword chars on this entry line
        "gloss":   "許慎說文動也…",   # explanation text (inside first backtick pair)
        "vol":     "卷之一",          # volume label
        "sheng":   "平聲一",         # tone label
      }
    """
    records: list[dict] = []
    md_files = sorted(glob.glob(pattern))
    if not md_files:
        raise SystemExit(f"No files matching '{pattern}' found.")

    for path in md_files:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()

        sheng = ""     # e.g. 平聲
        yun = ""       # e.g. 東
        fanqie = ""    # e.g. 都籠切

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            # ── Volume / tone heading  (# 集韻卷之一 平聲一)
            if line.startswith("# "):
                m = re.search(r"(\S+聲)", line)
                if m:
                    sheng = m.group(1)[:2]  # keep only first 2 chars e.g. 平聲
                continue

            # ── Rhyme-group heading  (## 東第一`都籠切獨用`)
            if line.startswith("## "):
                # strip leading ## and any backtick annotation, keep only first char
                yun_raw = line[3:].strip()
                yun_full = re.sub(r"`.*`", "", yun_raw).strip()
                yun = yun_full[0] if yun_full else ""
                continue

            # ── Fanqie / small-rhyme heading  (### 都籠切 文二十五)
            if line.startswith("### "):
                # first token before space is the fanqie
                fanqie = line[4:].split()[0]
                continue

            # ── Entry line: chars`gloss`
            # A line that contains at least one backtick, does NOT start with #,
            # and belongs to a proper small-rhyme section (fanqie must be set).
            if "`" in line and not line.startswith("#") and fanqie:
                # Split on the FIRST backtick to separate headword chars from gloss
                parts = line.split("`", 2)
                if len(parts) < 3:
                    continue  # malformed — skip

                chars_raw = parts[0].strip()
                gloss_raw = parts[1].strip()

                # Remove parenthesised IDS annotations for length check only
                chars_clean = re.sub(r"\([^)]*\)", "", chars_raw).strip()

                # Skip if empty or looks like continuous prose (> 10 real chars)
                if not chars_clean or len(chars_clean) > 10:
                    continue

                records.append({
                    "y": yun,
                    "f": fanqie,
                    "s": sheng[:1] if sheng else "",  # single tone char e.g. 平
                    "d": chars_raw,     # headword with IDS annotations (for display; strip parens for search)
                    "g": gloss_raw,
                })

    return records


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Build the static HTML page
# ─────────────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="kr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>集韻檢索</title>
<style>
/* ── Reset & Base ── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --bg:      #f0f4fd;
  --surface: #f7f9ff;
  --border:  #9ab3d4;
  --accent:  #1e3a6e;
  --accent2: #2e5fa3;
  --text:    #0e1a2c;
  --muted:   #526070;
  --tag-bg:  #dce6f5;
  --hi:      #ffe066;
  --radius:  6px;
  --shadow:  0 2px 8px rgba(0,0,0,.10);
}}
body {{
  font-family: "Noto Serif CJK TC", "Source Han Serif TC",
               "Noto Serif SC", "Source Han Serif SC",
               "FZSong", serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}}

/* ── Header ── */
header {{
  background: var(--accent);
  color: #fff;
  padding: 1.2rem 1.5rem .9rem;
  display: flex;
  align-items: baseline;
  gap: 1rem;
  flex-wrap: wrap;
}}
header h1 {{ font-size: 1.6rem; letter-spacing: .1em; }}
header p  {{ font-size: .85rem; opacity: .8; }}

/* ── Search bar ── */
#search-bar {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: .8rem 1.5rem;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow);
}}
.search-row {{
  display: flex;
  gap: .5rem;
  flex-wrap: wrap;
  align-items: center;
}}
.search-group {{
  display: flex;
  align-items: center;
  gap: .3rem;
  flex: 1 1 160px;
}}
.search-group label {{
  font-size: .8rem;
  color: var(--muted);
  white-space: nowrap;
  min-width: 2.5em;
}}
.search-group input {{
  flex: 1;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: .35rem .55rem;
  font-size: 1rem;
  font-family: inherit;
  background: #fff;
  color: var(--text);
  outline: none;
  transition: border-color .15s;
}}
.search-group input:focus {{ border-color: var(--accent2); }}
#btn-clear {{
  padding: .35rem .9rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: #fff;
  color: var(--accent);
  cursor: pointer;
  font-size: .85rem;
  font-family: inherit;
  transition: background .15s;
  white-space: nowrap;
}}
#btn-clear:hover {{ background: var(--tag-bg); }}

/* ── Status bar ── */
#status {{
  font-size: .78rem;
  color: var(--muted);
  padding: .35rem 1.5rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
}}

/* ── Results ── */
#results {{
  padding: .8rem 1.5rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
}}

/* Grid of cards */
.result-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: .75rem;
}}

/* Single entry card */
.entry {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: .7rem .9rem .65rem;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: .35rem;
  transition: box-shadow .15s;
}}
.entry:hover {{ box-shadow: 0 4px 14px rgba(0,0,0,.15); }}

/* Top row: headword + fanqie tag */
.entry-top {{
  display: flex;
  align-items: baseline;
  gap: .5rem;
  flex-wrap: wrap;
}}
.entry-chars {{
  font-size: 1.55rem;
  font-weight: bold;
  line-height: 1.15;
  word-break: break-all;
  color: var(--accent);
}}
.entry-chars sup.ids {{
  font-size: .85rem;
  font-weight: normal;
  color: var(--muted);
  vertical-align: super;
  letter-spacing: 0;
}}
.tag {{
  display: inline-block;
  font-size: .7rem;
  padding: .1em .45em;
  border-radius: 3px;
  background: var(--tag-bg);
  color: var(--accent);
  border: 1px solid var(--border);
  white-space: nowrap;
  line-height: 1.5;
}}
.tag.fanqie {{ background: #ddf0e8; border-color: #7abda0; color: #1a5038; }}

/* Breadcrumb row */
.entry-meta {{
  font-size: .72rem;
  color: var(--muted);
  display: flex;
  gap: .3rem;
  flex-wrap: wrap;
  align-items: center;
}}
.entry-meta span + span::before {{
  content: " › ";
  opacity: .5;
}}

/* Gloss */
.entry-gloss {{
  font-size: .85rem;
  line-height: 1.55;
  color: var(--text);
  word-break: break-all;
}}

/* Highlight mark */
mark {{
  background: var(--hi);
  color: inherit;
  border-radius: 2px;
  padding: 0 1px;
}}

/* Empty-state */
.empty-state {{
  text-align: center;
  padding: 4rem 1rem;
  color: var(--muted);
  font-size: 1rem;
}}
.empty-state p {{ margin-top: .5rem; font-size: .85rem; }}

/* Pagination */
#pagination {{
  display: flex;
  justify-content: center;
  gap: .4rem;
  padding: 1rem 0 0;
  flex-wrap: wrap;
}}
.page-btn {{
  padding: .3rem .7rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: #fff;
  color: var(--accent);
  cursor: pointer;
  font-family: inherit;
  font-size: .82rem;
  transition: background .12s;
}}
.page-btn:hover {{ background: var(--tag-bg); }}
.page-btn.active {{
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}}
.page-btn:disabled {{
  opacity: .4;
  cursor: default;
}}

/* Responsive */
@media (max-width: 500px) {{
  .search-group {{ flex: 1 1 140px; }}
  .result-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<header>
  <h1>集韻檢索</h1>
  <p>共 {total} 條字目 · {total_yunbu} 韻部 · {total_fanqie} 小韻</p>
</header>

<div id="search-bar">
  <div class="search-row">
    <div class="search-group">
      <label for="q-yun">韻部</label>
      <input id="q-yun" list="yun-list" placeholder="東…" autocomplete="off" spellcheck="false">
      <datalist id="yun-list">{yun_options}</datalist>
    </div>
    <div class="search-group">
      <label for="q-fc">反切</label>
      <input id="q-fc" type="search" placeholder="都籠切…" autocomplete="off" spellcheck="false">
    </div>
    <div class="search-group">
      <label for="q-ch">字頭</label>
      <input id="q-ch" type="search" placeholder="東…" autocomplete="off" spellcheck="false">
    </div>
    <div class="search-group">
      <label for="q-gl">解釋</label>
      <input id="q-gl" type="search" placeholder="說文…" autocomplete="off" spellcheck="false">
    </div>
    <button id="btn-clear">清空</button>
  </div>
</div>

<div id="status"></div>

<div id="results">
  <div class="empty-state" id="empty-state">
    <p>在上方輸入關鍵詞開始檢索</p>
    <p>可同時在多個字段篩選</p>
  </div>
  <div class="result-grid" id="grid"></div>
  <div id="pagination"></div>
</div>

<script>
// ── Embedded data ──────────────────────────────────────────────────────────
const DATA = {data_json};

// ── Sync datalist selection to search ─────────────────────────────────────
// The datalist fires 'input' just like a typed value, no extra handling needed.

// ── Constants ──────────────────────────────────────────────────────────────
const PAGE_SIZE = 60;

// ── State ──────────────────────────────────────────────────────────────────
let filtered = [];
let currentPage = 1;

// ── Elements ───────────────────────────────────────────────────────────────
const qYun  = document.getElementById("q-yun");
const qFc   = document.getElementById("q-fc");
const qCh   = document.getElementById("q-ch");
const qGl   = document.getElementById("q-gl");
const status  = document.getElementById("status");
const grid    = document.getElementById("grid");
const paging  = document.getElementById("pagination");
const empty   = document.getElementById("empty-state");
const btnClear = document.getElementById("btn-clear");

// ── Helpers ─────────────────────────────────────────────────────────────────
/**
 * Escape a string for use in RegExp.
 */
function escRe(s) {{
  return s.replace(/[.*+?^${{}}()|[\\]\\\\]/g, "\\\\$&");
}}

/**
 * Highlight all occurrences of `term` inside `text` (HTML-safe).
 */
function highlight(text, term) {{
  if (!term) return escHtml(text);
  const re = new RegExp("(" + escRe(term) + ")", "g");
  return escHtml(text).replace(
    new RegExp("(" + escRe(escHtml(term)) + ")", "g"),
    "<mark>$1</mark>"
  );
}}

function escHtml(s) {{
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}}

// ── Search ──────────────────────────────────────────────────────────────────
function doSearch() {{
  const vYun = qYun.value.trim();
  const vFc  = qFc.value.trim();
  const vCh  = qCh.value.trim();
  const vGl  = qGl.value.trim();

  const allEmpty = !vYun && !vFc && !vCh && !vGl;

  if (allEmpty) {{
    filtered = [];
    currentPage = 1;
    render();
    return;
  }}

  // Build regex filters (case-insensitive where relevant)
  const rYun = vYun ? new RegExp(escRe(vYun)) : null;
  const rFc  = vFc  ? new RegExp(escRe(vFc))  : null;
  const rCh  = vCh  ? new RegExp(escRe(vCh))  : null;
  const rGl  = vGl  ? new RegExp(escRe(vGl))  : null;

  filtered = DATA.filter(d =>
    (!rYun || rYun.test(d.y)) &&
    (!rFc  || rFc.test(d.f))  &&
    (!rCh  || rCh.test(d.d.replace(/\([^)]*\)/g, "")))  &&
    (!rGl  || rGl.test(d.g))
  );

  currentPage = 1;
  render();
}}

// ── Render ───────────────────────────────────────────────────────────────────
function render() {{
  const vYun = qYun.value.trim();
  const vFc  = qFc.value.trim();
  const vCh  = qCh.value.trim();
  const vGl  = qGl.value.trim();

  const allEmpty = !vYun && !vFc && !vCh && !vGl;

  if (allEmpty) {{
    grid.innerHTML = "";
    paging.innerHTML = "";
    status.textContent = "";
    empty.style.display = "";
    return;
  }}

  empty.style.display = "none";

  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  currentPage = Math.min(currentPage, totalPages);

  const start = (currentPage - 1) * PAGE_SIZE;
  const slice = filtered.slice(start, start + PAGE_SIZE);

  status.textContent =
    `找到 ${{total}} 條結果` +
    (totalPages > 1 ? `，第 ${{currentPage}} / ${{totalPages}} 頁，共 ${{totalPages}} 頁` : "");

  // Cards
  grid.innerHTML = slice.map(d => {{
    // Convert IDS annotations (parenthesised) to superscript for display
    const cdispHtml = escHtml(d.d)
      .replace(/[(]([^)]+)[)]/g, '<sup class="ids">$1</sup>');
    // Highlight matched chars (only outside tags)
    const charsHtml = vCh
      ? cdispHtml.replace(
          new RegExp("(" + escRe(escHtml(vCh)) + ")", "g"),
          "<mark>$1</mark>"
        )
      : cdispHtml;
    const glossHtml = highlight(d.g, vGl);
    const yunHtml   = highlight(d.y, vYun);
    const fcHtml    = highlight(d.f, vFc);
    return `
    <div class="entry">
      <div class="entry-top">
        <span class="entry-chars">${{charsHtml}}</span>
        <span class="tag fanqie">${{fcHtml}}</span>
        <span class="tag">${{yunHtml}}韻</span>
        ${{d.s ? `<span class="tag">${{escHtml(d.s)}}聲</span>` : ""}}
      </div>
      <div class="entry-gloss">${{glossHtml}}</div>
    </div>`;
  }}).join("");

  // Pagination
  renderPaging(totalPages);
}}

function renderPaging(totalPages) {{
  if (totalPages <= 1) {{ paging.innerHTML = ""; return; }}

  const buttons = [];

  const addBtn = (label, page, disabled, active) => {{
    buttons.push(
      `<button class="page-btn${{active ? " active" : ""}}"
               ${{disabled ? "disabled" : ""}}
               onclick="goPage(${{page}})">${{label}}</button>`
    );
  }};

  addBtn("«", 1, currentPage === 1, false);
  addBtn("‹", currentPage - 1, currentPage === 1, false);

  // Window of pages
  const WING = 2;
  let lo = Math.max(1, currentPage - WING);
  let hi = Math.min(totalPages, currentPage + WING);
  if (lo > 1) buttons.push('<span style="align-self:center;color:var(--muted)">…</span>');
  for (let p = lo; p <= hi; p++) {{
    addBtn(p, p, false, p === currentPage);
  }}
  if (hi < totalPages) buttons.push('<span style="align-self:center;color:var(--muted)">…</span>');

  addBtn("›", currentPage + 1, currentPage === totalPages, false);
  addBtn("»", totalPages, currentPage === totalPages, false);

  paging.innerHTML = buttons.join("");
}}

function goPage(p) {{
  currentPage = p;
  render();
  window.scrollTo({{ top: 0, behavior: "smooth" }});
}}

// ── Event listeners ─────────────────────────────────────────────────────────
[qYun, qFc, qCh, qGl].forEach(el => {{
  el.addEventListener("input", doSearch);
}});

btnClear.addEventListener("click", () => {{
  qYun.value = qFc.value = qCh.value = qGl.value = "";
  doSearch();
}});

// Support URL hash for sharing simple queries, e.g. #chars=東
(function loadFromHash() {{
  const hash = location.hash.slice(1);
  if (!hash) return;
  const params = new URLSearchParams(hash);
  if (params.get("yun"))  qYun.value = params.get("yun");
  if (params.get("fc"))   qFc.value  = params.get("fc");
  if (params.get("chars")) qCh.value = params.get("chars");
  if (params.get("gl"))   qGl.value  = params.get("gl");
  if (params.get("yun") || params.get("fc") || params.get("chars") || params.get("gl")) {{
    doSearch();
  }}
}})();
</script>
</body>
</html>
"""


def build_html(records: list[dict], output: str = "index.html") -> None:
    """Serialize records to JSON and inject into the HTML template."""
    # Collect statistics for the subtitle
    # Preserve insertion order (dict.fromkeys keeps first-seen order)
    yunbu_ordered = list(dict.fromkeys(r["y"] for r in records if r["y"]))
    yunbu_set = set(yunbu_ordered)
    fanqie_set = set((r["y"], r["f"]) for r in records if r["f"])

    # Count total headword characters (each char in `chars` is one entry)
    total_chars = sum(len(re.sub(r"\([^)]*\)", "", r["d"])) for r in records)

    data_json = json.dumps(records, ensure_ascii=False, separators=(",", ":"))

    # Build <option> elements for the yun datalist
    yun_options = "".join(f'<option value="{y}">' for y in yunbu_ordered)

    html = HTML_TEMPLATE.format(
        total=total_chars,
        total_yunbu=len(yunbu_set),
        total_fanqie=len(fanqie_set),
        data_json=data_json,
        yun_options=yun_options,
    )

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = len(html.encode("utf-8")) / 1024
    print(f"Written → {output}  ({size_kb:.0f} KB, {total_chars} chars in {len(records)} entries)")


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a static search page for 集韻."
    )
    parser.add_argument(
        "-o", "--output", default="index.html",
        help="Output HTML file (default: index.html)"
    )
    parser.add_argument(
        "--pattern", default="[0-9][0-9].md",
        help="Glob pattern for source Markdown files"
    )
    args = parser.parse_args()

    print("Parsing Markdown files…")
    records = parse_md_files(args.pattern)
    print(f"Parsed {len(records)} entries.")

    print("Building HTML…")
    build_html(records, args.output)
    print("Done.")
