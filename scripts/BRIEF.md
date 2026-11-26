# Brief: proofread and translate one unit of Weiss, *Dor Dor ve-Dorshav*

You work on the Open Seforim reader of Isaac Hirsch Weiss, *Dor Dor ve-Dorshav* (vol. 1, Vienna 1871), a history of
the Oral Law in Hebrew. The repository is `C:\Users\ezrab\Ezra Brandt\Claude\weiss-dor-dor` (below: REPO). Vol. 1,
pp. 1–3 are done (the pilot). Your unit is about five page images of the Daat scan. Many agents work in parallel on
other units, so stay inside your own pages and files.

Use `py -3.13` for Python (never `python`), and put `sys.stdout.reconfigure(encoding="utf-8")` at the top of every
script. Write scripts and crops only inside your unit folder `REPO\data\work\uNNN\`. Write no other files than the
ones named under "Output". Do not run git and do not use the network.

## Inputs

- `REPO\data\work\uNNN\input.txt`: Kraken OCR of your pages, one line per printed line, as `[stem:line] text`, body
  and footnotes together, not corrected. Each page block starts with `=== page STEM (image PATH)`. The last block may
  be the next unit's page: read it only to finish your last paragraph or footnote.
- The page images (PNG, 1664×2493). To read them, crop each page into horizontal strips with a small overlap: the body
  (large type) in about 3 strips at 1.5×, the footnotes (small type) in strips of about 8 lines each at 2× (PIL,
  LANCZOS). Save the crops in your unit folder and Read them, at most about 8 images per Read batch. Enlarge a single
  word further when you are in doubt.
- Style model: read `REPO\data\he\v1_02_03.txt`, the first two paragraphs of `REPO\data\en\part-01.en.txt` and
  `REPO\data\en\part-01.fn.en.txt` before you start. (Those English files use the old note tokens `{1}`; you use the
  new tokens described below.)

## 1. Proofread the Hebrew and write one file per page

Compare every OCR line with the image and correct it. Typical OCR errors in this type: ג read as נ, ר as ד, ח as ת or ה,
ז as ו, ט as מ, ס as ם, ב as כ. Decide by the image first, then by sense; never correct from memory of the source
quoted. Keep spelling, abbreviations and punctuation as printed (do not expand ר"ע, הלממ"ס, etc.).

Write `REPO\data\he\STEM.txt` for each page of your unit (not for the next unit's page), in this format:

```
@ 98
first line of the body as printed
...
last line of the body
---
1) first line of footnote 1 as printed
second line of footnote 1
2) footnote 2 ...
```

- Line 1 is `@ N`, the printed page number from the top of the page (Arabic for the text, as printed; for front matter
  use the Roman number, or leave the line out if none is printed).
- One line per printed line. Drop the running page number and the catchword at the foot of the page.
- If the first line of the page **begins a new paragraph** (it is indented) put one empty line right after `@ N`. If
  it continues the paragraph of the page before, start with that line directly.
- An empty line marks a paragraph break (an indented line) inside the page.
- A heading (book or chapter title, the chapter's summary line, any centered line) is a line of its own starting with
  `# `, e.g. `# פרק שני`.
- A footnote call in the body stays as printed, a number and a parenthesis after the word: `ממחלוקת 1)`. A note marked
  with a star stays `*)`.
- `---` on its own line, then the footnotes, each starting `N)` as printed. If the page's footnote block begins with
  the end of a note from the previous page (no number), put those lines first, right after `---`, without a number.
  If the page has no footnotes, leave out `---`.

## 2. Translate

You write English **rows**: one row for every heading and every paragraph that **begins** on your pages, in order.
Skip the lines at the top of your first page that finish a paragraph from the page before (the previous unit
translates them). Finish the paragraph that is still open at the end of your last page, reading on into the next page
(the `[next unit's page]` block and its image) as far as needed. Some paragraphs run over two or more pages: then read
the further pages' OCR in `C:\Users\ezrab\Ezra Brandt\Claude\openseforim-scans\kaggle\merged\weiss-v1\STEM.txt` and
their images in `REPO\data\pages\v1\STEM.png` until the paragraph ends (skip page files that repeat the page before). Do the same for footnotes: translate every footnote
that begins on your pages, finish one that continues onto the next page, and skip a footnote continuation at the top
of your first page's footnote block.

- English close to the Hebrew, plain and readable, in Weiss's voice (first person plural where he uses it). No
  hedging words, no summaries, nothing left out.
- **Footnote calls:** where the Hebrew has a call `1)`, put the token `{STEM:1}` in the English at the same place
  (STEM is the page where the call stands, e.g. `{v1_02_05:1}`; a star note is `{v1_02_05:*}`).
  A call that stands on the next unit's page, inside the paragraph you finish, also gets its token; that footnote is
  translated by the unit that owns the page. A number in parentheses that is a page or chapter reference, e.g.
  `(צד 74)`, is not a call.
- **References:** keep Weiss's references as he gives them, in English form: `(ברכות לא:)` → `(Berakhot 31b)`,
  `(שבת נו.)` → `(Shabbat 56a)`, `ירושלמי פאה פ"א ה"א` → `Yerushalmi Pe'ah 1:1`, `ת"כ` → `Sifra`, `מ"ר` and the
  like spelled out (`Exodus Rabbah`). Do not correct his references; if one looks wrong, keep it and add a ⚠ note.
  Bible verse figures that he prints as `(42, 22)` become `(42:22)`.
