"""Build the Weiss reader, Dor Dor ve-Dorshav: docs/part-NN.html per translated part, docs/index.html, docs/work.json.

  py -3.13 -I scripts/build_site.py

Hebrew: checked pages data/he/vV_FF_PP.txt (Daat page files), line for line as printed, with marks:
  '# text'   a heading (book, chapter, chapter summary), one unit each
  blank line a paragraph break (paragraphs run on across pages)
  '---'      the footnote rule: the lines after it are the page's footnotes, each starting 'N)'
English: data/en/part-NN.en.txt, one block per Hebrew unit (headings and paragraphs, in order), blank lines between;
data/en/part-NN.fn.en.txt, one block per footnote ('N) ...'), in order; ⚠n uncertain, explained in part-NN.notes.json.
Page starts are kept as {page:FILESTEM} in the text and shown as 'p. N' boxes that link to the Daat PDF page and carry
a page image for the shared scan panel (docs/scans/<stem>.jpg, made by scripts/make_scans.py)."""
import html
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
e = html.escape
DAAT = "https://www.daat.ac.il/daat/vl/dorvolume{v}/dorvolume{v}{f}.pdf#page={p}"
TOK = re.compile(r"\{page:(v(\d)_(\d\d)_(\d\d))\}")

# part number -> (title, subtitle, list of page files)
PARTS = {
    1: ("Book One, chapter 1: The first traces of oral tradition",
        "The opening of the work: why the Oral Law must be studied historically, and what the earliest sources show",
        ["v1_02_01", "v1_02_02", "v1_02_03"]),
}
PRINTED = {}  # page file -> printed page number (filled from the checked pages' first line '@ N', if any)

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:ital,wght@0,400;0,600;1,400&family=Noto+Serif+Hebrew:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<link rel="stylesheet" href="/assets/os.css">
<script src="/assets/os.js" defer></script>
</head>
<body>
"""


def read_blocks(path):
    blocks, cur = [], []
    for raw in path.read_text(encoding="utf-8").split("\n"):
        line = raw.strip()
        if line:
            cur.append(line)
        elif cur:
            blocks.append(" ".join(cur)); cur = []
    if cur:
        blocks.append(" ".join(cur))
    return blocks


def parse_pages(stems):
    """Units (('h'|'p', text)) and footnotes ((page stem, number, text)) of a run of checked pages."""
    units, notes, para = [], [], []
    call = re.compile(r"(?<=[א-ת׳״'\")])\s?(\d{1,2})\)")
    nonlocal_seq = [0]  # the print numbers notes per page; the reader numbers them through the part
    for stem in stems:
        local = {}
        lines = (ROOT / "data" / "he" / f"{stem}.txt").read_text(encoding="utf-8").splitlines()
        if lines and lines[0].startswith("@"):
            PRINTED[stem] = lines[0][1:].strip(); lines = lines[1:]
        body, fn = lines, []
        if "---" in [l.strip() for l in lines]:
            k = [l.strip() for l in lines].index("---")
            body, fn = lines[:k], lines[k + 1:]
        first = True
        for l in body:
            s = l.strip()
            def num(m):
                nonlocal_seq[0] += 1; local[m.group(1)] = nonlocal_seq[0]
                return f"⟦{nonlocal_seq[0]}⟧"
            s = call.sub(num, s)
            if first and s:
                s = f"{{page:{stem}}} " + s
                first = False
            if not s:
                if para:
                    units.append(("p", " ".join(para))); para = []
            elif s.lstrip("{}page:v_0123456789 ").startswith("#"):
                if para:
                    units.append(("p", " ".join(para))); para = []
                tok = re.match(r"(\{page:[^}]+\}\s*)?#\s*(.*)", s)
                units.append(("h", (tok.group(1) or "") + tok.group(2)))
            else:
                para.append(s)
        cur = None
        for l in fn:
            s = l.strip()
            m = re.match(r"^(\d+)\)\s*(.*)", s)
            if m:
                if m.group(1) not in local:
                    sys.exit(f"{stem}: footnote {m.group(1)} has no call in the text")
                cur = [stem, str(local[m.group(1)]), m.group(2)]; notes.append(cur)
            elif cur and s:
                cur[2] += " " + s
    if para:
        units.append(("p", " ".join(para)))
    return units, notes


def page_label(stem):
    return PRINTED.get(stem) or str(int(stem.split("_")[2]))


def fmt_he(text, stem_for_calls):
    out = e(text, quote=False)
    def box(m):
        stem, v, f, p = m.group(1), m.group(2), m.group(3), int(m.group(4))
        return (f'<a class="scanlink" href="{DAAT.format(v=v, f=f, p=p)}" data-scan-img="scans/{stem}.jpg" '
                f'data-scan-label="p. {page_label(stem)}" title="Page {page_label(stem)} (Daat scan)">p. {page_label(stem)}</a>')
    out = TOK.sub(box, out)
    # footnote calls, renumbered through the part by parse_pages as ⟦n⟧
    return re.sub(r"⟦(\d+)⟧", lambda m: f'<sup class="fn"><a href="#fn-{m.group(1)}">{m.group(1)}</a></sup>', out)


def fmt_en(text):
    text = e(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]", r'<span class="ref">[\1]</span>', text)
    text = re.sub(r"\{(\d{1,2})\}", r'<sup class="fn" id="fnref-\1"><a href="#fn-\1">\1</a></sup>', text)
    return re.sub(r"\s*⚠(\d+)", r' <a class="warn" href="#n\1" id="r\1" title="uncertain rendering">⚠\1</a>', text)


def part_page(num):
    title, subtitle, stems = PARTS[num]
    units, notes = parse_pages(stems)
    en = read_blocks(ROOT / "data" / "en" / f"part-{num:02d}.en.txt")
    fn_en = read_blocks(ROOT / "data" / "en" / f"part-{num:02d}.fn.en.txt")
    warn = json.loads((ROOT / "data" / "en" / f"part-{num:02d}.notes.json").read_text(encoding="utf-8"))
    if len(units) != len(en) or len(notes) != len(fn_en):
        sys.exit(f"part {num}: Hebrew {len(units)} units / {len(notes)} footnotes, English {len(en)} / {len(fn_en)}")
    for stem in stems:
        if not (DOCS / "scans" / f"{stem}.jpg").exists():
            sys.exit(f"part {num}: no page image docs/scans/{stem}.jpg; run scripts/make_scans.py")
    rows, cur = [], None
    for i, ((kind, h), x) in enumerate(zip(units, en), 1):
        cls = "row head" if kind == "h" else "row"
        starts = [m.group(1) for m in TOK.finditer(h)]
        pg = ([cur] if cur and not h.startswith("{page:") else []) + starts
        cur = starts[-1] if starts else cur
        nums = [page_label(x) for x in pg]
        lab = f"row {i}, " + (f"p. {nums[0]}" if len(nums) == 1 else f"pp. {nums[0]}–{nums[-1]}")
        rows.append(f'<div class="{cls}" id="u{i}" data-label="{lab}"><a class="ln" href="#u{i}">{i}</a>'
                    f'<p class="en">{fmt_en(x)}</p><p class="he" lang="he" dir="rtl">{fmt_he(h, None)}</p></div>')
    fnrows = []
    for (stem, n, h), x in zip(notes, fn_en):
        x = re.sub(r"^\d+\)\s*", "", x)
        fnrows.append(f'<div class="row fnrow" id="fn-{n}" data-label="note {n} (p. {page_label(stem)})"><a class="ln back" href="#fnref-{n}" title="Back to the text">{n}<span aria-hidden="true"> ↩</span></a>'
                      f'<p class="en">{fmt_en(x)} <a class="fnback" href="#fnref-{n}">↩ back to the text</a></p><p class="he" lang="he" dir="rtl">{e(h, quote=False)}'
                      f' <span class="fnpage">(p. {page_label(stem)})</span></p></div>')
    marks = set(re.findall(r"⚠(\d+)", " ".join(en + fn_en)))
    if marks - set(warn):
        sys.exit(f"part {num}: notes missing for ⚠{sorted(marks - set(warn))}")
    warn_rows = "\n".join(f'<li id="n{k}"><a href="#r{k}">⚠{k}</a> <span lang="he" dir="rtl" class="he-inline">{e(v["he"])}</span>'
                          f' — {e(v["note"], quote=False)}</li>' for k, v in warn.items())
    pages = ", ".join(page_label(s) for s in stems)
    page = HEAD.format(title=f"{e(title)} — Weiss, Dor Dor ve-Dorshav") + f"""<header class="chapter">
