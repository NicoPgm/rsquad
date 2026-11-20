# State of the art: open-source code review agents

*Surveyed on 2026-11-20, from GitHub. Everything below is a reading of READMEs and of the prompt
and configuration files they point to. **Nothing was executed**, and no tool here was run on a
corpus of ours. Where a number comes from a project describing itself it is marked
**reported**. Star counts and dates are as of the survey and move daily. §3.8 is the exception: it
describes a diagram supplied by the repository owner, not a GitHub project.*

## 0. What to take away

1. **The field converged on one shape: find, then verify each finding separately, with tools.**
   At least six of the projects read do it: Anthropic's `/code-review`, Sashiko,
   OpenQodex (all read closely), Magpie, adamsreview and PR-AF (README level). RSquad's refutation round is the same idea. It is not
   an outlier.
2. **The sharpest design evidence is about what to keep out of the model's hands.** Alibaba's
   OpenCodeReview reports three failures of reviewers that are only a skill and a prompt:
   selective coverage on large changes, line numbers that drift off the code, and quality that
   moves with prompt wording. It answers with deterministic file selection, bundling, rule
   matching and comment positioning. OpenQodex checks every quoted line by script, and checks
   that every changed line reached a reviewer. Google's command, by contrast, asks the model to
   comment only on added or removed lines: an instruction, not a guard.
3. **Running on the host agent's subscription, with no API key, is mainstream** (OCR's
   `delegate` mode, Magpie's CLI providers, OpenQodex, adamsreview). The honest projects say what
   it costs: OCR calls delegation a lesser pipeline. OpenQodex's matrix says Cursor can start a
   review but cannot be the reviewer; that is a limit of OpenQodex, not of Cursor (§7).
4. **Measurement is the youngest part, and it moved fastest.** Three public benchmarks appeared
   in 2026 (January, February, September). All use human-annotated golden findings and an LLM
   judge. GitHub's reports 96.6 % judge-versus-human agreement on true versus false positive, and
   only 62.9 % exact agreement on severity.
5. **Precision versus recall is a declared choice, and the field is split.** OCR reports trading
   recall for precision on purpose; PR-AF reports being first in recall. Neither figure means
   much without the other.
6. **Stars measure attention, not review quality.** OCR has 54k stars after six months. Sashiko,
   which reviews Linux kernel patches in production, has 1.5k.
7. **A practitioner's end-to-end workflow (a screenshot, not a project) adds ideas the
   repositories lack**: escalating to a five-model panel by change size, rating issues by
   frequency times impact with an explicit "overthinking" check, reproducing before building,
   and loops that check what landed. It is one person's process with no measurement (§3.8).

## 1. How this was surveyed, and what that cannot tell you

