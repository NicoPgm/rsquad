# Writing a harness driver

A driver runs the tasks RSquad exported and writes the replies back. That is the whole job.
There are two drivers in this repository — `harness/claude-code.workflow.js`, the batch driver
used for evaluation, and the skill in `.claude/skills/rsquad-review/`, which has the host agent
run each task in a read-only subagent and save its reply (ADR-0009) — and both are examples, not
the interface. **A Claude Code workflow does not run in Cursor**, which is
why the seam is a directory on disk and not an SDK (ADR-0005, ADR-0008).

This document is written to be read by whoever is building the second driver, human or agent, so
that nobody has to reconstruct the contract from the source.

## The contract, in full

```
<job>/
  manifest.json                     what to run, and what each reply must satisfy
  schema/<contract>.json            JSON Schema, one per contract used in this round
  round-<n>/
    tasks/<task id>.md              a complete, self-contained prompt
    results/<task id>.json          ← the driver writes this, and nothing else
```

**The driver reads `manifest.json` and writes `round-<n>/results/<id>.json`. Nothing else.**
It does not create directories, rename anything, or touch `tasks/`.

### The loop

```
manifest = read <job>/manifest.json
n        = manifest.round
for task in manifest.tasks:
    prompt = read <job>/round-<n>/tasks/<task.id>.md
    schema = read <job>/schema/<task.contract>.json
    reply  = <your model>(prompt, constrained to schema)
    write reply as raw JSON to <job>/round-<n>/results/<task.id>.json
```

Tasks are independent. Order does not matter, and running them concurrently is expected — the
Claude Code driver runs a whole job in parallel. A task that fails should simply leave no file;
see *Failure is a first-class outcome* below.

### `manifest.json`

| field | meaning for the driver |
|---|---|
| `version` | `1`. A driver may refuse anything else. |
| `round` | `1` = the lenses, `2` = refutation. It names the directory: `round-<round>/`. |
| `model` | the model RSquad intends for the lenses. Superseded by `task.model` where a task carries one. |
| `tasks[]` | `id`, `contract`, `lens`, `file`, `model`; refutation tasks also carry `finding`, the claim under test. **`task.model` is the one to honour** (lenses and refuter may differ, ADR-0009), and record what you actually used if you cannot — see *The model is not decoration*. |
| `refute_model`, `context` | RSquad's own bookkeeping for the next round. Ignore. |
| `base`, `head`, `repo`, `specs`, `path`, `case` | RSquad's own bookkeeping for `ingest`. **A driver has no use for these.** The repository a task may search is the job's own `repo/`, never the one `repo` names. |
| `carried` | present in round 2; findings that get no refuter and ride to the queue. Not tasks. Ignore. |

`task.id` is already filesystem-safe: `<lens>--PR` for a lens, which reads every file of the
change in one task (ADR-0011), and the file path with separators replaced for the others. Use it
verbatim as the filename. Do not sanitise it further, or `ingest` will not find the reply.

### The three contracts

`task.contract` is one of `finding`, `conformance`, `verdict`. The authoritative schema is the
file in `schema/`; this table is a summary so a driver author knows what shape to expect.

| contract | reply shape | required per item |
|---|---|---|
| `finding` | `{"findings": [...]}` | `file`, `line`, `snippet`, `kind`, `severity`, `inputs`, `consequence` |
| `conformance` | `{"findings": [...]}` | `file`, `line`, `snippet`, `requirement`, `mismatch`, `kind`, `severity` |
| `verdict` | a single object | `verdict`, `reason`, `evidence_line`, `evidence_snippet` |

`kind`, `severity` and `verdict` are **closed enumerations**. The values are in the schema file.
A value outside the list is not a near miss, it is a rejected reply.

`{"findings": []}` is a valid and meaningful answer: it means *this lens read the change and has
nothing to say*. It is not the same as no file, and the difference is load-bearing — see below.

## What a driver must never do

The seam exists so that everything which makes a finding trustworthy stays on RSquad's side. A
driver that does any of the following has moved the line and the results stop being comparable
to anything else this project has measured:

- **judge, filter or drop a finding.** `ingest` runs the two mechanical guards. That is its job.
- **rank, sort or renumber.** `ranking` does that, afterwards.
- **edit the prompt** — no preamble, no "be concise", no system message of your own. The task
  file is the prompt, whole.
- **merge tasks into one call.** Lenses are blind to each other by construction; batching two
  lenses into one context destroys the property the whole design rests on.
- **point an agent at another repository.** A task may read and search the job's `repo/`, the
  tree at head that `export` wrote, and says so itself. The working copy, its history and its
  uncommitted files are a different change from the one under review.

## Failure is a first-class outcome

**A task that could not be answered must leave no file.** Do not write `{}`, do not write
`{"findings": []}`, do not write an error object.

`ingest` distinguishes three cases and reports each as a number:

