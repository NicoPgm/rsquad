# ADR-0004 — One file per unit, plus a computed context pack

**Status:** accepted
**Date:** 2026-08-22

## Context

A lens sees one changed file. That misses any defect whose cause lives across an import — a call
whose signature changed on the other side, a filter reading a field nothing populates.

The obvious fix is to give lenses file-reading tools. It costs two things: blindness stops being
enforceable (ADR-0002), and the run stops being reproducible, because what an agent chooses to
read varies between runs and a squad that cannot be replayed cannot be measured.

## Decision

The unit stays one file. The gap is narrowed by a **computed context pack**: the definitions of
first-party symbols that the *changed lines* reference, resolved deterministically from the
revision and attached to the payload.

- **Deterministic.** Same revision and diff give the same pack, in the same order, byte for
  byte. No model is involved and nothing is ranked by relevance.
- **Symbol-driven, never directory-driven.** It walks imports. There is no path from it to a
  specification, so blindness survives.
- **Announced.** The block says the definitions are not under review and that absence from it is
  not evidence of absence in the repository — the same reflex as the elision marker.

Resolution is per-language, so this is **question 6** of the adapter protocol. `base.py` had
already predicted a sixth question existed; it arrived from a conversation rather than a crash,
which was cheaper.

## Consequences

Measured over 34 changed source files across 20 commits of the sibling project: **65 % get at
least one definition, 3.2 on average**, up to 14 on orchestration files.

The distribution is the point. Leaf modules like `discover.py` resolve almost nothing — one
symbol — because they import almost nothing first-party, and they need nothing. Orchestration
files resolve the most, and need it most. A pack that looked empty on the first file tried was
not a broken resolver; it was a file with no coupling to resolve.

This does **not** close the gap. It resolves what the change names, not what a curious reader
would have gone looking for. Whether tools find materially more, and at what cost in false
anchors, is a measurement that has not been run — see ADR-0005.

Findings must still be reported in the file under review; context files are for understanding,
and a finding quoting one is dropped by the anchoring guard.
