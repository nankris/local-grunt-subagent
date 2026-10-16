# I gave Codex a free local helper model. It doubled the bill

*Draft. Tech in General experiment #029. Numbers are from 8 headless Codex runs and 132 local-model calls on 2026-10-14/15. All $ figures are estimates at API list price; the local model counts as free.*

Here's a tempting idea for cutting agent costs: let the expensive model act as a manager, and hand the boring per-item work to a tiny model running on your own machine for free. I tried it with Codex as the manager and Qwen3-0.6B, a 600-million-parameter model, running on a laptop-class CPU as the helper.

## The setup

Two small jobs, each with an answer key:

- label 24 product reviews as positive or negative (with some sarcasm and double negatives mixed in)
- convert 20 dates in assorted formats ("12/07/2024 (day/month/year)", "31-Dec-2027", "3rd Oct 2021") to `YYYY-MM-DD`

Codex CLI 0.162.1 (gpt-6.1-sol, ChatGPT Plus login) did each job twice on its own, and twice with an instruction to hand each line to the local model through a `qwen` command and assemble the result. I told it the final file was still its responsibility.

## What happened

Every run got every item right. But the version with a helper cost a lot more:

| | Items right | Codex tokens per run | Est. cost per run | Time |
|---|---|---|---|---|
| Codex alone | 88/88 | 59K | 2.3¢ | 27 s |
| Codex + local helper | 88/88 | 151K | 4.8¢ | 60 s |

## Why the helper didn't help

Two reasons.

**The grunt work was never the expensive part.** Labelling 24 short reviews takes Codex a few hundred output tokens. The real cost of a Codex run is its ~13K-token fixed prompt, re-read on every model call. Codex alone needed 4 calls. Managing the helper took about 10: write a script to call Qwen per line, run it, read 24 answers, check them, fix them, write the file.

**The helper was wrong often enough that Codex had to check everything.** Qwen got 87.5% of items right inside these runs. It called "Couldn't be more disappointed with this purchase" positive. It tripped on "the bass is not overdone" and "No complaints after six months". It left one date as `27-05-1937` and turned 1990 into 2090. Codex caught and fixed all 11 mistakes and overrode nothing that was already right. Without that check, one of the review runs would have scored 79%.

Codex also wrote better prompts for the small model than I did. My plain prompt got 75% on the reviews. Codex's version, which said "consider negation, sarcasm, and the final verdict", got 85%.

## The takeaway

A free local model only saves money when the work you hand it is big compared with the cost of managing and checking it. Short labels and date fixes aren't. For jobs like these, let the big model just do it. If you want to try delegation, try it on heavy per-item work (summarizing long documents, say) and measure whether the manager can afford to skip the checking.

*Caveats: tiny experiment (2 runs per arm per task), easy tasks, CPU-only helper on a shared machine. Full tables, prompts and raw logs are in the repo README.*
