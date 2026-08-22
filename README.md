# RSquad

A review squad, built in a deliberate order. The order carries the design more than the
components do.

```
[0] MECHANICAL GATE        no agent — tests, types, lint, coverage delta,
                           + do the new tests fail against the code as it was?
                           failure -> stop. Nothing reaches the agents.
                                      │
[1] CONFORMANCE LENS       1 agent, WITH the spec
                           "does the diff do what the spec says?"
                                      │
[2] BLIND LENSES           n agents, WITHOUT the spec
                           repro · bounds · call contract · test quality
                                      │
[3] REFUTATION             1 agent per finding, separate context
                           its job is to kill it. Doubt means refuted.
                                      │
[4] RANKED QUEUE           for a human. Not a verdict.
```

## What carries the design

**The mechanical gate runs first and does not negotiate.** Having a model comment on code that
does not compile produces confident noise. And the gate carries the one check nothing else
provides: *does a new test fail against the code as it was?* A test that passes before and after
does not test the change. Coverage does not see it — it rises either way — and neither does a
green suite. Reverting the patch and re-running answers it with zero judgement and zero agents.

**The blind lenses do not get the spec.** This is the point worth defending hardest. A reviewer
who knows the intent checks conformance to the intent, not what the code does. Step [1] already
covers that. The others must answer a different question: *what does this code actually do, and
where does it break?* If they share the spec context you have four agents doing one job while
believing they are doing four.

The blindness is enforced by **context assembly**, never by a prompt instruction. "Do not look at
the spec" is unverifiable; not putting the spec in the payload is a fact you can test.

**Reproduction or nothing.** A finding without concrete inputs is dropped mechanically, with no
discussion. "This is fragile" does not ship. "If `items` is empty, line 42 raises" does — and it
is checkable, therefore refutable, therefore worth arguing about on evidence.

**The refuter is a separate context, and it gets the benefit of the doubt.** The asymmetry is the
mechanism: finding is free, surviving refutation is not. Without it, an agent asked for problems
will always supply some.

**The queue ranks; it does not decide.** A system that orders human attention beats one that
claims to replace it.

## Status

| Step | State |
|---|---|
| [0] mechanical gate | **built** — `rsquad gate`, Python/pytest adapter |
| [1] conformance lens | not started |
| [2] blind lenses | not started |
| [3] refutation | not started |
| [4] ranked queue | not started |

```bash
rsquad gate                                  # HEAD against its parent
rsquad gate --base master --strict           # against the merge base with master
rsquad gate --head 4164d03                   # replay on a past commit
rsquad gate --replay 20 --repo ../other      # aggregate over the last 20 commits
```

`--replay` is not a convenience: replaying the gate over history is how you measure what it
would actually have caught, on data nobody arranged. Do that before trusting it.

## Porting to another stack

The core knows no language. Everything stack-specific fits into four questions
(`gate/adapters/base.py`):

1. Which files in the diff are tests?
2. Which test functions are new or modified? (by comparing function bodies across revisions)
3. How do we run that subset so it emits JUnit XML?
4. **How do we guarantee the code under test is the base's?**

Question 4 is the trap, and it differs in every ecosystem — editable installs, `node_modules`
resolution, classpath, NuGet caches. Expect to find your version of it **by running the gate**,
not by reading it. Every defect in the original implementation was found by execution; none by
review, and each one made the tool silently useless while looking green.

JUnit XML is the portable seam: pytest, Jest, Vitest, Surefire, gotestsum and .NET all emit it,
and it natively distinguishes `<failure>` (an assertion — the test discriminates) from `<error>`
(a crash — the module does not exist yet). Nothing to guess.

## What this will not do

- **It is blind to additions.** A test covering a function that did not exist can only fail with
  an import error — there is nothing to discriminate. The gate covers *modifications*. Code
  written by agents often adds whole modules, which is exactly the least covered case. The
  complement is **mutation testing**: not "does the test fail without the module?" (trivially
  yes) but "does it fail if the logic is subtly wrong?". Named here, not built.
- **It measures falsifiability, not relevance.** A test can discriminate perfectly and prove a
  property nobody needs. One real case: a test asserted `canonicalise("Huggy Face")` while the
  stored key held `huggyface` in one word. Perfectly discriminating, and useless. No mechanical
  check closes that gap.
- **Blind spots are correlated.** The lenses share the training distribution of the model that
  wrote the code.
- **No architectural findings.** It reads a diff, not a system.
- **A green verdict is not a validation.** Always read the number of tests *examined* next to the
  verdict: "0 suspect" very often means "nothing could be checked at all".

## Deploying it without getting it switched off

Expect an annotation phase. Two exemption markers exist because a measured run needed both:

- `characterization` — asserts a refactor changed nothing, so it *must* pass on the base.
- `guard` — asserts something does **not** happen; the base does not do it either, so it cannot
  fail there by construction.

On one measured sample, six flagged tests broke down as one genuine finding (an assertion
loosened from `== 5` to `>= 5` — precisely the failure mode worth catching) against five tests of
those two kinds. Deployed without the markers, that gate produces five false positives out of six
and is switched off within a week, taking the real finding with it.

And never let a judgement finding block a merge. The mechanical gate blocks. Opinions comment.

## License and provenance

The gate began in a private project as `tools/portail_tests.py` and was extracted here,
translated, and verified equivalent function-by-function across 20 real commits before any
behaviour was deliberately changed. See `docs/`.
