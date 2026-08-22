# ADR-0007 — The conformance lens quotes its requirement, or stays quiet

**Status:** accepted
**Date:** 2026-08-22

## Context

Step [1] is the only reader shown what the change was supposed to do. Every other step is kept
from it on purpose (ADR-0002), so this one asks the question nobody else can: *does the change do
what it said?*

It also has a failure mode none of the others has. A blind lens can hallucinate code, and the
anchoring guard catches that. This lens can hallucinate a **requirement** — and a fabricated
requirement is worse than a missed mismatch. It sounds authoritative, it sends a reader to argue
with a document that never said it, and a squad that does it twice has a conformance section
nobody reads.

## Decision

**Both ends are anchored.** `snippet` must appear in the file near its line, as everywhere else.
`requirement` must appear **verbatim in the stated intent**, checked by exact search after
whitespace normalisation. A paraphrase fails, and that is the point: a paraphrase is where an
invented requirement hides. If it cannot be quoted, it is not a requirement.

**The intent is named, never discovered.** The commit message is always included — it is the
author's own statement and it is free. Anything further is passed explicitly with `--spec`. A
lens that went looking for "the spec" by walking directories would be one directory-walk from
undoing ADR-0002, and would also be wrong about which document matters.

**Its vocabulary is its own**, disjoint from the blind lenses' (a test asserts it). Shown their
kinds it would report bugs, which three better-placed readers already cover. `stale-intent` — the
code is right and the document is out of date — is explicitly encouraged: a spec that has drifted
does more damage than a missing feature, because everyone downstream keeps trusting it.

**No refuter, and it is named rather than left to be discovered.** The refuter in step [3] walks
concrete inputs to a concrete consequence, which is not the shape of a conformance claim.
Conformance findings reach the reader uncontested, guarded only by the double anchor — less than
the blind lenses get. The run report says so per finding.

## Consequences

First run, `ai-video-digest@b404a93`, intent = the commit message. The lens reported
**`contradicts` at line 272** and landed on the same lines as all four blind lenses: the commit
message advertises `--tete` as a way to replay a past commit, and the code overwrites the
resolved revision with `HEAD`. That is the strongest shape a conformance finding can take — the
message promises what the code does not deliver — and it needed the intent to see it.

**Two defects surfaced by running it, both mine.**

*Documenting a gap does not close it.* The module said there was no refuter for conformance
claims; nothing stopped the refuter being handed one, and it crashed on a missing `inputs` key —
reported as "unparsable verdict", which was also the wrong error. A conformance finding now
yields an explicit "no refuter exists for this claim shape", recorded and visible, and the
finding survives to be read.

*A single representative buried the only account that mattered.* When conformance lands on the
same lines as the blind lenses, its account is the only one carrying a quoted requirement, and
picking one most-detailed representative hid it — the queue said `contradicts` and showed nothing
about what was contradicted. The queue now shows one account **per shape**.

Cost for all five steps on one file: $0.9968, five lens calls and eight refutations.
