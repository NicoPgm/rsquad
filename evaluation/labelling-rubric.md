# Labelling rubric — written before the cases, deliberately

`detectable_from_diff` decides which cases enter a denominator, so it decides the headline. A
rubric written *after* seeing the diffs is a rubric fitted to them, and the label would then
encode the answer it is supposed to be independent of.

This file is committed before any case of the young-repository pool is labelled. If a case turns
out not to fit the rubric, the rubric changes **here first**, with the reason and the date, and
every already-assigned label is reviewed against the new wording.

## What the label is about

The question is always the same, and it is not "is this defect subtle":

> A careful reader is handed **the origin commit's diff, restricted to the file under review**,
> plus that file at that revision. Nothing else — no issue, no fix, no later history. Can they
> reach the defect?

The reader is the standard the blind lenses are held to, so the rubric is written for what those
lenses actually receive (ADR-0004): one file, its diff, its numbered contents, and a context pack
of definitions the changed lines reference.

## The three values

**`yes` — the diff contradicts itself, or contradicts something inside the file.**
The evidence needed is present. A comment promising what the code does not do; a variable
computed and then not used; a condition that handles one half of a symmetric case; a shift that
sign-extends a masked field. The reader needs no fact from outside the file.

**`weak` — the diff carries a smell, and confirming it needs one fact from outside.**
The defect is visible as *something to check*, but knowing it is wrong requires a convention, an
API contract, or a caller the file does not show. `lastIndexOf(str, size - 1)` is weak: the
boundary is right there, and knowing `size` is correct depends on `lastIndexOf("")` returning the
length, which is a library convention.

**`no` — nothing in the diff distinguishes the defect from correct code.**
A wrong constant that looks like a right constant. A missing flag on a call that is otherwise
well-formed. A behaviour that is wrong only in combination with a file not shown. These are kept
in the set — they record what kinds of defect the codebase produces — and **excluded from every
rate**, because scoring against them measures nothing and drags the number down.

## Rules that bind the labeller

1. **Label from the origin diff, never from the fix.** The fix names the defect; reading it first
   makes everything look `yes`. Read the origin diff, decide, then read the fix only to confirm
   which line is the defect.
2. **The label is about the evidence, not the difficulty.** A defect can be hard to see and still
   be `yes` if the diff contains everything needed. Ease belongs to the result, not the label.
3. **When torn between two values, take the lower one.** `weak` over `yes`, `no` over `weak`.
   Over-labelling inflates the denominator with cases the squad cannot be expected to find, which
   makes a bad result look worse — and under-labelling has the opposite, more flattering effect,
   which is the one to guard against.
4. **Write the rationale in the same breath as the label**, naming the specific evidence. A label
   with no rationale cannot be audited, and being auditable afterwards is the whole point of
   freezing this before the run.
5. **A case whose defect cannot be located in the origin diff is dropped, not labelled `no`.**
   Those are two different statements: `no` says the squad could not have found it, dropped says
   the case was never constructed correctly.

## Covariates recorded beside the label, never folded into it

- `origin_date` — the memorisation stratum. Post-cutoff cases are the only ones where the model
  cannot have read the fixed version.
- `origin_lines` — how much unrelated change the defect is buried in. A 6-line diff and a 588-line
  diff are different tasks, and the label does not distinguish them.
- `origin_creates_file` — whether the commit added the file. Reviewing a whole new class is a
  realistic task and a different one.

These stay separate on purpose: folding "it was buried in 400 lines" into the label would mix a
property of the task with a property of the evidence, and then neither could be reported.

## Known bias of this rubric

It is applied by the same party that reads the results, and committing it first bounds that
rather than removing it. The honest fix is a second labeller, which is not available here — so
the rationale field exists to let a later reader disagree case by case, which is the next best
thing.