- **Bible verses quoted without a reference:** add the reference in square brackets after the quotation:
  `"he weighed, and sought out ..." [Ecclesiastes 12:9]`. Square brackets are only for the translator's additions.
- **Book titles in italics** with asterisks: `*Moreh Nevukhei ha-Zeman*`, `*Antiquities*`, `*Mishneh Torah*`,
  `*Kesef Mishneh*`. Names of Talmud tractates and of biblical books are not in italics.
- Names: R. Naḥman Krochmal (רנ"ק, הרנ"ק); Josephus for יוסיפון/יוסף בן מתתיהו; Simeon the Just; Antigonus of Sokho;
  the Men of the Great Assembly; the Scribes (סופרים); Simeon ben Shetaḥ; Judah ben Tabbai; Shemaiah and Avtalyon;
  Hillel; Shammai; Rabban Yoḥanan ben Zakkai; Rabban Gamaliel; R. Akiva; R. Ishmael; R. Eliezer; R. Joshua; R. Meir;
  R. Judah; R. Yose; R. Simeon; Rabbi (Judah the Prince); Rav; Samuel; R. Yoḥanan; Resh Lakish; Abaye; Rava;
  Pharisees, Sadducees, Boethusians, Essenes, Samaritans (כותים: "the Kutim [Samaritans]" the first time in a
  paragraph, then "the Kutim"); Hasmoneans; Antiochus; Ptolemy; Philo; Maimonides (רמב"ם); Rashi; Graetz; Zunz;
  Frankel; Geiger. Hebrew terms in plain roman letters: halakhah, aggadah, midrash, Mishnah, Tosefta, baraita, Tannaim,
  Amoraim, Sanhedrin, beit din (or "the court"). `הלכה למשה מסיני` / `הלממ"ס` → "a halakhah [given] to Moses at
  Sinai". Expand abbreviations in the English (ר"ע → R. Akiva, וכו' → etc.).
- Mark an uncertain rendering, an unreadable word, or a reference that looks wrong, with ⚠1, ⚠2 … (numbered from 1 in
  **each row or footnote**) and give a note for each: `{"he": "<the Hebrew words>", "note": "<why; your best
  reading>"}`. Keep notes short and factual; no notes on things you are sure of.
- Headings: translate as headings (`Chapter Two`, then the summary line as printed).

## 3. Special units

- **Unit 2 only (the pilot's continuation):** page v1_02_03 ended inside a paragraph and inside footnote 2 of that
  page. Translate the rest of that paragraph (the top lines of v1_02_04 up to the first paragraph break) into
  `cont_row`, and the rest of footnote 2 of v1_02_03 (the unnumbered lines at the start of v1_02_04's footnotes) into
  `cont_note`. Read the end of `REPO\data\en\part-01.en.txt` and `part-01.fn.en.txt` so that your text joins theirs
  mid-sentence. Then go on as usual.
- **Front matter unit (title page and table of contents):** In the Hebrew files, each entry of the contents is a
  paragraph of its own (empty line between entries), with its page range at the end as printed (`1—10`); drop the dot
  leaders. Chapter lines (`פרק ...`) are headings. In English, one row per entry, page ranges kept ("pp. 1–10"). The
  title page: each line a heading.
- **Index unit:** two columns per page, each entry `name pages`. Write the Hebrew files with one entry per line, right
  column first, then left column; an empty line before each new letter of the alphabet. In English, one row per letter
  section: the entries separated by "; ", each name transliterated or in its English form, with its page numbers.

## 4. Output

Write `REPO\data\work\uNNN.json` (UTF-8, `ensure_ascii=False`, indent 1):

```json
{"unit": 7, "pages": ["v1_03_09", "v1_03_10", "v1_03_11", "v1_03_12", "v1_03_13"],
 "rows": [
  {"start": "v1_03_09:12", "kind": "p",
   "en": "Rabban Yoḥanan ben Zakkai ...{v1_03_09:1} ...⚠1 ...",
   "notes": {"1": {"he": "...", "note": "..."}}},
  {"start": "v1_03_10:3", "kind": "h", "en": "Chapter Three", "notes": {}}
 ],
 "footnotes": [
  {"page": "v1_03_09", "n": "1", "en": "See ...", "notes": {}}
 ],
 "report": "two or three sentences: pages done, kinds of OCR errors fixed, anything the editor should check"}
```

`start` is the page and the line number in input.txt where the row begins; `kind` is `h` for a heading, `p` for a
paragraph. Unit 2 also has `"cont_row"` and `"cont_note"` (strings).

Then check your work with a short script: every row's ⚠n has a note n and the reverse; every `{STEM:N}` token in the
English has a call `N)` on that page in your Hebrew files, and each call on your pages (outside a continued paragraph
at the top of your first page) has a token; every footnote `N)` of your pages appears once in `footnotes`; the number
of rows equals the number of headings and paragraphs that begin on your pages; no OCR line is lost or doubled (compare
word counts per page with the OCR). Fix what fails. Reply with the report and the row and footnote counts only.
