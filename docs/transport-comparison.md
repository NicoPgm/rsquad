# Two transports on one commit — seven runs

**Date:** 2026-08-23
**Commit:** `ai-video-digest@b404a93`, one file, `tools/portail_tests.py`.
**Model:** `claude-opus-5` throughout. Same prompts, same schemas, same guards, same ranking.

Seven runs. Five of them — three API, two harness — share the **same full configuration**: four
blind lenses, the conformance lens, then one refuter per refutable finding. The two harness
exports were verified byte-identical before running, so any difference on that side comes from
the model and the harness, not from RSquad.

## Both transports are stable on places. That was not the expected result.

| Run | Transport | Places | Findings | Cost |
|---|---|---|---:|---:|
| C | API | `272` `258` | 8 | $0.9968 |
| F | API | `272` `258` | 7 | $0.9321 |
| G | API | `272` `258` | 6 | $0.7982 |
| D | Harness | `272` `258` `137` | 9 | 820,844 tokens |
| E | Harness | `272` `258` `137` | 8 | 763,928 tokens |

**Three API runs, one place set. Two harness runs, one place set.** `:272` — the ground-truth
case — is ranked first and `blocking` in all seven runs including the two earlier
different-configuration ones.

The finding *counts* move (6–8 on the API, 8–9 on the harness) and the corroboration counts move
(entry 2 drew 1, 2 or 3 lenses depending on the run). The *places* do not.

**This removes one of my own arguments.** ADR-0002 defended the API transport partly on
reproducibility, and the first comparison seemed to support it — three API runs had given three
different place sets. They had also had three different configurations. Held constant, the two
transports are equally stable here, and the reproducibility argument for the API path loses its
empirical support. What survives is the other one: blindness that a test can assert.

## The real difference is coverage, and the obvious explanation is wrong

`:137` is found by the harness **2 times out of 2** and by the API **0 times out of 3** in this
configuration. It is a real defect — the empty-retained-set bug, already fixed in this
repository — so every run that misses it is a false negative, not a matter of taste.

The tempting explanation is that harness agents have file-reading tools. **It does not hold.**
Line 137 is `if retenus and fonction not in retenus and not erreur_de_collecte:` — in
`tools/portail_tests.py`, the very file both transports were handed in full, inside the diff.
There was nothing to go and fetch.

So the difference is not file access. Candidates worth testing, none tested:

- sampling variance, which at these sample sizes explains it comfortably;
- the task file concatenating system and user text, where the API path keeps them separate;
- the agent's own loop — reading, re-reading, then writing — giving more passes over the same
  text than a single completion.

**0/3 against 2/2 is suggestive and not significant** (Fisher exact, two-tailed, p ≈ 0.1).
Distinguishing a real coverage difference from sampling would need roughly ten runs per
transport, which is $10 and an afternoon, not a conclusion available today.

## Cost, and which number is stable

| | API (3 runs) | Harness (2 runs) |
|---|---|---|
| Spread | $0.80 – $1.00, **25 %** | 763,928 – 820,844 tokens, **7 %** |

The harness's *cost* is the steadier number. For a CI budget that may matter more than the
steadiness of the queue: a budget is planned in advance, a queue is read afterwards.

In absolute terms the API run bills $0.80–$1.00 for 11–13 calls, which bounds it between roughly
40k and 200k tokens. The harness spends four to twenty times as many for the same work —
structural, not waste: each agent reads the task, reads the schema, writes a file, and none of
those turns exists when a payload is assembled once and sent.

**And that is still the argument that decides deployment, pointing the other way.** Under a
subscription the larger number is invisible and needs no approval; the smaller one needs an API
key, and at work an API key needs a chain of approvals — worse for CI than for a laptop
(ADR-0005). The cheaper transport is the one that cannot be deployed.

## Zero malformed replies, across 28 harness agents

On the API path the closed vocabulary is enforced by `output_config.format`. On the harness path
nothing forces it. Across four workflow invocations and 28 agents, not one reply failed schema
validation and not one snippet failed to anchor — in either transport, across all seven runs.

ADR-0008's prediction has now held twice: the constraint moves to ingest, where it costs a wasted
call instead of a wrong finding, and the observed cost is still zero wasted calls. It remains a
statement about one capable harness, which is why `ingest` validates regardless.

## What seven runs still do not establish

- **Whether the `:137` gap is real.** 0/3 against 2/2 is not enough, and the mechanism that
  would have explained it is ruled out.
- **Blindness under a harness.** In D and E the agents had file tools and a repository within
  reach: the lenses were blind by instruction, not by construction. The structural fix — a
  filesystem holding only the job — was not in place.
- **Anything beyond one file of one commit of one repository, in one language.**

ADR-0005 stays `proposed`. On this evidence the two transports are close enough that the choice
is an operational one — which budget is approvable, which harness the developer already has open
— rather than a technical one. That is a finding, not a failure to decide.