Twenty GitHub searches (description, README and topic matches for *code review*, *PR review*,
*AI code review*, *review agent*, and the `code-review`, `ai-code-review`, `pr-review` topics),
each sorted by stars, gave **1,400 distinct repositories** (three more searches, for
benchmarks, came after). Most are noise, because "review"
matches in any sense. Keeping those with *review* in the name or description and at least 120
stars left **166**. From those, and from names I expected but did not see (the official
Anthropic, Google and OpenAI repositories, two benchmarks), **17 were read** (6 closely, down to
the prompt files; 11 at README level) and **21 are known by description only**. The full list,
with what was and was not read, is [Appendix A](#appendix-a-the-projects).

What this cannot tell you:

- **Keyword search misses projects** named differently, written in other languages, or kept
  inside a company.
- **Closed products are invisible.** CodeRabbit, Greptile, Graphite, GitHub Copilot review,
  Cursor Bugbot, Devin and Qodo's current product appear here only as names on a benchmark's list
  of tools evaluated.
- **READMEs describe intent.** No code was audited, so "does X" below means "says it does X".
- **Licences matter for reuse.** Magpie, PR-AF, `openreview` and `claude-review-loop` carry no
  licence, which means all rights reserved: the ideas are free, the code is not. Kodus uses a
  custom licence that is not an SPDX identifier; read it before reusing anything.

## 2. The landscape: eight families

| | family | examples | state |
|---|---|---|---|
| **A** | **First-generation single-call bots**: diff, one model call, a comment | ChatGPT-CodeReview, ai-codereviewer, chatgpt-action; PR-Agent by age and lineage (its design was not examined) | mostly stale or archived (see below) |
| **B** | **Prompt-only commands and skills** inside a coding agent: one agent, a persona, a fixed output format | Google's Gemini CLI extension, Anthropic's official Actions, dozens of "code review skill" repositories | very active, shallow |
| **C** | **Parallel generalists plus validators, or a debate** | Anthropic `/code-review`, adamsreview, Magpie, cross-review, PR-AF | active, converging |
| **D** | **Staged specialists with consolidation** | Sashiko, Anthropic `pr-review-toolkit`, Metis and RepoLens (description only) | fewer, deeper |
| **E** | **Deterministic scaffold around an agent** | OpenCodeReview, OpenQodex, code-review-gate-skill | the newest, and the best argued |
| **F** | **Context and knowledge infrastructure** | code-review-graph, awesome-reviewers, Kodus rules, Sashiko's code notes | adjacent: they feed a reviewer |
| **G** | **Review inside the author's loop**: hook, gate, fix loop | roborev, OpenQodex's push gate, adamsreview's fix loop | growing |
| **H** | **Benchmarks** | AACR-Bench, Code Review Bench, ReviewBench, Sashiko's own | three new in 2026 |

**The first generation is gone.** `coderabbitai/ai-pr-reviewer` no longer resolves (404);
`villesau/ai-codereviewer` was last pushed in August 2024; `kxxt/chatgpt-action` and `codedog` are
archived. PR-Agent, the best known, was **donated to the community by Qodo**, whose commercial
successor is a closed platform; the project is now community-maintained and in the process of
moving to a foundation. One survivor, `anc95/ChatGPT-CodeReview`, still receives pushes. What
replaced the generation is not a better single call: it is a pipeline with a verification step.

## 3. Projects worth reading closely

### 3.1 Anthropic `/code-review` (`plugins/code-review` in `claude-plugins-official`)

The closest published match to a "skills and subagents" design, and a short file to read
(`commands/code-review.md`, about 7 KB). The sequence:

1. a **small model checks whether review is needed** at all: skip closed, draft, trivial or
   already-reviewed pull requests;
2. a small model lists the relevant `CLAUDE.md` files; a mid-size model summarises the change;
3. **four agents review in parallel**: two check `CLAUDE.md` compliance, two look for bugs: one
   **sees only the diff**, the other may read around it;
4. **one validator per finding** receives the PR description and the claim, and must confirm
   it (the largest model for bugs, a mid-size one for rule violations); findings that are not
   validated are dropped.

Three things to notice. **Models are tiered by difficulty** (small for the gate, mid-size for
summary and rule compliance, the largest for bugs and for validating them). **The agents are told
not to flag** pre-existing issues, anything a linter catches, style nitpicks, and general quality
concerns unless a rule requires it; the stated reason is that false positives erode trust.
And **the README and the command disagree**: the README describes a 0 to 100 confidence score
with a threshold of 80, while the command file contains no numeric score and filters by validator
instead. The mechanism changed and the documentation did not. Read the command, not the README.

Its sibling `pr-review-toolkit` takes the other philosophy: **six specialists by domain** (comment
accuracy, test coverage, silent failures, type design, general review, simplification), invoked
by natural-language triggers, with **no verification step**.

### 3.2 Alibaba OpenCodeReview (OCR)

Created in May 2026; 54.5k stars, 4.5k forks, a release almost daily. Reported to have started as
Alibaba's internal reviewer. **Hybrid by design**: deterministic code selects which files are
reviewed, bundles related files into units that each run as a sub-agent with isolated context,
matches review rules to each file with a template engine, and positions and re-checks comments in
separate modules; the agent decides what to read and what to say.

It states three failures of skill-based reviewers (see §0.2) and attributes them to a lack of
hard constraints on the process. **Reported**: with the same underlying model it beats a general
coding agent on precision and F1 using about one ninth of the tokens, at the price of lower
recall. Two cautions: the benchmark is **AACR-Bench, published by the same organisation**, and
these are the project's own figures.

**Delegation mode is the part that matters here.** A CLI (`ocr delegate preview`,
`ocr delegate rule`) does file selection and rule resolution with **no model on OCR's side**, and a
skill tells the host agent (Claude Code, Codex, Cursor and others) how to review: a checklist
with every previewed file, a structured comment format, and a final reconciliation of files
reviewed versus skipped. The project says plainly that this is *not* the native pipeline: the host
agent does the analysis, the positioning and the reporting. Note what that reconciliation is: the
agent counting its own coverage. It is a stronger instruction, not an enforcement.

### 3.3 Sashiko (Linux kernel, GCC, QEMU, Zephyr)

Rust, created January 2026, with public instances reviewing kernel patches from mailing lists and
**compute and tokens funded by Google** (as the README states). The pipeline:

- **parallel analysis stages**: `goal`, `implementation` and `execution-flow` always run; a
  planning stage picks others (resources, locking, security, performance, hardware);
- a **`verification` stage** consolidates concerns *and dismissed concerns*, emits the justified
  findings and dismissals, and routes contested or speculative candidates to a third bucket,
  `inconclusive_concerns`;
- a **`post-verification` stage** runs up to ten parallel per-finding verifiers **with repository
  tools** to confirm or disprove each inconclusive one.

Its prompts are layered in three: **code notes generated and verified against the source tree**,
human-curated maintainer notes, and universal procedures. Its benchmark tooling is the closest
thing seen to RSquad's methodology: suites built from fixing commits, some **checked to be real
defects visible in the buggy commit's own diff**, `expect_clean` neutral cases, a file of bugs
**missed after launch**, and multi-version patch series that test suppression of false positives.
**Reported**: a false-positive rate under 20 %, from manual sampling of kernel reviews.

### 3.4 OpenQodex

Scanners first (secret and static analysers, lockfiles against an advisory database), with no
model, keeping only findings on changed lines and **showing but never counting** advisories on
untouched lines. Then **finder sessions** read each part of the change with its callers and
propose candidates with a quoted line; **a script checks every quote against the code**;
**verifier sessions** must confirm or refute every candidate and every scanner finding, with a
reason; scripts check that **every scanner finding was answered and every changed line was given
to a reviewer**. Style notes are shown and do not block. Reviewers are fresh processes of Claude
Code or Codex with no memory of the session, on the user's own login, and the tool needs no
account or key.

Constraints worth knowing: Node 22, macOS and Linux, **no test runs on Windows**; and in its
support matrix **Cursor, Cline and Goose can start a review but cannot be the reviewer**, and have
no push gate, only a rule that asks the agent to review (README as of 0.22.0). For Cursor this is a limit of OpenQodex's implementation, not of
Cursor: its own documentation describes isolated subagents (§7).

### 3.5 Magpie, adamsreview, PR-AF

- **Magpie**: several models review independently, **debate** in rounds where all see the same
  information, then a tool-equipped verifier audits each issue against the code and recalibrates
  severity. **Providers can be CLIs on a subscription** (Claude Code, Codex, Gemini CLI and
  others), recommended over API keys. No licence; last pushed August 2026.
- **adamsreview**: up to seven lens agents, a dedup pass, a **cheap validation gate then a deep
  one**, persistent JSON state, and a fix loop that re-reviews and **reverts regressions before
  committing**. Runs on a Claude Code subscription; its author labels the comparison with other
  tools anecdotal. Last pushed May 2026.
- **PR-AF**: a review plan per PR, focused agents, evidence for each finding, a challenge round.
  **Reported**: first among open-source tools on the Code Review Bench subset it could run (38
  PRs), recall 0.706. This is a **recall** figure on a subset the project selected, and it
  reports finding about three times more issues than the leading commercial tools; precision is
  the other half of that claim. No licence.

### 3.6 Google's Gemini CLI extension

One command and one skill: a **persona** (principal engineer), an objective, a list of **negative
constraints** (do not tell the author to verify or ensure something, do not explain the change
back to them, comment only on `+` and `-` lines, never on licence headers), a four-level severity
scale, and a fixed output template. **Single agent, no verification.** The diff is fetched against the
merge base. Last pushed March 2026. This is the shape a CI job built on
`run-gemini-cli` would most naturally take.

### 3.7 PR-Agent, Kodus, code-review-graph

- **PR-Agent** is described above under family A.
- **Kodus**: self-hosted, bring your own model, **review rules written in plain language and
  scoped to an organisation, repository or path**, token-usage tracking, and a feature that
  tracks suggestions nobody implemented, which is a form of acceptance signal.
- **code-review-graph**: a tree-sitter graph of functions, classes, calls and tests, kept in a
  local SQLite file and served over MCP, so a reviewer reads **the callers, dependents and tests a
  change can reach** with a risk score instead of re-reading the repository. It is the
  deterministic cousin of RSquad's context pack, and a much wider one.

### 3.8 A practitioner's end-to-end workflow (not a project)

*Source: a screenshot of a diagram, supplied by the repository owner and attributed by them to
David Ondrej's company. I have not seen the video or any text around it, cannot verify the
attribution or the date, and the diagram reports no measurement. It is one practitioner's
process, anecdotal by nature. It is described here in my own words; the image is not reproduced.*

The diagram has three stages and three kinds of node: decisions that are the human's call,
independent reviewer agents, and loops. The models it names are labels I can only partly identify,
so none is assumed here.

1. **Build.** A task arrives in a thread. A bug is **reproduced end to end, as a real user would,
   before anything is built**. A big or risky change first gets the human's decisions and live
   measurements (two commands are named for this). One model builds. Then **tests, a type check
   and a screenshot of the real running app** are produced before any reviewer is involved.
2. **Review.** A size check picks the reviewer. A **normal** change goes to one reviewer from a
   **different model family than the builder**, in a **fresh, read-only thread**, at an extra-high
   effort setting. A **huge** change goes to a **panel of five models whose findings are
   de-duplicated**. Every issue is **rated 1 to 10 as how often it happens times how bad it is**.
   Then the diagram asks, in so many words, **whether this is a real must-fix or overthinking**.
   If unsure, a **second opinion from another reviewer**. If must-fix, the human approves, the
   builder fixes, and **the fix is re-reviewed, starting again at the size check**.
3. **Ship.** When nothing is left to fix, a push command rebases onto main. **Loops** then watch
   CI and check side effects and security **on what actually landed**; a bug found there opens a
   new thread and goes back to stage 1.

What it adds beyond the projects above:

- **Escalation by change size, in model count and not only in effort**: one reviewer for a normal
  change, five de-duplicated for a huge one. adamsreview offers an ensemble as an option; here it
  is triggered.
- **Cross-family review as the default path**, with the reviewer **read-only** and in a **fresh
  thread**.
- **A two-factor rating** (frequency times impact) instead of a severity word. Severity is the
  weakest axis in the only calibration published (§4); whether two factors agree better with
  humans is untested.
- **"Overthinking" named as a failure of the reviewer**, with a human gate and a second opinion
  for the unsure case. It is Sashiko's third verdict again, with a person and a different model
  at the junction.
- **Evidence before opinion on the author's side**: reproduce before building; mechanical checks
  and a screenshot before review.
- **A net after landing** for what is only visible once the change is in (CI, side effects,
  security), with a rule for what happens when it catches something.

What it does not show: any deterministic guard (anchoring, coverage reconciliation, schema). A
diagram shows orchestration, so absence here is not absence in practice. And no result: nothing
says whether the five-model panel finds more than one reviewer, or how often the verdict is
"overthinking". Its reviewers are named like slash commands, so in practice this is a skills-based
design: one data point for the skill route, with no evidence on what that route gives up.

## 4. How they measure

| | **AACR-Bench** (Alibaba) | **Code Review Bench** (Martian) | **ReviewBench** (GitHub) |
|---|---|---|---|
| created | Jan 2026 | Feb 2026 | Sep 2026 |
| size | 200 PRs, 50 repos, 10 languages | offline 50 PRs, 5 projects; online: continuously sampled | 219 tasks on the leaderboard; a 25-task test set sampled from them, across 25 repos |
| ground truth | ~1,500 comments annotated by experts; has negative examples | 173 golden comments with severity and category; online: **what the developer fixed after the bot commented** | golden findings reviewed by humans; labels for true and false positive, severity, category, scope |
| judge | LLM, semantic match per file | LLM, three judge models; top five tools reported identical across them | LLM classifier hill-climbed on a human-labelled set; published prompts |
| leakage | not addressed in what was read | acknowledged; the online arm exists to avoid it | repositories frozen as mirrors; a small test set beside the full set the leaderboard runs on |

What stands out:

- **True positive is defined by acceptance.** ReviewBench says outright that the question behind
  the label is whether a human reviewer or the PR author would appreciate and act on the
  finding. It defines a false positive as a finding a senior reviewer would not think worth
  addressing: wrong, unverifiable, out of scope, a duplicate, a nit below the project's bar, or
  one whose suggested action would not improve the change. **The subjective parts are factored
  out** into separate axes (severity, category, scope) so a consumer can re-weight them rather
  than inherit one culture's boundary.
- **The judge is calibrated, and the calibration is published.** Against senior engineers:
  **96.6 % agreement on true versus false positive**, every disagreement audited by hand, and in
  several cases the human label was the wrong one (a reported bug was already prevented by an
  existing guard). Humans also corrected 47 findings the classifier had labelled true. The
  classifier's residual failures are two: **missing an existing mitigation**, and **accepting a
  finding whose factual premise did not hold**. Severity agrees exactly only 62.9 % of the time
  (98.7 % within one level), and humans rated issues more severe about nine times as often as
  less. Category agrees 79.7 %.
- **The online arm of Code Review Bench is the only operationalisation of acceptance at scale
  seen**: precision is the share of a bot's suggestions that match what the developer then
  changed, recall the share of real fixes the bot had suggested.
- **The agent contract is a published interface.** ReviewBench runs each reviewer in a fresh
  container with the repository mounted, and reads one findings file with a file, a line range and
  a message. An empty list is accepted as "reviewed and found nothing"; a missing file or bad JSON
  fails the pull request; one failure fails the whole run rather than publishing a partial score.
  It tells vendors that **truncated output is a common failure** and that they lost a PR to it
  themselves.
- **Unread configuration is detected.** The run lists any configuration label whose value never
  appears in the agent's own output, because a setting the image never reads has no effect.
- **Author conflict is everywhere.** AACR-Bench and OCR are both Alibaba's. ReviewBench is
  GitHub's, and GitHub also ships a reviewer. Code Review Bench lists the tools it evaluated but I
  did not read its leaderboard. None of this makes the figures wrong; it means a figure from a
  tool's own benchmark is a claim, not a result.

## 5. Principles

Each is stated, with where it was seen, and what RSquad does today (from this repository, not
from the survey).

| # | principle | seen in | RSquad today |
|---|---|---|---|
| **P1** | **Put hard constraints on the process, not only in the prompt.** If a rule matters, a script should be able to fail the run when it is broken. | OCR's three failures and its deterministic selection, bundling, positioning; OpenQodex's quote check and coverage checks; Google's `+`/`-` rule as the counter-example | **yes**: units, closed schemas, anchoring, reproduction-or-nothing and missing-task accounting are all on the deterministic side |
| **P2** | **Verify each finding in its own context, with tools, and require a reason either way.** | Anthropic validators, Sashiko post-verification, OpenQodex verifiers, Magpie, adamsreview | **yes**: refutation round, blind to the lens and to other findings |
| **P3** | **Keep a third verdict.** "Refuted" and "could not decide" are different; refuting by default turns uncertainty into silence. | Sashiko `inconclusive_concerns`, code-review-gate-skill `unverified_items`; the §3.8 workflow routes "unsure" to a second opinion from another reviewer | **partly**: every refuted finding is listed with a named cause, but none of the six causes means "could not decide"; conformance findings have no refuter by design (ADR-0007) |
| **P4** | **State whether you optimise precision or recall, and report both.** | OCR against PR-AF; AACR-Bench's own caution that an unmatched comment may still be valid | **partly**: reader cost and detection are measured, no target is declared |
| **P5** | **Scope what each reviewer sees, and vary it on purpose.** Attention is the scarce resource. | Anthropic's diff-only bug agent beside a context-reading one; OCR's isolated bundles and per-file rules; Kodus scoped rules | **partly**: one file per unit and a context pack for Python and Java; no per-file rules, no diff-only variant |
| **P6** | **Spend by difficulty.** Small model for gates, large for judgement. | Anthropic's tiering; adamsreview's cheap-then-deep gate; OCR's token claim; the §3.8 workflow escalates from one reviewer to a five-model panel by change size | **no** on the harness path: one model and one effort level throughout |
| **P7** | **Decide what not to review, and what not to count.** | Anthropic's skip gate and pre-existing exclusion; OpenQodex shows but never counts untouched-line advisories; ReviewBench's scope axis | **partly**: a run with nothing readable stops before any model call, but trivial files (documentation, lockfiles) are not excluded, and the schema has no introduced-versus-pre-existing field |
| **P8** | **Give the reviewer project knowledge in layers, and keep derived layers re-verifiable.** | Sashiko's three layers; Anthropic's `CLAUDE.md` lens; Kodus rules; awesome-reviewers | **partly**: only the conformance lens reads documents, by design, to keep the others blind |
| **P9** | **Get independence from isolation and from model diversity.** | fresh no-memory processes (OpenQodex); several model families (Magpie, adamsreview `--ensemble`, cross-review); a reviewer from another family than the builder, fresh and read-only (§3.8) | **partly**: blind by assembly, but one model family, and the refuter shares the lenses' model |
| **P10** | **Put the reviewer in the author's loop, and keep a smaller net after landing.** The main review belongs before the merge; what only shows up afterwards (CI, side effects, security) needs its own check. | roborev's hook, OpenQodex's push gate, adamsreview's fix loop that reverts regressions; the §3.8 workflow's re-review of every fix and its post-landing loops | **no** |
| **P11** | **Treat subscription execution as first-class, and say what it gives up.** | OCR `delegate`, Magpie CLI providers, OpenQodex | **partly**: a Claude Code driver and a written contract; nothing for Cursor or Gemini yet |
| **P12** | **Measure with a frozen set, a fresh set and a calibrated judge.** | Code Review Bench's two arms; ReviewBench's split and published calibration; Sashiko's missed-after-launch file | **partly**: frozen, pre-registered sets and a clean corpus; no fresh arm, no calibrated judge, acceptance parked |
| **P13** | **Make silence and failure different outcomes; cap and parse output; detect settings nobody reads.** | ReviewBench's contract and its unread-label check | **yes**: missing versus empty, and the harness reads `manifest.model` since 2026-08-25 |
| **P14** | **Say what was not validated.** | code-review-gate-skill ("regression checks, not a recall claim", concurrency unvalidated); adamsreview's "anecdotal"; Sashiko's "manual sampling" | **yes** |
| **P15** | **Rate each finding on two factors, and let a human triage.** Frequency times impact, then "real must-fix or overthinking?", with approval before anything is fixed. A reviewer that over-flags is a failure to be named, not only a precision figure. | the §3.8 workflow; the weak severity agreement in §4 is the reason to try it, not evidence that it works | **partly**: closed severity enum and a ranked queue for a human; no frequency axis, no must-fix triage |
| **P16** | **Put evidence before opinion on the author's side too.** Reproduce a reported bug before building it; run the mechanical checks and capture the real app before a reviewer sees anything. | the §3.8 workflow; RSquad's own step [0] is the same idea for tests | **partly**: the gate exists for Python and pytest only; the build side is out of scope |

## 6. What this suggests for RSquad

*This section is my reading of the survey, not a finding of it.*

1. **The convergence is real but it proves less than it seems.** Several projects arrived at
   find-then-verify independently, which is evidence the shape is right. It is not evidence
   RSquad's implementation is, and I cannot tell who influenced whom.
2. **The rework is smaller than "from scratch" if the seam is kept.** What the best-argued projects
   keep deterministic (selection, units, closed output schema, quote checking, reconciliation) is
   what RSquad's CLI side already is. What they hand to skills and subagents is the model call.
   The survey supports **making the driver the product and the direct API transport optional**,
   not discarding the CLI side. It is the line OCR draws with its `delegate` commands.
3. **Skills-only is the option the evidence argues against.** OCR's three failures describe what
   happens when the process is language-driven, and Google's `+`/`-` instruction is an example of
   the failure class. If the rework moves to skills and subagents, the checks that matter should
   stay as code that can fail a run: anchoring, schema, missing-task accounting and, new, a
   **coverage reconciliation computed by the CLI rather than reported by the agent**. OCR's
   delegation mode is the cautionary version: the agent counts its own coverage.
4. **Three ideas fit its budget concern directly:** tier models by stage (P6), exclude trivial
   files before any model runs (P7), and a verdict that names doubt (P3). RSquad already lists
   every refuted finding with its cause; what it lacks is a cause meaning "could not decide".
5. **Blindness does not survive sub-agents by default.** None of the projects read treats
   *the lens does not see the specification* as a goal; Anthropic's diff-only agent gets a version
   of it by instruction. RSquad's own measurement (46 agents, 119 file operations, none outside the
   job) was an observation, not a property. A subagent design inside a working copy has the same
   exposure, probably larger. Decide whether blindness is still a requirement **before** choosing
   the architecture.
