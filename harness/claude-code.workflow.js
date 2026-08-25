/*
 * RSquad — Claude Code driver for the harness transport.
 *
 *   rsquad export <job> --head <rev> --repo <path>
 *   /workflows  →  this script, with args: { job: "<path>" } or { jobs: ["<path>", ...] }
 *   rsquad ingest <job>          (twice: once for the lenses, once for the refutations)
 *
 * This script does one thing: it runs the tasks RSquad wrote and saves the replies. It does not
 * decide what a lens is asked, what a reply must satisfy, or what survives — all of that stays
 * in RSquad, on the other side of the seam (ADR-0005, ADR-0008).
 *
 * **The model comes from the manifest, and did not always.** RSquad records the model it
 * intends; until 2026-08-25 this runner ignored the field and every task inherited whatever
 * the session happened to be. The two agreed across the whole Java campaign — by coincidence,
 * not by construction — so nothing ever looked wrong. It reads the field now, which is what
 * lets one measurement hold the model constant while another deliberately varies it.
 *
 * ── READ THIS BEFORE TRUSTING THE OUTPUT ──────────────────────────────────────────────────
 *
 * On the API transport a blind lens is blind because its request has no channel through which a
 * specification could arrive, and a test asserts the signature (ADR-0002). Here the lens is an
 * agent with file-reading tools. **It can read anything on the machine**, and "do not read the
 * spec" in a task file is an instruction, not a property.
 *
 * The mitigation is structural, not textual: **run this against a job directory and nothing
 * else.** A task file already carries the diff, the numbered file and the resolved context, so
 * an agent needs no repository to do its work. Copy the job somewhere with no checkout beside
 * it, and blindness is restored by there being nothing to peek at.
 *
 * Run it inside a working copy and the blind lenses are blind only by good manners. That is a
 * real difference between the transports and it belongs in the comparison, not in an argument.
 * ──────────────────────────────────────────────────────────────────────────────────────────
 */

export const meta = {
  name: 'rsquad',
  description: 'Run an exported RSquad review job: one agent per task, replies written back',
  whenToUse: 'After `rsquad export`. Pass args: { job: "<path>" } or { jobs: ["<path>", ...] }',
  phases: [
    { title: 'Manifest', detail: 'read the job manifest and list the tasks' },
    { title: 'Tasks', detail: 'one agent per task, reply written back as JSON' },
  ],
}

// One job or many. The clean-commit corpus is one job per commit, and running them one
// invocation at a time would be a dozen round trips for a single measurement.
const jobs = args && (args.jobs || (args.job ? [args.job] : null))
if (!jobs || !jobs.length) {
  throw new Error('pass args: { job: "<path>" } or { jobs: ["<path>", ...] }')
}

const MANIFEST = {
  type: 'object',
  additionalProperties: false,
  required: ['round', 'model', 'tasks'],
  properties: {
    round: { type: 'integer' },
    model: { type: 'string' },
    tasks: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['id', 'contract'],
        properties: { id: { type: 'string' }, contract: { type: 'string' } },
      },
    },
  },
}

const DONE = {
  type: 'object',
  additionalProperties: false,
  required: ['id', 'written', 'note'],
  properties: {
    id: { type: 'string' },
    written: { type: 'boolean' },
    note: { type: 'string' },
  },
}

const name = (job) => job.replace(/[\\/]+$/, '').split(/[\\/]/).pop()

// The manifest records a full model id; this runner names tiers. An id nobody here recognises
// returns undefined, which inherits the session's model — the old behaviour, and the reason this
// gap went unnoticed for the whole Java campaign: the manifest said `claude-opus-5`, the harness
// never read it, and the session happened to be Opus. It agreed by luck, not by construction,
// and a measurement that holds the model constant by luck is not holding it.
const TIERS = ['opus', 'sonnet', 'haiku', 'fable']
const alias = (model) => TIERS.find((tier) => (model || '').includes(tier))

const instruction = (job, round, task) =>
  `You are running one task of a code review job.\n\n` +
  `1. Read ${job}/round-${round}/tasks/${task.id}.md — it is a complete instruction, ` +
  `including the code under review. Follow it exactly.\n` +
  `2. Read ${job}/schema/${task.contract}.json. Your answer MUST validate against it: the ` +
  `enumerated fields are closed, every required field is required, and no extra field is ` +
  `allowed.\n` +
  `3. Write your answer as raw JSON — no prose, no markdown fence — to ` +
  `${job}/round-${round}/results/${task.id}.json\n\n` +
  `Read no other file. Everything you need is in those two, and reaching for the ` +
  `repository would answer a different question than the one the task asks.\n\n` +
  `Then return the task id, whether you wrote the file, and one short note.`

phase('Manifest')
log(`${jobs.length} job(s)`)

// A pipeline rather than a barrier: a job's tasks start as soon as its own manifest is read,
// instead of every job waiting for the slowest manifest.
const runs = await pipeline(
  jobs,
  (job) => agent(
    `Read the JSON file at ${job}/manifest.json and return its "round" number, its "model" ` +
    `string, and for every entry in its "tasks" array, that entry's "id" and "contract". Do ` +
    `not read anything else and do not summarise: return every task.`,
    { label: `manifest:${name(job)}`, schema: MANIFEST, effort: 'low', phase: 'Manifest' },
  ),
  async (listing, job) => {
    if (!listing || !listing.tasks.length) {
      log(`${name(job)}: no tasks in manifest`)
      return { job, round: null, written: [], failed: [] }
    }
    const round = listing.round
    const model = alias(listing.model)
    log(`${name(job)} round ${round}: ${listing.tasks.length} task(s) on ${model || 'the inherited model'}`)
    const results = await parallel(listing.tasks.map((task) => () => agent(
      instruction(job, round, task),
      { label: `${name(job)}/${task.id}`, schema: DONE, phase: 'Tasks', ...(model && { model }) },
    )))
    const written = results.filter((r) => r && r.written)
    log(`${name(job)} round ${round}: ${written.length}/${listing.tasks.length} written`)
    return {
      job,
      round,
      written: written.map((r) => r.id),
      failed: listing.tasks.map((t) => t.id).filter((id) => !written.some((r) => r.id === id)),
    }
  },
)

// Deliberately no verdict here. Nothing in this script judges a finding, drops one, or ranks
// anything — `rsquad ingest` validates every reply, runs both mechanical guards, and decides.
const done = runs.filter(Boolean)
return {
  jobs: done.length,
  written: done.reduce((n, r) => n + r.written.length, 0),
  failed: done.flatMap((r) => r.failed),
  next: done.map((r) => `rsquad ingest ${r.job}`),
}
