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


def main():
    recs = []
    for f in files():
        pages = ocr_pages(f["ocr"])
        rec = {k: f[k] for k in ("id", "ia", "s", "no", "d", "d2", "t", "v")}
        rec["pg"] = max(pages) if pages else 0
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
    json.dump([{**{k: f[k] for k in ("id", "ia", "s", "t", "pdf", "ocr")}} for f in files()],
              open(os.path.join(HERE, "files.json"), "w"), indent=1, ensure_ascii=False)
    tmp = os.path.join(HERE, "data.js.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("window.CATALOG=" + json.dumps(recs, ensure_ascii=False, separators=(",", ":")) + ";\n")
    os.replace(tmp, os.path.join(HERE, "data.js"))
    done = sum(1 for r in recs if not r.get("sk"))
    print(f"{len(recs)} reports ({done} catalogued), {sum(r['pg'] for r in recs)} pages -> data.js")


if __name__ == "__main__":
    main()
