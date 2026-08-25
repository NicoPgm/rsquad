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
| [1] conformance lens | **built** - the only step with the intent, and both ends anchored |
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

It is a **smoke test, not a measurement**. Eleven entries today, of which **four are scorable** —
the rest are either not findable from the diff at all, or were found by RSquad itself, and both
kinds measure nothing. On four cases a 25 % detection rate and a 75 % one are the same number.
It will catch a squad that finds nothing; it cannot tell 40 % from 70 %. The method, the cost and
what it cannot prove: [`docs/evaluation.md`](docs/evaluation.md).

**Third replay, 2026-08-23: 15 of 19 on real bug-introducing commits from two young Java
projects, $17.24.** The first campaign that measures what it claims to: the commit reviewed is
the one that first wrote the buggy line, verified, so the correct version is not in the diff.
**The memorisation gradient runs the wrong way for the hypothesis** — 5/5 on defects written
after the knowledge cutoff, 4/7 on the oldest, where recall would have helped most. All four misses returned a
different real bug instead, which is the
contradictions-not-omissions hypothesis holding on a set built not to favour it. Reader's cost,
measured for the first time: 2.6 findings per case, 35 of 50 not the known defect.
[`docs/step7b-first-run.md`](docs/step7b-first-run.md).

**The clean-commit corpus, 2026-08-23, on the harness: 1.5 findings per clean commit against 2.6
per defective one — and silence on 4 of 8 clean commits, against 0 of 19 defective ones**
(Fisher exact, two-tailed, p ≈ 0.008). The squad shuts up on half the code nobody has complained
about and never once shut up on a diff carrying a defect. Reading the twelve findings matters:
none is invented, so the honest figure is 1.5 *unrequested claims* per clean commit, of which an
unknown share are real. 3.28 million tokens, $0 billed — noise on the harness, detection on the
API, which is ADR-0005's operational split finally used rather than argued.
[`docs/step7c-clean-corpus.md`](docs/step7c-clean-corpus.md).

**Second replay, 2026-08-23: six Java cases from two open-source repositories, 6 of 6 — and
the number is not a detection rate.** The cases were fix commits replayed backwards, so the
correct code sat on the minus side of every diff and the lenses read it there. What the run does
establish is that the finding contract ports to a language it has never seen: 64 calls against
Java with an empty context pack, every reply schema-valid and every snippet anchored.
[`docs/step7-first-run.md`](docs/step7-first-run.md).

**First replay, 2026-08-23: 1 detected of 4, $7.05.** The three misses share a shape — every one
is a defect whose wrongness is invisible in the text, where the hit was a diff that contradicted
itself. **The blind lenses find contradictions, not omissions**, and an omission has no anchor to
quote. The run also found two live defects in RSquad's own gate.
[`docs/first-evaluation.md`](docs/first-evaluation.md).

```bash
rsquad gate                                  # HEAD against its parent
rsquad gate --base master --strict           # against the merge base with master
rsquad gate --head 4164d03                   # replay on a past commit
rsquad gate --replay 20 --repo ../other      # aggregate over the last 20 commits

rsquad review                                # what would be sent, and to how many lenses
rsquad review --confirm                      # actually spend
rsquad review --lens repro --confirm         # one lens only
rsquad review --spec docs/specs/03.md --confirm   # give step [1] a document to check against
rsquad review --no-refute --confirm          # skip step [3], cheaper and weaker

rsquad evaluate --repo ../ai-video-digest        # which cases are scorable, and why the rest are not
rsquad evaluate --repo ../ai-video-digest --confirm   # replay them and lay the evidence out
rsquad evaluate --case head-overwritten-before-use --repo ../x --confirm   # one case, bounded spend
```

`evaluate` writes a report and **no detection rate**. Whether a finding anchors at the defect is
mechanical; whether its consequence is the actual failure is not, so each case carries a verdict
line for a human. It states its denominator, and lists every case it excluded with the reason.

### Two transports

`rsquad review` calls the Claude API directly. `rsquad export` / `rsquad ingest` write the same
work as a job on disk that **any** harness can run — a Claude Code workflow, a Cursor rule, a
shell loop, a person:

```bash
rsquad export ./job --head HEAD --repo .      # every prompt rendered, one task per call
#   <harness runs each task, writes <task id>.json beside it>
rsquad ingest ./job                           # validates, guards, writes the refutation round
#   <harness runs those too>
rsquad ingest ./job                           # writes the queue
```

Everything that makes a finding trustworthy stays on this side of the seam. The harness makes a
model call; it cannot change what a lens was asked or what its answer must satisfy.

**One caveat, in the driver's own header too.** A harness agent has file-reading tools, so a
blind lens is blind only by instruction — unlike the API path, where a test asserts there is no
channel for a spec at all.

