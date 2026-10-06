# Brief: polish one report's catalogue (no source reading)

You are editing the catalogue of one monthly U.S. Occupation report (Japan, GHQ/SCAP; or Korea, USAMGIK; 1945–1948) for a research guide. You work ONLY from the catalogue JSON named in your task; do not open the OCR text.

The catalogue has `summary`, `highlights` and `sections`. Each section has a `title`, `level`, `start_page`, `end_page` and `summary`. Some sections contain others: a part (level 1) holds the level-2 sections whose pages fall inside it.

## What to do

1. **Section summaries.** For EVERY section, write a summary of one or two concise sentences, at most 35 words, that says something concrete: a name, a figure, a decision, a place or a date.
   - Start from the existing summary. Keep its most concrete facts, cut generalities, and shorten long ones.
   - For a part or other section that contains sections, you may draw on the summaries of the sections inside it.
   - Never add a fact that is not in the catalogue. Never restate the heading or write a generic line such as "This section covers labor matters".
   - "Front matter" and "Back matter" entries can simply say what they hold, for example "Cover, contents and list of charts."
   - If a section's existing text (and, for a part, its sub-sections' text) gives you nothing concrete to say, put its index in `needs_source` and give your best short summary anyway.
2. **Highlights.** Return 4–8 bullet points on the month's most notable events, decisions and figures. These may be longer than section summaries: one full sentence each, up to about 40 words, concrete and detailed (who, what, how many, where). Improve the existing highlights, drawing on the overall summary and the section summaries. Again, add nothing that is not in the catalogue.

## Output
Write ONE file with the Write tool, at the output path in your task, holding a single JSON object, and nothing else:

```json
{"summaries": {"0": "…", "1": "…"}, "highlights": ["…", "…"], "needs_source": [7, 12]}
```

The keys of `summaries` are the section indexes (0-based position in `sections`), as strings, with one entry for every section. Do not create, edit or delete any other file, do not run scripts, and do not run git or any network command. Reply with one line: the number of summaries written and the number of `needs_source` entries.
