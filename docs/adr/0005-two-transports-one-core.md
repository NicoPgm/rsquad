# ADR-0005 — Two transports, one core

**Status:** proposed — the choice of a primary transport is deferred to a measurement
**Date:** 2026-08-22

## Context

The squad exists as a standalone Python program calling the Claude API. A second shape is
possible: the same lenses as agents hosted by a coding harness (Claude Code workflow, Cursor),
which gives them file-reading tools and needs no API key.

The technical case for the standalone version is in ADR-0002 and ADR-0004: blindness stays
enforceable, runs stay reproducible and therefore measurable, and the thing runs unattended.

**That case was made without knowing the deployment constraints, and they change the weighting.**
As stated by the person who will deploy it:

- Two places, not one. **Locally after commit and before push** — interactive, in Cursor. And
  **in CI, on other people's pushes** — unattended.
- At work, a subscription budget is high enough to be treated as unlimited. **An API key
  requires a chain of approvals**, worse for CI than for a laptop.
- Personally, the harness cost — real, if not itemised — is well below the API cost.

So one of the standalone version's advantages inverts. *Cost is measurable per run* is a
technical virtue and an organisational obstacle: an architecture that cannot be deployed because
procurement has not answered is not deployed. Meanwhile the harness version's untraceable cost,
which reads as a weakness for budgeting, is exactly what makes it approvable.

## Decision

**Both transports, one core.** The lens definitions, the finding schema, the two mechanical
guards and the ranking are shared; only the transport differs.

Concretely: a harness-hosted version reads the same `prompts/lenses/*.v1.md`, requests the same
`api_schema()`, and pipes its output through the same `anchoring.sift` and `ranking.group`. **The
lens definitions are never duplicated.** That is the whole condition under which maintaining two
transports is cheap rather than a slow divergence into two squads, neither measurable.

The standalone version stays the **reference implementation and the measurement instrument**:
it is the one that can be replayed against `evaluation/defects.yaml`, so it is the one that
produces numbers anybody should believe.

Which transport becomes primary in daily use is **not decided here**, and will not be decided by
argument. The comparison to run: both transports, same commits, same prompts, same model, and
each run **twice**. What it has to report:

- findings dropped by the anchoring guard — more context is more to conflate
- overlap, and what each finds that the other misses
- **self-variance**: if the harness version disagrees with itself more than it disagrees with
  the standalone one, reproducibility is settled by measurement rather than by ADR-0002's
  reasoning. The sibling project has seen this before — replaying one card moved its cluster
  count from 13 to 14 and back to 13.

## Consequences

**The shared core is now load-bearing.** Anything transport-specific that creeps into
`findings`, `anchoring` or `ranking` costs twice and drifts.

**A Claude Code workflow does not run in Cursor.** "Adapted to Cursor" means a third
implementation against a third harness — which raises the price of every duplication and makes
the shared-core rule harder, not softer.

**The standalone version already covers the local pre-push case**, from a terminal, with no
harness at all. What a harness version adds there is exactly two things: file-reading tools, and
no key to manage. ADR-0004 buys back part of the first without giving up reproducibility; the
second is not a technical argument but it is a real one.

Nothing here is measured yet. This ADR records a constraint and a plan, not a result, and should
be superseded by one.

## Measured since, and it adds a use the plan did not have

**2026-08-23** — eight runs on one commit: both transports stable on places, the reproducibility
argument above loses its support, and the choice becomes operational
(`docs/transport-comparison.md`).

**2026-08-24** — the transports now also carry a *division of labour*, which this ADR did not
anticipate. Measuring costs money on one path and tokens on the other, and the two measurements
want opposite things:

- **noise wants volume and no human verdict** — the clean-commit corpus is a count, so it belongs
  on the harness. 3.28 million tokens, nothing billed (`docs/step7c-clean-corpus.md`).
- **detection wants a human verdict per case** and does not scale by paying more, so the API
  budget is better spent there.

`rsquad evaluate --jobs <dir> --export/--ingest` exists so the same selection, scoring rule and
report run on either path.

**But a number does not transfer between them.** On four identical cases the harness scored 3/4
against the API's 4/4 and returned 6 findings against 10 — the opposite direction from the one
earlier divergence, where it found more. So the deferred API budget should buy **calibration**,
not more cases: cases are free on the harness, and only the bridge costs
(`docs/transport-calibration.md`).
