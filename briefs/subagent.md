# Brief: catalogue one monthly report (Claude Code subagent version)

You are helping build a research guide to a series of U.S. Occupation monthly reports: the "Summation of Non-Military Activities in Japan" (GHQ/SCAP, 1945-1948) and the "Summation of United States Army Military Government Activities in Korea" / "South Korean Interim Government Activities" (USAMGIK, 1946-1948).

Your input is the OCR text (Markdown) of ONE monthly report. The text has a marker `<!-- page N -->` before each PDF page. N is the PDF page number. The report's own printed page numbers are DIFFERENT (often larger, because blank or unnumbered pages are missing from the scan). Use ONLY the `<!-- page N -->` numbers for start_page and end_page.

## How to read
The file is long. Read it with the Read tool in consecutive chunks (for example 600 lines at a time, using offset and limit) until you reach the end. Read all of it. Take notes on the headings and the PDF page where each one appears as you go. Grep can help you find a heading's line, but always confirm the page by the nearest `<!-- page N -->` marker above that line.

## What to produce
1. **sections**: the report's structure, in page order, as a table of contents.
   - If the report has a printed table of contents, follow it: its parts (level 1) and sections (level 2). Add level-3 subsections only for large sections where they help a reader find things.
   - For every entry, find the page where that heading actually appears in the text and give that PDF page as start_page. Do not compute it from the printed page number; locate the heading. Record the printed page number from the TOC in printed_page (empty string if none).
   - If there is no printed table of contents, build the structure from the headings in the text.
   - Put the cover, table of contents and lists of charts together as a first entry titled "Front matter". Include appendices, annexes, chart sections and maps as entries if present.
   - Every page from 1 to the last page must fall inside some level-1 or level-2 entry. end_page of an entry is the page before the next entry at the same or higher level starts; the last entry ends at the last page.
   - Give EVERY section, parts included, a short summary: one or two concise sentences (at most 35 words) of what it reports THIS month, with something concrete in it: a name, figure, decision, place or date. Never a generic description ("This section covers labor matters") and never a restatement of the heading. A part's summary can name the main points of its sections.
2. **summary**: 120-200 words on the report as a whole: the period, the main developments reported, and what a historian would find useful.
3. **highlights**: 4-8 bullet points on the month's most notable events, decisions and figures. These may be longer than section summaries (one full sentence each, up to about 40 words) and should be concrete and detailed: who, what, how many, where.
4. **keywords**: 8-15.
5. **printed_toc_found**: true if the report has its own printed table of contents.

BURIED ISSUES: some PDFs are bound volumes that hold more than one issue (look for a second title page, a library call number such as 'M 105.13:31', a new 'Number NN' cover, or a change of declassification stamp), or contain stray pages misbound from another issue. Catalogue ALL pages in `sections` as usual, and also list each such issue in `embedded_issues` with its title, number, month (YYYY-MM, or YYYY-MM/YYYY-MM), start_page (its title page), end_page and kind ('bound' or 'misbound'). The report named above is the host and is NOT listed there. If there are none, give an empty list.

Correct obvious OCR misreadings in headings. Never invent a page number: if you cannot find a heading in the text, use the nearest page where its content begins.

## Output
Write ONE file, a single JSON object, with the Write tool, to the output path given in your task. Nothing else: do not create, edit or delete any other file, and do not run git or any network command. The object must have exactly these keys:

```json
{
 "summary": "...",
 "highlights": ["...", "..."],
 "keywords": ["...", "..."],
 "printed_toc_found": true,
 "embedded_issues": [],
 "sections": [
  {"title": "Front matter", "level": 1, "printed_page": "", "start_page": 1, "end_page": 3, "summary": "Cover, table of contents and list of charts."},
  {"title": "Part I: General", "level": 1, "printed_page": "1", "start_page": 4, "end_page": 12, "summary": "..."},
  {"title": "Organization under SCAP", "level": 2, "printed_page": "3", "start_page": 5, "end_page": 6, "summary": "..."}
 ]
}
```

`level` is an integer; `start_page` and `end_page` are integers between 1 and the last page.

When done, reply in at most 5 lines: the number of sections, whether a printed TOC was found, and any headings whose page you could not locate.
