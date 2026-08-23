# Two transports on one commit — the first data point

**Date:** 2026-08-23
**Commit:** `ai-video-digest@b404a93`, one file, `tools/portail_tests.py`.
**Both runs:** same prompts, same schemas, same guards, same ranking, `claude-opus-5`.
Only the transport differed.

This is **one run each**. It is a data point, not the measurement ADR-0005 asks for — that one
needs each transport run twice, and the number it turns on is self-variance.

## They agree on what matters

| Rank | API (five steps) | Harness (five steps) |
|---|---|---|
| 1 | `:272` — blocking · **5 lenses agree** | `:272` — blocking · **5 lenses agree** |
| 2 | `:258` — significant · **3 lenses agree** | `:258` — significant · **3 lenses agree** |
| 3 | — | `:137` — significant |

Identical top two, down to the severity and the number of lenses that independently landed
there. `:272` is `head-overwritten-before-use`, the best case in `evaluation/defects.yaml`; both
transports put it first and both called it blocking.

The harness found a third place, `:137` — the empty-retained-set defect, real and already fixed
in this repository. **Do not read that as the harness finding more.** The API path produced 8, 6
and 8 findings across three runs of this same commit; one extra entry is inside that spread.
Attributing it to the transport would need repeats.

## What the harness cost in guard failures: nothing

| | API | Harness |
|---|---:|---:|
| Findings after the guards | 8 | 9 |
| **Dropped by the anchoring guard** | **0** | **0** |
| **Malformed replies** | n/a — schema forced | **0** |
| Missing replies | 0 | 0 |
| Refuted | 0 | 0 |

The interesting cell is *malformed: 0*. On the API path the closed vocabulary is enforced by
`output_config.format`. Here five agents read `schema/finding.json` and conformed **without any
mechanical constraint**. That is the prediction in ADR-0008 — the constraint moves to ingest,
where it costs a wasted call rather than a wrong finding — and the observed cost was zero wasted
calls.

Do not over-read it either. Five replies from one capable harness say nothing about a weaker
one, which is exactly why `ingest` validates regardless.

## What it cost in tokens: several times more

| | API | Harness |
|---|---:|---:|
| Model calls | 13 | 15 agents |
| Billed | **$0.9968** | not itemised |
| Subagent tokens | — | **820,844** |

A bound rather than a figure: $0.9968 is between 40k tokens (if every token were output at
$25/1M) and 199k (if every one were input at $5/1M). The harness spent 820,844. So it used
**roughly four to twenty times** the tokens for the same work, and the true multiple sits in the
middle of that range.

The reason is structural, not waste: each agent reads the task file, reads the schema, then
writes a file. Those turns do not exist on the API path, where the payload is assembled once and
sent.

**And this is the argument that decides deployment, pointing the other way.** Under a
subscription the larger number is invisible and needs no approval; the smaller number needs an
API key, and at work an API key needs a chain of approvals — worse for CI than for a laptop
(ADR-0005). The cheaper transport is the one that cannot be deployed.

## Two defects this run exposed, both in the transport

**A finding with no refuter fell off the edge of the round.** Nine findings entered round 2,
eight had refutation tasks, and the queue showed eight — the missing one was the only
conformance account in the run. The API path never had the bug: `refute_all` emits a "no refuter
for this claim shape" verdict and the finding survives. Across a job boundary there is no
memory. Fixed: unrefutable findings ride in the manifest and reach the queue uncontested and
marked as such.

**A `rm -rf` was refused by the deny list** while setting the run up. Working as intended,
recorded because a guard that never fires is a guard nobody has tested.

## What this still does not establish

- **Self-variance for the harness.** Zero data points. The API path has one comparison already:
  8 findings then 6, with severities moving. Until the harness is run twice on the same commit,
  ADR-0005's question is unanswered.
- **Blindness under the harness.** In this run the lenses were blind *by instruction*: the
  agents had file tools and a repository within reach. The structural fix — a filesystem holding
  only the job — was not in place, and until it is, the harness's blindness is unmeasured rather
  than absent.
- **Anything about other commits, other files, other stacks.** One file.
