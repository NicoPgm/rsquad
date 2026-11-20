# ADR-0006 — The refuter inherits no framing, and a broken refutation refutes nothing

**Status:** accepted
**Date:** 2026-08-22

## Context

Twenty-one findings came out of the first two paid runs and none had been contested, because
step [3] did not exist. A queue of uncontested findings is a list of suspicions: an agent asked
for problems supplies some, and most of what a review produces is plausible rather than true.

## Decision

One refuter per finding, in its own context, told to kill the claim.

**It inherits no framing.** It gets the file, the line, the snippet, the inputs and the claimed
consequence — never the lens that produced them, never the severity somebody assigned, never the
other findings. Those are the finder's opinions, and a refuter that saw them would be grading a
colleague instead of reading code, inheriting exactly the confidence it exists to test. A test
asserts none of the three appears in the payload.

**No confidence scale.** The verdict vocabulary is closed: `stands` lets a finding through, and
six other values each name a way it died. A scale is where a refuter hedges.

**Doubt means refuted.** The burden is on the claim; the reader's time gets the benefit of the
doubt.

**A refutation is held to the standard it enforces.** `evidence_snippet` must anchor in the file
exactly as a finding's snippet must.

**But an unanchored verdict refutes nothing.** This is the asymmetry inside the asymmetry, and
it is the decision most likely to be undone by someone tidying up. "Doubt means refuted" governs
the refuter's *reasoning*, not its *malfunctions*. A verdict whose evidence is not in the file is
a broken response, and letting one through would mean hallucinated evidence silently deleting
real work. Those verdicts are recorded and ignored; the finding survives to be read.

The refuter runs at the highest effort available. Its mistakes are the least visible in the
squad: a wrong refutation deletes a real finding and leaves nothing in the queue to notice.

## Consequences

Measured on the first run, `ai-video-digest@b404a93`, six findings, one refuted.

**The step did the exact discrimination it exists for.** Two lenses reported the same underlying
defect — `git rev-parse` on a bad revision returns non-empty stdout, so a `if not sha` guard
never fires — with different consequences attached:

- *"the tool prints 'no test file changed' and returns 0"* → **refuted**, `already-handled`. The
  refuter traced the path: with those inputs, `base_de_comparaison` resolves `<ref>~1`, that
  call *does* check the return code, and execution raises before ever reaching the message.
- *"execution continues and fails later with a misleading message"* → **stands**. Accurate, and
  it survived.

The underlying bug is real in both. One claim overstated its consequence and one did not, and
the refuter killed exactly the overstated one — without being told which lens wrote either, or
that they were about the same code. It refuted the claim as stated rather than improving it,
which is what the prompt asks and the harder thing to get.

**Cost roughly doubles.** $0.37 for four lens calls became $0.89 with six refutations at highest
effort. Refutation is about as expensive as finding.

**Self-variance is now visible and is not small.** The same commit, same prompts, same model
produced 8 findings on one run and 6 on the next, with severities moving between them. That is a
data point for ADR-0005's comparison — the standalone transport is not perfectly reproducible
either, and the question is which transport varies *less*, not which one is exact.

**2026-11-20** — ADR-0009 adds a seventh death, `undecided`: the payload does not settle the
claim. It is not a confidence scale and it lets nothing through; doubt still refutes. What it
changes is the record. With six causes, a refuter that could not decide had to name one that
might not hold, and the `Refuted` section then misreported why a finding died.
