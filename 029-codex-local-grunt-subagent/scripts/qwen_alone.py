#!/usr/bin/env python3
"""Reference arm: Qwen3-0.6B alone, one fixed prompt per item, no Codex. Writes results/qwen_alone.csv."""
import csv, json, os, re, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(HERE, "bin", "qwen")
rows = []
for task, fn, tmpl, n in [("G01_sentiment", "reviews.txt", "Classify the sentiment of this product review. Answer with exactly one word, positive or negative. Review: {}", 8),
                          ("G02_dates", "sentences.txt", "Convert the date in this sentence to ISO YYYY-MM-DD. Answer with the date only. Sentence: {}", 16)]:
    key = json.load(open(os.path.join(HERE, "keys", task + ".json")))
    for line in open(os.path.join(HERE, "fixtures", task, fn)):
        i, text = line.rstrip("\n").split("\t", 1)
        out = subprocess.run([Q, tmpl.format(text), str(n)], capture_output=True, text=True).stdout.strip().lower()
        m = re.search(r"\d{4}-\d{2}-\d{2}", out) if task == "G02_dates" else re.search(r"positive|negative", out)
        ans = m.group(0) if m else out
        rows.append(dict(task=task, id=i, qwen=ans, key=key[i], correct=int(ans == key[i])))
w = csv.DictWriter(open(os.path.join(HERE, "results", "qwen_alone.csv"), "w", newline=""), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for t in ("G01_sentiment", "G02_dates"):
    r = [x for x in rows if x["task"] == t]; print(t, sum(x["correct"] for x in r), "/", len(r))
