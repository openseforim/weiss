"""Part titles in data/parts.json from the English heading rows of each part.

  py -3.13 -I scripts/w_titles.py

A chapter part: title "Chapter N: <the chapter's summary heading>"; if a book begins in the part, the subtitle is
"Book N: <the book's summary>". Other parts (front matter, errata, indexes) take their first heading."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
EN = ROOT / "data" / "en"
FIXED = {0: ("Title page and contents", "Weiss's table of contents for vol. 1, with his summaries of each chapter")}


def blocks(p):
    return [b.replace("\n", " ").strip() for b in p.read_text(encoding="utf-8").split("\n\n") if b.strip()]


def clean(s):
    return re.sub(r"⚠\d+|\{[^}]+\}", "", s).strip().rstrip(".—– ").rstrip(".")


parts = json.loads((ROOT / "data" / "parts.json").read_text(encoding="utf-8"))
for p in parts:
    rows = blocks(EN / f"part-{p['num']:02d}.en.txt")
    heads = []
    for r in rows:
        if len(r) > 450:
            break
        heads.append(clean(r))
    if p["num"] in FIXED:
        p["title"], p["subtitle"] = FIXED[p["num"]]
    else:
        ch = next((i for i, h in enumerate(heads) if h.startswith("Chapter ")), None)
        if ch is not None:
            summ = heads[ch + 1] if ch + 1 < len(heads) else ""
            p["title"] = f"{heads[ch]}: {summ}" if summ else heads[ch]
            book = next((i for i, h in enumerate(heads[:ch]) if h.startswith("Book ")), None)
            p["subtitle"] = (f"{heads[book]}: " + "; ".join(heads[book + 1:ch])) if book is not None else ""
        else:
            p["title"], p["subtitle"] = heads[0], ""
    print(p["num"], "|", p["title"], "|", p["subtitle"][:80])
(ROOT / "data" / "parts.json").write_text(json.dumps(parts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
