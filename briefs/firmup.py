"""Firm up the catalogue: polish every report's summaries and highlights, then fill weak sections from the OCR.

  python3 briefs/firmup.py polish-jobs          -> logs/polish/jobs.json (one job per catalogued report)
  python3 briefs/firmup.py polish-merge         apply logs/polish/<id>.out.json to catalog/<id>.json
  python3 briefs/firmup.py weak                 list sections whose summary is empty, generic or flagged
  python3 briefs/firmup.py fill-jobs            cut OCR excerpts for the weak sections -> logs/fill/jobs.json
  python3 briefs/firmup.py fill-merge           apply logs/fill/*.out.json
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from build_data import ocr_pages, embedded  # noqa: E402

CAT = os.path.join(HERE, "catalog")
LOGS = os.path.join(HERE, "logs")
MAX_CHARS = 160_000
GENERIC = {"japan", "korea", "korean", "japanese", "scap", "usamgik", "part", "section", "summation", "military",
           "government", "american", "the", "this", "it", "in", "a", "an", "of", "and", "south", "united", "states"}


def ids():
    out = [f["id"] for f in json.load(open(os.path.join(HERE, "files.json")))] + [e["id"] for e in embedded()]
    return [i for i in out if os.path.exists(os.path.join(CAT, i + ".json"))]


def load(i):
    return json.load(open(os.path.join(CAT, i + ".json"), encoding="utf-8"))


def save(i, c):
    json.dump(c, open(os.path.join(CAT, i + ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def concrete(summary, title):
    """True if a summary says something specific: a figure, or a proper name that is not just the heading."""
    s = summary.strip()
    if len(s.split()) < 6: return False
    if re.search(r"\d", s): return True
    tw = {w.lower() for w in re.findall(r"[A-Za-z]+", title)}
    names = [w for w in re.findall(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]+", s) if w.lower() not in GENERIC and w.lower() not in tw]
    return len(names) >= 1 and not re.match(r"(?i)^(this|the) (section|part|chapter) (covers|reports|discusses|describes|deals)", s)


def weak_sections(c):
    out = set(c.get("_needs_source", []))
    for i, s in enumerate(c["sections"]):
        if re.match(r"(?i)(front|back) matter", s["title"]): continue
        t = s.get("summary", "").strip()
        if len(t.split()) < 6 or re.match(r"(?i)^(this|the) (section|part|chapter) (covers|reports|discusses|describes|deals)", t) \
                or t.lower().rstrip(".") == s["title"].lower(): out.add(i)
    return sorted(out)


def host_pages(i):
    host = i.split("-in-")[-1]
    f = next(x for x in json.load(open(os.path.join(HERE, "files.json"))) if x["id"] == host)
    return f, ocr_pages(f["ocr"])


def main(cmd):
    if cmd == "polish-jobs":
        os.makedirs(os.path.join(LOGS, "polish"), exist_ok=True)
        jobs = [{"id": i, "cat": os.path.join(CAT, i + ".json"), "out": os.path.join(LOGS, "polish", i + ".out.json"),
                 "title": load(i).get("summary", "")[:0] or i} for i in ids()]
        json.dump(jobs, open(os.path.join(LOGS, "polish", "jobs.json"), "w"), indent=1)
        print(len(jobs), "polish jobs")
    elif cmd == "polish-merge":
        for i in ids():
            out = os.path.join(LOGS, "polish", i + ".out.json")
            if not os.path.exists(out): print("  no polish output for", i); continue
            r, c = json.load(open(out, encoding="utf-8")), load(i)
            n = 0
            for k, v in r.get("summaries", {}).items():
                if v.strip() and int(k) < len(c["sections"]): c["sections"][int(k)]["summary"] = v.strip(); n += 1
            if len(r.get("highlights", [])) >= 3: c["highlights"] = r["highlights"]
            c["_needs_source"] = r.get("needs_source", [])
            c["_polished"] = True
            save(i, c)
            print(i, "polished", n, "of", len(c["sections"]), "flagged", len(c["_needs_source"]))
    elif cmd == "weak":
        tot = 0
        for i in ids():
            c = load(i); w = weak_sections(c); tot += len(w)
            if w: print(i, len(w), [c["sections"][j]["title"][:30] for j in w[:4]])
            if len(c.get("highlights", [])) < 4: print(i, "HIGHLIGHTS", len(c.get("highlights", [])))
        print("total weak sections:", tot)
    elif cmd == "fill-jobs":
        d = os.path.join(LOGS, "fill"); os.makedirs(d, exist_ok=True)
        jobs = []
        for i in ids():
            c = load(i); w = weak_sections(c)
            if not w: continue
            f, pages = host_pages(i)
            size = lambda a, b: sum(len(pages.get(p, "")) for p in range(a, b + 1))
            chunks, cur = [], []
            for j in w:
                s = c["sections"][j]
                if cur and size(min(c["sections"][k]["start_page"] for k in cur), max(c["sections"][k]["end_page"] for k in cur + [j])) > MAX_CHARS:
                    chunks.append(cur); cur = []
                cur.append(j)
            if cur: chunks.append(cur)
            for n, idx in enumerate(chunks, 1):
                secs = [c["sections"][k] for k in idx]
                name = f"{i}__{n:02d}"
                # only the pages of the listed sections, so the agent reads exactly what it needs
                want = sorted({p for s in secs for p in range(s["start_page"], s["end_page"] + 1)})
                with open(os.path.join(d, name + ".md"), "w", encoding="utf-8") as fh:
                    for p in want: fh.write(f"<!-- page {p} -->\n\n{pages.get(p, '')}\n\n")
                json.dump({"report": i, "sections": [{"index": k, "title": c["sections"][k]["title"], "level": c["sections"][k]["level"],
                           "start_page": c["sections"][k]["start_page"], "end_page": c["sections"][k]["end_page"],
                           "current_summary": c["sections"][k].get("summary", "")} for k in idx]},
                          open(os.path.join(d, name + ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
                jobs.append({"name": name, "md": os.path.join(d, name + ".md"), "json": os.path.join(d, name + ".json"),
                             "out": os.path.join(d, name + ".out.json"), "n": len(idx)})
        json.dump(jobs, open(os.path.join(d, "jobs.json"), "w"), indent=1)
        print(len(jobs), "fill jobs,", sum(j["n"] for j in jobs), "sections")
    elif cmd == "fill-merge":
        d = os.path.join(LOGS, "fill")
        for js in sorted(f for f in os.listdir(d) if f.endswith(".json") and ".out" not in f and f != "jobs.json"):
            out = os.path.join(d, js[:-5] + ".out.json")
            if not os.path.exists(out): print("  no output for", js[:-5]); continue
            meta = json.load(open(os.path.join(d, js))); i = meta["report"]; c = load(i)
            got = json.load(open(out, encoding="utf-8")).get("summaries", {})
            for s in meta["sections"]:
                v = got.get(str(s["index"]), "").strip()
                if v: c["sections"][s["index"]]["summary"] = v
            c["_needs_source"] = [k for k in c.get("_needs_source", []) if str(k) not in got]
            save(i, c)
        print("merged")


if __name__ == "__main__":
    main(sys.argv[1])
