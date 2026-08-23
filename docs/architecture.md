# Architecture

**What this document is for.** The README says what RSquad is and how to run it. This one says
why it has this shape, which parts survive being moved to another project, and which parts
degrade first — because that second question is why the tool became a separate repository rather
than a script inside the project that needed it.

> **It has run on one stack, one repository, one language.** Python with pytest, against a
> private project of 52 commits. Every number below names where it came from. Nothing here has
> been validated on a second stack, and the section that would need it most — the porting
> catalogue — is marked as hypotheses throughout (`porting.md`).

## The shape: three layers, and a one-way trust gradient

```
        MECHANICAL                 MODEL                  HUMAN
  ┌───────────────────┐   ┌─────────────────────┐   ┌──────────────┐
  │ [0] gate          │   │ [1] conformance     │   │ [4] queue    │
  │     the guards    │──▶│ [2] blind lenses    │──▶│              │
  │     the schema    │   │ [3] refutation      │   │              │
  └───────────────────┘   └─────────────────────┘   └──────────────┘
     blocks a merge          never blocks             decides
     deterministic           sampled                  accountable
```

Each layer may constrain the one to its right and never the reverse. The gate decides whether the
model layer runs at all. The schema and the two guards decide which of the model's outputs are
allowed to exist. The queue orders human attention and claims nothing else.

**This gradient is the architecture.** Everything else follows from it:

- A model call can be wrong, so nothing downstream of one may block a merge.
- A guard cannot be wrong in an interesting way, so it may delete a finding without appeal.
- A human is accountable, so the last step is a ranked list and not a verdict.

Invert any of those and you get a familiar failure. A model-gated CI that blocks on opinion gets
switched off. A guard that "flags for review" instead of dropping shifts the filtering cost onto
the reader — which is the cost the tool exists to reduce.

## The five steps: what each carries, and what it costs

| Step | Agents | Blocks? | What only it can do | Cost |
|---|---|---|---|---|
| [0] gate | 0 | **yes** | does a new test fail on the code as it was? | one test run |
| [1] conformance | 1 per file | no | compare the diff against a stated intent | 1 call |
| [2] blind lenses | 4 per file | no | say what the code does, unprimed by intent | 4 calls |
| [3] refutation | 1 per finding | no | make finding expensive instead of free | n calls |
| [4] queue | 0 | no | order attention, group duplicates | free |

### [0] The gate is first because everything else assumes it passed

Letting a model comment on code that does not compile produces confident noise, and at the queue
that noise is indistinguishable from signal. But the ordering argument is the weaker one. The
gate's real justification is a check **nothing else in the pipeline can perform**: revert the
patch, re-run the new tests, see whether they fail. A test that passes before and after does not
test the change. A green suite does not see it, coverage does not see it — it rises either way —
and no reviewer, human or model, reliably sees it either.

It answers that with zero judgement, which is why it is the only step allowed to block.

**Its limits are also the best measured thing here.** Over 20 real commits it can say nothing at
all about **79 % of new test functions** (`gate-baseline.md`). That is not a defect to fix; it is
the shape of the check. A test for a function that did not exist before can only fail by not
finding it, and "not found" discriminates nothing. The gate covers *modifications*.

The number matters more for deployment than for design: **a gate reporting "0 suspect" is usually
reporting "nothing could be checked"**, and any interface that hides the examined count next to
the verdict lies by omission.

### [1] and [2] are the same machinery pointed at two different questions

The conformance lens gets a stated intent — the commit message, plus any document named with
`--spec`, never anything discovered by walking a directory. The blind lenses get none of it.

**A reviewer who knows the intent checks conformance to the intent.** That is a real job and step
[1] does it. If the other four also hold the intent, you have four agents doing that one job
while believing they are doing four different ones — and the correlated blind spot is invisible,
because they agree.

So blindness is not a preference about prompt hygiene. It is what makes the second question —
*what does this code actually do, and where does it break?* — a different question at all.

**It is enforced structurally, and the two transports enforce it differently.** On the API path
`request()` is a pure function of `(unit, lens, model)`: there is no parameter through which a
specification could arrive, and a test asserts the signature. On the harness path the agent has
file-reading tools, and the instruction not to use them is an instruction. The fix has the same
shape as the original: run the harness against a job directory with no checkout beside it
(ADR-0002, ADR-0008).

