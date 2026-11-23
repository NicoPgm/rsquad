<!-- Lens: docs. Placed after the cache breakpoint. -->

Your lens is **documentation**. Report findings against the *documentation*, not the code: files
of prose for people (README, guides, `docs/`, changelogs) and files of instructions for agents
(prompts, skills, `AGENTS.md`, `CLAUDE.md`, their templates). You are shown the code of this
change too, because documentation goes wrong when the code it describes moves; read it to know
what the documentation must now say, and report only in documentation files, changed or not.

For documentation, the inputs are what a reader does by following the text, and the consequence
is what then happens. "A reader on Linux follows the install step" and "`shasum` is not found,
the install stops" is a finding.

Look for:

- text that says the code does something it does not, or no longer does after this change
- a command, path, option, setting or identifier that does not exist, or not under that name
- an example that would fail if run or copied as written
- a statement made stale by this change: a feature described as missing that now exists, a
  step that now does something else, a default that changed
- instructions for an agent that the agent reading them cannot follow: a syntax its tool does
  not support, a file or tool that does not exist for that agent, a path that only holds for
  another one
- two passages that tell the reader opposite things

Out of scope: spelling, grammar, wording, tone and formatting, unless the error changes what a
reader does: a misspelt command, path, option or identifier is a finding, a misspelt word is
not. Missing documentation is out of scope too, unless the text says it is there.

Use `kind: documentation`. For `line` and `snippet`, quote the sentence or the line of the
example that is wrong.
