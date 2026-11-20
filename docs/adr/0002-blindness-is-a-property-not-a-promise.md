# ADR-0002 — Blindness is a property of the payload, not an instruction in the prompt

**Status:** accepted
**Date:** 2026-08-22

## Context

Step [1] reads the change against its stated intent. Steps [2] must answer a different question
— *what does this code actually do, and where does it break?* — and a reviewer who knows the
intent checks conformance to the intent instead. If all the lenses share the spec you have four
agents doing one job while believing they are doing four.

The easy way to arrange that is to write *do not read the specification* in the prompt. It costs
nothing and it cannot be checked.

## Decision

The blind lenses are blind because **their request has no channel through which a specification
could arrive**, not because they were asked not to look.

`lenses.request()` is a pure function of `(unit, lens, model)`. A test asserts that signature; a
second test characterises the request completely — shared block, lens block, rendered unit — so
nothing else can be in it.

The same rule binds the context pack (ADR-0004): it walks imports, never directories, so there
is no path from it to `docs/`.

## Consequences

**A blind lens cannot be given file-reading tools.** An agent with `Read` and `Grep` can reach a
spec whenever it likes, and blindness would revert to a promise. This is the main reason the
lenses are a standalone program rather than harness-hosted agents (ADR-0005), and it is the
constraint any second transport has to satisfy or explicitly give up.

The cost is coverage: a lens cannot go looking for something it was not handed. ADR-0004 buys
back part of that without giving up the property.

A test that lists forbidden words does **not** enforce this, and one was written and removed:
the shared prompt legitimately contains "commit message", in the sentence explaining that the
lens is never shown one.

**2026-11-20** — on the harness, now the primary transport (ADR-0009), this decision is
scoped by ADR-0010: the payload stays blind and that stays tested; the agent's reach does
not, and is called blindness by instruction. On the frozen API path this ADR holds unchanged.
