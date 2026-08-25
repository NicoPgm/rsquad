# The tests lens, evaluated for the first time

**Result:** 28 raw findings over 36 cases, **25 past the guards** — against **5 raw over 53**
in every previous run. The lens was never underperforming. It was never shown a test.

**Model:** `claude-sonnet-5`, effort `high`. Deliberately not Opus, and the one arm where that
is defensible — see *The model, and why it is different here*.

## What was wrong before

`rsquad evaluate` reviews one unit per case: **the changed source file**. Every `tests` task in
the Java campaign therefore asked a lens to judge test quality in a payload with no test in it.
It answered anyway, rarely and off-topic, and the four-or-five findings that came back were read
as a yield problem. They were not a measurement of the lens at all.

| | previous runs | this run |
|---|---|---|
| tasks whose payload contained a test file | 0 of 53 | 36 of 36 |
| raw findings | 5 | 28 |
| per case | 0.09 | 0.78 |
| findings past the guards | — | 25 |
| cases where the lens spoke | — | 16 of 36 |

## The selection, fixed before the run

One test file per case, chosen mechanically by `evaluation/step7e_tests.py`: the test named for
the class under review (22 cases), failing that one whose name contains it (3), failing that the
first in sorted order (11). Which rule fired is recorded per case, because *"the test for this
class"* and *"the first file alphabetically"* are very different claims about relevance.

Two of the 38 frozen cases have an origin commit that touches no test at all, and are absent.

## Question 6 turned out to be a precondition, not a neighbour

31 of the 36 tasks carry a context pack, and **29 of them reach the class the test exercises**.
Run a week ago — before the Java resolver existed — this arm would have asked a lens to judge a
test against code it could not see. The two pieces of work were listed as independent; they were
not.

## What the lens actually says

The findings match the lens's own checklist rather than drifting into general review. A
representative sample, quoted from the queues:

- `assertThat(result).contains("\"result\"")` — the substring is already present verbatim in the
  canned mock body, so the test passes whether or not the code unwraps the value it claims to
  extract.
- `assertThatExceptionOfType(RuntimeException.class)` — the superclass of nearly every unchecked
  exception in Java; a `NullPointerException` from a misconfigured driver satisfies it.
- A `remove(id1)` followed immediately by `getAllEmbeddings()` with no `awaitUntilPersisted()`
  between them, on an eventually-consistent store.
- A test whose name promises one behaviour and whose body also asserts an unrelated contract, so
  a failure is reported under a name that does not describe it.

23 of the 25 carry `kind: test-quality`, the kind its prompt names; 2 drifted to `resource`.
Severity splits 13 minor / 12 significant.

## The guards refused a finding, for the first time in this project

Three findings were rejected by the anchoring guard — *snippet does not appear within 3 lines of
the claimed line*. Every previous Java run refused **zero**, across every lens and both
transports, and that unbroken record had started to look like a guard that never fires.

**Do not attribute this to the model.** Two things differ from every earlier run at once — the
lens is being shown a different kind of file, and the model is Sonnet rather than Opus. Either
could produce it. What the three refusals do establish is that the guard is load-bearing rather
than decorative: it is capable of firing, on real output, and it did so silently and correctly.

## The model, and why it is different here

Every other measurement in this campaign compares against a half already run on
`claude-opus-5`, so there the model must be held constant or two things move at once. This arm
has no counterpart — nothing has ever measured this lens — so a cheaper model costs a caveat
instead of a comparison. The choice is recorded in `selection.json` and in the manifest, and the
harness now reads the manifest's model rather than inheriting the session's.

**Binding condition:** these 25 findings must be **labelled by model** when they enter the
acceptance worksheet. Unlabelled, they would quietly make that corpus a mixture of two engines,
and the per-lens acceptance rate it exists to produce would be uninterpretable for this lens.

## What this is not

- **Not a detection rate.** The frozen labels name a defect in a *source* file; a finding about
  a test has nothing to be scored against. This is yield, and yield alone.
- **Not refuted.** These are round-1 findings past both mechanical guards. The refutation round
  was not run — 25 more calls — so every number here is pre-refutation and not comparable to the
  post-refutation figures elsewhere in `docs/`. Elsewhere refutation kills roughly one finding
  in ten.
- **Not an acceptance rate.** Whether these 25 are worth a reader's time is the one measurement
  a machine cannot make, and it is still missing.
- **One test per case.** 36 tests out of the ~120 the origin commits touch. A wider sample would
  change the yield per commit; it would not change the finding that the lens works when given
  its subject.
