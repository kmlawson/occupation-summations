#!/bin/zsh
# resume.sh : catalogue every report still missing, two at a time. When both models are out of quota, sleep until the
# earliest reset. A report that has failed (not for quota) 4 times is left out and reported.
cd "${0:A:h}/.." || exit 1
while true; do
  python3 - >| logs/queue.txt <<'PY'
import json, os
fails = {}
claimed = set(open("logs/claimed.txt").read().split()) if os.path.exists("logs/claimed.txt") else set()
for l in open("logs/done.txt"):
    w = l.split()
    if len(w) > 1 and w[1] == "fail": fails[w[0]] = fails.get(w[0], 0) + 1
for x in json.load(open("files.json")):
    if not os.path.exists(f"catalog/{x['id']}.json") and fails.get(x["id"], 0) < 4 and x["id"] not in claimed: print(x["id"])
PY
  [ -s logs/queue.txt ] || { echo "$(date +%H:%M) finished; $(ls catalog/*.json | wc -l | tr -d ' ') of 71 catalogued"; exit 0; }
  now=$(date +%s); out=0; soonest=0
  for f in logs/EXHAUSTED.*(N); do t=$(cat $f); [ $t -gt $now ] && { out=$((out+1)); [ $soonest = 0 -o $t -lt $soonest ] && soonest=$t; }; done
  if [ $out -ge 2 ]; then
    echo "$(date +%H:%M) both models out of quota; $(wc -l < logs/queue.txt | tr -d ' ') left; waiting until $(date -r $soonest +%H:%M)"
    sleep $((soonest - now)); continue
  fi
  echo "$(date +%H:%M) starting $(wc -l < logs/queue.txt | tr -d ' ') reports"
  xargs -P 2 -L 1 ./briefs/run1.sh < logs/queue.txt
  sleep 60
done
