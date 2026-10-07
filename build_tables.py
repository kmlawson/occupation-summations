"""Build tables-index.js (window.TINDEX), tables/r/<report>.json and tables.json from the transcribed tables in tables/src/*.json.

Each source file is one transcription job's output: {"tables": [...]} for a few pages of one report,
named <report id>__NN.json. Tables are ordered by report (as in data.js) and page.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "tables", "src")


# "check" only when a cell could not be read or a printed total does not add up; other notes are shown without the flag
DIS = re.compile(r"\bdisagree|do(?:es)? not (?:agree|equal|match|reconcile|add up)|doesn't (?:agree|match|add up)|\bdiffers?\b|mismatch|≠|\boff by\b|\bnot equal\b", re.I)


def needs_check(t):
    return bool(t["unr"]) or bool(DIS.search(t["tot"])) or any(DIS.search(w) and re.search(r"total|sum|add", w, re.I) for w in t["w"])


def main():
    order = {r["id"]: i for i, r in enumerate(json.loads(open(os.path.join(HERE, "data.js"), encoding="utf-8").read()[len("window.CATALOG="):-2]))}
    out = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".json"): continue
        rid = fn.split("__")[0]
        for t in json.load(open(os.path.join(SRC, fn), encoding="utf-8")).get("tables", []):
            rows, head = t.get("rows") or [], t.get("header") or []
            if not rows: continue
            out.append({"r": rid, "p": int(t.get("page") or (t.get("pages") or [0])[0]), "pp": t.get("pages") or [t.get("page")],
                        "t": t.get("title", "").strip() or "[Untitled table]", "u": t.get("units", ""), "pe": t.get("period", ""),
                        "src": t.get("source_note", ""), "h": head, "rows": rows, "fn": t.get("footnotes", []),
                        "unr": t.get("unreadable", []), "tot": t.get("totals_check", ""), "w": t.get("warnings", []),
                        "oc": t.get("ocr_check", "")})
    out.sort(key=lambda t: (order.get(t["r"], 999), t["p"]))
    seen = {}
    for t in out:   # stable IDs: <report>-p<page>[-n]
        k = f"{t['r']}-p{t['p']}"; seen[k] = seen.get(k, 0) + 1
        t["id"] = k if seen[k] == 1 else f"{k}-{seen[k]}"
    for t in out:
        if seen.get(f"{t['r']}-p{t['p']}", 0) > 1 and t["id"] == f"{t['r']}-p{t['p']}": t["id"] += "-1"
    for t in out: t["f"] = 1 if needs_check(t) else 0
    cells = sum(len(r) for t in out for r in t["rows"])
    # small index loaded on every page (pills, list of tables); full tables per report, fetched on demand
    with open(os.path.join(HERE, "tables-index.js"), "w", encoding="utf-8") as fh:
        idx = [[t["id"], t["r"], t["p"], t["f"], t["t"]] for t in out]
        fh.write("window.TINDEX=" + json.dumps(idx, ensure_ascii=False, separators=(",", ":")) + ";\n")
    rdir = os.path.join(HERE, "tables", "r"); os.makedirs(rdir, exist_ok=True)
    for f in os.listdir(rdir): os.remove(os.path.join(rdir, f))
    for r in sorted({t["r"] for t in out}):
        json.dump([t for t in out if t["r"] == r], open(os.path.join(rdir, r + ".json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    old = os.path.join(HERE, "tables.js")
    if os.path.exists(old): os.remove(old)
    json.dump(out, open(os.path.join(HERE, "tables.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"{len(out)} tables, {cells} cells, from {len({t['r'] for t in out})} reports -> tables-index.js, tables/r/*.json, tables.json")


if __name__ == "__main__":
    main()
