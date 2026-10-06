"""Second pass for even section coverage.

  python3 briefs/refine.py split <id> [<id> ...]   cut each report into excerpts that hold whole leaf sections
                                                    -> logs/refine/<id>__NN.md and <id>__NN.json
  python3 briefs/refine.py merge <id> [<id> ...]   put the rewritten summaries back into catalog/<id>.json

A leaf section (one with no deeper section inside it) is summarised from its full text. A part that only
contains sections keeps its short summary. Excerpts stay under MAX_CHARS so an agent can read every line.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from build_data import ocr_pages  # noqa: E402

OUT = os.path.join(HERE, "logs", "refine")
MAX_CHARS = 160_000


def leaves(secs):
    """Indexes of sections that have no deeper section starting inside their page range."""
    out = []
    for i, s in enumerate(secs):
        inner = any(t["level"] > s["level"] and s["start_page"] <= t["start_page"] <= s["end_page"] and j != i
                    for j, t in enumerate(secs))
        if not inner: out.append(i)
    return out


def split(fid):
    host = fid.split("-in-")[-1]   # a buried issue's pages are in its host PDF
    f = next(x for x in json.load(open(os.path.join(HERE, "files.json"))) if x["id"] == host)
    pages = ocr_pages(f["ocr"])
    if host != fid:
        f = dict(f, t=next(e["t"] for e in json.load(open(os.path.join(HERE, "catalog", "embedded.json"))) if f"-in-{e['host']}" in fid and f"-{e['no']:02d}-" in fid))
    c = json.load(open(os.path.join(HERE, "catalog", fid + ".json")))
    secs = c["sections"]
    size = lambda a, b: sum(len(pages.get(p, "")) for p in range(a, b + 1))
    chunks, cur = [], []
    for i in leaves(secs):
        s = secs[i]
        if cur:
            a = min(secs[j]["start_page"] for j in cur)
            if size(a, max(secs[j]["end_page"] for j in cur + [i])) > MAX_CHARS:
                chunks.append(cur); cur = []
        cur.append(i)
    if cur: chunks.append(cur)
    os.makedirs(OUT, exist_ok=True)
    for n, idx in enumerate(chunks, 1):
        a, b = min(secs[j]["start_page"] for j in idx), max(secs[j]["end_page"] for j in idx)
        name = f"{fid}__{n:02d}"
        with open(os.path.join(OUT, name + ".md"), "w", encoding="utf-8") as fh:
            for p in range(a, b + 1):
                fh.write(f"<!-- page {p} -->\n\n{pages.get(p, '')}\n\n")
        json.dump({"report": f["t"], "pages": [a, b], "sections": [
            {"index": j, "title": secs[j]["title"], "level": secs[j]["level"], "start_page": secs[j]["start_page"],
             "end_page": secs[j]["end_page"], "current_summary": secs[j]["summary"]} for j in idx]},
            open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(name, f"pp {a}-{b}", f"{size(a, b) // 1000}k chars", len(idx), "sections")


def merge(fid):
    path = os.path.join(HERE, "catalog", fid + ".json")
    c = json.load(open(path, encoding="utf-8"))
    done = missing = 0; added = []
    for js in sorted(f for f in os.listdir(OUT) if f.startswith(fid + "__") and f.endswith(".json") and ".out" not in f):
        out = os.path.join(OUT, js[:-5] + ".out.json")
        want = [s["index"] for s in json.load(open(os.path.join(OUT, js)))["sections"]]
        if not os.path.exists(out):
            print("  no output for", js[:-5]); missing += len(want); continue
        got = json.load(open(out, encoding="utf-8")).get("summaries", {})
        res = json.load(open(out, encoding="utf-8"))
        for i in want:
            s = got.get(str(i), "").strip()
            if s: c["sections"][i]["summary"] = s; done += 1
            else: missing += 1
        for n in res.get("new_subsections", []):   # finer structure inside long sections
            n = {k: n[k] for k in ("title", "level", "printed_page", "start_page", "end_page", "summary") if k in n}
            n.setdefault("printed_page", ""); added.append(n)
    secs = c["sections"]
    for n in sorted(added, key=lambda n: n["start_page"]):
        # insert after the last existing section that starts on or before it (keeps page order; parents come first)
        k = max([i for i, s in enumerate(secs) if s["start_page"] <= n["start_page"]] or [0])
        secs.insert(k + 1, n)
    c["_refined"] = f"{done} leaf summaries rewritten from full section text"
    json.dump(c, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(fid, "rewrote", done, "missing", missing, "added", len(added))


if __name__ == "__main__":
    {"split": split, "merge": merge}[sys.argv[1]] and [{"split": split, "merge": merge}[sys.argv[1]](i) for i in sys.argv[2:]]
