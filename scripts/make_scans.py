"""Page images for the scan panel: docs/scans/<stem>.jpg (900 px wide, greyscale) from the Daat page images
data/pages/vV/<stem>.png.   py -3.13 -I scripts/make_scans.py v1_02_01 v1_02_02 ...   (existing files are kept)"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "scans"
OUT.mkdir(parents=True, exist_ok=True)
for stem in sys.argv[1:]:
    out = OUT / f"{stem}.jpg"
    if out.exists():
        continue
    im = Image.open(ROOT / "data" / "pages" / stem.split("_")[0] / f"{stem}.png").convert("L")
    im = im.resize((900, round(im.height * 900 / im.width)), Image.LANCZOS)
    im.save(out, quality=70, optimize=True, progressive=True)
    print(out.name, im.size, f"{out.stat().st_size // 1024} KB")
