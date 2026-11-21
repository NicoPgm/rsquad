# Step 4 — Acceptance counts from work (no finding text)

**Date:** 2026-11-21
**Host:** Cursor (desktop agent chat), Windows; harness path (`rsquad export` / `ingest`)
**Skill / subagent:** `.claude/skills/rsquad-review/` and `.claude/agents/rsquad-task.md` in the
work clone (local exclude; not in the work repository's history)
**Subject:** already-merged pull requests in one Java / PowerShell work repository. Counts only -
no work path, file name, snippet, or finding text (`docs/step4-at-work.md` §6).
**Step-0 check:** [`step4-step0-cursor.md`](step4-step0-cursor.md) (included in these counts)

Stopping rule (`docs/step4-at-work.md` §5): record words until **50** survived findings, then look.
The work log stopped at the first look after that threshold.

## Models

| role | `manifest` id (intended) | what Cursor actually ran |
|---|---|---|
| lenses / conformance | `claude-sonnet-5` | `claude-sonnet-5-5-high` |
| refuter | `claude-opus-5` | `claude-opus-5-5-medium` |

Dollar cost on the harness path: **$0 billed** (Cursor subscription). Same tier pairing as the
step-0 check; not a reproduction of the API ids in `docs/step8-tiered-models.md`.

## How the denominator is built

Each survived finding carries an author word (`act` / `note` / `wrong` / `unsure`) decided when
the queue was read. Lens agreement multi-counts: a place seen by three lenses contributes three
to the squad total, each with the same word. The table below expands the work log's `seen by`
column that way.

One review's queue header claimed one more multi-count than its `seen by` tags (6 vs 5). That
orphan is **excluded** here, so the attributable total is **58**, not the log's running **59**.

## Squad-wide acceptance

| word | n | share |
|---|---:|---:|
| `act` | **41** | **71 %** |
| `note` | 17 | 29 % |
| `wrong` | 0 | 0 % |
| `unsure` | 0 | 0 % |
| **total** | **58** | 100 % |

At n ≈ 50, §5 gives about ±13 points on the squad share. **71 % sits clearly above** the ~30 %
line in `evaluation/acceptance/README.md` for keeping a lens. Unique places (one word per place,
ignoring multi-lens): 23 `act` / 37 = 62 % - same side of the line.

## Per lens (indicative only)

| lens | `act` | `note` | `wrong` | `unsure` | n | `act` share |
|---|---:|---:|---:|---:|---:|---:|
| `contract` | 12 | 2 | 0 | 0 | 14 | 86 % |
| `bounds` | 11 | 3 | 0 | 0 | 14 | 79 % |
| `repro` | 11 | 3 | 0 | 0 | 14 | 79 % |
| `tests` | 5 | 6 | 0 | 0 | 11 | 45 % |
| `conformance` | 2 | 3 | 0 | 0 | 5 | 40 % |

No lens is near the ~50 findings §5 wants for a per-lens verdict. None of these five rates is a
retirement decision; the squad-wide number is.

## Fixed before merge

Every attributed finding was logged `yes (merged)`. Reviews were after the fact on already-merged
pull requests, so this column does **not** measure a pre-merge fix gap for `act` items in this
campaign.

## Campaign shape (counts only)

| | n |
|---|---:|
| review blocks in the work log | 23 |
| of which empty queue (0 survived) | 8 |
| of which with at least one survived finding | 15 |
| survived findings (attributable) | 58 |
| ingest missing / malformed (reported per review) | 0 / 0 throughout |

Colleague misses on files RSquad reviewed: **not recorded** in this campaign.

## What this settles

**Settled:** on this author's Soft GA work, after the pre-registered 50-finding stop, squad-wide
acceptance is about **seven in ten** `act`, with no `wrong` or `unsure` in the sample. Step 4's
direct acceptance measure is no longer empty.

**Not settled:** per-lens retirement; pre-merge fix rate; whether another author or repository
would land the same share; the calibrated acceptance judge (ADR-0009 step 3, second half).
