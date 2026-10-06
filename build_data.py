"""Build data.js (window.CATALOG) and files.json from the two upload lists, the OCR text and catalog/<id>.json.

Every report appears even before it is catalogued (placeholder: title, date, page count; sk=1).
Run from anywhere: python3 build_data.py
"""
import csv, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)  # .../SCAP and USAMGIK Documents
SERIES = {
    "J": os.path.join(BASE, "Summation of Non-Military Activities in Japan", "Summation of Non-Military Activities in Japan"),
    "K": os.path.join(BASE, "Summation of US Army Military Government in Korea"),
}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def short_id(s, ia):
    """J-16, J-04-phw, J-04-nlm, K-12-v2, K-12-econ, K-23-1 ..."""
    m = re.search(r"-no-(\d+)(?:-part-(\d+))?-\d{4}-\d{2}(?:-(.*))?$", ia)
    sid = f"{s}-{int(m[1]):02d}" + (f"-{m[2]}" if m[2] else "")
    extra = {"public-health-welfare": "phw", "economic": "econ"}.get(m[3], m[3])
    return sid + (f"-{extra}" if extra else "")


def variant(title):
    if title.endswith(": Public Health and Welfare"): return "Public Health and Welfare section"
    if title.endswith(": Economic"): return "Economic section"
    if "[version 2]" in title: return "Second copy"
    if "[NLM copy]" in title: return "NLM copy"
    return ""


def ocr_pages(path):
    """{page: text} from Mistral OCR markdown with <!-- page N --> markers."""
    if not os.path.exists(path): return {}
    parts = re.split(r"^<!-- page (\d+) -->\s*$", open(path, encoding="utf-8").read(), flags=re.M)
    return {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts), 2)}


def files():
    """One dict per PDF, in date order (Japan before Korea within a month)."""
    out = []
    for s, folder in SERIES.items():
        for r in csv.DictReader(open(os.path.join(folder, "upload.csv"), encoding="utf-8")):
            ocr = os.path.join(folder, "ocr", os.path.basename(r["file"])[:-4] + ".md")
            title = re.sub(r"\s*\[(version 2|NLM copy)\]", "", r["title"])
            m = re.search(r"\((\w+)(?:-(\w+))? (\d{4})\)", title)
            d = f"{m[3]}-{MONTHS.index(m[1]) + 1:02d}"
            d2 = f"{m[3]}-{MONTHS.index(m[2]) + 1:02d}" if m[2] else ""
            no = re.search(r"No\. (\d+)", title)[1]
            out.append({"id": short_id(s, r["identifier"]), "ia": r["identifier"], "s": s, "no": int(no), "d": d, "d2": d2,
                        "t": title, "v": variant(r["title"]), "pdf": r["file"], "ocr": ocr})
    out.sort(key=lambda x: (x["d"], x["s"], x["no"], x["v"] != "", x["id"]))
    return out


def embedded():
    """Issues bound inside another PDF: catalog/embedded.json, plus any an agent reported in catalog/<id>.json
    (embedded_issues). One dict per buried issue: host, no, d, d2, t, ranges [[a, b], ...], kind."""
    out = json.load(open(os.path.join(HERE, "catalog", "embedded.json"), encoding="utf-8"))
    for f in files():
        cat = os.path.join(HERE, "catalog", f["id"] + ".json")
        if not os.path.exists(cat): continue
        for e in json.load(open(cat, encoding="utf-8")).get("embedded_issues", []):
            a = e.get("start_page", 0)
            if any(x["host"] == f["id"] and abs(x["ranges"][0][0] - a) <= 3 for x in out): continue
            m = re.match(r"(\d{4}-\d{2})(?:/(\d{4}-\d{2}))?", e.get("month", ""))
            if not (m and e.get("number")): continue
            out.append({"host": f["id"], "no": int(e["number"]), "d": m[1], "d2": m[2] or "", "t": e.get("title", ""),
                        "ranges": [[a, e["end_page"]]], "kind": e.get("kind", "bound"), "found": "reported by the cataloguing model"})
    for e in out:
        e["s"] = e["host"][0]
        e["id"] = f"{e['s']}-{e['no']:02d}-in-{e['host']}"
    return out


