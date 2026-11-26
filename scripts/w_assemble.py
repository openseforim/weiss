"""Join the subagent units of a volume into the reader's part files.

  py -3.13 -I scripts/w_assemble.py 1          -> check, then write data/en/part-NN.* and data/parts.json
  py -3.13 -I scripts/w_assemble.py 1 check    -> only the checks

Inputs: the checked Hebrew pages data/he/*.txt; the units data/work/uNNN.json (unit 0 = the pilot, vol. 1 pp. 1-3,
made once from the old part-01 files by `pilot`). For every unit the number of English rows must equal the number of
Hebrew units (headings and paragraphs) that begin on its pages, and every footnote of its pages must have an English
note. Parts: a volume is cut before each chapter heading (פרק ...) and before back matter headings, together with the
headings that directly precede it; the front matter is a part of its own.

Output per part: data/en/part-NN.en.txt (one block per row; footnote tokens {STEM:N}), part-NN.fn.en.txt (one block
per footnote, 'STEM:N) text', in the order of the calls), part-NN.notes.json (⚠ renumbered through the part)."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wtext  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "work"
EN = ROOT / "data" / "en"
SPLIT = re.compile(r"^(\{page:[^}]+\}\s*)?(פרק|תקונ|תיקונ|השמטות|מפתח|מפתחות|רשימת|שמות האנשים)")
TOKEN = re.compile(r"\{(v\d_\d\d_\d\d):(\d{1,2}|\*)\}")


def load_units(vol):
    meta = json.loads((WORK / f"units-v{vol}.json").read_text(encoding="utf-8"))
    out = []
    if vol == 1:
        out.append(json.loads((WORK / "u000.json").read_text(encoding="utf-8")))
    for u in meta["units"]:
        f = WORK / f"u{u['unit']:03d}.json"
        if not f.exists():
            print(f"missing unit {u['unit']}")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        d["pages"] = u["pages"]
        d["unit"] = u["unit"]
        out.append(d)
    out.sort(key=lambda d: d["pages"][0])  # the pilot (unit 0) comes after the front matter
    return out


def check_and_align(vol):
    units = load_units(vol)
    stems = [s for u in units for s in u["pages"]]
    missing = [s for s in stems if not (wtext.HE / f"{s}.txt").exists()]
    if missing:
        sys.exit(f"Hebrew page files missing: {missing}")
    he, notes, printed = wtext.parse_volume(stems)
    page_unit = {s: u["unit"] for u in units for s in u["pages"]}
    en_rows, fn_en, bad = [], {}, 0
    # unit 2 carries the end of the pilot's last paragraph and note
    def join(row, text, notes):
        k = len(row.get("notes", {}))
        text = re.sub(r"⚠(\d+)", lambda m: f"⚠{int(m.group(1)) + k}", text)
        row["en"] = row["en"].rstrip() + " " + text.strip()
        row.setdefault("notes", {}).update({str(int(a) + k): b for a, b in (notes or {}).items()})
    for u in units:
        prev = next(x for x in units if x["unit"] == 0)  # only unit 2 continues (the pilot)
        if u.get("cont_row"):
            join(prev["rows"][-1], u["cont_row"], u.get("cont_row_notes"))
        if u.get("cont_note"):
            join(prev["footnotes"][-1], u["cont_note"], u.get("cont_note_notes"))
    for u in units:
        mine = [h for h in he if page_unit.get(h["start"]) == u["unit"]]
        rows = u["rows"]
        if len(mine) != len(rows):
            bad += 1
            print(f"u{u['unit']:03d}: {len(mine)} Hebrew units begin on its pages, {len(rows)} English rows")
            for i in range(max(len(mine), len(rows))):
                a = mine[i]["he"][:50] if i < len(mine) else "-"
                b = rows[i]["en"][:50] if i < len(rows) else "-"
                print(f"   {i}: {a} | {b}")
        for r in rows:
            r["_unit"] = u["unit"]
        en_rows += rows
        for f in u["footnotes"]:
            key = f"{f['page']}:{f['n']}"
            if key in fn_en:
                print(f"u{u['unit']:03d}: footnote {key} twice"); bad += 1
            f["_unit"] = u["unit"]
            fn_en[key] = f
        for r in rows + u["footnotes"]:
            marks = set(re.findall(r"⚠(\d+)", r["en"]))
            if marks != set(r.get("notes", {})):
                print(f"u{u['unit']:03d}: ⚠ marks {sorted(marks)} vs notes {sorted(r.get('notes', {}))} in {r['en'][:40]}")
                bad += 1
    if len(he) == len(en_rows):
        for h, r in zip(he, en_rows):
            calls = re.findall(r"⟦([^⟧]+)⟧", h["he"])
            toks = [f"{a}:{b}" for a, b in TOKEN.findall(r["en"])]
            if sorted(calls) != sorted(toks):
                print(f"u{r['_unit']:03d}: calls {calls} vs English tokens {toks} in {h['he'][:40]}")
                bad += 1
    for k in notes:
        if k not in fn_en:
            print(f"u{page_unit.get(k.split(':')[0], 0):03d}: no English for footnote {k}"); bad += 1
    for k in fn_en:
        if k not in notes:
            print(f"u{fn_en[k]['_unit']:03d}: English footnote {k} has no Hebrew footnote"); bad += 1
    print(f"vol. {vol}: {len(he)} Hebrew units, {len(en_rows)} English rows, {len(notes)} footnotes; {bad} problems")
    return he, notes, printed, en_rows, fn_en, bad


def cut_parts(he):
    starts = [0]
    for i, h in enumerate(he):
        # the table of contents (Daat file 01) has chapter lines too; it stays one part
        if h["kind"] == "h" and SPLIT.match(h["he"]) and i and h["start"].split("_")[1] != "01":
            j = i
            while j > 0 and he[j - 1]["kind"] == "h":
                j -= 1
            if j > starts[-1]:
                starts.append(j)
    return [(a, b) for a, b in zip(starts, starts[1:] + [len(he)])]


def plain(s):
    return re.sub(r"\{page:[^}]+\}\s*|⟦[^⟧]+⟧", "", s).strip()


def write_parts(vol, he, notes, en_rows, fn_en):
    parts_file = ROOT / "data" / "parts.json"
    allparts = json.loads(parts_file.read_text(encoding="utf-8")) if parts_file.exists() else []
    old = {p["num"]: p for p in allparts}
    allparts = [p for p in allparts if p["vol"] != vol]
    first = max([p["num"] for p in allparts], default=-1) + 1 if vol > 1 else 0
    for k, (a, b) in enumerate(cut_parts(he)):
        num = first + k
        rows = en_rows[a:b]
        heads = [r["en"] for r in rows[:4] if r["kind"] == "h"]
        calls = [c for h in he[a:b] for c in re.findall(r"⟦([^⟧]+)⟧", h["he"])]
        wn, blocks, fblocks, n = {}, [], [], 0

        def renum(r):
            nonlocal n
            local = {}
            def sub(m):
                nonlocal n
                n += 1
                local[m.group(1)] = n
                return f"⚠{n}"
            t = re.sub(r"⚠(\d+)", sub, r["en"])
            for o, g in local.items():
                wn[str(g)] = r["notes"][o]
            return t
        for r in rows:
            blocks.append(renum(r))
        for c in calls:
            fblocks.append(f"{c}) " + renum(fn_en[c]))
        EN.joinpath(f"part-{num:02d}.en.txt").write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
        EN.joinpath(f"part-{num:02d}.fn.en.txt").write_text("\n\n".join(fblocks) + "\n", encoding="utf-8")
        EN.joinpath(f"part-{num:02d}.notes.json").write_text(json.dumps(wn, ensure_ascii=False, indent=2) + "\n",
                                                            encoding="utf-8")
        o = old.get(num, {})
        allparts.append({"num": num, "vol": vol, "start": a, "end": b,
                         "first_he": plain(he[a]["he"])[:60],
                         "title": o.get("title") or (heads[0] if heads else plain(rows[0]["en"])[:60]),
                         "subtitle": o.get("subtitle") or (" ".join(heads[1:]) if len(heads) > 1 else ""),
                         "pages": sorted({h["start"] for h in he[a:b]})})
        print(f"part {num}: units {a}-{b - 1}, {len(calls)} footnotes, {len(wn)} uncertain; {allparts[-1]['title'][:70]}")
    allparts.sort(key=lambda p: p["num"])
    parts_file.write_text(json.dumps(allparts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def pilot():
    """Unit 0 from the pilot's part-01 files (English tokens {1} -> {STEM:N}, ⚠ numbered per row)."""
    he, notes, _ = wtext.parse_volume(["v1_02_01", "v1_02_02", "v1_02_03"])
    keys = list(notes)
    def blocks(p):
        out, cur = [], []
        for line in p.read_text(encoding="utf-8").split("\n"):
            if line.strip():
                cur.append(line.strip())
            elif cur:
                out.append(" ".join(cur)); cur = []
        return out + ([" ".join(cur)] if cur else [])
    warn = json.loads((EN / "part-01.notes.json").read_text(encoding="utf-8"))
    def conv(t):
        t = re.sub(r"\{(\d+)\}", lambda m: "{" + keys[int(m.group(1)) - 1] + "}", t)
        local, nn = {}, 0
        def sub(m):
            nonlocal nn
            nn += 1
            local[str(nn)] = warn[m.group(1)]
            return f"⚠{nn}"
        return re.sub(r"⚠(\d+)", sub, t), local
    rows = []
    for h, b in zip(he, blocks(EN / "part-01.en.txt")):
        t, w = conv(b)
        rows.append({"start": h["start"], "kind": h["kind"], "en": t, "notes": w})
    fns = []
    for k, b in zip(keys, blocks(EN / "part-01.fn.en.txt")):
        t, w = conv(re.sub(r"^\d+\)\s*", "", b))
        fns.append({"page": k.split(":")[0], "n": k.split(":")[1], "en": t, "notes": w})
    d = {"unit": 0, "pages": ["v1_02_01", "v1_02_02", "v1_02_03"], "rows": rows, "footnotes": fns,
         "report": "pilot, 24-Nov-2026"}
    (WORK / "u000.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pilot: {len(rows)} rows, {len(fns)} footnotes")


if __name__ == "__main__":
    if sys.argv[1] == "pilot":
        pilot()
        sys.exit()
    vol = int(sys.argv[1])
    he, notes, printed, en_rows, fn_en, bad = check_and_align(vol)
    if sys.argv[2:] != ["check"] and not bad:
        write_parts(vol, he, notes, en_rows, fn_en)
