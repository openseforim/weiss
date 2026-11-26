# I. H. Weiss, *Dor Dor ve-Dorshav*: Hebrew and English

Site: <https://openseforim.org/weiss/>

Isaac Hirsch Weiss (1815–1905), teacher of Talmud at the Vienna Bet ha-Midrash, wrote the first full history of the
Oral Law in Hebrew, from the Bible to the end of the sixteenth century, in five volumes (Vienna 1871–91). It has no
English translation. This repository holds a Hebrew text checked against the scan, an English translation paragraph
by paragraph, and the scripts that build the reader.

## Status

| Part | Pages | Status |
|---|---|---|
| 0. Title page and contents | vol. 1, pp. [I]–XIV | 26-Nov-2026 |
| 1–25. Books One to Five, chapters 1–25 | vol. 1, pp. 1–227 | Pp. 1–3: pilot, 24-Nov-2026. Pp. 4–227: 26-Nov-2026 |
| 26. Errata | vol. 1, p. 227 | 26-Nov-2026 |
| 27–28. Index of subjects, index of names | vol. 1, pp. [228]–236 | 26-Nov-2026 |
| – | vols. 2–5 | OCR only, not checked or translated |

Vol. 1 has 415 rows, 238 notes by Weiss, and 406 uncertain renderings, each marked with ⚠ and a note. Pp. 4–236
were done by 46 Claude subagents, each with about five pages. Each agent checked the Hebrew against the scan and
translated its pages, following `scripts/BRIEF.md`. `scripts/w_assemble.py` checks the joins: each row has one Hebrew
unit, and each footnote call has one note.

## Sources

- **Base text:** the Daat virtual library scan. Its title page has no imprint (Daat's stamp stands in its place). It is a later printing, not the first edition of 1871: vol. 1 cites vols. 4 and 5 of the work and a journal of 1889. From the Daat virtual library
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
- `data/he/*.txt`: '#+ text' continues a heading that is printed on two lines. A footnote call is `N)` after a word.
  In the English it is the token `{STEM:N}`. The reader numbers the notes through each part.
- `data/work/uNNN.json`: the subagent units (Hebrew pages, English rows and notes). `data/parts.json`: the parts (the
  volume is cut before each chapter heading).
- `scripts/w_units.py`, `scripts/BRIEF.md`, `scripts/w_assemble.py`, `scripts/w_titles.py`: unit inputs, the agents'
  brief, the joining and checking of the units, and the part titles. `scripts/wtext.py` reads the Hebrew pages.
- `scripts/build_site.py`: builds `docs/`. `scripts/make_scans.py`: page images for the scan panel.

## Licence

Text and translation: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The Hebrew original is in the
public domain.
