---
name: rsquad-review
description: Review a committed change with RSquad - blind lenses, an adversarial refuter and a ranked queue - running every model call as an isolated, read-only subagent of this host. Use when the user asks for an RSquad review of a commit, a branch or a range of commits.
---

# RSquad review

You are the **driver**, not the reviewer. RSquad's command line decides what is reviewed, what
each reader is asked, what a reply must satisfy, what survives and in what order. Your job is to
run its tasks in isolated subagents, save their replies untouched, and hand the queue to the
user. Read `docs/writing-a-harness-driver.md` in the RSquad repository if anything below is
unclear; this skill is one driver written against that contract.

## Rules that do not bend

1. **You do not review.** Do not read the code under review, do not add, remove, merge, reword
   or re-rank a finding, and do not give your own opinion of the change alongside the queue.
   The queue is the answer.
2. **Every task runs in a fresh subagent, with read-only tools.** One task per subagent, never
   two, and never in your own context: the lenses are only independent if they never see each
   other, and the refuter only inherits no framing if it never sees the finder.
3. **A reply is saved exactly as the subagent returned it.** Never repair JSON, never re-run a
   task to get a better answer, never fill in a reply for a subagent that failed. `ingest`
   validates everything and counts what is missing or malformed; a repaired reply would hide
   that count.
4. **Coverage comes from RSquad, never from you.** Repeat what the command line printed about
   files not reviewed. Do not say the change was "fully reviewed".
5. **Subagents read their task file and its schema, and nothing else.** That is the only thing
   keeping a blind lens blind on this path (ADR-0010). Say so if the user asks how blind it is.

## Steps

### 0. Preconditions

- `python -m rsquad --help` must work. If not, the user installs it: `pip install -e <path to
  the rsquad checkout>`. Stop until they have.
- RSquad reviews **commits**. Uncommitted changes are not seen; tell the user if the working
  tree is dirty, and do not commit for them.

### 1. Choose the range

The user names a base, a head, or a branch. Otherwise: head is `HEAD`, base is the merge base
with the repository's main branch. If HEAD *is* the main branch, review HEAD against its parent
(omit `--base`). State the range you chose in one line.

### 2. Export

Pick a job directory **outside the working copy** (the system temp directory, e.g.
`<tmp>/rsquad-<12 characters of the head sha>`), so nothing next to the tasks invites a
subagent into the repository.

```
python -m rsquad export <job> --base <base> --head <head>
```

Optional flags, only when the user asks for them:

- `--spec <document>`, repeatable: what the change was supposed to do, for the conformance lens.
  The commit message is always included.
- `--model <id>` for the lenses and `--refute-model <id>` for the refuter. They default to
  Sonnet and Opus, the split measured at 30/38 against 31/38 for Opus throughout
  (`docs/step8-tiered-models.md`). Do not move the refuter to a cheaper model on your own: it is
  the step whose mistakes leave the least trace.
- `--lens <name>` repeatable, `--no-conformance`, `--context` (the context pack, off by default).

If the command prints `nothing readable changed`, report the files it listed as not reviewed and
stop. No model is called.

### 3. Say what it will cost, and wait

Read `<job>/manifest.json`. Tell the user, in three lines at most: the number of tasks, how many
per lens, the model each runs on, and the files not reviewed with their reasons (from the export
output). Add that refutation is a second round of one task per surviving finding, unknown until
round 1 is read. **Wait for their go-ahead.** The command line has a dry run for the same reason.

### 4. Run a round

For every entry in `manifest.json` → `tasks`, start one subagent:

- **fresh context**, **read-only tools** (reading files is all it needs). Under Claude Code, use
  the `rsquad-task` subagent (`.claude/agents/rsquad-task.md`): it has the file-reading tool and
  nothing else, which also keeps each task's fixed cost low. Elsewhere, any read-only subagent;
- on the model named by the entry's `model` field (fall back to the manifest's top-level
  `model`). Map the id to the host's choice of tier — an id containing `opus` to the Opus tier,
  `sonnet` to Sonnet, `haiku` to Haiku. If the host cannot choose a model per subagent, run it on
  what you have and **tell the user which model actually ran**: a review on another model is
  still a review, but it does not reproduce RSquad's published numbers;
- independent tasks run in parallel where the host allows it.

Give each subagent exactly this, with the placeholders filled in:

> You are running one task of a code review job.
>
> 1. Read `<job>/round-<round>/tasks/<id>.md`. It is a complete instruction, including the code
>    under review. Follow it exactly.
> 2. Read `<job>/schema/<contract>.json`. Your answer MUST validate against it: enumerated
>    fields are closed, every required field is required, and no extra field is allowed.
>
> Read no other file. Everything you need is in those two, and reaching for the repository would
> answer a different question than the one the task asks.
>
> Your final message is your answer: raw JSON and nothing else — no prose, no markdown fence.

When a subagent finishes, write its final message, unchanged, to
`<job>/round-<round>/results/<id>.json`. If it produced nothing, write nothing.

### 5. Ingest

```
python -m rsquad ingest <job> --out <job>/queue.md
```

- If it says it wrote refutation tasks, that is round 2: go back to step 4 with the new
  manifest, then ingest again. Do not ask again before round 2 unless the user asked you to.
- Otherwise it has written the queue.

### 6. Hand over the queue

Give the user the path of `queue.md`, the counts line `ingest` printed, and the queue's
findings as they appear in it, in order. Name any lens that failed and any task with no reply
or a malformed one. Nothing else: no summary verdict on the change, no extra findings.