### [3] Refutation exists to make finding expensive

An agent asked for problems supplies problems. The count is a property of the prompt, not of the
code. Refutation breaks that by making the two operations asymmetric: **finding is free,
surviving is not.**

Three things make it work, each a decision (ADR-0006):

- The refuter reads the finding and the code, and **not** which lens produced it, nor any other
  finding. Framing does not travel.
- Doubt refutes. The default is that the claim dies.
- A refutation that cannot anchor its own evidence refutes nothing. Otherwise a hallucinating
  refuter silently deletes real findings, and the failure is invisible — the queue simply gets
  shorter, which reads as success.

**Its own cost has not been isolated.** How many *true* findings the refuter kills is the number
that decides whether it earns its calls, and measuring it needs labelled cases — the deferred
work in `evaluation.md`. Across seven runs it has killed nothing, which is a weak signal in one
direction and not a measurement.

### [4] The queue ranks and does not decide

Findings are grouped by location, ranked by severity, and rendered with their evidence attached.
Representatives are chosen **one per claim shape**, because a conformance account and a
reproduction account of the same line are different information, and picking a single
representative buried one of them — found by running it.

The constraint is inherited: no threshold separates well enough to decide alone. The sibling
project reached the same conclusion about clustering by embedding and turned its automatic
grouping into a review queue for the same reason.

## What is portable, and what is not

| Portable — knows no language | Stack-specific |
|---|---|
| worktree, merge base, JUnit parsing, verdicts | which files are tests |
| the finding/verdict/conformance schemas | which test functions changed |
| both guards (anchoring, reproduction-or-nothing) | how to run a subset emitting JUnit XML |
| chunking a diff into units | **how to force the base's code under test** |
| ranking and grouping | which base failures mean "symbol does not exist yet" |
| both transports | resolving a symbol to its definition |

The right-hand column is the adapter protocol: six questions, one abstract class, one
implementation today. `porting.md` covers it in operational detail, including the catalogue of
per-stack traps — **explicitly labelled hypotheses**, since only the Python one has been executed.

Two of those six questions arrived *after* the protocol was declared complete. Anyone porting
should assume a seventh, and that only execution will surface it: every defect found in the
original gate implementation was found by running it, none by reading it.

## Two transports, one core

The same lens definitions, schemas, guards and ranking run behind two shapes:

- **`rsquad review`** — direct API calls. Blindness is a property a test can assert; runs are
  reproducible and therefore measurable; needs a key.
- **`rsquad export` / `rsquad ingest`** — the same work written as a job on disk that any harness
  can run: a Claude Code workflow, a Cursor rule, a shell loop, a person with a chat window.
  Needs no key. Blindness is an instruction unless the job runs alone on a filesystem.

Everything that makes a finding trustworthy stays on RSquad's side of the seam. The harness
contributes exactly one thing — a model call — and cannot change what a lens was asked or what
its answer must satisfy. Replies are validated at ingest regardless of what the harness could or
could not constrain: the mechanical constraint moves, it does not disappear.

**Seven runs on one commit, and the honest summary is that the choice is operational.** Both
transports returned the same set of places, run after run. The reproducibility argument ADR-0002
made for the API path lost its empirical support the moment configurations were held constant.
What survives is blindness a test can assert — and the cost, which points the other way: the
harness spends four to twenty times the tokens for the same work, and those tokens are invisible
under a subscription while an API key needs a chain of approvals (`transport-comparison.md`,
ADR-0005).

That is why ADR-0005 stays `proposed`. It is not indecision. On this evidence the two transports
are close enough that the deployment constraint decides — and the deployment constraint is not a
property of the tool.

## Deploying it where people work

This section has the least measurement behind it and the highest chance of deciding whether the
tool survives its first month.

### Confidentiality

The squad sends **source code and commit messages** to a model. Nothing else: no binaries, no
repository history beyond the diff and the files it touches, and no directory is ever walked to
find context — the context pack follows symbols the changed lines name, which is also what keeps
it from reaching a specification.

