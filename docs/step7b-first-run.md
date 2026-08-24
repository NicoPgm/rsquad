# Step 7b — 15 of 19, and this time the number means what it says

**Date:** 2026-08-23
**Pre-registration:** `evaluation/step7b.yaml`, committed at `0491ade` before any case ran.
**Cost:** 199 calls, **$17.24**, across four invocations.
**Reports:** `evaluation/step7b-langchain4j.md`, `-2.md`, `-3.md`, `evaluation/step7b-springai.md`.

| Arm | Scorable | Detected |
|---|---:|---:|
| langchain4j | 15 | **11** |
| spring-projects/spring-ai | 4 | **4** |
| | **19** | **15** |

The first pass stopped at 14 cases: `--max-usd` halted langchain4j at $5.095 of its $8 cap and
reported five cases as **not started**, never as misses — the first live exercise of that guard.
The bound was then raised to $21 by an explicit, dated amendment and those five were run, because
a tail selected by cost is a tail selected by finding count, which is not independent of the
result (`evaluation/step7b.yaml`, `amendment_2026_08_23`).

**15 / 19, and unlike every earlier campaign this one is measuring what it claims to.** The
commits under review are real commits from each project's own history — the one that first wrote
the buggy line, verified to carry that line as an addition. No reverse patch, so the correct
version is not sitting on the minus side of the diff.

## All four misses are the interesting half

Not one returned nothing. In every case the squad found **a different real bug** and never
mentioned the labelled one.

- `PgVectorEmbeddingStore` — the labelled defect is a builder field dropped from a long positional
  delegation. What came back instead: the RRF score threshold `score >= 0.7` is unreachable,
  because an RRF score maxes out at `2/61 ≈ 0.0328` for a document ranked first in both CTEs. That
  is arithmetic on the code in front of it, and it looks right.
- `OnnxScoringBertCrossEncoder` — the labelled defect is an unchecked `(float[][])` cast that
  breaks on 3D logits. What came back: the `OrtSession` is never closed when the constructor
  rethrows, leaking native memory for the life of the JVM.

- `GoogleCustomWebSearchEngine` — the labelled defect is `URI.create` throwing on a malformed
  link. What came back: a NullPointerException on `getPagemap()`. Same consequence, one bad result
  killing the whole search; different mechanism, different line.
- `InMemoryEmbeddingStore` — the labelled defect is an `UnsupportedOperationException` thrown for
  embedded objects that are neither `TextSegment` nor null. What came back pointed into that exact
  chain and argued the opposite direction, about `null` entries being kept.

The first two are **omissions** — a missing argument, a missing type check — and their
replacements are **contradictions** present in the text. That is the hypothesis of
`first-evaluation.md` holding up on a set built specifically not to favour it.

The finding counts agree: the two omission misses returned **one** finding each, the lowest in the
run. The squad was not confused; it was elsewhere.

## The memorisation gradient runs backwards

The covariate the whole young-repository detour was for:

| Origin of the defect | Detected |
|---|---|
| **after the May 2026 knowledge cutoff** | **5 / 5** |
| 2025 – 2026-05 | 6 / 7 |
| 2024 and earlier | 4 / 7 |

There is a gradient, and it runs **the wrong way for the memorisation hypothesis**. Recalling a
fixed version would make the *old* cases easier, since those have sat in training data longest in
both forms. Detection is highest on the five whose defect was written after the cutoff, where
recall is impossible, and lowest on the oldest.

So the confound the whole young-repository detour was built to expose does not appear, and the
data leans against it. What the gradient is instead — newer code in these projects being smaller,
or its defects being of a different shape — is not answered here.

By label: **5 / 5** on `yes`, **10 / 14** on `weak`. The rubric's `weak` did not predict failure —
five spring-ai and langchain4j cases were labelled `weak` precisely because confirming them needs
a fact outside the file (the `Flux.create` contract, Gson's number widening, Redis returning ten
results by default), and the lenses supplied that fact themselves, correctly, every time. The
rubric measures the evidence in the diff; the model brings its own.

## The reader's cost, measured for the first time

50 surviving findings across 19 cases — **2.6 per case**, of which **35 were not the known
defect**.

> **Corrected 2026-08-24.** 50 is the number of distinct `file:line` **places**, not of findings:
> several lenses reaching the same line collapse to one. The finding count is **97**, i.e. **5.1
> per case**, of which 82 were not the known defect. Both units are legitimate and this document
> used the wrong word for the one it counted. See `docs/transport-calibration-19.md`.

Calling those false positives would be wrong: several are real, and every one of the four misses
found a genuine bug instead. But 35 unlabelled claims is what a reader actually pays, and it is
the number that decides whether anyone keeps the tool. It has never been measurable before —
`evaluate` discarded it until this morning.

**Zero findings refused by the guards**, across 199 calls against Java. The anchoring guard and
"reproduction or nothing" rejected nothing, on a language they were never designed against and
with **no context pack at all** (question 6 is unimplemented for Java, so every lens ran on the
diff and the file alone).

## Cost

**$0.91 per case**, against the $0.84 the freeze budgeted from the earlier Java run. The
`--max-usd` guard reserves $3 for a case whose size cannot be known in advance — conservative by
design, and on the first pass that cost five cases which had to be run separately.

## One defect, found by paying for it

`langchain4j-145ff45` died mid-run with `expected str, bytes or os.PathLike object, not int`. The
origin sha is `632836213` — **all digits, so YAML parsed it as an integer** and `git rev-parse`
received an `int`. Same family as the `yes`/`no` boolean trap this repository already carries a
guard for.

The batch rule held: the case was reported as *did not run*, the other cases continued, and nothing
was recorded as a miss. Shas are quoted now, the renderer quotes them, and a test asserts it with
the exact error message in its docstring.

## What this still does not establish

- **19 scorable cases give about ±20 points.** 15/19 is 79 % with a confidence interval running
  from roughly 57 % to 92 %. Quote the fraction, not the percentage.
- **The five post-cutoff cases are five.** 5/5 is the most encouraging number here and the
  weakest evidence in it.
- **No false-positive corpus.** Every case contains a known defect. The 35 unlabelled findings
  bound the reader's cost on defective diffs, not on clean ones.
- **No context pack**, so this is a floor for Java rather than a comparable to the Python runs.
- **The labeller read the results.** The rubric and the labels were committed first, which bounds
  it and does not remove it.

## Postscript: two verdicts settled by checking rather than judging

`InMemoryEmbeddingStore` was nearly scored a hit. The finding argued that entries with a `null`
embedded object are silently kept "instead of raising UnsupportedOperationException". The pre-fix
code did throw that exception — for objects that are neither `TextSegment` nor null — and the fix
makes them non-matching instead. So the finding pointed into the defective chain and argued the
opposite direction. **Missed**, settled by reading the fix rather than by deciding it looked close
enough.

`GoogleCustomWebSearchEngine` is the same shape, one step further out: same consequence, different
mechanism, different line.

Both are the scoring rule doing what it was written for. A finding at the right place for the
wrong reason is a coincidence, and counting it inflates every number after it.
