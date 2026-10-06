"""Build tables.js (window.TABLES) and tables.json from the transcribed tables in tables/src/*.json.

Each source file is one transcription job's output: {"tables": [...]} for a few pages of one report,
named <report id>__NN.json. Tables are ordered by report (as in data.js) and page.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "tables", "src")


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
    cells = sum(len(r) for t in out for r in t["rows"])
    with open(os.path.join(HERE, "tables.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TABLES=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    json.dump(out, open(os.path.join(HERE, "tables.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"{len(out)} tables, {cells} cells, from {len({t['r'] for t in out})} reports -> tables.js, tables.json")


if __name__ == "__main__":
    main()
