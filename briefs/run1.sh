#!/bin/zsh
# run1.sh <id> : catalogue one report with agy; writes catalog/<id>.json. Gemini first, Sonnet once Gemini is out of quota.
cd "${0:A:h}/.." || exit 1
id=$1; mkdir -p logs catalog
[ -s "catalog/$id.json" ] && { echo "$id skip" >> logs/done.txt; exit 0; }
python3 - "$id" > "logs/$id.prompt" <<'PY'
import json, sys, re
f = next(x for x in json.load(open("files.json")) if x["id"] == sys.argv[1])
pages = max(int(n) for n in re.findall(r"^<!-- page (\d+) -->", open(f["ocr"], encoding="utf-8").read(), flags=re.M))
print(open("briefs/catalog.prompt").read().replace("{OCR}", f["ocr"]).replace("{TITLE}", f["t"]).replace("{PAGES}", str(pages)), end="")
PY
dir=$(python3 -c 'import json,sys,os;print(os.path.dirname(next(x for x in json.load(open("files.json")) if x["id"]==sys.argv[1])["ocr"]))' "$id")
for model in gemini-3.8-flash-high claude-sonnet-5-5-high; do
  [ "$model" = gemini-3.8-flash-high ] && [ -e logs/GEMINI_EXHAUSTED ] && continue
  taskpolicy -b agy -p "$(cat logs/$id.prompt)" --model $model --add-dir "$dir" --output-format json --json-schema briefs/schema.json \
     --print-timeout 40m > "logs/$id.$model.out" 2> "logs/$id.$model.err"; rc=$?
  if python3 briefs/check.py "$id" "logs/$id.$model.out" $model; then echo "$id ok $model" >> logs/done.txt; exit 0; fi
  if grep -qiE 'quota|rate.?limit|exhausted|429|resource_exhausted' "logs/$id.$model.err" "logs/$id.$model.out"; then
     [ $model = gemini-3.8-flash-high ] && touch logs/GEMINI_EXHAUSTED && continue
     echo "$id QUOTA $model" >> logs/done.txt; exit 2
  fi
  echo "$id fail $model rc=$rc" >> logs/done.txt; exit 1
done
