"""check.py <id> <agy output> <model>: validate the agent's JSON and save catalog/<id>.json. Exit 1 if unusable."""
import json, re, sys
fid, path, model = sys.argv[1:4]
f = next(x for x in json.load(open("files.json")) if x["id"] == fid)
pages = max(int(n) for n in re.findall(r"^<!-- page (\d+) -->", open(f["ocr"], encoding="utf-8").read(), flags=re.M))
raw = open(path, encoding="utf-8").read().strip()
m = re.search(r"\{.*\}", raw, re.S)
if not m: print(fid, "no JSON in output"); sys.exit(1)
try: c = json.loads(m.group(0))
except Exception as e: print(fid, "bad JSON", e); sys.exit(1)
for key in ("response", "result"):   # agy --output-format json wraps the answer: {"status": ..., "response": "<json>"}
    if "sections" not in c and key in c:
        v = c[key]
        if isinstance(v, str):
            v = json.loads(re.search(r"\{.*\}", v, re.S).group(0))
        c = v
secs = c.get("sections") or []
if not secs or not c.get("summary"): print(fid, "missing sections/summary"); sys.exit(1)
bad = [s["title"] for s in secs if not (1 <= s["start_page"] <= s["end_page"] <= pages)]
for s in secs: s["start_page"], s["end_page"] = max(1, min(s["start_page"], pages)), max(1, min(s["end_page"], pages))
top = sorted({p for s in secs if s["level"] <= 2 for p in range(s["start_page"], s["end_page"] + 1)})
gaps = sorted(set(range(1, pages + 1)) - set(top))
c["_model"], c["_pages"], c["_uncovered_pages"], c["_bad_ranges"] = model, pages, gaps, bad
json.dump(c, open(f"catalog/{fid}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(fid, "ok", len(secs), "sections;", len(gaps), "uncovered pages;", len(bad), "bad ranges")
