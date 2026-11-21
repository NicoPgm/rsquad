# Step 4, step 0 — Cursor check, run rather than read

**Date:** 2026-11-21
**Host:** Cursor (desktop agent chat), Windows
**Skill:** `.claude/skills/rsquad-review/` copied into a work repository under `.claude/`
**Subagent:** `.claude/agents/rsquad-task.md` (declared `tools: Read` only)
**Subject:** one already-merged commit in a Java work repository (two source files under review;
one third file in the same commit was excluded - see below). No work path, snippet, or finding
text appears in this note.

ADR-0009 step 0 had been answered from Cursor's documentation. This run is the check the
documentation asked for. The five answers belong here as plain facts; the queue and the log stay
at work (`docs/step4-at-work.md` §6).

## The five checks

| # | check | result |
|---|---|---|
| 1 | agent follows the skill: range, task count, then **waits** | **pass** - skill loaded from `.claude/skills/`; export reported the task count; work started only after an explicit go-ahead |
| 2 | each task in **its own subagent** | **pass** - eleven separate `rsquad-task` subagents (six lens/conformance tasks, then five refuters); nothing reviewed in the parent conversation |
| 3 | subagents **read-only** | **pass** - host used the `rsquad-task` custom agent from `.claude/agents/` |
| 4 | **which model** ran | **recorded** - see table below. Cursor accepted a per-subagent model slug; the ids are the host's tiers, not the literal `manifest.model` strings |
| 5 | `ingest` **0 missing, 0 malformed** | **pass** - round 1 and round 2 both reported 0 missing and 0 malformed |

## Models

| role | `manifest` id (intended) | what Cursor actually ran |
|---|---|---|
| lenses / conformance | `claude-sonnet-5` | `claude-sonnet-5-5-high` |
| refuter | `claude-opus-5` | `claude-opus-5-5-medium` |

A review on these tiers is still a review. It does not reproduce the published step-8 figures
(`docs/step8-tiered-models.md`), which were measured under the API ids above.

## Pipeline counts (no finding text)

- Round 1: 6 finding(s) ingested, 0 dropped by the guards, 0 missing, 0 malformed
- Round 2: 5 refutation task(s); 1 finding carried with no refuter (conformance shape)
- After refutation: **5 survived, 1 refuted** (`undecided`)
- Dollar cost: **$0 billed** on the harness path (Cursor subscription)

## Export hitch (product fact, not work code)

`rsquad export` of the full commit failed with `unrendered placeholder in prompt: {{HEAD}}`.
One changed file in that commit embeds Mustache-like tokens (`{{HEAD}}`, `{{BASELINE}}`) in its
own content. Prompt rendering treats leftover `{{NAME}}` forms as template errors, so **any
reviewed file that contains those tokens cannot be exported today**.

Workaround used for the check: `--path` restricted to the two files without those tokens. The
third file was therefore not reviewed. This is a seam bug in RSquad (content colliding with the
template alphabet), not a Cursor or skill failure. No change was made to the core in this
session; the observation is recorded so a later fix has a measured case.

## What this does and does not settle

**Settled:** Cursor can drive the skill end to end - isolated read-only subagents, schema-valid
replies, both ingest rounds clean. ADR-0009 step 0 is no longer documentation-only.

**Done next:** the acceptance log on real pull requests reached the 50-finding stop; counts only
are in [`step4-acceptance-counts.md`](step4-acceptance-counts.md) (2026-11-21).
