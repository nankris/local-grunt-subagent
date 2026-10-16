#!/usr/bin/env python3
"""check.py TASK : grade the output csv in cwd against keys/TASK.json. Pass = accuracy >= 0.9. Writes grade.json in cwd."""
import csv, json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = sys.argv[1]; key = json.load(open(os.path.join(HERE, "keys", t + ".json")))
fn, col = ("labels.csv", "label") if t == "G01_sentiment" else ("dates.csv", "date")
got = {}
try:
    for r in csv.DictReader(open(fn)): got[str(r.get("id", "")).strip()] = str(r.get(col, "")).strip().lower()
except Exception:
    pass
ok = sum(got.get(k) == v for k, v in key.items()); acc = ok / len(key)
json.dump({"correct": ok, "total": len(key), "accuracy": round(acc, 3), "wrong": {k: [got.get(k), v] for k, v in key.items() if got.get(k) != v}}, open("grade.json", "w"))
g = {"t": round(__import__("time").time(), 1), "cwd": os.getcwd(), "task": t, "correct": ok, "total": len(key), "accuracy": round(acc, 3),
     "wrong": {k: [got.get(k), v] for k, v in key.items() if got.get(k) != v}, "output_csv": open(fn).read() if os.path.exists(fn) else None}
open(os.path.join(HERE, "results", "grades.jsonl"), "a").write(json.dumps(g) + "\n")  # run_one.py deletes the work dir, so keep the grade here
print(f"{ok}/{len(key)}"); sys.exit(0 if acc >= 0.9 else 1)