6. **Your own setting may already give you cross-family review.** Code written in Cursor on one
   model family and reviewed in CI by Gemini is the default path of §3.8 and the independence
   of P9, by construction. The survey has no evidence on whether that finds more than
   same-family review; it is cheap to measure on a handful of your own pull requests.
7. **For measurement, the cheapest upgrade is a calibrated judge for acceptance, not a new
   corpus.** ReviewBench publishes its definition (true, relevant, in scope; subjective parts as
   separate axes), its prompts and its agreement figures. That is a better rubric than a single
   verdict word, and RSquad's parked acceptance study could borrow it and run the
   judge-versus-human check on a subset.

## 7. What this survey could not answer

- **What Cursor exposes as skills or subagents was answered the same day, from Cursor's own
  documentation** (skills, subagents and CLI pages, referring to Cursor 2.4 and 2.5): it loads
  Agent Skills, including from `.claude/skills/`; subagents start with a clean context, run in
  parallel and can be `readonly`; a custom subagent names its own `model`; a headless `agent -p`
  takes `--model` and `--output-format json`. Two caveats from the same pages: subagents share the
  parent's checkout unless a worktree is requested, and an admin can disable headless mode. Read
  in the documentation, not yet run.
- **Whether any reported figure holds outside its own benchmark.** Nothing was run, and the Code
  Review Bench leaderboard was not read.
