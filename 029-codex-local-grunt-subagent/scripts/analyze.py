#!/usr/bin/env python3
"""#029 summary + chart. Joins results/runs.csv with results/grades.jsonl (accuracy, by time window + task),
results/qwen_calls.jsonl (local-model calls and CPU seconds inside each run's window), and pulls the raw qwen answers
from each delegate run's command outputs to count how many Codex overrode."""
import json, os, re
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(HERE, "results")
df = pd.read_csv(os.path.join(R, "runs.csv"))
grades = [json.loads(l) for l in open(os.path.join(R, "grades.jsonl"))]
qcalls = [json.loads(l) for l in open(os.path.join(R, "qwen_calls.jsonl"))]
keys = {t: json.load(open(os.path.join(HERE, "keys", t + ".json"))) for t in ("G01_sentiment", "G02_dates")}
def norm(task, v):
    v = str(v).strip().lower()
    if task == "G02_dates":
        m = re.search(r"\d{4}-\d{2}-\d{2}", v); return m.group(0) if m else v
    m = re.search(r"positive|negative", v); return m.group(0) if m else v
rows = []
for _, r in df.iterrows():
    t0, t1 = r.start_epoch, r.start_epoch + r.wall_s + 150
    g = [x for x in grades if x["task"] == r.task and t0 <= x["t"] <= t1]
    g = g[0] if g else {}
    used_qwen = "/bin/qwen" in open(os.path.join(HERE, r.raw_jsonl)).read()  # alone runs overlapped in time with delegate runs
    qc = [x for x in qcalls if t0 <= x["t"] <= r.start_epoch + r.wall_s] if used_qwen else []
    final = {}
    for line in (g.get("output_csv") or "").splitlines()[1:]:
        p = line.split(",", 1)
        if len(p) == 2: final[p[0].strip()] = norm(r.task, p[1])
    raw_q = {}
    for l in open(os.path.join(HERE, r.raw_jsonl)):
        e = json.loads(l); it = e.get("item") or {}
        if e.get("type") == "item.completed" and it.get("type") == "command_execution" and "qwen" in (it.get("command") or ""):
            for m in re.finditer(r"^\s*(\d{1,2})[\s,:|]+'?([^'\n]+)'?\s*$", it.get("aggregated_output") or "", re.M):
                raw_q.setdefault(m.group(1), norm(r.task, m.group(2)))
    k = keys[r.task]
    q_ok = sum(raw_q.get(i) == v for i, v in k.items()) if raw_q else None
    overrides = sum(1 for i in k if i in raw_q and i in final and raw_q[i] != final[i]) if raw_q else None
    rows.append(dict(cond=r.cond, task=r.task, rep=r.rep, passed=r.passed, correct=g.get("correct"), total=g.get("total"),
                     accuracy=g.get("accuracy"), total_tokens=r.total_tokens, cached=r.cached_input_tokens,
                     uncached=r.uncached_input_tokens, output=r.output_tokens, est_cost_usd=r.est_cost_usd, model_calls=r.model_calls,
                     wall_s=r.wall_s, qwen_calls=len(qc), qwen_span_s=round(max(x["t"] + x["seconds"] for x in qc) - min(x["t"] for x in qc), 1) if qc else 0,
                     qwen_raw_items=len(raw_q), qwen_raw_correct=q_ok, codex_overrides=overrides))
d = pd.DataFrame(rows); d.to_csv(os.path.join(R, "per_run.csv"), index=False); print(d.to_string())
order = ["codex_alone", "codex_plus_qwen"]
g = d.groupby("cond")
s = pd.DataFrame({"runs": g.size(), "passes": g.passed.sum(), "accuracy_mean": g.accuracy.mean().round(3),
    "total_tokens_mean": g.total_tokens.mean().round(0), "uncached_mean": g.uncached.mean().round(0), "output_mean": g.output.mean().round(0),
    "model_calls_mean": g.model_calls.mean().round(2), "wall_s_mean": g.wall_s.mean().round(1), "qwen_calls_mean": g.qwen_calls.mean().round(1),
    "qwen_span_s_mean": g.qwen_span_s.mean().round(1), "qwen_raw_correct_total": g.qwen_raw_correct.sum(min_count=1), "qwen_raw_items_total": g.qwen_raw_items.sum(), "codex_overrides_total": g.codex_overrides.sum(min_count=1),
    "est_cost_mean_usd": g.est_cost_usd.mean().round(4)}).reindex(order)
s.to_csv(os.path.join(R, "summary.csv")); print(s.T.to_string())
qa = pd.read_csv(os.path.join(R, "qwen_alone.csv")); qs = qa.groupby("task").correct.agg(["sum", "count"]); qs.to_csv(os.path.join(R, "qwen_alone_summary.csv")); print(qs)
fig, ax = plt.subplots(1, 3, figsize=(15, 4.8)); tasks = ["G01_sentiment", "G02_dates"]; w = 0.2
cols = {"qwen alone": "#999999", "qwen answers inside delegate runs": "#c9c27a", "codex_alone": "#4c72b0", "codex_plus_qwen": "#55a868"}
for j, t in enumerate(tasks):
    dq = d[(d.cond == "codex_plus_qwen") & (d.task == t)]
    vals = [qs.loc[t, "sum"] / qs.loc[t, "count"] * 100, dq.qwen_raw_correct.sum() / dq.qwen_raw_items.sum() * 100] + [d[(d.cond == c) & (d.task == t)].accuracy.mean() * 100 for c in order]
    for i, (name, v) in enumerate(zip(list(cols), vals)):
        ax[0].bar(j + (i - 1.5) * w, v, w, color=cols[name], label=name if j == 0 else None); ax[0].text(j + (i - 1.5) * w, v + 1, f"{v:.0f}%", ha="center", fontsize=7.5)
ax[0].set_xticks(range(2)); ax[0].set_xticklabels(["24 review labels", "20 date conversions"]); ax[0].set_ylim(0, 135); ax[0].set_title("Items correct (mean of 2 runs)", fontsize=10); ax[0].legend(fontsize=7, loc="upper center", ncol=2)
for k, (col, title, sc) in enumerate([("total_tokens", "Codex tokens per run (K)", 1e-3), ("wall_s", "Wall time per run (s)", 1)]):
    a = ax[k + 1]
    for j, t in enumerate(tasks):
        for i, c in enumerate(order):
            v = d[(d.cond == c) & (d.task == t)][col] * sc
            a.bar(j + (i - 0.5) * 0.38, v.mean(), 0.38, color=cols[c], alpha=0.7, label=c if j == 0 else None)
            a.scatter([j + (i - 0.5) * 0.38] * len(v), v, color="black", s=12, zorder=3)
    a.set_xticks(range(2)); a.set_xticklabels(["reviews", "dates"]); a.set_title(title, fontsize=10); a.legend(fontsize=8); a.grid(axis="y", alpha=0.3)
fig.suptitle("Codex 0.162.1 alone vs Codex delegating per-item steps to a local Qwen3-0.6B (CPU)", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(R, "chart.png"), dpi=130); print("wrote chart")
