"""OCR a folder of page images (e.g. the archive.org jp2 set of the 1885 printing) with Kraken PP-OCRv6,
line by line (split_image.py), resumable.
  py -3.13 -I scripts/ocr_images.py IMGDIR OUTDIR [--scale 0.5] [--batch 4] [--threads 10]
Writes OUTDIR/lines/<stem>/NN.png and OUTDIR/text/<stem>.txt (logical order, one printed line per line)."""
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import split_image  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
KRAKEN = Path(r"C:\Users\ezrab\Ezra Brandt\Claude\syriac-ocr\.venv\Scripts\kraken.exe")
MODEL = Path(r"C:\Users\ezrab\AppData\Local\htrmopo\htrmopo\1980fa54-b49e-5256-95b6-928290bc48f8\medium.safetensors")
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
a = sys.argv[1:]
AUTOCROP = "--autocrop" in a
a = [x for x in a if x != "--autocrop"]
opt = {"--scale": 0.5, "--batch": 4, "--threads": 10, "--min-height": 0}
for k in list(opt):
    if k in a:
        i = a.index(k); opt[k] = type(opt[k])(a[i + 1]); del a[i:i + 2]
imgdir, out = Path(a[0]), Path(a[1])
(out / "text").mkdir(parents=True, exist_ok=True)
imgs = sorted(p for p in imgdir.iterdir() if p.suffix.lower() in (".jp2", ".jpg", ".png", ".tif"))
todo = [p for p in imgs if not (out / "text" / f"{p.stem}.txt").exists()]
print(f"{len(todo)} of {len(imgs)} pages to do", flush=True)
t0 = time.time()
for k in range(0, len(todo), opt["--batch"]):
    pages, cmd, per = todo[k:k + opt["--batch"]], [str(KRAKEN), "--threads", str(opt["--threads"])], {}
    for p in pages:
        ld = out / "lines" / p.stem
        try:
            k_lines, med = split_image.run(p, ld, opt["--scale"], AUTOCROP)
            if med < opt["--min-height"]:   # blank page or cover: no real text lines
                for f in ld.glob("*.png"):
                    f.unlink()
                (out / "text" / f"{p.stem}.txt").write_text("", encoding="utf-8")
                print(f"{p.stem} skipped (no text, line height {med}px)", flush=True)
                continue
        except Exception as e:  # noqa: BLE001
            print(f"{p.stem} SPLIT FAILED: {e}", flush=True)
            continue
        per[p] = sorted(ld.glob("[0-9][0-9].png"))
        for im in per[p]:
            cmd += ["-i", str(im), str(im.with_suffix(".R.txt"))]
    if len(cmd) > 3:
        cmd += ["ocr", "-m", str(MODEL), "--no-segmentation", "-B", "16", "--base-dir", "R"]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    for p, ims in per.items():
        got = [im.with_suffix(".R.txt") for im in ims]
        if ims and not any(g.exists() for g in got):
            print(f"{p.stem} FAILED: {r.stderr[-300:]}", flush=True)
            continue
        text = "\n".join(g.read_text(encoding="utf-8").strip() if g.exists() else "" for g in got)
        (out / "text" / f"{p.stem}.txt").write_text(text + "\n", encoding="utf-8")
        print(f"{p.stem} ok {len(ims)} lines", flush=True)
    done = k + len(pages)
    print(f"  {done}/{len(todo)} pages, {(time.time() - t0) / done * (len(todo) - done) / 60:.0f} min left", flush=True)
print("finished", flush=True)
