# Step 8 — Sonnet lenses, Opus refuter: 30/38, against 31/38 for Opus throughout

**Date:** 2026-11-20
**Pre-registration:** `evaluation/step8-tiered.yaml` (`0a1baa9`), committed before any case ran.
**Reports:** `evaluation/step8-step7b-*.md`, `evaluation/step8-step7d-*.md`.
**Decision, by the rule frozen beforehand:** 30 ≥ 29, so no measurable loss. `rsquad export` now
defaults to Sonnet for the lenses and Opus for the refuter.

| | baseline (all Opus) | this run (Sonnet lenses, Opus refuter) |
|---|---:|---:|
| step7b | 14 / 19 | 14 / 19 |
| step7d | 17 / 19 | 16 / 19 |
| **detected** | **31 / 38** | **30 / 38** |
| findings surviving refutation | 198 | **134** |

## Case for case: one lost to the lenses, one to the refuter, one gained

Thirty-five cases land on the same side in both runs. Three move:

- **`e1dc391`, lost by the lenses.** A charset-less `InputStreamReader` on the error path. In the
  baseline, two Opus lenses (`bounds`, `contract`) quoted it. Here no Sonnet lens did; they
  reported a connect timeout applied to the pool lease and an unguarded `getBody()`, both standing.
  This is the one loss attributable to the variable under test.
- **`7ddb6ff`, lost by the refuter.** Two Sonnet lenses found the labelled defect — the decoded
  answer discarded and a fixed sentence returned in its place — and **the Opus refuter killed both
  as `intended`**. The baseline used the same refuter model and let it stand. So this miss is not
  the lenses', and it is the failure the refutation module warns about in its own words: a wrong
  refutation deletes a real finding. It is not silent — both appear under `Refuted` in that case's
  queue — but it is not in the detection count either.
- **`ca3b112`, gained.** The metadata filter applied to the kNN leg of the RRF query and not to
  the full-text leg. The baseline missed it and found a different real bug in the same place. Here
  `repro` and `contract` both found the labelled one.

No case changed side because of the `tests` routing: the one lens loss was found by `bounds` and
`contract` in the baseline.

## What else moved

- **Surviving findings fell from 198 to 134, a third fewer**, in both halves (90 → 62, 108 → 72).
  Three causes are mixed and this run cannot separate them: Sonnet lenses, the `tests` lens no
  longer reading source files, and the new refuter verdict. For a reader it is a third less to
  read for one detection fewer.
- **`undecided` was used 9 times in 145 refutations.** Verdicts: 132 `stands`, 9 `undecided`,
  3 `intended`, 1 `misread`.
- **Every reply was well formed**: 152/152 lens replies, 145/145 verdicts, none dropped by the
  guards.

## Cost, from the driver's own accounting

| round | agents | tokens | 5-hour window |
|---|---:|---:|---|
| step7b lenses, Sonnet | 95 | 6.46 M | 5 % → 16 % |
| step7b refutation, Opus | 88 | 5.98 M | 16 % → 30 % |
| step7d lenses, Sonnet | 95 | 6.48 M | 30 % → 41 % |
| step7d refutation, Opus | 95 | 6.42 M | 41 % → 55 % (read before this report was written) |

About 25 M tokens for the 38 cases, against about 21 M reported for the baseline. The two are not
counted the same way (this one includes the driver's manifest-reading agents), so no saving in
tokens is claimed. Token totals do not price models anyway: on the plan's window, a Sonnet lens
round cost about 11 points and an Opus refutation round about 14, for similar token counts. The
saving is in the lens half only, and the refutation half is the larger bill.

## What this does not establish

- **One run per arm.** `7ddb6ff` shows the refuter alone can move a case between runs; a one-case
  difference in either direction is inside what a re-run could produce.
- **The labeller read the results**, as in every earlier campaign; the labels were frozen first.
- **Nothing about acceptance.** 134 findings for 30 detections is still a bill, and ADR-0009's next
  measurement — a judge calibrated against a person — is what would price it.
