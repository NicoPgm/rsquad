# Two transports on one commit — five runs

**Date:** 2026-08-23
**Commit:** `ai-video-digest@b404a93`, one file, `tools/portail_tests.py`.
**Model:** `claude-opus-5` throughout. Same prompts, same schemas, same guards, same ranking.

Five runs: three on the API transport, two on the harness transport. The two harness exports
were verified **byte-identical** before running, so any difference on that side comes from the
model and the harness, not from RSquad.

## The places each run reported

| Run | Transport | Configuration | Places | Findings kept |
|---|---|---|---|---:|
| A | API | 4 blind lenses | `272` `258` `137` | 8 |
| B | API | 4 lenses + refutation | `272` `259` `258` | 6 |
| C | API | 5 steps, full | `272` `258` | 8 |
| D | Harness | 5 steps, full | `272` `258` `137` | 9 |
| E | Harness | 5 steps, full | `272` `258` `137` | 8 |

**`:272` is in every run, ranked first in every run, `blocking` in every run.** That is the
ground-truth case, `head-overwritten-before-use`, and the top of the queue does not move.

**The two harness runs returned the identical place set, in the identical order, with identical
severities.** The only difference between D and E is the corroboration on entry 2: three lenses
agreed, then two.

**The three API runs returned three different place sets.** But read that carefully: A, B and C
had *different configurations* — A predates refutation, B predates the conformance lens. Only C
is comparable to D and E. **There is no pair of identical-configuration API runs**, so the API's
self-variance is not actually measured, and the apparent contrast is partly an artefact of how
the runs happened.

What can be said fairly:

- The blind-lens stage produced 8, 6 and 7 findings on the API, and 8 and 7 on the harness.
  Comparable spread; nothing distinguishes them.
- The harness's two runs agreed on places; the API has no like-for-like pair to compare.
- **Two runs do not give a variance, they give a difference.** They can show a transport is
  unstable; they cannot show it is stable. "No difference observed across two runs" is the whole
  claim.

## Zero malformed replies, across 28 agents

| | Run D | Run E |
|---|---:|---:|
| Findings after the guards | 9 | 8 |
| Dropped by the anchoring guard | **0** | **0** |
| **Malformed replies** | **0** | **0** |
| Missing replies | 0 | 0 |
| Refuted | 0 | 0 |

On the API path the closed vocabulary is enforced by `output_config.format`. On the harness path
nothing forces it: an agent reads `schema/finding.json` and conforms, or does not. Across four
workflow invocations and 28 agents, **not one reply failed validation and not one snippet failed
to anchor**.

That is the prediction of ADR-0008 holding twice — the constraint moves to ingest, where it costs
a wasted call instead of a wrong finding, and the observed cost is still zero wasted calls. It
remains a statement about one capable harness, which is why `ingest` validates regardless.

## Cost

| | Run D | Run E |
|---|---:|---:|
| Round 1 (5 lens tasks) | 331,680 | 330,144 |
| Round 2 (refutations) | 489,164 | 433,784 |
| **Total subagent tokens** | **820,844** | **763,928** |

Seven per cent apart. For a CI budget that stability may matter more than the stability of the
findings: a budget is planned in advance, a queue is read after the fact.

Run C, the comparable API run, billed **$0.9968** for 13 calls — which bounds it between 40k
tokens (all output at $25/1M) and 199k (all input at $5/1M). The harness spends **four to twenty
times** as many tokens for the same work. The gap is structural: each agent reads the task, reads
the schema, then writes a file, and none of those turns exists when a payload is assembled once
and sent.

**And that is the argument that decides deployment, pointing the other way.** Under a
subscription the larger number is invisible and needs no approval; the smaller one needs an API
key, and at work an API key needs a chain of approvals — worse for CI than for a laptop
(ADR-0005). The cheaper transport is the one that cannot be deployed.

## What five runs still do not establish

- **A like-for-like self-variance comparison.** It needs two API runs in the *same*
  configuration as D and E. Until then the headline above is "no difference observed on the
  harness across two runs", and nothing about the API.
- **Blindness under a harness.** In D and E the agents had file tools and a repository within
  reach: the lenses were blind by instruction, not by construction. The structural fix — a
  filesystem holding only the job — was not in place.
- **Anything beyond one file of one commit of one repository, in one language.**

ADR-0005 stays `proposed`.
