# Brief: write missing section summaries from the source text

You are filling gaps in a research guide to U.S. Occupation monthly reports on Japan (GHQ/SCAP) and Korea (USAMGIK), 1945–1948. Some sections in a report's table of contents have no summary, or only a generic one. You write those summaries from the report's own text.

## Your input (two files, named in your task)
- `<name>.md`: an excerpt of the report's OCR text. A marker `<!-- page N -->` comes before each PDF page.
- `<name>.json`: the sections to write, each with `index`, `title`, `level`, `start_page`, `end_page` and the `current_summary`.

## What to do
1. Read each listed section's pages in the excerpt, every line, with the Read tool (use offset and limit; Grep can find where a page starts).
2. For each section, write a summary of one or two concise sentences, at most 35 words, of what it reports THIS month. Include something concrete: a name, a figure, a decision, a place or a date.
   - Never restate the heading or write a generic line.
   - Never invent a figure. If a number is garbled in the OCR, leave it out. Correct obvious OCR misspellings of names.
   - If the section's pages really hold nothing but a chart, a table without readable text, or blank pages, say exactly that in one short sentence. For example: "Chart of monthly coal output, January–June 1947; no text."

## Output
Write ONE file with the Write tool, at the output path in your task, holding a single JSON object, and nothing else:

```json
{"summaries": {"12": "…", "13": "…"}}
```

The keys are the `index` values from the input JSON, as strings, with one for every section listed. Do not create, edit or delete any other file, do not run scripts, and do not run git or any network command. Reply with one line: how many summaries you wrote, and any section you could not find in the text.
