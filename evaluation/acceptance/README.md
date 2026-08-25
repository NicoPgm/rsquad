# Measuring acceptance

Every other number in this project is a count. Whether a reader would **act** on a finding is a
judgement, and it is the judgement that decides whether a lens stays: below roughly **30 %** a
lens earns its removal, and one kept below that teaches the reader to skim the others too.

**The worksheet deliberately says none of that.** Its instructions are the four verdict words and
nothing else — no stakes, no threshold, no hint that the items are grouped. A judge told that 30 %
is the retirement line has been handed a target, and a judge told there are three hidden groups of
73, 65 and 65 items has been invited to balance them. That is why the design lives here and the
items live there, and why the same file can be handed to a person or to a model without either
being steered.

## Blinding

- **The lens is hidden**, and `kind` and `severity` with it: `boundary` and `contract` name their
  lenses out loud, and `severity` is the lens grading its own homework.
- **The case is hidden**: known defect or not, clean commit or not, refuted or not. All of it is
  in `key.json`, which nobody opens before finishing.
- **The order is shuffled**, seed 7, so it reproduces. That buys two things: no lens arrives in a
  block, and *any prefix is a random sample* — a run that stops early is still unbiased about
  which findings were seen.

## Where to stop

| after | per measurable lens | what it can answer |
|---|---|---|
| **90 items** | ~30 | whether the three big lenses differ from each other by a lot (±17 pts) |
| **150 items** | ~50 | whether a lens sits above or below the 30 % line (±13 pts) |
| **207 items (all)** | ~68 | the same, tighter, plus clean-commit and refuted-finding acceptance |

**Stop at a checkpoint, not when the numbers look good.** Choosing where to stop after seeing
results is the one bias shuffling cannot fix.

## What cannot be measured, and why that is the answer

Three lenses carry enough findings: **`contract` 73, `bounds` 65, `repro` 65**.

`tests` produced **4** findings in 46 reviews and `conformance` **8**. Neither has enough for a
rate — but the reasons are different, and one of them is our fault.

**`tests` was never given a test file.** `evaluate` reviews exactly one unit per case, the changed
*source* file, so every `tests` task went out asking about tests that were not in the payload. Its
4 findings are the lens answering out of scope, not a yield. **The tests lens has therefore never
been evaluated at all**, and no number here says anything about it.

> **Resolved 2026-08-25.** It has been evaluated now: shown one test file per case it produced
> **28 raw findings over 36 cases**, 25 past the guards, against 5 over 53 before
> (`docs/step7e-tests-lens.md`). Those 25 belong in this worksheet — and they must carry a
> **model label**, because that arm ran on `claude-sonnet-5` while everything already in the
> worksheet ran on `claude-opus-5`. Mixed in unlabelled, the per-lens rate this study exists
> to produce would be uninterpretable for exactly the lens it just became possible to measure.

**`conformance` really did stay quiet**, and that is closer to a measurement: on these Java
repositories there is no spec, so its "requirement" is the commit message, and ADR-0007 tells it
to quote a requirement or say nothing. Eight findings is that rule working as written on a corpus
with almost nothing to quote.

`conformance` is absent from the worksheet entirely, for a second reason: its findings carry a
different schema — a quoted `requirement` and a `mismatch`, not `inputs` and `consequence` — so
every one of its blocks would announce its own lens.

## If a model judges instead of a person

It measures a different thing, and the report must say so: **model-judged acceptance**, never
acceptance. The findings were written by an LLM and refuted by an LLM; a third LLM shares the
finder's priors, and `docs/architecture.md` already lists correlated blind spots as a known limit.
Expect an upward bias, and expect it to track how persuasively a finding is *written* — which is
exactly the axis that could differ by lens, and so exactly the axis that would contaminate the
comparison being made.

It is still worth doing, as a **second rater** rather than a replacement — the rubric says a
second labeller is the honest fix and was not available. The design that works is the one this
repository just used on its two transports: run both on identical items, report the human number
as the headline, and report the agreement. If they agree, later campaigns can be judged at scale
for nothing. If they do not, that is worth knowing before anyone trusts a model-judged number.

Two conditions for it to be worth anything:

- **One item per fresh context.** A model judging 207 items in one conversation is influenced by
  its own earlier verdicts and starts balancing them. This repository already applies that rule to
  the refuter — one reader per finding, separate context — for the same reason.
- **A different model family from the one that wrote the findings**, which reduces the shared-prior
  problem without removing it.

## Scoring

    python evaluation/acceptance/score.py [worksheet.md]

It refuses a rate below 25 verdicts, flags items skipped inside the judged range, and prints
beside acceptance the number of places where each lens spoke alone — 19 of 96 for `contract`, 8
each for `repro` and `bounds`. **A lens earns its place by acceptance and by solitude.** A high
rate on claims another lens also made is a lens that could be removed for free.
