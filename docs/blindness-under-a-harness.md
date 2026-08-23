# Blindness under a harness — measured, and one mitigation was wrong

**Date:** 2026-08-23
**Subject:** run H — `ai-video-digest@b404a93`, `tools/portail_tests.py`, harness transport, the
job exported to a directory with no checkout in it.
**Method:** read the agents' own transcripts and classify every file operation as inside or
outside the job directory. Not asked of the agents; recorded from what they did.

On the API path a blind lens is blind because its request has no parameter through which a
specification could arrive, and a test asserts the signature (ADR-0002). On the harness path the
lens is an agent with file-reading tools. ADR-0008 recorded that as blindness degrading from a
property to a promise, and proposed a fix. This is the measurement of both.

## The result: 46 agents, 119 file operations, none outside the job

| Run | Round | Agents | File ops in the job | Outside |
|---|---|---:|---:|---:|
| D | lenses | 6 | 15 | **0** |
| D | refutation | 9 | 24 | **0** |
| E | lenses | 6 | 16 | **0** |
| E | refutation | 8 | 20 | **0** |
| **H** | lenses | 6 | 16 | **0** |
| **H** | refutation | 11 | 28 | **0** |
| | | **46** | **119** | **0** |

Not one agent read a file belonging to the repository under review. Every read was a task file,
a schema, or a reply it had just written.

**And run H found the same places as the two before it:** `272`, `258`, `137`, with `:272` first
and `blocking`, agreed by all five lenses. Three harness runs, one place set — and the third one
had no repository within arm's reach for any of it. Whatever access the earlier runs had, it
contributed nothing to the result.

## The mitigation ADR-0008 proposed does not work

> *"Copy the job somewhere with no repository beside it and blindness is restored by there being
> nothing to peek at."* — ADR-0008, before this run

That is wrong, and run H is not what proves it. **Runs D and E had already exported their jobs to
a temp directory.** The relocation had happened, and it changed nothing about what the agents
could reach: a Claude Code agent reads absolute paths, and the repository was still on the
machine — and still the working directory its shell started in.

The evidence is in the transcripts. In two separate runs an agent checking a claim about
`git rev-parse` ran:

```
git rev-parse nexistepas; echo "---exit:$?"
```

with no `cd`. That executed **inside the repository under review**. It read nothing there, but the
claim that there was nothing to peek at is false: there was, and an agent was already standing in
it.

**Moving the job removes proximity, not reach.** The reach is the agent's tool permissions, and
those cover the machine. A structural fix has to confine the *agent* — a container or sandbox
whose filesystem holds only the job, or a harness whose tools cannot leave their working
directory. Neither was in place here, and neither is a change to RSquad.

## So: observed, not enforced

That distinction is the whole finding, and it is worth stating without softening.

| | API transport | Harness transport |
|---|---|---|
| What guarantees blindness | the request has no channel for a spec | nothing |
| How you know | a test asserts the signature, before any call | a transcript, after the run |
| Failure mode | impossible by construction | possible, and silent |

46 out of 46 is a strong observation. It is still an observation. A single agent that decided the
task would go better with a look at the specification would produce a finding indistinguishable
from the others, and only the transcript would say so — after the money was spent and the queue
was read.

**A useful consequence: the transcript check is cheap and repeatable.** It reads files that
already exist, costs nothing, and belongs in any deployment where the blind lenses matter. It
does not make blindness a property. It makes a breach detectable, which is the next best thing.

## What the agents did with their tools instead

They verified claims empirically — which the API path structurally cannot do.

In run H, an agent examining the `git rev-parse` finding created a throwaway repository in a temp
directory, committed nothing into it, ran `git rev-parse bogusref`, observed that git exits 128
**and echoes the argument on stdout**, then deleted the directory and wrote its verdict. An
earlier run put it in the verdict text: *verified empirically*.

That was not in ADR-0005's list of what the harness transport buys, and it should have been. A
refuter that can run the code is a different instrument from one reasoning about it — and it is a
strictly better one for exactly the claim shape this squad demands, since "reproduction or
nothing" means every finding names concrete inputs somebody could execute.

It also complicates the isolation argument. A sandbox that holds only the job would restore
blindness as a property **and** take this away, because a repository the agent can create is a
repository the agent can create. The two goods are not obviously separable, and nothing here
measures which is worth more.

## Cost

Run H spent **949,350 tokens** across 17 agents — above runs D (820,844) and E (763,928), with
the caveat that it produced 11 findings and ran 10 refutations where the earlier runs ran 8 and 9.
More findings cost more; that is the mechanism working, not drift.

## What this still does not establish

- **Whether an agent would peek if peeking helped.** Every run so far was on a task the context
  pack already answered. A case where the file alone is genuinely insufficient is the one that
  would test the instruction, and it has not been run.
- **Blindness as a property on this transport.** That needs the sandbox, not another run.
- **Anything about a harness other than Claude Code.** A Cursor rule, a shell loop and a person
  with a chat window have three different answers to "what can it read", and the seam was built
  to accept all three.
