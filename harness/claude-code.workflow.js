/*
 * RSquad — Claude Code driver for the harness transport.
 *
 *   rsquad export <job> --head <rev> --repo <path>
 *   /workflows  →  this script, with args: { job: "<absolute path to job>" }
 *   rsquad ingest <job>          (twice: once for the lenses, once for the refutations)
 *
 * This script does one thing: it runs the tasks RSquad wrote and saves the replies. It does not
 * decide what a lens is asked, what a reply must satisfy, or what survives — all of that stays
 * in RSquad, on the other side of the seam (ADR-0005, ADR-0008).
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
  whenToUse: 'After `rsquad export`. Pass args: { job: "<absolute path to the job directory>" }',
  phases: [
    { title: 'Manifest', detail: 'read the job manifest and list the tasks' },
    { title: 'Tasks', detail: 'one agent per task, reply written back as JSON' },
  ],
}

const job = args && args.job
if (!job) throw new Error('pass args: { job: "<absolute path to the job directory>" }')

const MANIFEST = {
  type: 'object',
  additionalProperties: false,
  required: ['round', 'tasks'],
  properties: {
    round: { type: 'integer' },
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

phase('Manifest')

const listing = await agent(
  `Read the JSON file at ${job}/manifest.json and return its "round" number and, for every ` +
  `entry in its "tasks" array, that entry's "id" and "contract". Do not read anything else ` +
  `and do not summarise: return every task.`,
  { label: 'manifest', schema: MANIFEST, effort: 'low' },
)

if (!listing || !listing.tasks.length) throw new Error(`no tasks in ${job}/manifest.json`)

const round = listing.round
log(`round ${round}: ${listing.tasks.length} task(s)`)

phase('Tasks')

const results = await parallel(listing.tasks.map((task) => async () => {
  return agent(
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
    `Then return the task id, whether you wrote the file, and one short note.`,
    { label: task.id, schema: DONE, phase: 'Tasks' },
  )
}))

const written = results.filter((r) => r && r.written)
log(`${written.length}/${listing.tasks.length} replies written`)

// Deliberately no verdict here. Nothing in this script judges a finding, drops one, or ranks
// anything — `rsquad ingest` validates every reply, runs both mechanical guards, and decides.
return {
  round,
  written: written.map((r) => r.id),
  failed: listing.tasks.map((t) => t.id).filter((id) => !written.some((r) => r.id === id)),
  next: `rsquad ingest ${job}`,
}
