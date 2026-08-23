# First evaluation against ground truth — 1 of 4

**Date:** 2026-08-23
**Command:** `rsquad evaluate --repo ../ai-video-digest --confirm`
**Cost:** 56 calls, **$7.05**, `claude-opus-5`, full configuration.
**Artifact:** `evaluation/report.md` — the four cases with their findings and filled-in verdicts.

Four scorable cases of eleven. Seven excluded and each printed with its reason: one is not
findable from its diff, six were found by RSquad itself.

| Case | Detectable | Result |
|---|---|---|
| `head-overwritten-before-use` | yes | **detected** — 5 independent accounts at `:272` |
| `verdict-depends-on-import-style` | weak | missed |
| `words-per-video-invented` | weak | missed |
| `since-flag-never-bit` | **yes** | missed |

**1 / 4.** Four cases do not make a rate — 1/4 and 3/4 are indistinguishable at this size, which
is why `evaluation/defects.yaml` has said "smoke test, not a measurement" since it was written.
What four cases *can* show is a pattern, and there is one.

Before scoring, each defect was checked to be genuinely inside the diff the lenses were handed.
All three misses were. None is a case of "the code was not shown".

## The three misses share a shape

**Every miss is a defect whose wrongness is invisible in the text.**

- A `yt-dlp` command missing `--extractor-args youtubetab:approximate_date` looks like a `yt-dlp`
  command. Twelve lines above it, a docstring discusses `approximate_date` precision — the code
  documents a precision it never requests, which should have made this *easier*.
- `MOTS_PAR_VIDEO = 2400` looks exactly like a correct constant.
- `<failure>` versus `<error>` is a distinction the code draws correctly and means wrongly.

In each case the code says what it does. What it does is not what it should do, and only
knowledge from outside the file says so.

**The hit is the opposite shape.** At `:272` a variable is resolved, used, and reassigned before
its use — self-contradictory *within the diff*. Five lenses found it independently.

## So the limit is sharper than "it reads a diff, not a system"

**The blind lenses find contradictions, not omissions.**

An omission has no anchor to quote, and `snippet` — the guard that makes a finding checkable, and
the only anti-hallucination mechanism that depends on no provider — requires one. A lens that
wanted to report "this command is missing a flag" has nothing to put in `snippet` but the command
that is *correct as far as it goes*.

**The contract that stops hallucination may be the same thing that stops this class of finding.**
Nothing measured here separates the two, and it is the most interesting question this run raised.
It is testable: run the same four cases with the anchoring guard reporting rather than dropping,
and read what it refuses.

## It also relocates the conformance lens

Two of the three misses are exactly what a stated intent should catch. The commit message for
`22a9680` announces a **bounded** backfill; a `--depuis` filter that matches everything
contradicts it directly.

Step [1] ran on both cases, against those commit messages, and returned **zero findings**.

Two explanations, and one paid run per case would separate them: the commit messages are too thin
to constrain anything, or the conformance lens is weaker than the blind ones. Until then, the
claim in `architecture.md` that step [1] is "the first thing to lose" when porting is generous —
it may already be the weakest step here, on a repository that has specifications.

## The run found two live defects in RSquad

On the case it *missed*, the lenses returned six findings on the file. Four are already in the
set as `self_found`. Two were not, and both survived the extraction into RSquad — verified by
running the code, not by reading it:

- **`exemption-lost-and-stolen-on-async-tests`** — a marker above `async def test_x` matches
  neither branch of the marker scan, so the async test loses its exemption *and* the exemption
  lands on the next plain test, which never carried one. The second half is the bad one: the gate
  silently reports `valid` for a non-discriminating test, which is precisely what it exists to
  catch.
- **`filters-match-bare-names-across-files`** — the changed-function filter and the exemption set
  hold bare names, so a same-named test in an untouched file gets examined and reported suspect.

Both are now in `defects.yaml` as `self_found: true`, and both are unfixed.

**This is the second paid run to find live defects in the tool that produced it.** The first found
five. That is the strongest available evidence that the squad does something, and it is not a
detection rate — it is the same circularity the `self_found` field exists to keep out of one.

## What this does not say

- **Not a detection rate.** Four cases.
- **Nothing about false positives.** Every case is a diff known to contain a defect. The three
  misses each returned three to six *other* findings that were not scored at all, and several of
  them look real. A reader's cost is unmeasured.
- **Nothing about the refuter's true-kill rate.** Across the four cases it killed 5 of 34 claims
  (2 `no-consequence`, 2 `intended`, 1 `misread`). Whether any of the five was true needs the
  same run twice, with and without `--no-refute`.
- **One repository, one language, one author.** The deferred open-source case is still the only
  thing that would produce a number worth publishing (`evaluation.md`).
