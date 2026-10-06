"""Write records.jsonl: one record per OCR'd page, for build.mjs to index with Pagefind.

Pages come from the Mistral OCR markdown (../files.json gives the paths); the report's catalogue
(../catalog/<id>.json), where present, names the section each page belongs to.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
sys.path.insert(0, WEB)
from build_data import ocr_pages  # noqa: E402

SERIES = {"J": "Japan (SCAP)", "K": "Korea (USAMGIK)"}
CAT = {r["id"]: r for r in json.loads(open(os.path.join(WEB, "data.js"), encoding="utf-8").read()[len("window.CATALOG="):-2])}


def section(rec, p):
    """Number (1-based) and title of the most specific catalogued section covering page p; (0, '') if none."""
    best = (0, "", -1)
    for i, s in enumerate(rec.get("toc", []), 1):
        if s["p"][0] <= p <= s["p"][1] and s["lv"] >= best[2]:
            best = (i, s["t"], s["lv"])
    return best[:2]


def clean(md):
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)          # image placeholders
    md = re.sub(r"[#*|_`>]+|-{3,}|\.{4,}|(?:\. ){4,}", " ", md)  # markdown and TOC leader dots
    return re.sub(r"\s+", " ", md).strip()


n = 0
with open(os.path.join(HERE, "records.jsonl"), "w", encoding="utf-8") as out:
    for f in json.load(open(os.path.join(WEB, "files.json"), encoding="utf-8")):
        rec = CAT[f["id"]]
        for p, md in sorted(ocr_pages(f["ocr"]).items()):
            body = clean(md)
            if not body: continue
            seq, stitle = section(rec, p)
            out.write(json.dumps({
                "url": f"#d/{f['id']}/pg/{p}", "content": body,
                "meta": {"title": rec["t"], "page": str(p), "id": f["id"], "ia": f["ia"], "sec": stitle, "seq": str(seq)},
                "filters": {"series": [SERIES[rec["s"]]], "year": [rec["d"][:4]], "doc": [f["id"]], "sec": [f"{f['id']}#{seq}"]},
                "sort": {"date": f"{rec['d']}|{f['id']}|{p:05d}"}}, ensure_ascii=False) + "\n")
            n += 1
print(n, "pages written to records.jsonl")
