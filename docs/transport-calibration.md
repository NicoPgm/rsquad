# Calibrating the harness against the API — same cases, and they disagree

> **Superseded 2026-08-24 by `docs/transport-calibration-19.md`**, which ran all nineteen cases
> on both transports for $0 — because the API half was already bought, so the replay had to go
> the *other* way. On nineteen cases the two agree on eighteen, and the whole disagreement is the
> single case named below. The sentence "the transports are not interchangeable per case" was
> built on a four-case window and does not survive.
>
> Two corrections of fact: the counts below labelled "findings" are **distinct places** (19
> findings against 16, for 10 places against 6), and the closing recommendation to spend the API
> budget on calibration is wrong — calibration turned out to be free.

**Date:** 2026-08-24
**Cases:** the four scorable spring-ai cases of `step7b.yaml`, run on both transports.
**Cost:** 46 agents, 2.65 million tokens, **$0** — the API half was already paid for on 2026-08-23.

The API budget is unavailable for a while, and scaling a detection rate to forty cases costs
dollars there and tokens on the harness. So the question is no longer *which transport is better*
but **whether a number measured on the harness transfers to the API one.** These are the first
four cases where both have run on identical inputs.

## They do not agree

| Case | API | harness |
|---|---|---|
| `b1384c8` audio transcription leak | detected, 5 findings | detected, 3 findings |
| `4fbb484` Gson widens numbers | detected, 2 | detected, 1 |
| `c256cfa` null parent observation | **detected**, 1 | **silent**, 0 |
| `ec1e052` Redis pagination | detected, 2 | detected, 2 |
| | **4 / 4**, 10 findings | **3 / 4**, 6 findings |

On four cases 3/4 against 4/4 is worth nothing statistically (Fisher exact, p = 1.0). The
direction is what matters, because it is the second time the transports have disagreed and it is
**the other way round from the first time**:

- `transport-comparison.md`: the harness found `tools/portail_tests.py:137` in 3 runs out of 3
  where the API found it in 0 out of 3. The harness found **more**.
- here: the harness returned 6 findings against 10, and missed a case the API caught. The harness
  found **less**.

So the difference is not a constant offset in either direction. The transports are not
interchangeable per case, and neither is systematically the more sensitive one on this evidence.

## The missed case is the smallest one

`c256cfa` is a seven-line diff. The API found exactly one thing in it — `getOrDefault(KEY, null)`
producing a parent observation that then overwrites a parent Micrometer had already resolved. The
harness found nothing at all.

That is a hypothesis worth naming and not worth believing yet: on a diff with almost nothing in
it, the harness path may be less inclined to report the single subtle thing that is there. It
would matter, because small diffs are exactly what a pre-push review sees most of.

Nothing here tests it. Four cases, one divergence.

## What this changes about the plan

The intention was to scale to forty cases on the harness, since cases are free there. That still
holds — **but the number it produces is a harness number.** Calling it the squad's detection rate
would assume a transfer this measurement does not support.

So the deferred API budget should not be spent on more cases. **It should be spent on
calibration**: the same cases on both transports, enough of them to size the disagreement. More
cases are free; only the bridge between the two costs money, and the bridge is what is missing.

Concretely, when the budget returns: ten to fifteen cases already run on the harness, replayed on
the API, compared case by case. At $0.90 a case that is $9 to $14 — far less than the $35 that
scaling on the API would have cost, and it buys the thing that scaling cannot.

## What the run also confirmed

The harness evaluation path works end to end: `--export` wrote four jobs, the harness ran 20 lens
tasks and 18 refutations, `--ingest` advanced the round and then assembled the same report shape
the API path produces. No reply was missing or malformed, and no finding was refused by the
guards.

`ec1e052` reproduced on the harness the second bug the API found there — `String.replace` strips
every occurrence of the key prefix, so `embedding:embedding:42` becomes `42` and the loop deletes
an unrelated document. Independent rediscovery across transports is the closest thing to
corroboration this project has.
