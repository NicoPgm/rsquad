# ReviewBench pilot — five pull requests, a baseline and two arms

**Date:** 2026-11-22
**Bench:** [ReviewBench](https://github.com/review-bench/ReviewBench) (GitHub, MIT), test set,
commit `082f65f`. Judge: the bench's own `npm run judge`, Anthropic provider, `claude-sonnet-5`,
the model the leaderboard is judged with.
**Adapter:** `evaluation/reviewbench.py` (`58f8b06`): a finished job, one entry per place.
**Not pre-registered.** This is a pilot, chosen to price a campaign and to look; no decision rule
was frozen, and none is drawn.

## In one paragraph

On the five smallest test-set pull requests, RSquad as shipped made **15 findings, all judged
true**, and covered **11 of the 44 true golden findings (25 %)**. The public leaderboard ranks
reviewers by grounded F1 on high-severity issues; its rows sit at 91–99 % precision and **20–76 %
recall on those issues** (read 2026-11-22). Precision is not where reviewers differ, recall is.
On high-severity golden findings RSquad covered 2 of 6 here, and 5 of 12 on the ten pull requests
of arm C (28–42 %): near the bottom of the leaderboard (see the correction at the end; a first
version of this paragraph compared recall over all severities with the leaderboard's). Two changes were then measured on the same five pull requests, one at a time: letting
every reader see the repository (A), and relaxing the lenses' proof-or-silence rule (B). **Neither
moved grounded recall by more than two golden findings out of 44**, which five pull requests
cannot tell from noise.

## Setup

- **Selection:** the five test-set pull requests with the fewest changed files, by the bench's own
  `files_changed`. One of them (TechDebtMCP #135) is listed at 2 files and its three-dot diff has
  10; it was kept, since the diff is what the judge sees.
- **Checkout:** base and head fetched from the `review-bench` mirror, as `scripts/try-agent.sh`
  does. Base equals the merge base in all five, so `base..head` is the bench's three-dot diff.
- **Intent:** the pull request's title and body, passed as `--spec`, since the bench gives them
  to every agent.
- **Run:** harness path, Claude Code workflow driver, Sonnet lenses and Opus refuter (the step-8
  defaults). Jobs outside any checkout; readers had the file-reading tool only, no network. The
  golden findings were downloaded **after** the baseline review, and no job directory held them.
- **Units:** 14 code files reviewed, 3 documentation files excluded, 46 lens and conformance
  tasks per arm.

| pull request | language | files reviewed | golden true findings |
|---|---|---:|---:|
| AA-Factory/aafactory-prototype #17 | Python | 1 | 9 |
| PierreJanineh/TechDebtMCP #135 | TypeScript | 7 | 9 |
| k1LoW/gh-copilot-review #9 | Go | 2 | 7 |
| konturio/disaster-ninja-fe #1230 | TypeScript | 2 | 13 |
| renedierking/LANdalf #88 | C# | 2 | 6 |

## Results

Micro figures (summed over the five pull requests). *Grounded* counts only the golden set;
*augmented* also credits findings the judge classifies as true that the golden set lacks.

| | entries | golden true covered | of 6 high | grounded P | grounded R | augmented R |
|---|---:|---:|---:|---:|---:|---:|
| **baseline** | 15 | 11 / 44 | 2 | 100 % | 25.0 % | 31.3 % |
| A, repository access — before refutation | 18 | 13 | 3 | 92.3 % | 29.5 % | 35.4 % |
| A — after refutation | 16 | 11 | 3 | 91.7 % | 25.0 % | 29.8 % |
| B, relaxed proof — before refutation | 31 | 15 | 2 | 86.7 % | 34.1 % | 50.0 % |
| B — after refutation | 23 | 13 | 2 | 92.3 % | 29.5 % | 42.6 % |

The baseline's refuter removed two findings, both sharing a place with a survivor, so its entries
are the same before and after refutation.

### Where the baseline missed

Of the 33 golden findings it missed, 5 are outside RSquad's scope by design (documentation,
maintainability, API architecture). The other 28 are correctness, reliability, security and
testing defects in code the pull request introduced. The bench labels the context each needs:
**34 of the 44 need files beyond the diff**, and the baseline found 9 of those.

The four missed high-severity findings, by what the reader would have needed:

| golden finding | what RSquad was shown |
|---|---|
| test fixtures from two packages the project does not declare | the test file only; the declaration is in `pyproject.toml` |
| a freshness check that runs after a call hiding the review it checks | `root.go` only; what the call does is in `github.go` |
| a library API called in a form it does not accept | the renderer only; the right form is in the library and another file |
| a user path reaching file reads unvalidated | **the lines were in the file shown**; four lenses said nothing |

### Arm A — every reader may read the repository at head

The head checkout sat in `repo/` inside each job; the lens, conformance and refutation prompts
said so, and the driver allowed it. Findings still had to be anchored in the file under review.

It found **two of the four missed high-severity findings**, both cross-file (the freshness order
and the library call), and lost a third high one the baseline had. It added two false positives.
Net, after refutation: the same 11 golden findings as the baseline, at 92 % precision. The
undeclared dependency and the unvalidated path stayed missed.

### Arm B — the lenses may report what they cannot reduce to exact inputs

The blind lenses' system prompt lost "if you cannot name the inputs, say nothing" and "an empty
result is a normal, frequent, and correct answer", and gained "report every defect you find",
including a pre-existing one the change touches. The refuter was unchanged, so doubt still kills.

It doubled the findings. Most of what it added is **true and absent from the golden set** (14
before refutation, 10 after), which raises augmented recall to 43–50 % and leaves grounded recall
two findings above the baseline. The leaderboard ranks on grounded scores. The refuter removed 8
entries, 2 of them golden. No high-severity finding was gained. Two lens replies were malformed
(invalid `\'` escapes in JSON); as the skill requires, they were not repaired and count as failed
tasks.

## What this does not establish

- **Five pull requests, the smallest of 25.** ±2 golden findings is inside what a re-run could
  move; arms A and B are not shown to differ from the baseline, in either direction.
- **Not a leaderboard comparison.** The leaderboard scores 219 pull requests three times, and the
  page read did not say whether its figures are macro or micro. The 20–76 % range locates the
  baseline; it does not rank it.
- **The arms were written after reading the baseline's misses.** Arm A's prompt names
  dependencies and written conventions because two misses needed them. Arm B's second example
  ("when the cancellation token fires during the ping…") paraphrases a golden finding of
  LANdalf #88 read while analysing the baseline. The baseline had already found that one, and
  arm B covered nothing more on LANdalf, so it bought nothing; it is still a leak, and a re-run
  should use an example from outside the set.
- **One untested explanation.** Each lens reviews one file and anchors its findings there, even
  with the repository in reach. The reviewers at the top of the leaderboard are, as far as their
  descriptions say, shown the whole pull request at once. Testing that means units spanning
  files, a change to the core rather than to a prompt.

## Cost

| | 5-hour window | weekly | judge |
|---|---:|---:|---|
| baseline, both rounds | 10 points | 2 points | 1 run |
| arms A and B, both rounds | 25 points | 3 points | 4 runs |

Subagent tokens: about 5 M for the baseline, 5.3 M for A, 6.7 M for B. The judge reports no usage
of its own; its calls were billed to the API key and are not itemised here.

Two setup facts, for whoever repeats this. The judge needs Node ≥ 22.19 (its bundled `undici`
fails on 20.17). And the `models.json` given in the bench's `docs/OFFLINE_EVAL.md` declares
`claude-sonnet-5` without `"compat": {"forceAdaptiveThinking": true}`, so the judge sends
budget-based thinking, the model refuses it, and the matcher reports "invalid JSON response".

## Arm C, pre-registered — whole-pull-request units: not adopted

**Pre-registration:** `evaluation/reviewbench-c.yaml` (`b4360b1`), with the arm as
`evaluation/reviewbench-c.diff`, committed before any arm-C or new baseline task ran and before
the golden findings of the five new pull requests were downloaded.

Each blind lens got one task over every file it reads, and the refuter got the claim with every
file of the same kind; conformance stayed per file. The set grew to ten: the pilot's five (S1,
whose golden findings had been read) and the next five by size (S2, unseen: superyyrrzz/ForgeMap
#106, NCATSTranslator/translator-ingests #336, Marvell-Consulting/statswales-frontend #626,
ardevd/jadx-collaboration #3, allan-mobley-jr/gimmes #468). The baseline on S1 is the pilot's run;
on S2 it was run from `b4360b1`. Everything was judged again together, after refutation.

| | entries | golden true covered (of 96) | S1 (of 44) | S2 (of 52) | high (of 12) | grounded P | grounded R |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 29 | **20** | 11 | 9 | 5 | 100 % | 20.8 % |
| arm C | 24 | **19** | 11 | 8 | 4 | 94.7 % | 19.8 % |

The rule, as frozen:

| condition | required | measured | |
|---|---|---|---|
| covered(C) ≥ covered(baseline) + 6 | ≥ 26 | 19 | **fails** |
| covered(C, S2) ≥ covered(baseline, S2) | ≥ 9 | 8 | **fails** |
| grounded precision(C) ≥ 90 % | ≥ 90 % | 94.7 % | holds |

**Per-file units stay.** Seeing the whole pull request did not make the lenses find more: they
made fewer findings (48 kept in round 1, against 50 for the baseline on the same ten), and the
same golden findings, give or take one. On S2, the unseen half, the baseline's recall is 17 %
(9 of 52), lower than on S1; the pilot's 25 % was not flattering it by chance.

Two lens replies of the baseline and one of arm C were malformed, all on jadx-collaboration #3;
none was repaired. One S2 pull request (statswales-frontend #626) drew no finding from either arm
against six golden ones.

Cost of the pre-registered run: 32 points of the 5-hour window (39 % → 71 %) and 4 weekly points;
subagent tokens 6.2 M for the new baseline, 9.3 M for arm C; two judge runs on the API key.

**What this leaves.** Three explanations of the recall gap have now been measured, and none moved
it: repository access, a relaxed proof rule, whole-pull-request units. As the pre-registration
says, the bench work stops here unless a new explanation is named. The one finding that holds
across all of it is that RSquad, as built, is a high-precision, low-recall reviewer: 100 % then
94.7 % grounded precision, about 20 % recall over all severities, and 28–42 % on high-severity
issues, where the leaderboard's high-severity recall runs 20–76 %.

## Correction — comparing like with like

The leaderboard ranks on high-severity issues only. The first version of this report set RSquad's
recall over all severities (20–25 %) against the leaderboard's high-severity recall (20–76 %). The
like-for-like figures, from the same judge runs:

| run | pull requests | high-severity golden covered | micro recall | macro recall | high candidates | high precision |
|---|---:|---:|---:|---:|---:|---:|
| pilot baseline | 5 | 2 / 6 | 33 % | 17 % | 2 | 100 % |
| A, after refutation | 5 | 3 / 6 | 50 % | 58 % | 3 | 100 % |
| B, after refutation | 5 | 2 / 6 | 33 % | 17 % | 4 | 100 % |
| baseline | 10 | 5 / 12 | 42 % | 28 % | 6 | 100 % |
| arm C | 10 | 4 / 12 | 33 % | 22 % | 5 | 100 % |

Macro recall averages over the pull requests that have a high-severity golden finding, so it can
sit above micro (arm A). The leaderboard does not say which of the two it shows. Either way the
ten-PR baseline, at 28–42 %, would sit 23rd of 25 rows: above Cubic (22.1 %) and Greptile
(20.2 %), below diffox (43.7 %) and Cursor (44.5 %). Twelve golden findings cannot place it more
finely, and the leaderboard scores 219 pull requests three times; the placement is indicative.
The conclusion stands, and the figures name its shape: on ten pull requests RSquad put forward
**6 high-severity candidates for 12 high-severity golden findings**, every one of them true. It
is not saying wrong things; it is saying too few.

## Annex — the two arms, as diffs against `58f8b06`

**A**, `prompts/user.v1.md` (the same paragraph, with the evidence sentence adapted, was added to
`conformance-user.v1.md` and `refutation-user.v1.md`):

```diff
+## The rest of the repository
+
+The whole repository, as it stands after this change, is checked out in the `repo/` directory of this job: the directory that holds `round-1/` and `schema/`. You may read any file there to see how the code under review is called, what it calls, what the project declares (dependencies, configuration, its own written conventions), and what the changed code relies on. Read what you need, not everything. A defect may depend on another file, but it must still be reported at a line of `{{FILE}}`, with a snippet copied from the numbered file above.
+
 {{CONTEXT}}{{ELISION}}Report findings in `{{FILE}}` only. If there is nothing to report, return an empty list.
```

and the driver, `harness/claude-code.workflow.js`:

```diff
-  `Read no other file. Everything you need is in those two, and reaching for the ` +
-  `repository would answer a different question than the one the task asks.\n\n` +
+  `Read no other file, except what the task file itself allows: it may point you to a ` +
+  `checkout of the repository, which you may read as it says.\n\n` +
```

**B**, `prompts/system.v1.md`:

```diff
-A finding is a defect you can trigger. It has concrete inputs and an observable consequence.
+A finding is a defect you have good reason to believe is real: code that, under some
+condition, gives a wrong result, fails, leaks, or exposes what it should not.
+- Ships: "when the cancellation token fires during the ping, the generic catch swallows it
+  and the caller proceeds as if the host were down"
-If you cannot name the inputs that trigger it, you do not have a finding. Say nothing.
+Name the condition that triggers it as precisely as you can: exact values when you have
+them, otherwise the situation in which it happens. A defect you can describe but not reduce
+to exact values is still a finding.
-**An empty result is a normal, frequent, and correct answer.** Most diffs contain no defect.
-You are not scored on volume, and a padded list makes the whole squad ignorable. Reporting
-nothing when there is nothing is the single most useful thing you can do.
+**Report every defect you find, not only the one you are surest of.** That includes a defect
+that was already there, if the change touches it or makes it easier to reach. An empty
+result is right when you found nothing, and only then.
```

and `prompts/lenses/repro.v1.md`:

```diff
-Report only what you can trigger. For each finding, state the inputs you walked with.
+For each finding, state the inputs or the situation you walked with.
```