- **Precision at equal recall across tools.** The benchmarks' headline metrics are not directly
  comparable.
- **Whether subscription-hosted subagents are cheaper in practice.** The evidence is OCR's token
  claim and one author's remark about billing pools, not a measurement.
- **Whether size-triggered escalation or a two-factor rating helps.** The §3.8 diagram reports
  no data, and it is one practitioner's process.
- **Anything about closed products** beyond their names.

## Appendix A: the projects

Family letters are those of §2. **Read**: `R` = README and its prompt or configuration files;
`r` = README only; `d` = description only (not read; do not treat as endorsed). Stars, licence
and dates come from the GitHub API on 2026-11-20.

| project | family | read | stars | licence | created | last push | what it is |
|---|---|---|---:|---|---|---|---|
| `anthropics/claude-plugins-official` | B/C | R | 47,771 | Apache-2.0 | 2025-11 | 2026-11-20 | plugins/code-review (4 parallel agents + per-issue validators), plugins/pr-review-toolkit (6 specialists) |
| `alibaba/open-code-review` | E | R | 54,508 | Apache-2.0 | 2026-05 | 2026-11-20 | deterministic CLI + agent; `delegate` mode runs on the host agent's model |
| `sashiko-dev/sashiko` | D | R | 1,480 | Apache-2.0 | 2026-01 | 2026-11-20 | staged specialists, consolidation, per-finding post-verification; Linux kernel first |
| `openqodex/openqodex` | E | R | 1,191 | Apache-2.0 | 2026-10 | 2026-11-20 | scanners, then finders, quote check by script, then verifiers |
| `kyy-logs/code-review-gate-skill` | E | r | 514 | MIT | 2026-10 | 2026-11-19 | static-first skill, four probes, JSON-derived gate, `unverified_items` |
| `liliu-z/magpie` | C | r | 180 | none | 2026-01 | 2026-08-17 | several models review and debate, then a tool-equipped verifier; CLI providers on a subscription |
| `adamjgmiller/adamsreview` | C | r | 245 | MIT | 2026-04 | 2026-05-17 | up to seven lenses, dedup, cheap-then-deep validation, fix loop that reverts regressions |
| `Agent-Field/pr-af` | C/D | r | 668 | none | 2026-03 | 2026-11-13 | review plan per PR, focused agents, evidence, challenge round; recall-first |
| `gemini-cli-extensions/code-review` | B | R | 536 | Apache-2.0 | 2025-09 | 2026-03-10 | one command, one persona skill, fixed output format |
| `The-PR-Agent/pr-agent` | A | r | 16,470 | MIT | 2023-07 | 2026-11-20 | the original open-source PR bot; donated by Qodo to the community; filed under A by age and lineage, design not examined |
| `kodustech/kodus-ai` | prod | r | 1,633 | NOASSERTION | 2025-03 | 2026-11-19 | self-hosted, bring your own model, rules in plain language, tracks unimplemented suggestions |
| `tirth8205/code-review-graph` | F | r | 32,882 | MIT | 2026-02 | 2026-11-16 | tree-sitter code graph served over MCP; blast radius and risk score |
| `kenn-io/roborev` | G | r | 1,822 | MIT | 2026-01 | 2026-11-20 | post-commit hook reviews every commit in the background |
| `baz-scm/awesome-reviewers` | F | r | 155 | Apache-2.0 | 2025-06 | 2026-11-04 | review instructions distilled from real review discussions |
| `withmartian/code-review-benchmark` | bench | r | 306 | MIT | 2026-02 | 2026-11-19 | offline: 50 PRs, 173 golden comments; online: fresh bot-reviewed PRs |
| `alibaba/aacr-bench` | bench | r | 266 | Apache-2.0 | 2026-01 | 2026-11-16 | 200 PRs, 50 repositories, 10 languages, ~1,500 annotated comments |
| `review-bench/ReviewBench` | bench | R | 114 | MIT | 2026-09 | 2026-11-19 | GitHub's benchmark: 25-task test set, 219-task full set, agent contract, calibrated judge |
| `mattzcarey/shippie` | prod | d | 2,530 | MIT | 2023-07 | 2026-10-21 | extendable review and QA agent |
| `vercel-labs/openreview` | prod | d | 1,709 | none | 2026-03 | 2026-03-06 | self-hosted review bot |
| `HexmosTech/git-lrc` | G | d | 1,493 | NOASSERTION | 2026-02 | 2026-11-12 | micro reviews on git commit |
| `spencermarx/open-code-review` | C | d | 390 | Apache-2.0 | 2026-01 | 2026-11-11 | simulates a team of engineers reviewing |
| `TheMorpheus407/RepoLens` | D | d | 305 | Apache-2.0 | 2026-03 | 2026-10-24 | multi-lens audit with many expert agents |
| `arm/metis` | D | d | 896 | Apache-2.0 | 2025-07 | 2026-11-17 | AI-driven deep security code review |
| `AsyncFuncAI/AsyncReview` | D | d | 463 | MIT | 2026-01 | 2026-04-27 | agentic review with recursive language models |
| `miracodeai/mira` | prod | d | 416 | Apache-2.0 | 2026-02 | 2026-11-20 | self-hosted reviewer with indexed PR reviews |
| `Nayjest/Gito` | prod | d | 476 | MIT | 2025-04 | 2026-10-01 | high-confidence, high-impact issues only |
| `Nikita-Filonov/ai-review` | prod | d | 612 | Apache-2.0 | 2025-09 | 2026-10-03 | multi-forge AI review |
| `hamelsmu/claude-review-loop` | G | d | 734 | none | 2026-02 | 2026-03-15 | Claude Code plugin: review loop with Codex |
| `lploc94/cross-review` | C | d | 168 | MIT | 2026-02 | 2026-11-11 | cross-model review skills for Claude Code and Codex |
| `anc95/ChatGPT-CodeReview` | A | d | 4,482 | ISC | 2023-02 | 2026-08-10 | first-generation single-call bot |
| `villesau/ai-codereviewer` | A | d | 1,047 | MIT | 2023-03 | 2024-08-19 | first-generation single-call bot |
| `sourcery-ai/sourcery` | prod | d | 1,888 | MIT | 2019-07 | 2026-11-10 | instant AI code reviews |
| `greptileai/skills` | B | d | 439 | MIT | 2026-02 | 2026-11-03 | skill for checking PR review comments and status |
| `anthropics/claude-code-action` | B | d | 10,024 | MIT | 2025-05 | 2026-11-19 | official GitHub Action |
| `anthropics/claude-code-security-review` | B | d | 7,033 | MIT | 2025-08 | 2026-02-11 | official security-review Action |
| `google-github-actions/run-gemini-cli` | B | d | 2,129 | Apache-2.0 | 2025-07 | 2026-11-19 | official Gemini CLI Action |
| `reviewdog/reviewdog` | pre-AI | d | 9,753 | MIT | 2016-10 | 2026-11-20 | linter-output-to-review-comment bridge |
| `danger/danger-js` | pre-AI | d | 5,519 | MIT | 2016-08 | 2026-10-26 | rules as code for PR hygiene |

## Appendix B: queries

Run with `gh search repos <query> --sort stars --limit 100`, adding `--match description` where
shown; results merged and de-duplicated by full name.

```
"code review" --match description          "pr review" --match description
"pull request review" --match description  "code reviewer" --match description
"ai code review" --match description,readme  "review agent" --match description
"reviewer llm" --match description         "claude code review" --match description
--topic code-review                        --topic ai-code-review
--topic pr-review                          --topic code-reviewer
--topic pull-request-review                --topic llm-code-review
--topic review-bot                         --topic code-review --topic agent
--topic code-review --topic claude         --topic code-review --topic gpt
--topic pull-requests --topic llm          --topic github-action --topic code-review
"code review benchmark"                    --topic code-review --topic benchmark
"automated code review dataset"
```
