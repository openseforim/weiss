"""Read the checked Hebrew pages of a volume (data/he/vV_FF_PP.txt) as one stream of units.

Page file format (see README): '@ N' printed page; '# text' heading; empty line = paragraph break (an empty line right
after '@ N' means the page begins a new paragraph); '---' then the footnotes, each 'N)' or '*)'; unnumbered lines
right after '---' continue the last footnote of the page before.

parse_volume(stems) -> (units, notes, printed)
  units:   list of {"kind": "h"|"p", "he": text, "start": stem}; the text carries '{page:STEM}' where a printed page
           begins and '⟦STEM:N⟧' for a footnote call.
  notes:   {"STEM:N": Hebrew text of the footnote}, in page order.
  printed: {stem: printed page label}"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HE = ROOT / "data" / "he"
CALL = re.compile(r"(?<=\S)\s?(\d{1,2}|\*)\)")  # a call is kept only if the page has that note
NOTE = re.compile(r"^(\d{1,2}|\*)\)\s*(.*)")


def stems_of(vol):
    return sorted(p.stem for p in HE.glob(f"v{vol}_*.txt"))


def parse_volume(stems):
    units, notes, printed = [], {}, {}
    para, para_start, last_note = [], None, None

    def flush():
        nonlocal para, para_start
        if para:
            units.append({"kind": "p", "he": " ".join(para), "start": para_start})
        para, para_start = [], None

    for stem in stems:
        lines = (HE / f"{stem}.txt").read_text(encoding="utf-8").splitlines()
        if lines and lines[0].startswith("@"):
            printed[stem] = lines[0][1:].strip()
            lines = lines[1:]
        strip = [l.strip() for l in lines]
        body, fn = (lines[:strip.index("---")], lines[strip.index("---") + 1:]) if "---" in strip else (lines, [])
        first = True
        for l in body:
            s = l.strip()
            if not s:
                flush()
                continue
            have = {m.group(1) for m in (NOTE.match(x.strip()) for x in fn) if m}
            s = CALL.sub(lambda m: f"⟦{stem}:{m.group(1)}⟧" if m.group(1) in have and not (
                m.string[:m.start()].count("(") > m.string[:m.start()].count(")")) else m.group(0), s)
            tok = f"{{page:{stem}}} " if first else ""
            first = False
            if s.startswith("#+") and units and units[-1]["kind"] == "h" and not para:
                units[-1]["he"] += " " + s[2:].strip()  # '#+ text': a heading that runs over two printed lines
            elif s.startswith("#"):
                flush()
                units.append({"kind": "h", "he": tok + s.lstrip("#").strip(), "start": stem})
            else:
                if not para:
                    para_start = stem
                para.append(tok + s)
        for l in fn:
            s = l.strip()
            if not s:
                continue
            m = NOTE.match(s)
            if m:
                last_note = f"{stem}:{m.group(1)}"
                if last_note in notes:
                    raise ValueError(f"{stem}: footnote {m.group(1)} twice")
                notes[last_note] = m.group(2)
            elif last_note:
                notes[last_note] += " " + s
            else:
                raise ValueError(f"{stem}: footnote line without a note: {s[:40]}")
    flush()
    return units, notes, printed
