# Step 8, first half — Sonnet lenses, Opus refuter: 14/19, the same fourteen

**Date:** 2026-11-20
**Pre-registration:** `evaluation/step8-tiered.yaml` (`0a1baa9`), committed before any case ran.
**Reports:** `evaluation/step8-step7b-langchain4j.md`, `evaluation/step8-step7b-spring-ai.md`.
**Scope:** the nineteen `step7b` cases. The nineteen `step7d` cases have not run; the decision
rule in the pre-registration is stated for all 38 and is **not** applied here.

| | baseline (all Opus) | this run (Sonnet lenses, Opus refuter) |
|---|---:|---:|
| detected | 14 / 19 | **14 / 19** |
| findings surviving refutation | 90 | **62** |
| refutation tasks | — | 69 |

**Case for case, the same fourteen.** Detected in both: `d5b13be`, `7e622bf`, `840330c`,
`145ff45`, `196bc5d`, `96a3af9`, `0626661`, `f274731`, `23098bd`, `0d16d28`, `34b8d34`,
`b1384c8`, `4fbb484`, `ec1e052`. Missed in both: `771b0d2`, `e59754e`, `575eb46`, `95a3aff`,
`c256cfa`. No case changed side, so nothing needs attributing to the `tests` routing or to
`undecided`.

The misses are the same misses for the same reasons where the two runs can be compared:
`e59754e` again reports the RRF score against a similarity threshold instead of the missing
builder field, and `95a3aff` again reports the null branch rather than the fall-through.

## What else moved

- **Surviving findings fell from 90 to 62, a third fewer, with no detection lost.** Three causes
  are mixed here and this run cannot separate them: Sonnet lenses, the `tests` lens no longer
  reading source files, and the refuter's new verdict. It is the reader's cost going down, which
  is the number ADR-0009 cares about after detection.
- **`undecided` was used 7 times in 69.** Verdicts: 60 `stands`, 7 `undecided`, 1 `misread`,
  1 `intended`. Before this verdict existed, those seven would have been filed under a cause
  that may not have held.
- **Every reply was well formed**: 76/76 lens replies, 69/69 verdicts, none dropped by the
  guards.

## Cost, from the driver's own accounting

| round | agents | tokens | 5-hour window |
|---|---:|---:|---|
| 1 — lenses, Sonnet | 95 (76 tasks + 19 manifest reads) | 6.46 M | 5 % → 16 % |
| 2 — refutation, Opus | 88 (69 tasks + 19 manifest reads) | 5.98 M | 16 % → 30 % |

The baseline's lens round is not itemised the same way, so no saving is claimed here. What can
be said: the Sonnet round, with more tasks, cost the window less than the Opus round.

## What this does not establish

- **Nineteen cases.** The interval is about ±20 points. Two runs agreeing case for case is
  stronger than the totals alone, and still not the 38 the rule was written for.
- **The labeller read the results**, as for every earlier campaign; the labels themselves were
  frozen first.
- **Nothing about acceptance.** 62 findings for 14 detections is still a bill.
