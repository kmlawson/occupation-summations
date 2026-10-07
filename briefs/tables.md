# Brief: transcribe the statistical tables on a few report pages

You are transcribing tables from scanned pages of a U.S. Occupation monthly report (Japan, GHQ/SCAP; or Korea, USAMGIK; 1945–1948) for a research guide.

## Read the page images yourself
- For each page in your task there is a page image (JPEG) and that page's OCR text. **Look at the image with the Read tool and transcribe what you see.**
- Do NOT run OCR, do not use any image-description service, skill or script, and do not copy the OCR text without checking it. The OCR is only a cross-check: it often misreads digits, merges columns and drops rows.
- If a table continues from or onto a page not in your task, you may open that neighbouring image (same folder, same naming) to complete it.

## What counts as a table
A grid of figures or entries with rows and columns, printed as a table in the report. Include small tables (3 rows or more). Skip the report's own table of contents, lists of charts, running text, charts and graphs, and maps. For a chart with no printed figures, transcribe nothing.

## How to transcribe
- Copy every cell exactly as printed: the same digits, commas, decimal points, dashes ("-", "—"), "n.a." and so on. Do not convert units, round or add thousands separators.
- **Never guess a figure.** If you cannot read a cell, leave it as an empty string "" and record it in `unreadable` (for example "row 'Seoul', column 'Cases': digit after 1, illegible").
- An empty cell in the original is also "". Note in `notes` that blank cells are blank in the original, if that is not obvious.
- `header`: one or more header rows, each the same length as the body rows. For a header cell that spans several columns, repeat its text in each column it spans.
- `rows`: the body rows, top to bottom, each a list of strings, all the same length as the header rows. Keep row labels in the first column, including indentation shown with leading "  " if the table nests rows.
- Keep printed totals and subtotals as ordinary rows.
- **Totals:** wherever a total, subtotal or percentage column is printed, add up the parts yourself and say so in `totals_check`: what you summed, the printed total, your sum, and whether they agree. Do not correct the source; a disagreement goes in `warnings` too.
- Units ("in thousands of yen", "metric tons"), the date or period of the figures, and the source line printed under the table go in `units`, `period` and `source_note`. Footnotes go in `footnotes`.
- Title: the table's printed title, word for word, in normal capitalisation. Do not add words or qualifiers to it. If it has none, write a short descriptive title in [square brackets].
- In `ocr_check`, say in one sentence how the OCR compared: for example "OCR matched except row 4, where it read 1,836 for 1,886", or "OCR missed the table".

## Output
Write ONE file with the Write tool, at the output path in your task, holding a single JSON object, and nothing else:

```json
{"tables": [
  {"page": 12, "pages": [12], "title": "Communicable diseases reported, week ending 13 October 1945",
   "units": "cases", "period": "week ending 13 October 1945", "source_note": "",
   "header": [["Disease", "Cases", "Deaths"]],
   "rows": [["Dysentery", "1,234", "56"], ["Typhoid", "789", ""]],
   "footnotes": [], "unreadable": ["row 'Typhoid', column 'Deaths'"],
   "totals_check": "No total printed.", "warnings": [], "ocr_check": "OCR matched except Typhoid cases (read 769)."}
]}
```

If a page has no tables, it simply contributes none. Do not create, edit or delete any other file, do not run scripts or OCR, and do not run git or any network command. Reply with one line: how many tables you transcribed, how many cells you could not read, and how many totals disagreed.
