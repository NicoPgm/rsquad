# ADR-0010 — Under a harness, blindness is by instruction, and is called that

**Status:** accepted
**Date:** 2026-11-20
**Scopes:** ADR-0002, on the primary transport chosen in ADR-0009.

## Context

ADR-0002 made a blind lens's blindness a property of its payload, and said any second transport
must satisfy that constraint or explicitly give it up. ADR-0009 makes the harness the primary
transport, and a harness agent has file-reading tools.

What has been measured (`docs/blindness-under-a-harness.md`): across 46 harness agents and 119
file operations, none read a file outside its job. That is an observation, not a property, and
moving the job away from a checkout did not turn it into one: an agent's reach is set by its tool
permissions, not by what sits next to the job. A skill running inside a working copy, which is
where ADR-0009 puts it, is more exposed, not less. Confining an agent is a sandbox, and a sandbox is
not RSquad's to build.

None of the review agents surveyed treats spec-blindness as a goal
(`docs/state-of-the-art-review-agents.md`).

## Decision

**This is the explicit giving-up that ADR-0002 asked for, and it is partial.**

- **The payload stays blind.** The CLI never puts a specification, a ticket or a commit message in
  a blind lens's task, and the test asserting that stays. That half of ADR-0002 costs nothing and
  is kept.
- **Under a harness, blindness is by instruction.** No sandbox and no confinement work.
  Documentation and reports call it that, and stop presenting it as guaranteed on that path.
- **Where the harness keeps transcripts, checking which files each agent read remains the way to
  detect a breach.** It makes a breach visible, not impossible.

## Consequences

- ADR-0002 still holds in full on the frozen API path.
- **A CI runner restores the property by construction.** A driver that sends a task's text to a
  model API, with no tools, gives the model nothing to read but the payload. Of the paths
  ADR-0009 keeps, that is the one where blindness is a fact again.
- If a transcript ever shows a breach, this decision is reopened, with that evidence.
