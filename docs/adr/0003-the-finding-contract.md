# ADR-0003 — Closed vocabulary and two mechanical guards

**Status:** accepted
**Date:** 2026-08-22

## Context

A review squad's failure mode is not missing defects, it is producing plausible ones. An agent
asked for problems supplies some. Left unchecked, the queue fills with confident prose about
code that is not quite there, and the reader learns to skip it — taking the real findings along.

## Decision

Everything a lens produces passes `schema/finding.v1.json`:

```
file · line · snippet · kind · severity · inputs · consequence
```

**`kind` and `severity` are closed enumerations**, constrained by the API's structured-output
format rather than by prose. They exist once, in the schema, with the gloss that explains each
value; the prompt text is rendered from them at run time, so the two cannot drift.

**Anchoring.** `snippet` must appear in the file within a few lines of `line`, by exact search
after whitespace normalisation. Checking it *near the claimed line* validates the quote and the
location together. This is the only anti-hallucination guard that depends on no provider, no
model and no prompt — a direct transposition of the sibling project's rule that an entity absent
from the transcript is deleted however plausible it reads.

**Reproduction or nothing.** `inputs` and `consequence` are required and must not be vacuous.
"This is fragile" does not ship; "if `items` is empty, line 42 raises" does, and is therefore
checkable, refutable, and worth arguing about on evidence.

Rejected findings are returned beside kept ones, never dropped silently.

## Consequences

The guards are deliberately weak where they cannot be strong. The vacuity check rejects the
empty and the evasive; it cannot separate a specific claim from a confidently-worded vague one,
and a test pins that limit so nobody mistakes it for a quality check. Judging prose is step [3].

**Not every constraint survives the wire.** Measured against the live API: `minimum` on an
integer is rejected outright, `minLength` on a string is accepted. So `api_schema()` strips the
numeric bound and `validate()` keeps it client-side — the sibling project's eleventh constraint,
met for real: cardinality is not guaranteed by structured outputs.

First measured result: 21 findings across two runs, **none dropped by the anchoring guard**. The
guard exists for the day that number is not zero.
