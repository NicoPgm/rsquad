# ADR-0011 — The lenses investigate the whole change, on Opus, and doubt no longer refutes

**Status:** accepted
**Date:** 2026-11-23
**Amends:** ADR-0004 (one file per unit), ADR-0006 (doubt refutes), ADR-0010 (what a harness
agent is given), and the step 8 lens tier (`docs/step8-tiered-models.md`). On the harness
transport only; the API transport stays frozen (ADR-0009), and inherits the shared prompts.

## Context

On ReviewBench, RSquad as shipped covered a fifth to a quarter of the golden findings, and its
high-severity recall would have sat 23rd of 25 rows (`docs/reviewbench-pilot.md`). The reviewers
at the top publish a common recipe: investigate the whole change with the repository in reach,
report every defect rather than the surest one, and let a verifier drop a claim only on evidence.

Arm D applied that recipe and covered 34 golden findings on ten pull requests, against 20. It
failed the pre-registered 90 % grounded-precision guard (86.5 %), and was not adopted. Taken apart
on five pull requests nobody here had read, the gain held: 21 golden findings against 6. No
variant passed the 90 % guard there, master included (85.7 %), so the rule adopted none.

The cheapest variant close to D's gain was **V4: the recipe on a single Opus pass**: 19 golden
findings against 6, with 88.6 % augmented precision, so about one entry in ten for the reader to
discard. Neither ingredient works alone: the recipe on Sonnet found 10, Opus with master's rules
found 9. A second pass on the other model added 2.

## Decision

**V4 becomes the default on the harness transport.** This is the user's decision, taken outside
the bench rule: the 90 % guard was not met, and the precision a reader will accept is measured at
work, by the person who reads the queue (step 4 of ADR-0009).

- **A lens reads the whole change in one task.** `<lens>--PR`, one task per lens over every file
  that lens reads, so a defect spanning files is visible. Routing by file kind is kept. Each
  finding is still anchored in the file it names. ADR-0004's one-file unit stays the unit of
  anchoring, conformance and refutation.
- **Every reader may search the repository.** `export` writes the tree at head into the job's
  `repo/`, from `git archive`: no history, no commit message, nothing uncommitted. The task
  agent gains search tools (`Read, Grep, Glob`), still read-only. A specification checked into
  the repository is now within a blind lens's reach, so blindness to the intent is by
  instruction only; ADR-0010 already said so of the agent, and this says it of the payload's
  surroundings too. The payload itself still carries no intent.
- **The lenses report every defect they have good reason to believe**, not only those they can
  reduce to exact inputs. The schema is unchanged: `inputs` and `consequence` stay required, and
  a condition described precisely fills `inputs`.
- **The refuter drops a claim only on evidence.** `undecided` lets the finding through, and the
  queue marks it. This reverses ADR-0006's "doubt means refuted"; the rest of ADR-0006, a refuter
  that inherits no framing and a broken refutation that refutes nothing, stands.
- **The lenses run on Opus by default.** The refuter already did.

## Consequences

- **More noise reaches the reader, knowingly.** Grounded precision was 79.2 % for V4 on the five
  unseen pull requests (85.7 % for master there) and 86.5 % for D on the ten (100 % for master).
  Every false positive D matched was low or medium severity; on high-severity issues it was at
  100 %. Whether a reader at work accepts that is the second campaign's question.
- **The cost per review rises.** Opus lenses that investigate a repository use more tokens than
  Sonnet lenses reading one file; arm D cost about 7.6 points of a 5-hour window per pull request
  with conformance and refutation. The second campaign measures it on real pull requests.
- **A large change makes a large task.** Every file a lens reads is in one prompt. No bound is
  set until a real change hits one.
- **Two shared prompts mention `repo/` on the API transport**, where there is none (conformance
  and refutation). The API transport is frozen and untouched otherwise; the sentence is wrong
  there, not harmful.
- **What reverts it:** the second campaign showing that readers at work discard enough of the
  queue to stop reading it. The commit that introduces this ADR is the one to revert.
