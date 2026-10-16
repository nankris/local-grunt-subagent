# #029 Local model as a grunt subagent for Codex

**Question.** If Codex hands simple per-item sub-steps to a small local model (Qwen3-0.6B on CPU) instead of doing them itself, does it save Codex tokens, and what happens to quality? (Originally planned with Claude as the main agent; run with Codex here.) Kept deliberately small: 2 tasks × 2 arms × 2 reps = 8 Codex runs.

**Short answer (this build, these tasks).** Delegation **cost more, not less.** Codex still read every input, wrote a script to call Qwen once per item, then read Qwen's answers and checked each one. Codex tokens went up **2.5×** (59K → 151K per run), estimated cost **2.1×** ($0.023 → $0.048 per run), and wall time **2.3×** (27 s → 60 s). Quality held at **100% in both arms (8/8 runs, every item right)** only because Codex caught all of Qwen's mistakes. Qwen's own answers inside the delegate runs were 77/88 correct (87.5%), and Codex overrode exactly those 11 wrong ones. All $ figures are *estimates*.

## Setup

- Main agent: Codex CLI `codex-cli 0.162.1`, model `gpt-6.1-sol`, default reasoning effort, ChatGPT Plus login, headless `codex exec --json` on a fresh temp copy per run (shared harness `run_one.py`).
- Grunt model: Qwen3-0.6B (local weights), float32 on CPU (2 threads, 2-vCPU arm64 sandbox), greedy decoding, thinking off, served once by `scripts/qwen_server.py` on 127.0.0.1 and called with `bin/qwen "PROMPT" [MAX_NEW_TOKENS]` (~3 s per call). Every call is logged to `results/qwen_calls.jsonl`.
- Tasks (synthetic text written for this experiment, `scripts/make_fixtures.py`; answer keys in `keys/`, outside the task folders):
  - `G01_sentiment`: label 24 short product reviews positive/negative into `labels.csv`, including sarcasm, negation and mixed verdicts.
  - `G02_dates`: convert 20 sentences' dates (mixed formats: `12/07/2024 (day/month/year)`, `31-Dec-2027`, `2025.12.01`, ordinals…) to ISO into `dates.csv`.
- Pass = accuracy ≥ 90% against the key (`scripts/check.py`, which also logs the graded CSV to `results/grades.jsonl` because the harness deletes the work dir).
- Arms:
  - `codex_alone`: "Read TASK.md and do the task it describes in this folder. Do not create any other files."
  - `codex_plus_qwen`: same, plus: "A small local language model (Qwen3-0.6B on CPU) is available as the command `…/bin/qwen "PROMPT" [MAX_NEW_TOKENS]`; it prints its answer and takes about 3 seconds per call. Delegate the simple per-item sub-steps to it (one qwen call per line) instead of doing them yourself, then assemble the file. You are responsible for the final file being correct."
