"""tables_jobs.py IMGDIR ID [ID ...] : build table-transcription jobs (logs/tables/jobs-<first id>.json).

Candidate pages are those whose OCR has a markdown table or a "Table" heading; jobs hold up to 5 pages.
Page images must already be rendered to IMGDIR/<id>/p-NN.jpg (pdftoppm naming). Reports whose images
came out blank (1x1 px, a pdftoppm failure on some scans) are listed so they can be re-extracted.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from build_data import ocr_pages  # noqa: E402


def main(img, ids):
    F = {f["id"]: f for f in json.load(open(os.path.join(HERE, "files.json")))}
    D = os.path.join(HERE, "logs", "tables"); os.makedirs(D, exist_ok=True)
    jobs, bad = [], []
    for i in ids:
        names = sorted(os.listdir(os.path.join(img, i)))
        w = len(re.search(r"p-(\d+)\.jpg", names[-1]).group(1))
        probe = os.path.join(img, i, names[len(names) // 2])
        if "pixelWidth: 1\n" in subprocess.run(["sips", "-g", "pixelWidth", probe], capture_output=True, text=True).stdout + "\n":
            bad.append(i); continue
        pg = ocr_pages(F[i]["ocr"])
        cand = [p for p, t in sorted(pg.items()) if t.count("\n|") >= 3 or re.search(r"(?im)^#*\s*table\b", t)]
        for k in range(0, len(cand), 5):
            ps = cand[k:k + 5]; name = f"{i}__{k // 5 + 1:02d}"
            if os.path.exists(os.path.join(D, name + ".out.json")): continue
            with open(os.path.join(D, name + ".ocr.md"), "w") as fh:
                for p in ps: fh.write(f"<!-- page {p} -->\n\n{pg[p]}\n\n")
            jobs.append({"n": name, "id": i, "t": F[i]["t"], "p": ps, "w": w})
    out = os.path.join(D, f"jobs-{ids[0]}.json")
    json.dump(jobs, open(out, "w"), indent=1)
    print(len(jobs), "jobs,", sum(len(j["p"]) for j in jobs), "pages ->", out)
    if bad: print("BLANK IMAGES (re-extract with pdfimages):", bad)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
