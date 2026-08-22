# The first paid run — what four blind lenses found, and in what

**Date:** 2026-08-22
**Command:** `rsquad review --head <commit> --repo ../ai-video-digest --path tools/ --confirm`
**Model:** `claude-opus-5`, adaptive thinking, effort `high` (`medium` for the tests lens).

Two commits of the source project were reviewed: `2a21282`, which adds the mechanical gate, and
`b404a93`, which adds its `--tete` replay flag.

| | `2a21282` | `b404a93` |
|---|---:|---:|
| Calls | 4 | 4 |
| Findings kept | 13 | 8 |
| **Dropped by the guards** | **0** | **0** |
| Lens failures | 0 | 0 |
| Billed | $0.7068 | $0.3660 |
| Cache | 4104 written, 4104 read | 4104 written, 4104 read |

The cache behaved as designed: one write and three reads per run, because the four lenses share
a byte-identical prefix and differ only after the breakpoint.

**Not one finding was dropped by the anchoring guard.** Twenty-one findings, every snippet found
verbatim within three lines of the line it claimed. That is worth stating precisely because it
is the opposite of what the guard was built to expect — it was built for the day that number is
not zero.

## The ground-truth case was found, and ranked first

`head-overwritten-before-use` is the best case in `evaluation/defects.yaml`: a variable resolved,
used, then silently reassigned before its remaining uses. The queue on `b404a93`:

> **1. `tools/portail_tests.py:272` — blocking · 4 lenses agree**
>
> *Inputs* — `--tete 4164d03` where 4164d03 is an ancestor of HEAD
> *Consequence* — the resolved `--tete` SHA is discarded and overwritten with HEAD before it is
> used, so the tool compares old code against today's tests

Position one, severity `blocking`, all four blind lenses independently. The account is exact,
including a downstream effect the ground-truth entry does not mention: tests touched at the
target commit but modified since are silently excluded from the retained set.

## The ground truth was wrong, and the run is what proved it

The same defect was labelled `introduced_in: 2a21282`, and the squad found nothing of the kind
there. It was right: at `2a21282` the `--tete` flag does not exist yet, so `tete = HEAD` is
simply correct. The defect is born in `b404a93`, which adds the flag around that line without
removing it.

`git log -S` reports when a **line** first appeared, not when a **defect** did. Taking one for
the other put a false label in the evaluation set — the kind of error that makes a ground truth
lie quietly, forever, in the direction of "the squad missed it".

## Five defects in the tool the squad grew out of

All five are real, all were verified by reading the code before being accepted, and four of them
had been inherited into RSquad's own gate by the extraction at `6984c72`.

| Defect | Lenses | Severity |
|---|---|---|
| Empty retained set disables the per-function filter entirely | **4 of 4** | significant |
| Exemption lost on parametrized tests (`test_x[1]` vs `test_x`) | **4 of 4** | significant |
| A missing runner report reads as "nothing found" | repro | blocking |
| Temp directory stranded when the worktree fails | 3 of 4 | minor |
| `git rev-parse` on a bad revision exits 128 **and echoes the argument** | 3 of 4 | significant |

The last one is the most instructive. A lens claimed that `git rev-parse nonsense` returns
non-empty stdout, so the guard `if not sha: raise` never fires. That was checked against git
before being believed — and it is exactly true. The same pattern was in this repository in two
places.

The first two were each reported by **all four lenses independently**, which is what
corroboration between blind reviewers is supposed to look like. Both are in the code the
surrounding docstring claims to have designed the problem out of.

### The fixes did not move the baseline, and that was checked

`rsquad gate --replay 20 --head 6ade3ff` after all five fixes returns exactly what it returned
before: 129 new test functions, 27 examined (21 %), 22 valid, 5 suspect, 41 no signal. Every one
of the five lives on a path none of those twenty commits takes — an empty retained set, a
parametrized exempt test, a runner that fails to start, a worktree that is refused, a mistyped
revision.

That is worth two sentences rather than a shrug. It means the defects were real but latent, so
nothing in `gate-baseline.md` needs revising; and it means the five would have surfaced only on
the day something went wrong, which is the day a gate is least able to afford being wrong.

## What this does not establish

**Nothing about a detection rate.** Two commits, one file each. The four self-found defects are
now in the evaluation set marked `self_found: true`, and any future rate has to be reported
twice — over all scorable cases, and over the ones the squad did not discover itself. Only the
second number means anything.

**Nothing about false positives.** Twenty-one findings were kept and none has been refuted yet,
because step [3] does not exist. The refuter is the half that makes finding expensive, and until
it is built the useful question — *how many of these survive an adversary?* — has no answer.

**Nothing about other stacks.** One repository, one language, one file per unit.

## Costs, measured

$1.07 for eight calls across two commits, one file each. No figure is projected from that: two
invented cost constants from the source project are in the evaluation set for exactly this
reason, and a per-review number needs a spread of real diffs, not two.
