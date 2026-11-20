# ADR-0009 — The skill is the product; the API transport is frozen

**Status:** accepted
**Date:** 2026-11-20
**Decides:** ADR-0005, which deferred the choice of a primary transport to a measurement.

## Context

ADR-0005 kept two transports and deferred the choice of a primary one to a measurement. That
measurement exists: on the 19 cases run on both transports they agree on 18
(`docs/transport-calibration-19.md`), and the detection set was scaled to 38 cases on the harness
alone, with nothing billed (`docs/step7d-forty-cases.md`).

The deployment constraints it recorded have hardened. At work there is a coding-agent subscription
with credits and no Anthropic key; a Gemini key is planned for CI. At home the binding constraint
is a subscription allowance, which the evaluation campaign exhausted more than once. Neither place
wants a squad whose primary path is a metered API call.

The survey of open-source review agents (`docs/state-of-the-art-review-agents.md`) adds two
things. Running on the host agent's model, with no key of its own, is now common, and one project
draws exactly this line: a CLI that selects files and resolves rules with no model on its side,
and a skill that has the host agent do the review. The survey also records the case against going
further: a reviewer that is only a skill and a prompt is reported to skip files on large changes,
to drift off its line numbers, and to change quality with the wording of its prompt.

## Decision

**The primary transport is the job on disk (ADR-0008), run by the host agent, and a portable skill
is its front door.**

- **The CLI keeps everything that must not depend on a model**: unit selection, the account of
  what was excluded and why, prompt rendering, schema validation, anchoring,
  reproduction-or-nothing, missing-task accounting and ranking. Nothing on that side calls a model
  by default. **Coverage is counted by the CLI, never reported by the agent.**
- **The skill is the product.** It drives `export`, runs the tasks (as isolated subagents where
  the host allows it), and calls `ingest` twice. The Claude Code workflow stays, as the batch
  driver for evaluation.
- **The API transport is frozen.** `rsquad review --confirm`, `rsquad evaluate --confirm` and the
  budget accounting keep working and stay tested, take no new features, and move behind an
  optional dependency (`rsquad[api]`). It is kept rather than deleted because it is the only path
  where the schema is enforced at generation time and the only one with an itemised cost, and
  calibration between transports needs both.
- **A CI runner against a Gemini key is a driver, not a transport.** It is written against
  `docs/writing-a-harness-driver.md` when the key exists, and lives outside the core.

## Consequences

**What follows, in order.** Each step is small, and each is decided by what the one before found.

0. **Cursor's capabilities, answered from its documentation on 2026-11-20** (pages referring to
   Cursor 2.4 and 2.5): it loads Agent Skills, including from `.claude/skills/`, so one skill
   directory serves both hosts; subagents start with a clean context, run in parallel, can be
   marked `readonly`, and a custom subagent names its own `model`; a headless `agent -p` takes
   `--model` and `--output-format json`, one process per task. So the lenses and the refuter can
   be independent, read-only subagents on a chosen model. Two caveats from the same pages:
   subagents share the parent's checkout unless a worktree is requested (ADR-0010 applies), and
   an admin can disable headless mode. **This was read, not run**: the skill's first use in
   Cursor is the check.
1. **Five changes to the core**, none of which needs a model to test:
   - every changed file is either reviewed or **excluded with a reason** (deleted, binary,
     documentation, lockfile, generated), and a run with nothing left stops before any model is
     called. Today deleted files and binaries are dropped without a word;
   - **lenses are routed by file kind**: `tests` reads test files only, the other blind lenses read
     everything else. `docs/step7e-tests-lens.md`: the lens speaks when it is shown a test, and in
     the whole Java campaign it never was;
   - **the context pack is off by default**, the mechanism kept behind an option.
     `docs/step7b-context-pack.md`: 14/19 with and without it, the same fourteen cases, for 30 %
     more payload;
   - the refuter gains a seventh closed verdict, **`undecided`**: the payload does not settle the
     claim. Doubt still refutes, as ADR-0006 requires. What changes is that a finding killed by
     doubt is recorded as such, instead of under one of six causes that may not hold;
   - **the manifest carries a model tier per task**, which the driver reads.
2. **The skill.**
3. **Measurement on the frozen 38 cases**: the lenses on a smaller model with the refuter on the
   largest, against 31/38. Then acceptance on a subset, with a judge calibrated against a person,
   using ReviewBench's definition of a true positive.
4. **At work, on real pull requests**: what was fixed after the review. It is the only direct
   measure of acceptance this project can get.

**Not now, each with what would justify it:**

| | would be justified by |
|---|---|
| a multi-model panel | a measurement showing one reviewer misses what a panel finds |
| a frequency-times-impact rating | evidence that it agrees with people better than a severity word |
| a project-rules lens | a project with written rules worth enforcing |
| the Java gate adapter | Java at work |
| a code graph | the context pack first showing any effect |
| post-landing loops | a deployment to watch |

**What the primary path gives up**, all of it named in ADR-0005 and measured since: schema
enforcement moves from generation to ingest (the guards refused nothing in the Java campaign until
the tests-lens arm's three); prompt caching belongs to the host; cost is no longer itemised per
run. Blindness is the fourth loss, and it has its own decision: ADR-0010.

**`anthropic` stops being a required dependency.** The three modules that import it (`lenses`,
`refutation`, `conformance`) import it only when the API path actually runs.

**2026-11-20** — steps 1 and 2 written. Step 1 is five changes to the core, each tested without a
model. Step 2 is `.claude/skills/rsquad-review/SKILL.md`: subagents are read-only, so the driver,
not the subagent, writes each reply to disk, verbatim. The skill has not yet run in either host;
its first run is also the check on step 0.

**2026-11-20** — step 3, first half: Sonnet lenses with an Opus refuter detect 30/38 against 31/38,
above the 29 frozen beforehand, so they become the default of `rsquad export`
(`docs/step8-tiered-models.md`). One case was lost by the lenses, one by the refuter, one gained.
The calibrated acceptance judge, step 3's second half, has not been built.
