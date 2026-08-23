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
pack, so an agent needs no checkout to do its work. ~~Copy the job somewhere with no repository
beside it and blindness is restored by there being nothing to peek at.~~

> **That last sentence is wrong, and was corrected on 2026-08-23 by measuring it.** Relocating
> the job removes proximity, not reach: a Claude Code agent reads absolute paths, and the
> repository is still on the machine — and still the working directory its shell starts in. Runs
> D and E had *already* exported their jobs to a temp directory, and a transcript shows an agent
> running `git rev-parse` with no `cd`, which executed inside the repository under review.
>
> A structural fix has to confine the **agent** — a sandbox whose filesystem holds only the job,
> or a harness whose tools cannot leave their working directory. Neither is a change to RSquad,
> and neither was in place.
>
> What *was* measured, across 46 agents and 119 file operations in six workflow invocations:
> **not one read a file outside the job.** Blindness on this transport is therefore **observed,
> not enforced** — a transcript after the run, where the API path has a test before the call.
> The check is free and repeatable, and it makes a breach detectable rather than impossible.
> See `docs/blindness-under-a-harness.md`.

Run it inside a working copy and the blind lenses are blind only by good manners. Both modes are
usable; only one is defensible, and the driver says so at the top rather than in a footnote.

**First measured, same day.** Run end to end on `ai-video-digest@b404a93` against the API path:
identical top two entries, down to severity and the number of lenses that independently agreed;
zero replies dropped by the anchoring guard; and **zero malformed replies without any mechanical
constraint** — five agents read the schema and conformed. Roughly four to twenty times the tokens
for the same work, invisible under a subscription. See `docs/transport-comparison.md`.

The run also exposed a defect in this transport, now fixed: a finding with no refuter fell off
the edge of round 2, and the one that vanished was the only conformance account. The API path
never had it, because `refute_all` keeps such findings alive; across a job boundary there is no
memory.

**Measured since.** Self-variance: three harness runs on the same commit returned the same three
places (`transport-comparison.md`, `blindness-under-a-harness.md`). Blindness: 46 agents, zero
reads outside the job — see the correction above for what that does and does not establish.

**And one consequence nobody listed.** The agents used their tools to **verify claims
empirically** — one built a throwaway git repository, ran `git rev-parse` against a nonexistent
ref, and confirmed that git exits 128 while echoing the argument on stdout. The API path cannot
do that at all. For a squad whose contract is "reproduction or nothing", a refuter that can run
the reproduction is a different instrument, and it belongs in ADR-0005's comparison.
