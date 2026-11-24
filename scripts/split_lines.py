"""Cut a Ma'agal Tov page into line images by horizontal ink profile (clean single-column print).
  py -3.13 -I scripts/split_lines.py 30 [120 ...]      -> data/lines/sNNN/LL.png  (+ data/lines/sNNN_boxes.png preview)
Margin line numbers (the 5, 10, 15 ... in the outer margin) are cut off each line."""
import io
import sys
from pathlib import Path

import numpy as np
try:
    import pymupdf  # only needed for the HebrewBooks PDF (page_image); page-image runs work without it
except ImportError:
    pymupdf = None
from PIL import Image, ImageDraw, ImageFilter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
PDF = Path(r"C:\Users\ezrab\Ezra Brandt\Claude\openseforim-scans\scans\hida-maagal-tov\hebrewbooks_21838_freimann.pdf")
OUT = ROOT / "data" / "lines"      # variant s2: 2x, softened
SCALE = 2


def set_variant(v):
    """'s1' = native resolution, no blur (data/lines_s1); 's2' = 2x Lanczos + blur (data/lines)."""
    global OUT, SCALE
    if v == "s1":
        OUT, SCALE = ROOT / "data" / "lines_s1", 1
    else:
        OUT, SCALE = ROOT / "data" / "lines", 2


def page_image(n, doc=None):
    d = doc or pymupdf.open(PDF)
    x = d.extract_image(d[n - 1].get_images()[0][0])
    return Image.open(io.BytesIO(x["image"])).convert("L")


def runs(mask):
    """Start/end index pairs of True runs."""
    m = np.concatenate([[False], mask, [False]])
    d = np.diff(m.astype(int))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def find_lines(ink):
    """Line centres = peaks of the smoothed row profile, at least 0.6 x line pitch apart; cut at the minimum
    between two centres. Robust when ascenders and descenders of neighbouring lines touch."""
    h, w = ink.shape
    prof = ink.sum(1).astype(float)
    sm = np.convolve(prof, np.ones(7) / 7, mode="same")
    x = sm - sm.mean()
    ac = np.correlate(x, x, mode="full")[len(x) - 1:]
    lo, hi = 20, min(120, len(ac) - 1)
    if hi <= lo or sm.max() == 0:
        return [], 30
    # line pitch = the FIRST strong peak of the autocorrelation, not the strongest: on some pages the repeat every
    # two lines (2 x pitch) is stronger, and then neighbouring lines were merged in pairs (Weiss, 24-Nov-2026)
    seg = ac[lo:hi]
    top = seg.max()
    peaks_ac = [i for i in range(1, len(seg) - 1) if seg[i] >= seg[i - 1] and seg[i] >= seg[i + 1] and seg[i] >= 0.5 * top]
    pitch = lo + (peaks_ac[0] if peaks_ac else int(np.argmax(seg)))
    win = max(3, int(0.3 * pitch))
    thr = 0.12 * sm.max()
    peaks = []
    for y in range(h):
        if sm[y] < thr:
            continue
        a, b = max(0, y - win), min(h, y + win + 1)
        if sm[y] == sm[a:b].max() and (not peaks or y - peaks[-1] > 0.6 * pitch):
            peaks.append(y)
    lines = []
    for i, p in enumerate(peaks):
        top = (peaks[i - 1] + int(np.argmin(sm[peaks[i - 1]:p]))) if i else max(0, p - int(0.6 * pitch))
        bot = (p + int(np.argmin(sm[p:peaks[i + 1]]))) if i + 1 < len(peaks) else min(h, p + int(0.6 * pitch))
        if i == 0 or (top - lines[-1][1]) > 0:  # first line, or a real gap above: shrink to inked rows
            pass
        lines.append((top, bot))
    # trim blank rows at both ends of each band
    out = []
    for a, b in lines:
        rows = np.where(prof[a:b] > 0)[0]
        if len(rows) == 0 or ink[a:b].sum() < 0.002 * w * (b - a) or rows[-1] - rows[0] < 0.25 * pitch:
            continue
        out.append((a + rows[0], a + rows[-1] + 1))
    return out, int(0.7 * pitch)


def x_extent(ink_line, med):
    """Horizontal extent of the line, dropping a narrow ink cluster cut off by a wide gap at either edge
    (margin line numbers)."""
    cols = runs(ink_line.sum(0) > 0)
    if not cols:
        return None
    # group column runs separated by gaps < 1.2 * med (word spaces are smaller)
    groups = [[cols[0][0], cols[0][1]]]
    for a, b in cols[1:]:
        if a - groups[-1][1] < 1.2 * med:
            groups[-1][1] = b
        else:
            groups.append([a, b])
    total = sum(b - a for a, b in groups)
    while len(groups) > 1 and groups[0][1] - groups[0][0] < 2.5 * med and groups[0][1] - groups[0][0] < 0.15 * total:
        groups.pop(0)
    while len(groups) > 1 and groups[-1][1] - groups[-1][0] < 2.5 * med and groups[-1][1] - groups[-1][0] < 0.15 * total:
        groups.pop()
    return groups[0][0], groups[-1][1]


