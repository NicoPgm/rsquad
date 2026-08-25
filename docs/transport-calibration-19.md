# The full calibration — nineteen cases on both transports, and they agree far more than four suggested

**Date:** 2026-08-24
**Cases:** every scorable case of `evaluation/step7b.yaml`, on both transports.
**Cost:** **$0.** 176 harness agents, 9.6 million tokens. The API half was paid on 2026-08-23.
**Reports:** `evaluation/step7b-langchain4j-harness.md`, `evaluation/step7b-springai-harness.md`.

`docs/transport-calibration.md`, written yesterday on four cases, concluded that the deferred API
budget should buy calibration rather than more cases: ten to fifteen cases replayed on the API at
$9–14. **That was the wrong direction, and it was expensive advice.** The nineteen cases were
already bought. Replaying them on the *harness* costs nothing, and it is the same bridge.

So the bridge is now nineteen cases wide, and it cost nothing to build.

## Result

| Arm | Scorable | API | harness |
|---|---:|---:|---:|
| langchain4j | 15 | 11 | **11** |
| spring-ai | 4 | 4 | **3** |
| | **19** | **15** | **14** |

**On langchain4j the two transports agree case for case — 11 of 15 each, and the same four
misses**: `PgVectorEmbeddingStore`, `OnnxScoringBertCrossEncoder`, `GoogleCustomWebSearchEngine`,
`InMemoryEmbeddingStore`. Not the same count reached by different routes. The same cases.

More than that, on three of those four the two transports **missed in the same way**: each
returned the same substitute bug instead of the labelled one — the unreachable RRF score
threshold on PgVector, the unclosed `OrtSession` on the ONNX encoder, the `getPagemap()` NPE on
the search engine. The transports do not merely score alike; they are wrong about the same things
for the same reasons.

The whole disagreement over nineteen cases is **one case**: `spring-ai-c256cfa`, the seven-line
null-parent observation the API caught with its single finding and the harness did not see at
all. That is the case yesterday's document already named.

## What this does to yesterday's conclusion

Yesterday, on four cases: 3/4 against 4/4, "the transports are not interchangeable per case."
Today, on nineteen, the disagreement is the same single case — it was simply a quarter of a
four-case sample and is now a nineteenth of a nineteen-case one.

**The honest reading is that four cases could not support the sentence built on them.** The
direction still holds — `transport-comparison.md` had the harness finding `:137` three times out
of three where the API found it zero times out of three, so divergence in both directions is
real — but its size is much smaller than a four-case window suggested.

What survives from yesterday: the missed case is still the smallest diff in the set, and it is
still the only miss. What does not survive: "neither is systematically the more sensitive one on
this evidence" was a claim about a difference that is one case wide.

## The reader's cost, and a unit error that halved it

Counted in two units, because this repository has been quietly mixing them:

| | cases | findings | distinct places | findings/case | places/case |
|---|---:|---:|---:|---:|---:|
| **API**, defect cases | 19 | 97 | 50 | 5.1 | 2.6 |
| **harness**, defect cases | 19 | 90 | 44 | 4.7 | 2.3 |
| **harness**, clean commits | 8 | 12 | 6 | 1.5 | 0.8 |

A *finding* is one lens's claim. A *place* is a distinct `file:line`; several lenses reaching the
same line independently collapse to one. Both are legitimate — places are what a reader scrolls
past, findings are what the refuter had to kill — but they are not the same number, and
`docs/step7b-first-run.md` published "50 surviving findings … 2.6 per case" when 50 is the count
of **places** and the finding count is 97. Same for `docs/transport-calibration.md`'s "10 findings
against 6": those are places, and the findings are 19 against 16.

That mislabelling was harmless where both sides of a comparison used the same unit. It was not
harmless in `docs/step7c-clean-corpus.md`, which put **12 raw findings** for clean commits beside
**50 places** for defect cases in one table and read 1.5 against 2.6 from it. In matching units
the contrast is **1.5 against 5.1** — more than three times, not less than twice.

**The correction strengthens every conclusion drawn from it**, which is exactly why it needed
finding: a number that flatters the argument it supports is the one nobody re-checks. All three
documents are corrected in place with a dated note.

## What still is not established

- **Nineteen cases, one disagreement.** A single differing case cannot size an offset. It can only
  say the offset is small on this set.
- **Two repositories, one language, no context pack.** ~~Unchanged, and still the biggest
  limit.~~ **Measured 2026-08-25:** it was not the biggest limit, or any limit at all on these
  nineteen cases — see `docs/step7b-context-pack.md`.
- **The two transports share a model.** Agreement between them is not independent confirmation of
  anything; it says the transport matters less than the lens prompts do.
- **Nothing here is a human acceptance rate.** 97 findings against 15 known defects is a reader's
  bill, not a verdict on whether the reader would pay it.
