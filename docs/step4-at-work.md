# Step 4 — RSquad at work, on real pull requests

ADR-0009's fourth step: run the skill on your own changes, and record what you did with each
finding. It is the only direct measure of acceptance this project can get — a person deciding,
on their own code, whether a finding was worth acting on.

This page is written to be read by you and by the agent in your editor. It assumes Cursor with
its own model access, no Anthropic key, and nothing installed beyond Python.

## 1. Install (once)

```bash
git clone https://github.com/NicoPgm/rsquad
pip install -e ./rsquad          # Python 3.11.4+; no extra needed, the harness path calls no API
python -m rsquad --help          # must work before anything else
```

In the repository you want reviewed, copy two things from the rsquad checkout:

```
rsquad/.claude/skills/rsquad-review/   ->  <work repo>/.claude/skills/rsquad-review/
rsquad/.claude/agents/rsquad-task.md   ->  <work repo>/.claude/agents/rsquad-task.md
```

Unless your team agrees to share them, keep them out of the work repository's history by adding
both paths to `<work repo>/.git/info/exclude`. That file is local to your clone and not
versioned.

## 2. The first run is a check, not a review

ADR-0009 step 0 was first answered from Cursor's documentation. It has since been **run**: the
five answers are in [`step4-step0-cursor.md`](step4-step0-cursor.md) (2026-11-21). To repeat the
check elsewhere, pick a small change that is already merged (one or two code files), ask the
agent for *"an RSquad review of commit `<sha>`"*, and watch for five things:

| # | check | if it fails |
|---|---|---|
| 1 | the agent follows the skill: states the range and the task count, then **waits** | the skill was not loaded from `.claude/skills/`; look for where Cursor expects skills and copy it there |
| 2 | each task runs in **its own subagent**, not in the main conversation | the lenses are no longer independent; note it, and read the queue as one agent's opinion |
| 3 | subagents are **read-only** (the `rsquad-task` agent, or Cursor's equivalent) | `.claude/agents/` was not read; define the same agent where Cursor keeps custom subagents: one tool, read files, and the same instructions |
| 4 | **which model ran** each task | if Cursor cannot choose per subagent, write down what ran. A review on another model is still a review; it does not reproduce `docs/step8-tiered-models.md` |
| 5 | `ingest` reports **0 missing, 0 malformed** | a subagent wrapped its JSON in prose or a fence; the skill forbids it, so tighten nothing in RSquad and note how often it happens |

Write the five answers down. They are the step-0 result, and they belong in this repository as
plain facts (no work code) once you have them.

## 3. Use it on your own pull requests

Run it on your changes **before** asking a colleague for review: that is where you, the author,
decide what to do with each finding, which is the thing being measured. Commit first — RSquad
reviews commits, not the working tree.

Defaults since step 8: lenses on Sonnet, refuter on Opus. Each task costs a subagent; with the
general-purpose agent that was about 42 k tokens per task, most of it fixed overhead, and
`rsquad-task` exists to cut that. A two-file change is roughly 8 lens tasks plus one refutation
per finding.

## 4. Record what you did — one line per finding

Keep this log **at work, outside both repositories** (your home directory is fine). One block per
review:

```markdown
## <date> · PR <id> · <n> files · model: <what actually ran>

| # | file:line | seen by | word | fixed before merge |
|---|---|---|---|---|
| 1 | Foo.java:42 | repro, bounds | act | yes |
| 2 | Bar.java:17 | contract | note | no |
```

`seen by` is copied from the queue (the line under each entry's title). Without it, acceptance
can only be counted for the squad as a whole, and the 30 % line below is per lens.

The word is the acceptance worksheet's vocabulary (`evaluation/acceptance/worksheet.md`), decided
when you read the queue, before fixing anything:

| word | means |
|---|---|
| `act` | I would change this code, or file it. |
| `note` | True, and I would not act on it — too minor, out of scope, a known trade-off. |
| `wrong` | The claim is false, or the consequence does not follow from the inputs. |
| `unsure` | I cannot tell without more work than this finding deserves. |

`fixed before merge` is filled in when the PR merges. A finding marked `act` and not fixed is
still `act`; the gap between the two columns is worth seeing.

Also note, per review, anything a colleague later caught in a file RSquad reviewed. That is the
only miss this setting can observe.

## 5. When to stop and look

**At 50 findings**, fixed now so the stopping point is not chosen after seeing the numbers. That
is roughly ten small pull requests. At 50, the share of `act` for the squad as a whole is
known to about ±13 points: enough to say whether it sits clearly above or below the 30 % line
that `evaluation/acceptance/README.md` gives for keeping a lens. Per lens it takes about 50
findings *each*, so a per-lens verdict needs more pull requests; the squad-wide number comes
first.

## 6. What stays at work

**Code, queues, finding text and the log stay at work.** This repository is public. What may come
back here is counts only: findings per word, fixed or not, per lens if you recorded it, the five
step-0 answers, and the models that ran. Never a snippet, a file name from work, or a finding's
text.

The first campaign's counts are in [`step4-acceptance-counts.md`](step4-acceptance-counts.md)
(2026-11-21): 41 `act` / 58 attributable survived findings (71 %), above the ~30 % line.

## 7. Second campaign: before merge

Fixed on 2026-11-22, before any of it ran, so the stopping points are not chosen after seeing the
numbers.

The first campaign reviewed pull requests **after** they merged. It measured the author's word,
not what the review changed: every finding was logged `fixed before merge: yes (merged)`. This
campaign runs RSquad on each pull request **before** a colleague reviews it, with the same log
and the same four words, decided when the queue is read and before anything is fixed.

**It answers two questions, each with its own stop.**

1. **What the review changes.** Among survived findings marked `act`, the share fixed before the
   pull request merges. **Stop at 50 survived findings in this campaign**, counted squad-wide the
   way `step4-acceptance-counts.md` counts them (one per lens that saw the place). The first
   campaign reached 58 in 23 reviews, so expect about twenty pull requests.
2. **Whether the `tests` lens stays.** It sat at 45 % on 11 findings, the nearest any lens with
   numbers came to the 30 % line. Its words are pooled across **both** campaigns: they are decided
   the same way, when the queue is read. **Stop at 40 `tests` findings in total**, so 29 more.
   At 40, a share near 45 % is known to about ±15 points, enough to say whether the lens sits
   above the line or cannot be told from it. At the first campaign's pace of about one `tests`
   finding every two reviews, that is roughly sixty pull requests. The two stops do not wait for
   each other: stop 1 is reported when it is reached, and the log carries on for stop 2.

**`conformance` gets no verdict from this campaign.** It produced 5 findings in 23 reviews; forty
would take about two hundred. Its counts are still recorded and reported.

**What changes in the log:** `fixed before merge` is filled in when the pull request merges, and
now means something. A finding marked `act` and not fixed stays `act`. Also record, per review,
anything a colleague caught in a file RSquad reviewed: it is the only miss this setting can see.

Reported here as counts only, under the rules of §6.
