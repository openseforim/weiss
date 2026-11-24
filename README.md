# I. H. Weiss, *Dor Dor ve-Dorshav*: Hebrew and English

Site: <https://openseforim.org/weiss/>

Isaac Hirsch Weiss (1815–1905), teacher of Talmud at the Vienna Bet ha-Midrash, wrote the first full history of the
Oral Law in Hebrew, from the Bible to the end of the sixteenth century, in five volumes (Vienna 1871–91). It has no
English translation. This repository holds a Hebrew text checked against the scan, an English translation paragraph
by paragraph, and the scripts that build the reader.

## Status

| Part | Pages | Status |
|---|---|---|
| 1. Book One, chapter 1 (opening) | vol. 1, pp. 1–3 | 24-Nov-2026. Hebrew checked against the scan line by line; 9 rows and 3 of Weiss's notes translated; 4 uncertain renderings. The part ends mid-sentence at the foot of p. 3. |
| 2– | rest of vol. 1, vols. 2–5 | OCR only, not checked or translated |

## Sources

- **Base text:** the first edition, Vienna 1871–91, from the Daat virtual library
  ([vol. 1](https://www.daat.ac.il/daat/vl/tohen.asp?id=349)), one PDF per chapter, about 300 dpi. Page files are named
  `vV_FF_PP` (volume, Daat file, page in that file). The hidden text layer of the PDFs (an older OCR) is not used: its
  words are reversed and out of order.
- **Other scans:** HathiTrust has the first edition (Columbia and California copies) and the Vilna 1904 and Berlin 1923
  printings.
- **Translations that exist:** none in English is known. Yiddish: *Di grinder un boyer fun Yudentum* (New York, 1920–22).

## Method

- **OCR:** [Kraken](https://kraken.re/) with the PP-OCRv6 medium model, line by line. Lines are found from the row ink
  profile (`scripts/split_lines.py`), not by Kraken's segmenter, then read with `ocr --no-segmentation --base-dir R`
  (`scripts/ocr_images.py`). The line pitch is the first strong peak of the profile's autocorrelation; an earlier
  version took the highest peak, which on about a third of the pages was the two-line repeat, and merged lines in pairs.
- **Checking:** every line compared with the scan by eye; doubtful words enlarged from the line image, never corrected
  from memory. Spelling, abbreviations and punctuation are as printed; the catchword at the foot of each page is dropped.
  Typical OCR errors in this type: ג read as נ, ר as ד, ח as ת, ז as ו.
- **Notes:** the print numbers Weiss's notes page by page; the reader numbers them through the part.
- **English:** close to the Hebrew; Weiss's references are kept as he gives them, with verse references added in
  [gray brackets]. The translation is by Claude (Anthropic), directed and reviewed by Ezra Brand.

## Files

- `data/he/vV_FF_PP.txt`: checked Hebrew, one file per printed page (`@ N` printed page number; `#` heading; blank line
  = paragraph break; `---` then the page's notes).
- `data/en/part-NN.en.txt`, `part-NN.fn.en.txt`, `part-NN.notes.json`: English rows, English notes, uncertain renderings.
- `scripts/build_site.py`: builds `docs/`. `scripts/make_scans.py`: page images for the scan panel.

## Licence

Text and translation: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The Hebrew original is in the
public domain.
