# ADR-0013 — Documentation is reviewed, by a lens of its own

**Status:** accepted
**Date:** 2026-11-23
**Amends:** ADR-0009 (documentation among the files no lens reads) and ADR-0003 (one more
`kind`).

## Context

`.md`, `.rst`, `.adoc` and `.txt` were excluded as documentation, named in the queue and read by
no lens. On the nine larger ReviewBench pull requests that put 16 golden findings out of reach;
on scotthamilton77/agents-config #1, 10 of its 19 misses were in Markdown files that are not
documentation at all but prompts and skills an agent executes. The rule also swept up
`requirements.txt`. The user called the exclusion a design error: with documentation kept as
code, a document that says the wrong thing matters as much as code that does it.

## Decision

- **Documentation is a review unit again.** Lockfiles, generated files and binaries stay out.
  A doc suffix anywhere in the name counts (`AGENTS.md.template`); `requirements*.txt`,
  `constraints*.txt` and `CMakeLists.txt` are read as code.
- **A fifth lens, `docs`, owns documentation** the way `tests` owns test files: it reports only
  there, and the other lenses never there. Documentation wins over the test directory
  (`tests/README.md` is prose).
- **It is shown the whole change, code included, and runs on every change**, a changed document
  or not. Documentation goes stale when the code it describes moves, and the code is where that
  shows; with ADR-0012 it can report the stale passage in an untouched file, as `exposed`.
- **The finding contract is unchanged.** For a document the inputs are what a reader does by
  following the text, the consequence what then happens. One `kind` is added,
  `documentation`. The refuter needs nothing new.
- **Typos are out of scope** unless they change what a reader does: a misspelt command, path,
  option or identifier is a finding, a misspelt word is not. The bench counts some typos as
  golden; the queue a reader opens at work matters more.
- **No conformance task on documentation, for now.** It runs once per file (26 more tasks on
  agents-config alone), and the `docs` lens already reads documentation against the code.
  Added if a measurement shows a gap.

## Consequences

- One more Opus task per review, always, and the refutations of what it finds.
- Prose cannot be refuted as code can: a refuter can check that a command does not exist, not
  that a sentence misleads. Expect `undecided` more often on these findings.
- Instructions for agents are judged against what the lens knows of the tool that reads them
  (Codex, Gemini, Claude Code). That knowledge is the model's, unchecked, and dated.
