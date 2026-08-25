# Thirty-eight cases on the harness — 31 detected, and widening the pool did not cost anything

**Date:** 2026-08-25
**Pre-registration:** `evaluation/step7b.yaml` (`0491ade`) and `evaluation/step7d.yaml` (`1d89e16`),
both committed before any of their cases ran.
**Cost:** **$0.** Roughly 390 harness agents and about 21 million tokens, against a subscription.
The same campaign on the API would have billed about $35.
**Reports:** `evaluation/step7b-*-harness.md`, `evaluation/step7d-*-harness.md`.

| Set | Scorable | Detected |
|---|---:|---:|
| step7b (the frozen 19, replayed on the harness) | 19 | 14 |
| step7d (the extension) | 19 | **17** |
| | **38** | **31** |

**31 / 38 — 82 %, 95 % Wilson interval 67 % to 91 %.** Quote the fraction. The interval is ±12
points rather than the ±20 that 19 cases gave, which is the whole reason for doing this.

## The widening did not lower the number, and that was the thing to watch

`evaluation/step7d.yaml` raises `MAX_FILES_IN_ORIGIN` from 10 to 20 **after** the 15/19 result was
known. Its own header says that is met in form and not in spirit, and that what bounds it is
structural: the 24 older cases are untouched, so the two subsets can be read side by side.

They can, and they say the extension is the **harder-looking** half:

| | step7b | step7d |
|---|---:|---:|
| median origin diff | 73 lines | **191 lines** |
| origin creates the file | 10 / 19 | **17 / 19** |
| detected | 14 / 19 | **17 / 19** |

The new cases are buried in diffs 2.6× larger and are mostly whole-new-class reviews, and the
score went **up**, not down. So the widened bound did not quietly admit easier cases — if
anything the reverse — and nobody has to take that on trust, because the split is in the data.

## Every miss is a different real bug, never silence

Seven misses in 38, and **not one returned nothing**. In every case the squad reported a genuine
defect elsewhere in the same file and never mentioned the labelled one. That is now the single
most reproducible behaviour in this project: it held on 4 misses in `step7b`, and on both of
step7d's.

- `MultipartBodyPublisher` — the labelled defect is an unguarded `"Content-Type: " + contentType()`
  emitting a literal `Content-Type: null`. What came back: the same header line is unescaped for
  `fileName()`, so a quote or a CRLF injects part headers; and the boundary is a fixed constant
  never checked against the payload. **The right line, twice, for a different reason** — which the
  scoring rule counts as a miss, because a finding at the right place for the wrong reason is a
  coincidence.
- `ElasticsearchConfigurationHybrid` — the labelled defect is a metadata filter applied to the KNN
  leg and not to the full-text leg of the same RRF query. What came back: `minScore`, a 0–1
  similarity, is passed as Elasticsearch's `min_score` against RRF fusion scores that cap at
  `2/61 ≈ 0.033`, so any threshold above that returns nothing.

**That second one is the same bug the squad found instead of the labelled defect on
`PgVectorEmbeddingStore` in `step7b`** — a similarity threshold compared against a reciprocal-rank
score — in a different project, a different vector store, a different quarter. Two independent
rediscoveries of one mistake pattern, both times while missing what it was asked about.

## The deduplication rule, validated by accident

`step7d.yaml` drops four candidates because two fixes traced back to the same commit and the same
file, which makes them the same review unit. One dropped case was `b44723943`, the Apache HTTP
client mapping `connectTimeout` onto `setConnectionRequestTimeout` — the pool-lease timeout, not
connection establishment.

The squad found it anyway, three times, while reviewing the case that was kept
(`e1dc391`, the same unit). The rule is right: the unit carries both defects, so running it twice
would have counted one review as two.

## The reader's cost is stable across transports and across sets

| | cases | findings | places | findings/case | places/case |
|---|---:|---:|---:|---:|---:|
| step7b, API | 19 | 97 | 50 | 5.1 | 2.6 |
| step7b, harness | 19 | 90 | 44 | 4.7 | 2.3 |
| step7d, harness | 19 | 108 | 50 | 5.7 | 2.6 |
| **all defect cases, harness** | **38** | **198** | **94** | **5.2** | **2.5** |
| clean commits, harness | 8 | 12 | 6 | 1.5 | 0.8 |

Doubling the case count moved 4.7 to 5.7 per case and left places per case at 2.6. A reader pays
about five claims per reviewed file, of which two or three are distinct places.

**And silence still separates the two corpora.** One case in 38 produced nothing — `c256cfa`,
already known — against four of eight clean commits. Fisher exact, two-tailed, **p ≈ 0.002**,
firmer than the p ≈ 0.008 the eight-case corpus gave on its own.

**Zero findings refused by the mechanical guards**, now across the whole Java campaign. The
anchoring guard and "reproduction or nothing" have never rejected anything on this language, with
no context pack at all.

## What the covariates say now

| | detected |
|---|---|
| label `yes` | **11 / 12** |
| label `weak` | **20 / 26** |

The rubric predicts weakly and in the right direction, as it did at 19 cases.

| Origin of the defect | detected |
|---|---|
| after the May 2026 cutoff | 4 / 5 |
| 2025 – 2026-05 | 18 / 21 |
| 2024 and earlier | 9 / 12 |

**The gradient reported at 19 cases has gone flat.** `docs/step7b-first-run.md` found detection
highest on post-cutoff cases and lowest on the oldest, and called that evidence leaning against
the memorisation hypothesis. At 38 cases the three strata are 80 %, 86 % and 75 % — no gradient in
either direction, which is the null result. The earlier reading was over-read from small strata,
and the honest statement now is that **this data shows no memorisation effect and no reverse
effect either**.

Note that step7d added **no** post-cutoff scorable case: its only two post-cutoff candidates were
both labelled `no`. That stratum is still five cases and is still the weakest evidence here.

## What this does not establish

- **A harness number.** All 38 ran on the harness. Nineteen of them also ran on the API and the
  two agreed on eighteen (`docs/transport-calibration-19.md`), which is close — but the extension
  has no API half and nobody should assume one.
- **Two repositories, one language, no context pack.** Question 6 was unimplemented for Java,
  so every lens ran on the diff and the file alone. ~~31/38 is a floor for what a context pack
  would give.~~ **Measured 2026-08-25:** the pack is implemented, and the nineteen step7b cases
  re-run with it detect the same fourteen, case for case (`docs/step7b-context-pack.md`). The
  step7d nineteen were exported with packs and left unrun.
- **The labeller reads the results.** The rubric and every label were committed first, which
  bounds it and does not remove it.
- **Nothing here is an acceptance rate.** 198 findings against 31 detected defects is a bill, not
  a verdict on whether a reader would pay it. That measurement still does not exist, and it is
  still the only one that decides whether anyone keeps the tool.
