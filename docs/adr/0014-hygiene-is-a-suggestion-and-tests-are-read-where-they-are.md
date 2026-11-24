# ADR-0014 — Hygiene becomes a suggestion, and the tests of the changed code are read where they are

**Status:** accepted
**Date:** 2026-11-24
**Amends:** ADR-0003 (one more `kind`), ADR-0006 (one kind of finding is not refuted),
ADR-0009 (what the `tests` lens is shown) and the shared out-of-scope list.

## Context

On the nine larger ReviewBench pull requests V4 covered 4 of the 44 golden findings that are
hygiene (tests to add, misleading names, maintainability, documentation), against 68 of 124
defects. After ADR-0012 and ADR-0013, tp #152 still missed 10 of 14: five were hygiene the shared
prompt rules out ("test coverage", "naming", "refactoring suggestions"), and two were weak tests
in test files the pull request did not touch, which the `tests` lens was never shown. The bench
counts all of them as true, and the reviewers at the top of its leaderboard report them.

## Decision

- **A sixth lens, `hygiene`**, takes back a narrow part of the out-of-scope list: a new or changed
  behaviour no test would catch breaking (reported at the behaviour, naming the missing test), a
  name that says something other than what the code does, a declaration that contradicts the
  value, a fragile idiom where a sound one is standard. Formatting, style and preferences stay
  out. It reads and reports in code and tests, not documentation.
- **Its findings are `maintainability`, a new `kind`, and are not refuted.** Nothing fails yet,
  so a refuter has nothing to show wrong; it would only add cost. They ride to the queue like a
  conformance claim.
- **The queue sets them apart, last, under "Suggestions"**: never a reason to hold the change.
  An entry that also holds an account of a real defect stays with the defects.
- **The `tests` lens is shown the code of the change and runs on every change.** It reads the
  existing tests of the changed code in `repo/`, changed or not: a test of that code that cannot
  fail is now guarding the change. Such a finding is `exposed` or `pre-existing`.

## Consequences

- Two more Opus tasks per review in the worst case (`hygiene`, and `tests` where no test
  changed), and no refutation for suggestions.
- More entries. The Suggestions part is where noise will gather first; it is last in the queue
  for that reason, and it is the first place to cut if the campaign at work says so.
- Any lens may now use `maintainability` and skip the refuter. Only `hygiene` is told to; the
  others are still told that style and naming are out of scope.