<nav class="crumb" aria-label="Parts"><span><a href="index.html">All parts</a> · Part {num}</span></nav>
<p class="title-he" lang="he" dir="rtl">דור דור ודורשיו</p>
<h1>{e(title)}</h1>
<p class="sub">{e(subtitle)}</p>
<details class="about"><summary>About this text</summary>
<p class="meta">Vol. 1, pp. {pages} (Vienna 1871). One row is one heading or one paragraph of the print; Weiss's own
footnotes follow the text, numbered through the part (the print numbers them page by page). Boxes marked "p. N" in the Hebrew show where a printed page begins; they link to the page in
the Daat scan, and the <b>Scan</b> button at the top shows it beside the text. References in
<span class="ref">[gray brackets]</span> are the translator's. <a class="warn" href="#notes">⚠</a> marks an uncertain
rendering. The Hebrew was checked against the scan line by line; spelling and abbreviations are as printed.</p>
</details>
</header>
<main class="prose">
{chr(10).join(rows)}
<h2 class="fnhead">Weiss's notes</h2>
{chr(10).join(fnrows)}
</main>
<footer id="notes">
<h2>Uncertain renderings</h2>
<ul class="notes">
{warn_rows}
</ul>
<nav class="crumb foot" aria-label="Parts"><span><a href="index.html">All parts</a></span></nav>
</footer>
</body>
</html>
"""
    (DOCS / f"part-{num:02d}.html").write_text(page, encoding="utf-8")
    print(f"wrote docs/part-{num:02d}.html: {len(units)} units, {len(notes)} footnotes")
    return len(units)


def index_page(counts):
    rows = "\n".join(f'<tr class="done"><td><a href="part-{k:02d}.html">{k}</a></td><td><a href="part-{k:02d}.html">{e(PARTS[k][0])}</a>: '
                     f'{e(PARTS[k][1])}</td><td>{", ".join(page_label(s) for s in PARTS[k][2])}</td><td>{counts[k]} units</td></tr>'
                     for k in sorted(PARTS))
    page = HEAD.format(title="Weiss, Dor Dor ve-Dorshav: Hebrew and English") + f"""<header>
