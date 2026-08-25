# The context pack changed nothing — nineteen cases, case for case

**Result:** 14/19 detected with the pack, 14/19 without. **The same fourteen cases, and the same
five misses.** Not one verdict differs.

**Model:** `claude-opus-5`, effort `high`, on both sides — verified from the agent transcripts
rather than assumed, after finding that the harness had been ignoring the model recorded in the
manifest and inheriting the session's. The two agreed across all 21 workflow runs, by
coincidence rather than by construction. The driver reads the field now.

## What was varied, and what was held

One variable: whether a blind lens receives the definitions its diff references.

Everything else is the same object — the same 22-case freeze filtered to the same 19 scorable,
the same origin commits, the same prompts, the same closed vocabularies, the same two mechanical
guards, the same refutation round, the same rubric, and the same reader applying it. The
without-pack half is the run published in `step7b-langchain4j-harness.md` and
`step7b-springai-harness.md`; it was not re-run.

| | without pack | with pack |
|---|---|---|
| cases | 19 | 19 |
| **detected** | **14/19** | **14/19** |
| tasks carrying a pack | 0 of 190 | 175 of 190 |
| average task payload | 24 406 chars | 31 844 chars (+30 %) |
| findings surviving refutation | 90 | 83 |
| distinct places | 44 | 41 |
| findings refused by the guards | 0 | 0 |

14/19 is 74 %, Wilson 95 % [51 %, 88 %].

## Why the packs were empty before

The resolver was chosen once per run, globally, and it was Python's. Handed a `.java` file it
raised `SyntaxError`, returned an empty list, and an empty pack renders as an empty string.
Nothing failed and nothing said so, so every Java number this project has published is a
measurement of the squad without the pack — which is what made this comparison worth running.

Question 6 now routes per file. A test command is a property of the repository; a context pack
is a property of the file being read, and one change can touch both languages.

## The claim this retires

Every Java report carried a caveat: *the context pack is unimplemented for this stack, so the
detection rate is a floor.* That was a reasonable thing to believe and it is now measured. **It
does not hold at n = 19.** The pack is not what was missing.

The five misses say it more sharply than the totals do, because in two of them **the definition
the labelled defect needed was in the payload**:

| missed case | what the pack delivered | what the squad reported instead |
|---|---|---|
| `langchain4j-575eb46` | `WebSearchOrganicResult`, which declares the `getLink()` feeding the unguarded `URI.create` | a `NullPointerException` on `getPagemap().isEmpty()`, elsewhere in the same method |
| `langchain4j-e59754e` | `EmbeddingSearchRequest`, whose constructor runs `ensureBetween(minScore, 0.0, 1.0)` | the RRF-scale bug — a real defect, and not the labelled one |
| `langchain4j-95a3aff` | 7 definitions | a conformance note on the null branch, not the unhandled general case |
| `langchain4j-771b0d2` | **nothing** — every reference is third-party ONNX | an `OrtSession` leak |
| `spring-ai-c256cfa` | 9 definitions including `ToolCallingObservationContext` | nothing at all; the one silent case, silent on both transports and now with the pack too |

Four of the five were handed relevant context and went somewhere else. Whatever bounds this
squad on those cases, **it is selection, not information.** That is a different problem and it
will not be fixed by a bigger payload — which is worth knowing before anyone spends a week
building a richer one.

## What this does not say

- **It does not say the pack is worthless.** [51 %, 88 %] cannot exclude a small effect, and a
  null result at n = 19 is a bound, not a proof. It says the effect is not large.
- **It measures a replay, not a review.** Each case is one file at one commit. A real
  `rsquad review` cuts a change into several units, and the defect that lives *between* two
  changed files is exactly the shape a pack should help with and this corpus cannot contain.
- **It says nothing about the other three lenses' appetite for context**, only about the
  aggregate.
- The reader cost moved the *right* way and that was not guaranteed: 30 % more payload could
  easily have produced 30 % more to read. It produced 8 % less.

## Reproducing it

    python evaluation/step7b_prepare.py <workspace> evaluation/step7b.yaml
    python -m rsquad evaluate --defects <workspace>/step7b.langchain4j.defects.yaml \
        --repo <workspace>/langchain4j --export --jobs <jobs>/b7lc
    # run the harness over <jobs>/b7lc, then ingest twice — lenses, then refutations
    python -m rsquad evaluate --defects ... --ingest --jobs <jobs>/b7lc --out <report>

The step7d half of the forty-case set was exported with packs and **not run**: 19 more cases
would tighten the interval, not change the answer, and the measurement above is complete on its
own terms.