Three consequences for a workplace:

- **The harness transport moves the question, it does not remove it.** A subscription-hosted
  agent still reads the code. What changes is who signed the contract, not what crosses.
- **The job directory is a readable artifact.** `rsquad export` writes every prompt, every unit
  and every context pack as plain files. Anyone who must approve the tool can read exactly what
  would be sent, before anything is sent. In an approval conversation that is worth more than any
  description of the tool.
- **A dry run costs nothing and sends nothing.** `rsquad review` without `--confirm` reports what
  would be sent, and to how many lenses.

### CI, and the two costs that are not the API bill

**Latency.** Steps [1] and [2] are one call per lens per file — parallel, bounded by the slowest.
Step [3] is a second round that cannot start until the first finishes, because a refuter needs a
finding. A pipeline that blocks a merge on this pays two model round-trips of wall clock. A
pipeline that comments does not care.

**Fan-out.** The unit is one file, so cost scales with files touched, not with repository size. A
20-file change is 20 × (4 + 1) calls before refutation. Bound it explicitly — by path, by lens,
or by skipping refutation — rather than discovering the bill.

**The third cost is the one that ends deployments: attention.** A queue nobody reads is worse
than no queue, because it turns a real finding into evidence that the tool cries wolf.

### The annotation phase is not optional

Expect one, and budget it. Two exemption markers exist because a measured run needed both:

- `characterization` — asserts a refactor changed nothing, so it *must* pass on the base.
- `guard` — asserts something does **not** happen; the base does not do it either, so it cannot
  fail there by construction.

On a real sample, six flagged tests were one genuine finding — an assertion loosened from `== 5`
to `>= 5`, exactly the failure mode the gate exists for — against five tests of those two kinds.
**Without the markers that gate produces five false positives out of six**, is switched off inside
a week, and takes the real finding with it.

On an existing codebase the markers do not exist yet. Someone has to add them, and the honest way
to schedule that is: run the gate in report-only mode first, annotate what it flags, and only
then let it block.

### The rule that keeps it alive

**The mechanical blocks. Opinions comment.**

The gate is deterministic, so a red gate is a fact and arguing with it is arguing with a test run.
Everything downstream of a model call is a suggestion, and a suggestion that blocks a merge
teaches the team that the tool is an obstacle. The two must never be reported through the same
channel: a reader who learns to dismiss one learns to dismiss both.

## What degrades first when you move this

In order, most fragile first. This is the real answer to "does it generalise".

1. **The conformance lens [1].** It needs a stated intent, and most repositories do not have one.
   The commit message is the floor, and it is often one line. It degrades gracefully — no intent,
   no step — but it is the first thing to lose.
2. **The gate's coverage [0].** 21 % here. The figure depends on how much of a change is
   *modification* rather than *addition*, and agent-written code skews hard toward addition,
   which is the least covered case.
3. **The context pack.** 65 % of changed files resolve at least one definition, 3.2 on average —
   and both numbers come from one language's import rules. A stack where resolution is dynamic or
   configuration-driven will resolve less.
4. **Exemption markers.** They must exist in the codebase before the gate is useful, and adding
   them is human work proportional to the test suite.
5. **The blind lenses [2] and refutation [3].** These are the most portable things here: they need
   a diff, a numbered file and a schema. They do not know what language they are reading.

Note the inversion. **The model-driven steps port most easily; the mechanical ones port least.**
That is the opposite of the intuition, and worth stating plainly to anyone who assumes the agents
are the hard part.

## What this architecture does not address

- **No architectural findings.** It reads a diff, not a system. Nothing here notices that a module
  should not exist.
- **Correlated blind spots.** The lenses share the training distribution of the model that wrote
  the code they are reading. Four lenses are four questions, not four independent observers.
- **The model has never been benched for this task.** `claude-opus-5` is a reasoned starting
  point. The criterion that should decide it is the detection rate on labelled defects, and that
  set is a smoke test today (`evaluation.md`).
- **Falsifiability is not relevance.** The gate can confirm that a test discriminates perfectly
  and proves a property nobody needs. No mechanical check closes that.
