# ADR-0008 — The second transport is a job on disk, not a workflow

**Status:** accepted
**Date:** 2026-08-23
**Refines:** [ADR-0005](0005-two-transports-one-core.md)

## Context

ADR-0005 committed to two transports and one core, and named the second transport "harness-hosted
agents". The obvious build was a Claude Code workflow.

It is the wrong shape for the stated need. The deployment is *locally before push, in Cursor* and
*in CI*, and **a Claude Code workflow runs in neither**. Building against one harness would have
produced a third implementation the first time the editor changed — which is the divergence
ADR-0005 exists to prevent.

## Decision

The seam is a **job directory**, and the harness is whatever runs it.

```
rsquad export <job>     units, context packs, every prompt rendered, one task per call
<any harness>           read a task, run it, write the JSON reply beside it
rsquad ingest <job>     validate, run both guards, write the next round or the queue
```

Everything that makes the squad trustworthy stays on RSquad's side: the closed vocabularies, the
anchoring guard, "reproduction or nothing", the ranking, and what each lens is asked. The harness
contributes exactly one thing — a model call — and cannot quietly change the question or the
standard the answer must meet.

`harness/claude-code.workflow.js` is *a* driver, not *the* transport. A Cursor rule, a shell
loop, or a person with a chat window are equally valid drivers, and none of them requires a line
of RSquad to change.

**Refutation is two rounds.** A refuter needs a finding, so it cannot ship alongside the lenses.
`ingest` reads round 1 and writes round 2; run it again on round 2 and it writes the queue.

## Consequences

**Mechanical constraint moves rather than disappears.** A harness that supports structured
output can force the schema — the job hands it the same one the API path uses. One that cannot
will return prose-wrapped JSON, and `ingest` validates every reply and drops what does not
conform. The constraint moves from generation time to ingest time, where it costs a wasted call
instead of a wrong finding. Tested: a reply using a `kind` outside the enum is dropped as
malformed, a hallucinated snippet is dropped by the anchor, and a missing reply is reported as
missing rather than read as "nothing found".

**Prompt caching stops being ours.** On the API path the four lenses share a byte-identical
prefix — one cache write, three reads, measured twice. Here the harness decides. That points the
opposite way from the billing argument in ADR-0005, which is why the choice stays a measurement.

### Blindness degrades from a property to a promise, and there is a fix

This is what building the transport revealed, and it is the consequence ADR-0002 predicted
without being able to price.

A harness agent has file-reading tools. It **can** read the specification, the ticket, the rest
of the repository. A task file saying "read no other file" is an instruction, and an instruction
is not a property — the exact distinction ADR-0002 was written to defend.

The mitigation is structural rather than textual: **run the harness against a job directory and
nothing else.** A task file already carries the diff, the numbered file and the resolved context
pack, so an agent needs no checkout to do its work. Copy the job somewhere with no repository
beside it and blindness is restored by there being nothing to peek at.

Run it inside a working copy and the blind lenses are blind only by good manners. Both modes are
usable; only one is defensible, and the driver says so at the top rather than in a footnote.

**What is still not measured.** Whether the two transports find the same things, at what cost,
and — the number ADR-0005 actually turns on — which one varies less against itself. The API path
has one data point already: the same commit gave 8 findings then 6. Nothing yet for this one.
