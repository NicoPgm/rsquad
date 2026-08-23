# Evaluation — the method, its cost, and what it does not prove

The only non-circular way to know whether a review squad finds anything is to replay it on diffs
that are **known** to contain a defect, where the label came from reality — somebody hit the bug
and fixed it — rather than from a model's opinion.

Everything else measures agreement. A squad scored against findings a model produced is a squad
scored against itself.

## The honest denominator today is four

`evaluation/defects.yaml` holds nine defects. Two fields decide how many of them can appear in a
detection rate.

**`detectable_from_diff`** — not every real defect is findable by reading the diff that introduced
it. A wrong constant looks like a right constant. A no-op flag looks like a working flag when the
reason it is a no-op lives in another file. Scoring against undetectable cases measures nothing
and makes the squad look worse than it is: the same self-deception, pointed the other way.

**`self_found`** — four entries were found by RSquad itself. They are real defects and worth
keeping, but scoring a squad on cases it discovered measures only that it can repeat itself.

|  | `self_found: false` | `self_found: true` | |
|---|---:|---:|---:|
| `detectable: yes` | **2** | 4 | 6 |
| `detectable: weak` | **2** | 0 | 2 |
| `detectable: no` | 0 | 0 | 1 |
| | **4 scorable** | 4 circular | 9 |

**Four cases.** On four cases a 25 % detection rate and a 75 % one are the same measurement. This
set will catch gross blindness — a squad that finds nothing, or that only ever finds style — and
nothing finer. Any number computed from it must be reported as a fraction with its denominator
visible, never as a percentage.

### What is already known about those four

One of them has been replayed, by hand, seven times. `head-overwritten-before-use` at
`tools/portail_tests.py:272` in `ai-video-digest@b404a93` was found **first and `blocking` in all
seven runs**, across both transports and three configurations (`transport-comparison.md`).

That is 1/1 with high reliability, and it is worth stating precisely because it is so easy to
inflate. It says the squad reliably finds *this* defect. It says nothing about a rate.

## The method

### Scoring one case

A case is `(repo, introduced_in, file, and the defect's location)`. Replay is:

```
rsquad review --repo <repo> --head <introduced_in> --path <file> --confirm
```

and then ask whether any surviving finding **names the defect**. The scoring rule has to be
decided before the run, not after reading the queue, and the workable one is:

- **Detected** — a surviving finding anchors within a few lines of the defect *and* its
  `consequence` describes the actual failure. Both halves are required. A finding that points at
  the right line for the wrong reason is a coincidence, and counting it inflates every subsequent
  number.
- **Missed** — otherwise.

The second half cannot be automated honestly. It is a human judgement per case, which at four
cases is fine and at four hundred is the reason nobody does this.

### What the run must report

Three numbers, and the third is the one everybody omits:

1. **Detected / scorable**, as a fraction with the denominator visible.
2. **The same fraction restricted to `self_found: false`** — the only one that means anything.
3. **Findings produced that were not the known defect.** Not "false positives" — a genuine
   second bug in the same diff is not an error — but the count bounds the reader's cost, and it
   is the number that decides whether anyone keeps using the tool.

### Cost

Measured on one file of one commit, full configuration — four blind lenses, the conformance lens,
one refuter per refutable finding:

| | |
|---|---|
| API transport | **$0.80 – $1.00 per case**, 11–13 calls (three runs) |
| Harness transport | 764k – 821k tokens per case (two runs) |

So the current four scorable cases cost roughly **$4** on the API path, and replaying all nine
costs under $10. That is cheap enough that the reason it has not been automated is not money.

Both transports returned the same set of places on repeated runs, so a single pass per case is
defensible. That was not obvious in advance and it halves the cost of any future measurement.

## What this method does not prove

**No false-positive rate.** Every case in the set is a diff known to contain a defect. Nothing
here replays a *clean* commit and counts what comes back. That measurement needs the opposite
corpus, and it is arguably the more useful of the two: a squad that finds the bug and eleven other
things has not helped.

**Nothing about the refuter's real cost.** How many *true* findings refutation kills is the
number that decides whether it earns its calls. Measuring it means running each case twice —
`--no-refute` and with — and comparing. Across seven runs the refuter has killed nothing, which is
a weak signal in one direction and not a measurement.

**Nothing about relevance.** The gate can confirm a test discriminates perfectly and proves a
property nobody needs. The same applies one layer up: a finding can be true, anchored, refutation-
proof, and about something no reader cares about. No mechanical check closes that gap, and the
only real judge is **the human acceptance rate per lens**. Below roughly 30 %, a lens should be
withdrawn — otherwise the team learns to skim the queue, and the other lenses go with it.

**Nothing about generality.** One repository, one language, one author's habits. The lenses were
shaped around the kinds of defect this codebase produces, which is visible in the set itself: six
of nine are `correctness`, one is `resource`, none is concurrency, none is security.

## What a real measurement needs

The deferred work, with its selection criteria stated in advance so the choice cannot be made to
flatter the result:

**An open-source repository with**

- a rich history of **issue-linked fixes** — the label has to come from a bug report, not from a
  reading of the diff;
- a real test suite, so the gate has something to examine;
- **a non-Python stack**, which validates the adapter protocol and produces a detection rate in the
  same pass.

Fixing the target repository, the commit range and the scoring rule **before** running anything is
the whole discipline. The published 47 % figure in the source project survived two weeks and three
defects before becoming 21 %; it was not dishonest, it was unfixed-in-advance.

**And there is no reason to expect the result to be good.** The four scorable cases here are the
easy shape: a single-file logic error, visible in the diff, in code written by the same tools
being asked to review it — which is the correlated blind spot, not a control for it.
