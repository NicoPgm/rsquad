# ADR-0001 — Record decisions in ADRs

**Status:** accepted
**Date:** 2026-08-22

## Context

Three days of decisions accumulated in commit messages, module docstrings and a conversation.
Each was reasoned and most were measured, but a decision that lives in a commit message is
findable only by someone who already knows it exists. The first person to ask "why is the unit
one file?" would have had to read the whole history to find out — or, more likely, would have
changed it.

The sibling project uses ADRs and they earned their keep: `docs/adr/0007` is the reason a
non-publication constraint survived a moment when it was inconvenient.

This ADR exists because the gap was pointed out, not because it was noticed.

## Decision

Every decision that constrains future work gets an ADR. One file, numbered, in `docs/adr/`.

A decision qualifies when reversing it would be expensive, or when a newcomer could plausibly
undo it by accident. Prompt wording, thresholds and naming do not qualify; what a lens is
allowed to see does.

Each ADR states what was true when it was written, including the measurements. When a decision
changes, the old ADR is superseded rather than edited: the reasoning that turned out wrong is
the most useful part of the record.

## Consequences

`docs/*.md` keeps holding measurement reports — `gate-baseline.md`, `first-run.md` — and ADRs
hold decisions. A report says what happened; an ADR says what we will do about it.
