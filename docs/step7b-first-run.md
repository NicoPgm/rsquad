# Step 7b — 12 of 14, and this time the number means what it says

**Date:** 2026-08-23
**Pre-registration:** `evaluation/step7b.yaml`, committed at `0491ade` before any case ran.
**Cost:** 143 calls, **$12.55** — $5.10 + $2.93 (langchain4j) and $4.53 (spring-ai).
**Reports:** `evaluation/step7b-langchain4j.md`, `-2.md`, `evaluation/step7b-springai.md`.

| Arm | Scorable | Run | Detected |
|---|---:|---:|---:|
| langchain4j | 15 | 10 | **8** |
| spring-projects/spring-ai | 4 | 4 | **4** |
| | **19** | **14** | **12** |

Five langchain4j cases were never started: `--max-usd` stopped the arm, and they are reported as
**not started**, never as misses. The first live exercise of that guard.

**12 / 14, and unlike every earlier campaign this one is measuring what it claims to.** The
commits under review are real commits from each project's own history — the one that first wrote
the buggy line, verified to carry that line as an addition. No reverse patch, so the correct
version is not sitting on the minus side of the diff.

## The two misses are the interesting half

Neither returned nothing. In both, the squad found **a different real bug** and did not mention
the labelled one.

- `PgVectorEmbeddingStore` — the labelled defect is a builder field dropped from a long positional
  delegation. What came back instead: the RRF score threshold `score >= 0.7` is unreachable,
  because an RRF score maxes out at `2/61 ≈ 0.0328` for a document ranked first in both CTEs. That
  is arithmetic on the code in front of it, and it looks right.
- `OnnxScoringBertCrossEncoder` — the labelled defect is an unchecked `(float[][])` cast that
  breaks on 3D logits. What came back: the `OrtSession` is never closed when the constructor
  rethrows, leaking native memory for the life of the JVM.

Both misses are **omissions** — a missing argument, a missing type check — and both replacements
are **contradictions** present in the text. That is the hypothesis of `first-evaluation.md`
holding up on a set built specifically not to favour it.

Their finding counts say the same thing: the two missed cases returned **one** finding each, the
lowest in the run. The squad was not confused; it was elsewhere.

## No sign of memorisation

The covariate the whole young-repository detour was for:

| Origin of the defect | Detected |
|---|---|
| **after the May 2026 knowledge cutoff** | **3 / 3** |
| 2025 – 2026-05 | 5 / 6 |
| 2024 and earlier | 4 / 5 |

The post-cutoff cases — code whose fixed form the model cannot have read — did at least as well as
the rest. **No gradient.** Three cases is far too few to settle it, but the direction that would
have invalidated the headline is not there, and it is the first time this question has had any
data at all.

By label: **4 / 4** on `yes`, **8 / 10** on `weak`. The rubric's `weak` did not predict failure —
five spring-ai and langchain4j cases were labelled `weak` precisely because confirming them needs
a fact outside the file (the `Flux.create` contract, Gson's number widening, Redis returning ten
results by default), and the lenses supplied that fact themselves, correctly, every time. The
rubric measures the evidence in the diff; the model brings its own.

## The reader's cost, measured for the first time

32 surviving findings across 14 cases — **2.3 per case**, of which **20 were not the known
defect**.

Calling those false positives would be wrong: several are real, and one of the misses above found
a genuine unreachable-threshold bug. But 20 unlabelled claims is what a reader actually pays, and
it is the number that decides whether anyone keeps the tool. It has never been measurable before —
`evaluate` discarded it until this morning.

**Zero findings refused by the guards**, across 143 calls against Java. The anchoring guard and
"reproduction or nothing" rejected nothing, on a language they were never designed against and
with **no context pack at all** (question 6 is unimplemented for Java, so every lens ran on the
diff and the file alone).

## Cost

**$0.90 per case**, against the $0.84 the freeze budgeted from the earlier Java run. The
`--max-usd` guard stopped langchain4j at $5.095 of its $8 cap, reserving $3 for a case that could
not be guaranteed to fit — conservative by design, and it cost five cases.

## One defect, found by paying for it

`langchain4j-145ff45` died mid-run with `expected str, bytes or os.PathLike object, not int`. The
origin sha is `632836213` — **all digits, so YAML parsed it as an integer** and `git rev-parse`
received an `int`. Same family as the `yes`/`no` boolean trap this repository already carries a
guard for.

The batch rule held: the case was reported as *did not run*, the other six continued, and nothing
was recorded as a miss. Shas are quoted now, the renderer quotes them, and a test asserts it with
the exact error message in its docstring.

## What this still does not establish

- **19 scorable cases give about ±20 points**, and only 14 ran. 12/14 is not 86 % of anything.
- **Five cases are unrun**, and they are not a random five: `--max-usd` stopped on cost, and cost
  tracks the number of findings. Whatever those five would have shown, they are the cheap tail.
- **No false-positive corpus.** Every case here contains a known defect. The 20 unlabelled
  findings bound the reader's cost on defective diffs, not on clean ones.
- **No context pack**, so this is a floor for Java rather than a comparable to the Python runs.
- **The labeller read the results.** The rubric and the labels were committed first, which bounds
  it and does not remove it.