def deskew(im):
    """Rotate by the angle (within +-2.5 deg) that makes the row profile sharpest."""
    small = im.resize((im.width // 2, im.height // 2))
    best = (0, -1)
    for ang in np.arange(-2.5, 2.51, 0.1):
        r = np.asarray(small.rotate(ang, resample=Image.BILINEAR, fillcolor=255)) < 128
        v = np.var(r.sum(1))
        if v > best[1]:
            best = (ang, v)
    a0 = best[0]
    for ang in np.arange(a0 - 0.1, a0 + 0.101, 0.02):
        r = np.asarray(small.rotate(ang, resample=Image.BILINEAR, fillcolor=255)) < 128
        v = np.var(r.sum(1))
        if v > best[1]:
            best = (ang, v)
    return im.rotate(best[0], resample=Image.BICUBIC, fillcolor=255), best[0]


def margin_trim(ink_line, med, L, R, ext):
    """Cut a margin number: while the line starts (ends) well outside the block edge, skip one ink run and the
    gap after it. Digits of '20' have small gaps between them, so this repeats."""
    x0, x1 = ext
    col = ink_line.sum(0) > 0
    n = len(col)
    for _ in range(6):
        if x0 >= L - 0.4 * med:
            break
        x = x0
        while x < n and col[x]:
            x += 1
        g = x
        while g < n and not col[g]:
            g += 1
        if g >= n or g - x < 2:
            break
        x0 = g
    for _ in range(6):
        if x1 <= R + 0.4 * med:
            break
        x = x1 - 1
        while x > 0 and col[x]:
            x -= 1
        g = x
        while g > 0 and not col[g]:
            g -= 1
        if g <= 0 or x - g < 2:
            break
        x1 = g + 1
    return x0, x1


def deskew(im):
    """Rotate by the angle (within +-2.5 deg) that makes the row profile sharpest."""
    small = im.resize((im.width // 2, im.height // 2))
    best = (0, -1)
    for ang in np.arange(-2.5, 2.51, 0.1):
        r = np.asarray(small.rotate(ang, resample=Image.BILINEAR, fillcolor=255)) < 128
        v = np.var(r.sum(1))
        if v > best[1]:
            best = (ang, v)
    a0 = best[0]
    for ang in np.arange(a0 - 0.1, a0 + 0.101, 0.02):
        r = np.asarray(small.rotate(ang, resample=Image.BILINEAR, fillcolor=255)) < 128
        v = np.var(r.sum(1))
        if v > best[1]:
            best = (ang, v)
    return im.rotate(best[0], resample=Image.BICUBIC, fillcolor=255), best[0]


def deskew(im):
    """Rotate by the angle (within +-2.5 deg) that makes the row profile sharpest."""
    small = im.resize((im.width // 2, im.height // 2))
    best = (0, -1)
    for ang in np.arange(-2.5, 2.51, 0.1):
        r = np.asarray(small.rotate(ang, resample=Image.BILINEAR, fillcolor=255)) < 128
        v = np.var(r.sum(1))
        if v > best[1]:
            best = (ang, v)
    a0 = best[0]
    for ang in np.arange(a0 - 0.1, a0 + 0.101, 0.02):
        r = np.asarray(small.rotate(ang, resample=Image.BILINEAR, fillcolor=255)) < 128
        v = np.var(r.sum(1))
        if v > best[1]:
            best = (ang, v)
    return im.rotate(best[0], resample=Image.BICUBIC, fillcolor=255), best[0]


def split(n, doc=None):
    im, angle = deskew(page_image(n, doc))
    a_img = np.asarray(im)
    ink = a_img < 128
    lines, med = find_lines(ink)
    d = OUT / f"s{n:03d}"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.png"):
        f.unlink()
    prev = im.convert("RGB")
    dr = ImageDraw.Draw(prev)
    boxes = []
    exts = [x_extent(ink[a:b], med) for a, b in lines]
    if not any(exts):
        prev.save(OUT / f"s{n:03d}_boxes.png")
        return 0, med, angle
    lefts = sorted(e[0] for e in exts if e)
    rights = sorted(e[1] for e in exts if e)
    L, R = lefts[len(lefts) // 2], rights[len(rights) // 2]   # the text block's usual edges
    for i, ((a, b), ext) in enumerate(zip(lines, exts), 1):
        if not ext:
            continue
        x0, x1 = margin_trim(ink[a:b], med, L, R, ext)
        if x1 - x0 < 0.5 * med:   # trim went wrong (title or short line far from the block edges): keep the full extent
            x0, x1 = ext
        pad_y, pad_x = int(0.12 * med), int(0.5 * med)
        box = (max(0, x0 - pad_x), max(0, a - pad_y), min(im.width, x1 + pad_x), min(im.height, b + pad_y))
        crop = im.crop(box)
        if SCALE != 1:
            crop = crop.resize((crop.width * SCALE, crop.height * SCALE), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
        crop.save(d / f"{i:02d}.png")
        boxes.append(box)
        dr.rectangle(box, outline=(255, 0, 0), width=2)
        dr.text((5, a), str(i), fill=(0, 0, 255))
    prev.save(OUT / f"s{n:03d}_boxes.png")
    return len(boxes), med, angle


if __name__ == "__main__":
    doc = pymupdf.open(PDF)
    a = sys.argv[1:]
    if a and a[0] in ("s1", "s2"):
        set_variant(a.pop(0))
    for n in map(int, a):
        k, med, ang = split(n, doc)
        print(f"s{n:03d}: {k} lines (median line height {med}px, deskew {ang:+.2f} deg)", flush=True)
