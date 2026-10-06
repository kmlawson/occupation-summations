# Brief: rewrite section summaries from the full text (second pass)

You are improving a research guide to U.S. Occupation monthly reports on Japan (GHQ/SCAP) and Korea (USAMGIK), 1945–1948. A first pass made a table of contents for each report, but many section summaries were written from a skim and are thin or generic. Your job is to make every section's summary specific and evenly detailed.

## Your input (two files, named in your task)
- `<name>.md`: an excerpt of the report's OCR text. A marker `<!-- page N -->` comes before each PDF page.
- `<name>.json`: the sections whose text is in this excerpt, each with `index`, `title`, `level`, `start_page`, `end_page` and the `current_summary`.

## What to do
1. **Read the whole excerpt, every line**, with the Read tool in consecutive chunks (offset and limit, about 500 lines at a time) until the end. Do not grep or skim instead of reading; the point of this pass is a full read.
2. For **every** section in the JSON, write a new summary of what that section reports THIS month, from its own pages (start_page to end_page):
   - 2–3 sentences, 35–70 words: the main developments, decisions, figures and names, as specific as the text allows.
   - Every section gets the same care, whether it is the first in the excerpt or the last; aim for even length and detail.
   - Report what the text says. Never invent a figure; if a number is garbled in the OCR, leave it out. Correct obvious OCR misspellings of names.
3. **Long sections:** if a section in the JSON runs more than 20 pages and has clear sub-headings in the text, you may also add finer entries under it in `new_subsections`. Give each its title (as printed, title case), `level` (one more than its parent), `printed_page` (empty string if none), `start_page` (the PDF page where its heading appears; find it under its `<!-- page N -->` marker), `end_page`, and a summary written the same way. Sub-entries must lie inside the parent's page range, be in page order and not overlap one another.

## Output
Write ONE file with the Write tool, at the output path in your task, holding a single JSON object, and nothing else:

```json
{
 "summaries": {"12": "…", "13": "…"},
 "new_subsections": [
  {"title": "Rice Collection", "level": 3, "printed_page": "", "start_page": 41, "end_page": 44, "summary": "…"}
 ]
}
```

The keys of `summaries` are the `index` values from the input JSON, as strings, and there must be one for every section listed there. `new_subsections` may be an empty list.

Do not create, edit or delete any other file, and do not run git or any network command. Reply in at most 3 lines: how many summaries you wrote, how many subsections you added, and anything you could not read.