Measured across 46 harness agents and 119 file operations: **not one read a file outside the
job.** That is an observation and not a property, and relocating the job does not make it one —
the reach is the agent's tool permissions, not the job's neighbours. A real fix confines the
agent, which is a sandbox and not a change to RSquad. The transcript check that produced this
number is free and repeatable, and it makes a breach detectable rather than impossible.
See [`docs/blindness-under-a-harness.md`](docs/blindness-under-a-harness.md) and ADR-0008.

`rsquad review` is a dry run unless you pass `--confirm`, and the dry run prints **no cost
estimate**. Two invented cost constants from the source project are sitting in
`evaluation/defects.yaml`; this tool reports what was billed, not what it guessed.

The credential is read from `ANTHROPIC_API_KEY`, or from a `.env` at the repository root, or
from whatever `RSQUAD_ENV_FILE` points at — so a key you already keep for another project can be
reused in place instead of copied. A secret duplicated is a secret with two places to leak from.

`--replay` is not a convenience: replaying the gate over history is how you measure what it
would actually have caught, on data nobody arranged. Do that before trusting it.

## Porting to another stack

Summarised here; the operational version, with a per-stack catalogue of traps and an acceptance
criterion for a port, is [`docs/porting.md`](docs/porting.md).

The core knows no language. Everything stack-specific fits into seven questions
(`gate/adapters/base.py`):

1. Which files in the diff are tests?
2. Which test functions are new or modified? (by comparing function bodies across revisions)
3. How do we run that subset so it emits JUnit XML?
4. **How do we guarantee the code under test is the base's?**
5. Which base failures mean "the symbol does not exist yet" rather than "the test caught
   something"?
6. Which definitions elsewhere in the repository does a change reference?
7. What will the runner call the module a test lives in?

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

**Question 7 is what the runner calls a test's module** — `tests/sub/test_beta.py` becomes
`tests.sub.test_beta` in pytest's JUnit `classname`, and the core matches it as a dotted prefix
so a method in a class still resolves. Without it a test name carries no file, and two files each
holding a `test_roundtrip` are the same test. Its default returns the path unchanged, so a stack
nobody has taught this falls back to bare-name matching: today's noise, never silence.

**Assume an eighth exists.** Five, six and seven all arrived after the protocol was declared
complete — one from a crash, one from a conversation, one from the squad reviewing this gate's
own ancestor.

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
| [0007](docs/adr/0007-the-conformance-lens-quotes-or-stays-quiet.md) | the conformance lens quotes its requirement, or stays quiet |
| [0008](docs/adr/0008-the-seam-is-a-job-on-disk.md) | the second transport is a job on disk, not a workflow |

### The written-down parts

| | |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | why the shape is what it is, and what degrades first when you move it |
| [`docs/porting.md`](docs/porting.md) | the seven questions in operational detail, and a per-stack catalogue of traps |
| [`docs/evaluation.md`](docs/evaluation.md) | how a detection rate would be measured, what it costs, and what it cannot prove |
| [`docs/gate-baseline.md`](docs/gate-baseline.md) | what the gate actually catches, measured over 20 commits |
| [`docs/transport-comparison.md`](docs/transport-comparison.md) | eight runs across both transports on one commit |
| [`docs/blindness-under-a-harness.md`](docs/blindness-under-a-harness.md) | 46 agents, 119 file operations, and a mitigation that did not work |
| [`docs/extraction.md`](docs/extraction.md) | the extraction from the source project, verified function by function |
| [`docs/first-run.md`](docs/first-run.md) | the first paid run, and the five defects it found in this repository |
| [`docs/first-evaluation.md`](docs/first-evaluation.md) | the first replay against ground truth: 1 of 4, and what the misses have in common |
| [`docs/step7-first-run.md`](docs/step7-first-run.md) | six Java cases, 6 of 6, and why that number measures the wrong thing |
| [`docs/step7b-first-run.md`](docs/step7b-first-run.md) | 15 of 19 on real introducing commits, and no sign of memorisation |
| [`docs/step7c-clean-corpus.md`](docs/step7c-clean-corpus.md) | what the squad says about code nobody has complained about |
| [`docs/transport-calibration.md`](docs/transport-calibration.md) | the same four cases on both transports — *superseded* |
| [`docs/transport-calibration-19.md`](docs/transport-calibration-19.md) | all nineteen cases on both transports, for nothing, and they agree on eighteen |
| [`docs/step7d-forty-cases.md`](docs/step7d-forty-cases.md) | thirty-eight cases on the harness: 31 detected, and the widening cost nothing |

## License and provenance

The gate began in a private project as `tools/portail_tests.py` and was extracted here,
translated, and verified equivalent function-by-function across 20 real commits before any
behaviour was deliberately changed. See `docs/`.