- Reference: `qwen alone`, one fixed prompt per item with no Codex (`scripts/qwen_alone.py`).
- The two arms ran side by side (one run at a time per arm). Qwen calls are attributed to the delegate run whose time window they fall in. Alone runs never called Qwen.
- Cost estimate: gpt-6.1-sol API list price $2.00/M uncached input, $0.10/M cached input, $10.00/M output (https://developers.openai.com/api/docs/models/gpt-6.1-sol, checked 2026-10-14). The local model is counted as $0. **Estimates only**; Plus is a flat subscription.

## Exact commands

```bash
source /workspace/tools/setup.sh
python3 scripts/make_fixtures.py
/workspace/tools/mlenv/bin/python -u scripts/qwen_server.py &          # load Qwen3-0.6B once (stop it when done)
python3 scripts/qwen_alone.py                                         # reference arm
scripts/harness/driver.sh scripts/jobs_alone.txt 1 results/driver_alone.log &
scripts/harness/driver.sh scripts/jobs_delegate.txt 1 results/driver_delegate.log; wait
/workspace/tools/mlenv/bin/python scripts/analyze.py
```

## Results (8 Codex runs + 44 reference calls, 2026-10-14 20:00–20:04 UTC / 2026-10-15 01:30–01:34 IST)

| Arm | Runs | Pass | Items correct | Codex tokens | Uncached input | Output | Codex model calls | Qwen calls | Wall | Est. cost / run |
|---|---|---|---|---|---|---|---|---|---|---|
| codex_alone | 4 | 4/4 | 88/88 | 59.2K | 6.6K | 478 | 4.0 | 0 | 26.5 s | $0.0232 |
| codex_plus_qwen | 4 | 4/4 | 88/88 | 150.8K | 12.4K | 948 | 9.75 | 22 | 60.4 s | $0.0481 |

Quality of the local model:

| | Reviews (24) | Dates (20) |
|---|---|---|
| Qwen alone, my fixed prompt | 18/24 (75%) | 18/20 (90%) |
| Qwen's answers inside delegate runs (Codex wrote the prompt) | 41/48 (85%) | 36/40 (90%) |
| Final file after Codex review | 48/48 | 40/40 |
| Codex overrides of Qwen's answer | 7 (all corrections) | 4 (all corrections) |

Per run: `results/per_run.csv`. Chart: `results/chart.png` (items correct, Codex tokens, wall time).

### What the numbers say
1. **The expensive part wasn't the per-item work.** Codex alone did each task in 4 model calls and ~500 output tokens. Labelling 24 reviews is a few hundred tokens of output, which is cheap next to Codex's fixed ~13K-token prompt prefix. Delegating added 5–7 model calls to write the calling script, read 20–24 answers back and verify them, each re-reading that prefix.
2. **Codex didn't trust the grunt, and was right not to.** In every delegate run it re-checked Qwen's output and fixed its errors: "Couldn't be more disappointed with this purchase" marked positive, "the bass is not overdone" and "No complaints after six months" marked negative (negation traps), `27-05-1937` left in the wrong order, and 1990 turned into 2090 (both date runs made the same two mistakes). Without that review the reviews task would have failed the 90% bar in one of two runs (19/24).
3. **Codex wrote better prompts for Qwen than I did** (85% vs 75% on reviews), e.g. "Consider negation, sarcasm, and the final verdict".
4. **Wall time more than doubled**: 20–24 local calls (median 2.5 s, range 0.7–6.5 s; rep 1 of each task called them in a loop, rep 2 in a 4-thread pool) plus the extra model calls.

## Caveats
- Tiny n (2 runs per arm per task) and two easy, short tasks. Delegation could pay off where the per-item work is large (long documents per item) and the main agent can skip verifying, neither of which held here.
- The prompt told Codex it was responsible for correctness, which invites the verification pass. A "trust the subagent" prompt would be cheaper and less accurate. Not tested.
- CPU-only local model on a shared 2-vCPU sandbox, with other experiments running at the same time. Qwen latency includes queueing.
- Qwen's answers inside delegate runs were parsed from Codex's command output (`scripts/analyze.py`); all 4 runs printed one answer per line and parsed cleanly (88/88 items).
- Rate-limit percentages in `runs.csv` include other experiments on the same account.

## Files
- `scripts/harness/`: copy of the shared harness (`run_one.py`, `driver.sh`, `chain.sh`, `backfill.py`, fixtures)
- `scripts/make_fixtures.py`, `scripts/check.py`, `scripts/qwen_server.py`, `scripts/qwen_alone.py`, `scripts/jobs_alone.txt`, `scripts/jobs_delegate.txt`, `scripts/analyze.py`, `bin/qwen`
- `fixtures/G01_sentiment`, `fixtures/G02_dates`, `keys/*.json`
- `results/runs.csv` (one row per Codex run), `results/per_run.csv`, `results/summary.csv`, `results/grades.jsonl`, `results/qwen_calls.jsonl`, `results/qwen_alone.csv`, `results/qwen_alone_summary.csv`, `results/driver_*.log`
- `results/raw/*.jsonl`: raw `codex exec --json` streams