| on disk | `ingest` calls it | what it means |
|---|---|---|
| no file | `missing` | the driver could not speak |
| file, invalid against the schema | `malformed` | the model spoke and did not conform |
| file, valid | ingested | the reply enters the guards |

Saying nothing and being unable to speak look identical in a queue, and only one of them means
the code is fine. A driver that writes `{"findings": []}` on failure converts an outage into a
clean bill of health, silently.

## Structured output is best-effort here, and that is measured, not assumed

On the API transport RSquad forces the schema at generation time. Across the seam it cannot, so
`ingest` validates every reply against the same schema and drops what does not conform. **The
constraint never disappears; it moves from generation time to ingest time**, where it costs a
wasted call instead of a wrong finding.

Practical consequence for a driver: use your runtime's structured-output feature if it has one
(most do — OpenAI-style `response_format`, Gemini's `responseSchema`, Anthropic's
`output_config.format`). Hand it the schema file as-is. If it has none, ask for raw JSON with no
prose and no markdown fence, and expect a higher `malformed` count. Both are legitimate; only
one is cheaper.

## The two guards, so a driver author knows what gets rejected downstream

Neither is the driver's responsibility, but knowing them explains most rejected replies:

- **Anchoring.** `snippet` must appear in the file under review within **3 lines** of `line`,
  compared insensitively to whitespace. Rejected with *"snippet does not appear within 3 lines of
  the claimed line"*. Quoting from the context pack instead of from the file under review trips
  this, which is why the pack says so in its own header.
- **Reproduction or nothing.** `inputs` and `consequence` must be present and non-empty. "This is
  fragile" is rejected mechanically rather than by judgement.

Across the Java campaign every run refused **zero** until the tests-lens arm, which refused
**three**, all anchoring. That is the measured base rate, and it is why a driver that suddenly
produces many rejections is reporting something about its own model or prompt handling rather
than about the code under review.

## Two rounds, and the second one exists

Refutation needs a finding, so it cannot be exported alongside the lenses. The sequence is:

```
rsquad export <job> ...          # writes round-1
<driver runs round-1>
rsquad ingest <job>              # validates, guards, writes round-2
<driver runs round-2>            # same loop, round is now 2
rsquad ingest <job>              # writes the ranked queue
```

A driver that only ever handles round 1 works, and produces a queue of uncontested suspicions.
That is a real option — `ingest --no-refute` names it — and it is roughly half the cost and
meaningfully weaker. Say which one you ran.

## The model is not decoration

`task.model` records the model RSquad intends for that task; jobs written before 2026-11-20
carry only `manifest.model`, so fall back to it. Until 2026-08-25 the Claude Code driver
ignored it and inherited whatever the session was set to; the two agreed for an entire campaign
by coincidence, and a measurement that holds the model constant by coincidence is not holding it.

If your runtime lets you choose, honour the field. If it does not — a Cursor agent runs whatever
Cursor is configured with — then **record what actually ran**, next to the results, in whatever
form you like. Without that, a comparison between two runs is a comparison of two unknowns.

Every number published in `docs/` before step 8 is `claude-opus-5` at effort `high`; step 8 (`docs/step8-tiered-models.md`) is Sonnet lenses with an Opus refuter; since ADR-0011 both
are Opus by default. A run on another model
answers *"does this find real things in our code"*. It does not reproduce those figures and
should not be reported as if it did.

## Blindness degrades under a harness, and it is worth knowing how much

On the API transport a blind lens is blind because its request has no channel through which a
specification could arrive, and a test asserts it. Under a harness the lens is an agent with
file-reading tools: *"do not read the spec"* in a task file is an instruction, not a property.

Since ADR-0011 the job holds the tree at head in `repo/`, and every task tells its reader to
search it. A specification checked into the repository is then within a blind lens's reach. What
stays out is the history, the commit message and anything uncommitted — provided the driver runs
against a job directory **outside the working copy**.

Measured before ADR-0011, across 46 harness agents and 119 file operations: not one read a file
outside the job.
That is an observation, not a property. The transcript check that produced it is free and
repeatable, and it makes a breach detectable rather than impossible. See
[`blindness-under-a-harness.md`](blindness-under-a-harness.md).

## Checking a new driver before trusting it

There is no test suite for drivers, and there cannot be one — the driver is where the model
lives. Three checks, in increasing cost:

1. **One task by hand.** Export a job for a single-file commit (5 tasks), run one, and confirm
   `ingest` reports `1 finding(s), 0 dropped, 0 missing, 0 malformed` — or a deliberate zero.
   Most driver bugs are a wrong path or a mangled task id, and they surface here.
2. **A whole job.** `missing` and `malformed` should both be 0. A non-zero `malformed` is a
   structured-output problem in the driver, not a model quality problem.
3. **A commit whose defect you already know**, and read whether the queue names it. That is what
   `evaluation/` does at scale, and one case is enough to tell a working driver from a plausible
   one.

`harness/claude-code.workflow.js` is 149 lines including its long header. A second driver should not
be larger.
