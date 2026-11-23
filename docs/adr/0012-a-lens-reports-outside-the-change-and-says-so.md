# ADR-0012 — A lens reports outside the change, and says which side of it a defect is on

**Status:** accepted
**Date:** 2026-11-23
**Amends:** ADR-0003 (the finding contract: a new required field) and ADR-0011 (a finding had to
be reported at a line of a file under review). On the harness transport; the API transport
inherits the schema and the shared prompt, and its lenses still see one file.

## Context

On the nine larger ReviewBench pull requests, V4 covered 3 of the 17 golden findings the bench
labels pre-existing, against 69 of 147 introduced by the pull request. One miss shows the
mechanism: on tp #152, the pull request made a delete command reachable that deletes nothing.
The command's file was not in the change, so the lens reported it at the nearest changed line,
and the refuter confirmed the defect and removed it as `wrong-location` (fixed separately: that
verdict now lets the finding through). The lens had found it; the contract had nowhere to put
it.

The bench is not the reason. A reader at work wants a defect the change exposes in untouched
code before merging, and wants the older ones too, as technical debt, as long as the two are not
mixed.

## Decision

- **A lens may report a defect in any file of the job's `repo/`**, at the line where it lives.
  It anchors against that copy, under the same guard. The routing by file kind still holds, and
  a changed file a lens was not shown stays closed to it.
- **The instruction is wide**: every defect found, whether or not the change has anything to do
  with it. A tight variant ("only what the change makes reachable") was considered and left out
  until a measured cost asks for it; the cheapest form of it would drop `pre-existing` findings
  before refutation, with the same prompt.
- **Every finding carries `scope`**: `introduced`, `exposed` or `pre-existing`, a closed
  vocabulary like `kind`, aligned with ReviewBench's own scope axis. It is the lens's claim and
  nothing checks it, except one rule: a finding in a file the change does not touch cannot be
  `introduced`, and is dropped by the guards if it says so.
- **The queue is cut in two.** What the change introduced or exposed comes first, ranked as
  before. "Already there" follows, as candidates for technical-debt tickets. One lens placing a
  defect in the change is enough to keep it in the first part.
- A finding outside the change gets a refuter like any other, given the whole file and told the
  change does not touch it.

## Consequences

- **More findings, so more refutations.** A refutation cost about 0.26 points of a 5-hour window
  on the nine pull requests, more than the lenses in total. How many pre-existing defects a wide
  instruction adds is unmeasured; it is the first number to read on the next run.
- **Jobs exported before this change cannot be ingested**: their replies lack `scope` and fail
  the schema, and are counted as malformed.
- **The scope is self-reported.** A lens can call an old defect `introduced` inside a changed
  file, and nothing will catch it. The split is a reading order, as severity is.
