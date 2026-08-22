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
| the finding contract | **built** — `schema/finding.v1.json` + both guards, no model involved |
| [1] conformance lens | not started |
| [2] blind lenses | **built** — `rsquad review`, four lenses, blindness enforced by signature |
| [3] refutation | **built** — one refuter per finding, no inherited framing |
| [4] ranked queue | **built** — grouped by location, ranked, never a verdict |

### The finding contract

Everything a lens produces passes through `schema/finding.v1.json`, and the two guards are built
into its shape rather than asked for in prose:

```
file · line · snippet · kind · severity · inputs · consequence
```

**Anchoring.** `snippet` must appear in the file within a few lines of `line`, by exact search
after whitespace normalisation. Checking it *near the claimed line* validates the quote and the
location together — a finding that quotes real code but points at the wrong place is not
actionable. This is the only anti-hallucination guard that depends on no provider, no model and
no prompt.

**Reproduction or nothing.** `inputs` and `consequence` are required and must not be vacuous.
"This is fragile" does not ship. "If `items` is empty, line 42 raises" does. The guard rejects
the empty and the evasive; it cannot separate a specific claim from a confidently-worded vague
one, and does not pretend to — that is the refuter's job in step [3].

`kind` and `severity` are **closed enumerations**, constrained by the API's structured-output
format rather than by a line of prompt asking nicely. They exist once, in the schema, with the
gloss that explains each value; `findings.vocabulary_block()` renders the prompt text from them
at run time so the two cannot drift.

Rejected findings are returned alongside kept ones, never dropped silently — what the guards
refuse is a measurement of how the lenses are behaving.

### Ground truth

`evaluation/defects.yaml` holds real defects with the commit that introduced each one, so a
squad can be replayed against diffs whose label came from reality rather than from a model.

It is a **smoke test, not a measurement** — five cases today. It will catch a squad that finds
nothing; it cannot tell 40 % from 70 %. Its most important field is `detectable_from_diff`:
some real defects are simply not findable by reading the diff that introduced them, and scoring
against those measures nothing.

```bash
rsquad gate                                  # HEAD against its parent
rsquad gate --base master --strict           # against the merge base with master
rsquad gate --head 4164d03                   # replay on a past commit
rsquad gate --replay 20 --repo ../other      # aggregate over the last 20 commits

rsquad review                                # what would be sent, and to how many lenses
rsquad review --confirm                      # actually spend
rsquad review --lens repro --confirm         # one lens only
rsquad review --no-refute --confirm          # skip step [3], cheaper and weaker
```

`rsquad review` is a dry run unless you pass `--confirm`, and the dry run prints **no cost
estimate**. Two invented cost constants from the source project are sitting in
`evaluation/defects.yaml`; this tool reports what was billed, not what it guessed.

The credential is read from `ANTHROPIC_API_KEY`, or from a `.env` at the repository root, or
from whatever `RSQUAD_ENV_FILE` points at — so a key you already keep for another project can be
reused in place instead of copied. A secret duplicated is a secret with two places to leak from.

`--replay` is not a convenience: replaying the gate over history is how you measure what it
would actually have caught, on data nobody arranged. Do that before trusting it.

## Porting to another stack

The core knows no language. Everything stack-specific fits into six questions
(`gate/adapters/base.py`):

1. Which files in the diff are tests?
2. Which test functions are new or modified? (by comparing function bodies across revisions)
3. How do we run that subset so it emits JUnit XML?
4. **How do we guarantee the code under test is the base's?**
5. Which base failures mean "the symbol does not exist yet" rather than "the test caught
   something"?
6. Which definitions elsewhere in the repository does a change reference?

Question 4 is the trap, and it differs in every ecosystem — editable installs, `node_modules`
resolution, classpath, NuGet caches. Expect to find your version of it **by running the gate**,
not by reading it. Every defect in the original implementation was found by execution; none by
review, and each one made the tool silently useless while looking green.

JUnit XML is the portable seam: pytest, Jest, Vitest, Surefire, gotestsum and .NET all emit it,
and it distinguishes `<failure>` (an assertion) from `<error>` (a crash during collection or
setup).

**That seam is not quite where it looks, which is question 5.** A symbol that does not exist yet
lands on either side depending on how the test names it — `from mod import thing` fails at
collection (`<error>`), while `import mod` then `mod.thing(...)` fails in the body (`<failure>`,
reading as a discriminating test). Same missing symbol, opposite verdicts, decided by import
style. So the classification needs a per-language predicate, and it must be narrow: the risk is
the false negative. `AttributeError: module 'x' has no attribute 'y'` means the symbol is absent;
`AttributeError: 'NoneType' object has no attribute 'y'` is a test catching a real defect, and
discarding it would be worse than the problem being fixed.

**Question 6 is the context pack** (ADR-0004): the definitions of first-party symbols the
changed lines name, resolved deterministically so a lens can check how the change uses its
neighbours without being handed file-reading tools. Measured on 34 changed files: 65 % resolve at
least one definition, 3.2 on average. Leaf modules resolve nothing and need nothing;
orchestration files resolve the most and need it most.

Assume a seventh question exists. Five and six both arrived after the protocol was declared
complete — one from a crash, one from a conversation.

## What this will not do

- **It is blind to additions, and more so than it looks.** A test covering a function that did
  not exist can only fail by not finding it — there is nothing to discriminate. The gate covers
  *modifications*. Measured over 20 real commits: **it can say nothing about 79 % of new test
  functions** (`docs/gate-baseline.md`). Code written by agents often adds whole modules, which
  is exactly the least covered case. The complement is **mutation testing**: not "does the test
  fail without the module?" (trivially yes) but "does it fail if the logic is subtly wrong?".
  Named here, not built.
- **It measures falsifiability, not relevance.** A test can discriminate perfectly and prove a
  property nobody needs. One real case: a test asserted `canonicalise("Huggy Face")` while the
  stored key held `huggyface` in one word. Perfectly discriminating, and useless. No mechanical
  check closes that gap.
- **Blind spots are correlated.** The lenses share the training distribution of the model that
  wrote the code.
- **No architectural findings.** It reads a diff, not a system.
- **A green verdict is not a validation.** Always read the number of tests *examined* next to the
  verdict: "0 suspect" very often means "nothing could be checked at all". The gate's own
  published coverage was 47 % for two weeks; the real figure is **21 %**, and the gap was three
  defects nobody caught by reading the code.

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

## Decisions

`docs/adr/` holds the decisions that constrain future work; `docs/*.md` holds measurement
reports. A report says what happened, an ADR says what we do about it.

| | |
|---|---|
| [0001](docs/adr/0001-record-decisions-in-adrs.md) | record decisions in ADRs |
| [0002](docs/adr/0002-blindness-is-a-property-not-a-promise.md) | blindness is a property of the payload, not a prompt instruction |
| [0003](docs/adr/0003-the-finding-contract.md) | closed vocabulary and two mechanical guards |
| [0004](docs/adr/0004-one-file-per-unit-with-a-computed-context-pack.md) | one file per unit, plus a computed context pack |
| [0005](docs/adr/0005-two-transports-one-core.md) | two transports, one core — *proposed* |
| [0006](docs/adr/0006-refutation-inherits-no-framing.md) | the refuter inherits no framing, and a broken refutation refutes nothing |

## License and provenance

The gate began in a private project as `tools/portail_tests.py` and was extracted here,
translated, and verified equivalent function-by-function across 20 real commits before any
behaviour was deliberately changed. See `docs/`.