<h1>I. H. Weiss, <i>Dor Dor ve-Dorshav</i></h1>
<p class="sub">The history of the Oral Law, with an English translation paragraph by paragraph · <span lang="he" dir="rtl">דור דור ודורשיו</span></p>
<p class="meta">Isaac Hirsch Weiss (1815–1905), teacher of Talmud at the Vienna Bet ha-Midrash, wrote the first full
history of the Oral Law in Hebrew, from the Bible to the end of the sixteenth century, in five volumes (Vienna 1871–91).
It is still a standard work, and it has no English translation.</p>
</header>
<article>
<h2>Parts</h2>
<div class="tablewrap">
<table>
<tr><th>Part</th><th>Contents</th><th>Pages</th><th>Status</th></tr>
{rows}
<tr><td>2–</td><td>The rest of vol. 1 and vols. 2–5</td><td></td><td>OCR only, not checked or translated</td></tr>
</table>
</div>

<h2>The Hebrew text</h2>
<ul>
<li><b>Base text:</b> the first edition, Vienna 1871–91. Scan: the Daat virtual library
(<a href="https://www.daat.ac.il/daat/vl/tohen.asp?id=349">vol. 1</a>), about 300 dpi. The hidden text layer of the Daat
PDFs (an older OCR) is not used: its words are reversed and out of order.</li>
<li><b>OCR:</b> Kraken with the PP-OCRv6 model, line by line, then checked against the scan by eye.</li>
<li><b>Other scans:</b> HathiTrust has the first edition (Columbia and California copies) and the Vilna 1904 and Berlin 1923 printings.</li>
</ul>

<h2>Method</h2>
<ul>
<li><b>Rows.</b> One row is one heading or one paragraph of the print. Weiss's footnotes follow the text of each part.</li>
<li><b>English.</b> Close to the Hebrew; Weiss's references to sources are kept as he gives them.</li>
<li><b>Uncertain renderings</b> have the mark ⚠ and a note at the end of the page.</li>
<li><b>Translator.</b> The translation is by Claude (Anthropic), directed and reviewed by Ezra Brand.</li>
</ul>

<h2>Translations that exist</h2>
<ul><li>None in English is known. Yiddish: <i>Di grinder un boyer fun Yudentum</i> (New York, 1920–22).</li></ul>
</article>
</body>
</html>
"""
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    print("wrote docs/index.html")


def work_json():
    w = {"schema": 1, "slug": "weiss", "order": 35, "kind": "translation",
         "title": "I. H. Weiss, *Dor Dor ve-Dorshav*", "short_title": "*Dor Dor ve-Dorshav*", "title_he": "דור דור ודורשיו",
         "author": "Isaac Hirsch Weiss (1815–1905)",
         "status_label": "In progress · vol. 1, chapter 1 (pilot)",
         "start": "part-01.html", "start_label": "Book One, chapter 1",
         "summary": "The classic history of the Oral Law, from the Bible to the sixteenth century, with an English translation paragraph by paragraph.",
         "base_edition": {"label": "Vienna 1871–91; Daat scan", "scan_url": "https://www.daat.ac.il/daat/vl/tohen.asp?id=349"},
         "method": "Paragraph-aligned Hebrew and English; Hebrew from Kraken OCR checked against the scan.",
         "cite": "Isaac Hirsch Weiss, *Dor Dor ve-Dorshav*, Hebrew text with English translation, ed. Ezra Brand. Open Seforim",
         "url": "https://openseforim.org/weiss/", "repo": "https://github.com/openseforim/weiss",
         "licence": {"name": "CC BY-SA 4.0", "url": "https://creativecommons.org/licenses/by-sa/4.0/"}}
    (DOCS / "work.json").write_text(json.dumps(w, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    DOCS.mkdir(exist_ok=True)
    counts = {k: part_page(k) for k in sorted(PARTS)}
    index_page(counts)
    work_json()


if __name__ == "__main__":
    main()
    import subprocess
    tool = ROOT.parent / "openseforim-site" / "tools" / "postbuild.py"
    if tool.exists():
        subprocess.run([sys.executable, str(tool), "weiss", str(DOCS)], check=False)