def inside(sec, ranges):
    return any(a <= sec["p"][0] and sec["p"][1] <= b for a, b in ranges)


OVERRIDES = json.load(open(os.path.join(HERE, "catalog", "overrides.json"), encoding="utf-8"))


def main():
    recs = []
    for f in files():
        pages = ocr_pages(f["ocr"])
        rec = {k: f[k] for k in ("id", "ia", "s", "no", "d", "d2", "t", "v")}
        rec["pg"] = max(pages) if pages else 0
        rec.update(OVERRIDES.get(f["id"], {}))   # corrections, e.g. a PDF filed under the wrong series
        cat = os.path.join(HERE, "catalog", f["id"] + ".json")
        if os.path.exists(cat):
            c = json.load(open(cat, encoding="utf-8"))
            rec.update({"o": c.get("summary", ""), "h": c.get("highlights", []), "k": c.get("keywords", []),
                        "toc": [{"t": x["title"], "lv": x.get("level", 1), "p": [x["start_page"], x["end_page"]],
                                 "pp": x.get("printed_page", ""), "s": x.get("summary", "")} for x in c.get("sections", [])],
                        "by": c.get("_model", "")})
        else:
            rec.update({"o": "", "h": [], "k": [], "toc": [], "sk": 1})
        recs.append(rec)
    # buried issues: their own records; the host keeps only its own sections
    by = {r["id"]: r for r in recs}
    for e in embedded():
        host = by[e["host"]]
        rec = {"id": e["id"], "ia": host["ia"], "s": e["s"], "no": e["no"], "d": e["d"], "d2": e["d2"], "t": e["t"],
               "v": ("Misbound pages in " if e["kind"] == "misbound" else "Bound in ") + e["host"],
               "host": e["host"], "rg": e["ranges"], "kind": e["kind"], "found": e["found"],
               "pg": sum(b - a + 1 for a, b in e["ranges"])}
        own = os.path.join(HERE, "catalog", e["id"] + ".json")
        if os.path.exists(own):
            c = json.load(open(own, encoding="utf-8"))
            rec.update({"o": c.get("summary", ""), "h": c.get("highlights", []), "k": c.get("keywords", []),
                        "toc": [{"t": x["title"], "lv": x.get("level", 1), "p": [x["start_page"], x["end_page"]],
                                 "pp": x.get("printed_page", ""), "s": x.get("summary", "")} for x in c.get("sections", [])],
                        "by": c.get("_model", "")})
        elif not host.get("sk"):
            toc = [dict(x) for x in host["toc"] if inside(x, e["ranges"])]
            # drop a wrapper entry that spans the whole buried issue, and start levels at 1
            wrap = [x for x in toc if [x["p"]] == e["ranges"] or (x["p"][0] <= e["ranges"][0][0] and x["p"][1] >= e["ranges"][-1][1])]
            toc = [x for x in toc if x not in wrap[:1]]
            low = min([x["lv"] for x in toc] or [1])
            for x in toc: x["lv"] = x["lv"] - low + 1
            rec.update({"o": wrap[0]["s"] if wrap else "", "h": [], "k": [], "toc": toc, "by": host.get("by", "")})
        else:
            rec.update({"o": "", "h": [], "k": [], "toc": [], "sk": 1})
        host.setdefault("emb", []).append(e["id"])
        host["toc"] = [x for x in host["toc"] if not inside(x, e["ranges"])]
        recs.append(rec)
    recs.sort(key=lambda x: (x["d"], x["s"], x["no"], "host" in x, x.get("v", "") != "", x["id"]))
    json.dump([{**{k: f[k] for k in ("id", "ia", "s", "t", "pdf", "ocr")}} for f in files()],
              open(os.path.join(HERE, "files.json"), "w"), indent=1, ensure_ascii=False)
    tmp = os.path.join(HERE, "data.js.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("window.CATALOG=" + json.dumps(recs, ensure_ascii=False, separators=(",", ":")) + ";\n")
    os.replace(tmp, os.path.join(HERE, "data.js"))
    done = sum(1 for r in recs if not r.get("sk"))
    print(f"{len(recs)} records incl. {sum('host' in r for r in recs)} buried issues ({done} catalogued), {sum(r['pg'] for r in recs)} pages -> data.js")


if __name__ == "__main__":
    main()
