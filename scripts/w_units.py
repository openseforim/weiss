"""Work units for the subagent run: five page files per unit, with the Kaggle OCR of each page.

  py -3.13 -I scripts/w_units.py 1          -> data/work/units-v1.json and data/work/uNNN/input.txt for vol. 1
  py -3.13 -I scripts/w_units.py 1 status   -> which units have an output file data/work/uNNN.json

The first page of each Daat file (from the second file on) repeats the last page of the file before it; those
repeated page files are skipped (the earlier copy is used). Units are numbered through the work: vol. 1 starts at 1.
Unit numbers of later volumes start at 100 * V. The pilot pages v1_02_01..03 are unit 0 (already done).
Special units: the front matter (title page and table of contents, file 01) and the back matter (name index) of a
volume are units of their own, of kind "front" and "index"."""
import difflib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
OCR = ROOT.parent / "openseforim-scans" / "kaggle" / "merged"
WORK = ROOT / "data" / "work"
PER = 5


def page_stems(v):
    """Unique page stems of vol. v in order (repeated first pages of Daat files dropped)."""
    files = sorted((OCR / f"weiss-v{v}").glob(f"v{v}_*.txt"))
    out, prev_text = [], None
    for f in files:
        t = f.read_text(encoding="utf-8")
        if out and f.stem.split("_")[1] != out[-1].split("_")[1] and prev_text is not None:
            if difflib.SequenceMatcher(None, t[:800], prev_text[:800]).ratio() > 0.9:
                continue
        out.append(f.stem)
        prev_text = t
    return out


def image(stem):
    return ROOT / "data" / "pages" / stem.split("_")[0] / f"{stem}.png"


def make_units(v, front_files=("01",), index_files=()):
    stems = page_stems(v)
    done = {p.stem for p in (ROOT / "data" / "he").glob(f"v{v}_*.txt")}
    front = [s for s in stems if s.split("_")[1] in front_files]
    index = [s for s in stems if s.split("_")[1] in index_files]
    body = [s for s in stems if s not in front and s not in index and s not in done]
    units = []
    n = 100 * (v - 1) + 1
    if front:
        units.append({"unit": n, "kind": "front", "pages": front}); n += 1
    for i in range(0, len(body), PER):
        units.append({"unit": n, "kind": "text", "pages": body[i:i + PER]}); n += 1
    if index:
        units.append({"unit": n, "kind": "index", "pages": index}); n += 1
    order = [s for s in stems]
    for u in units:
        last = order.index(u["pages"][-1])
        nxt = order[last + 1] if last + 1 < len(order) else None
        u["next"] = nxt if u["kind"] == "text" and nxt not in index else None
        d = WORK / f"u{u['unit']:03d}"
        d.mkdir(parents=True, exist_ok=True)
        lines = []
        for s in u["pages"] + ([u["next"]] if u["next"] else []):
            tag = "  [next unit's page: read only to finish your last paragraph or note]" if s == u["next"] else ""
            lines.append(f"=== page {s} (image {image(s)}){tag}")
            raw = (OCR / f"weiss-v{v}" / f"{s}.txt").read_text(encoding="utf-8").splitlines()
            lines += [f"[{s}:{i}] {t}" for i, t in enumerate(raw, 1)]
        (d / "input.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (WORK / f"units-v{v}.json").write_text(json.dumps({"stems": order, "units": units}, indent=1), encoding="utf-8")
    print(f"vol. {v}: {len(order)} unique pages, {len(units)} units written to {WORK}")


def status(v):
    us = json.loads((WORK / f"units-v{v}.json").read_text(encoding="utf-8"))["units"]
    miss = [u["unit"] for u in us if not (WORK / f"u{u['unit']:03d}.json").exists()]
    print(f"{len(us) - len(miss)}/{len(us)} done; missing: {miss}")


if __name__ == "__main__":
    vol = int(sys.argv[1])
    if sys.argv[2:] == ["status"]:
        status(vol)
    else:
        make_units(vol, index_files=("13",) if vol == 1 else ())
