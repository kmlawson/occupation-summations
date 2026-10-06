#!/bin/zsh
# run1.sh <id> : catalogue one report with agy; writes catalog/<id>.json.
# Tries Gemini, then Sonnet. A model out of quota is skipped until its reset time (logs/EXHAUSTED.<model> holds the epoch).
# Exit 0 done, 1 failed, 255 every model out of quota (stops xargs from starting more jobs).
cd "${0:A:h}/.." || exit 1
id=$1; mkdir -p logs catalog
[ -s "catalog/$id.json" ] && exit 0
grep -qx "$id" logs/claimed.txt 2>/dev/null && exit 0   # being catalogued elsewhere
python3 - "$id" >| "logs/$id.prompt" <<'PY'
import json, sys, re
f = next(x for x in json.load(open("files.json")) if x["id"] == sys.argv[1])
pages = max(int(n) for n in re.findall(r"^<!-- page (\d+) -->", open(f["ocr"], encoding="utf-8").read(), flags=re.M))
print(open("briefs/catalog.prompt").read().replace("{OCR}", f["ocr"]).replace("{TITLE}", f["t"]).replace("{PAGES}", str(pages)), end="")
PY
dir=$(python3 -c 'import json,sys,os;print(os.path.dirname(next(x for x in json.load(open("files.json")) if x["id"]==sys.argv[1])["ocr"]))' "$id")
for model in gemini-3.8-flash-high claude-sonnet-5-5-high; do
  ex=logs/EXHAUSTED.$model
  [ -e $ex ] && [ $(cat $ex) -gt $(date +%s) ] && continue
  for try in 1 2; do
    taskpolicy -b agy -p "$(cat logs/$id.prompt)" --model $model --add-dir "$dir" --output-format json --json-schema briefs/schema.json \
       --print-timeout 40m >| "logs/$id.$model.out" 2>| "logs/$id.$model.err"; rc=$?
    if python3 briefs/check.py "$id" "logs/$id.$model.out" $model >> logs/check.txt; then echo "$id ok $model" >> logs/done.txt; exit 0; fi
    if grep -q 'RESOURCE_EXHAUSTED' "logs/$id.$model.err"; then
      python3 - "logs/$id.$model.err" >| $ex <<'PY'
import re, sys, time
m = re.search(r"Resets in (?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", open(sys.argv[1]).read())
secs = (int(m[1] or 0) * 3600 + int(m[2] or 0) * 60 + int(m[3] or 0)) if m else 3600
print(int(time.time()) + secs + 120)
PY
      echo "$id QUOTA $model until $(date -r $(cat $ex) +%H:%M)" >> logs/done.txt; continue 2
    fi
    echo "$id fail $model rc=$rc try $try" >> logs/done.txt   # e.g. an empty response: retry once, then the next model
  done
done
# every model either failed or is out of quota: 255 only if both are out of quota now
n=0; for f in logs/EXHAUSTED.*(N); do [ $(cat $f) -gt $(date +%s) ] && n=$((n+1)); done
[ $n -ge 2 ] && exit 255
exit 1
