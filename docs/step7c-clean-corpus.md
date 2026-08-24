# The clean-commit corpus — the squad is silent on half of it, and was never silent on a defect

**Date:** 2026-08-23
**Transport:** harness. 62 agents, **3.28 million tokens, $0 billed** — the measurement that
needs volume, run on the path where volume is free.
**Selection:** `evaluation/step7c_clean.py`, rules fixed before anything ran.

Every case in `step7b.yaml` is a diff **known** to contain a defect, so nothing measured there
says what the squad does to code nobody has complained about. 35 of its 50 findings were not the
known defect, and that number is uninterpretable without this one.

## Result

| | clean commits | defect cases |
|---|---:|---:|
| cases | 8 | 19 |
| surviving findings | **12** | ~~50~~ **97** |
| per case | **1.5** | ~~2.6~~ **5.1** |
| **cases with no finding at all** | **4 / 8** | **0 / 19** |
| refuted | 0 | 1 |
| refused by the guards | 0 | 0 |

> **Corrected 2026-08-24.** The two columns were counted in different units: 12 is raw findings,
> 50 was distinct `file:line` places. In matching units it is 12 against 97, so **1.5 per case
> against 5.1** — the contrast is more than threefold, not less than twofold. In places it is 0.8
> against 2.6, the same ratio. The correction strengthens this page's argument, which is why it
> had to be looked for. `docs/transport-calibration-19.md`.

**The second-to-last row is the result.** The squad said nothing on half the clean commits, and
never once said nothing on a diff that contained a defect. On 4/8 against 0/19 that is Fisher
exact, two-tailed, **p ≈ 0.008** — the only statistically significant number this project has
produced, and it is about silence rather than detection.

It is not a size effect. The silent commits changed 51, 33, 18 and 15 lines; the ones that
produced findings changed 66, 24, 15 and 5. The most talked-about commit and the largest silent
one are comparable, and the smallest commit in the set (5 lines) produced three findings.

## What the twelve findings actually say

Counting them as false positives would be wrong, and reading them is the only way to know:

- `PatternBasedPromptInjectionGuardrail:123` — `UserMessage.singleText()` throws rather than
  returning null for a multi-content message, so the guardrail propagates an exception instead of
  guarding. Three lenses agreed independently.
- `PatternBasedPromptInjectionGuardrail:130` — the full raw user text is logged at WARN with no
  length bound and no sanitisation, so an attacker controls log volume.
- `TransformersEmbeddingModel:271` — the null guard protects against a never-initialised session,
  not an already-closed one, and `OrtSession.close()` throws on the second call.
- `MongoDBAtlasVectorStoreAutoConfiguration` — `ObjectProvider.ifAvailable` delegates to
  `getIfAvailable()`, which throws `NoUniqueBeanDefinitionException` when several candidates match;
  only `getIfUnique()` returns null.

None of these is invented. They are latent concerns in code nobody has filed a bug against —
**which is exactly what the definition of "clean" admits**: a defect nobody has hit yet still
counts as clean, so this figure is a lower bound on noise and an upper bound on nothing.

So the honest sentence is not "1.5 false positives per clean commit". It is **1.5 unrequested
claims per clean commit, of which an unknown share are real**.

## What "clean" means here, and what it cannot mean

Nobody can establish that a commit contains no bug. The operational definition, fixed before the
run:

> a commit whose changed source file has **not been touched by any later fix commit**

Nobody has reported a bug in it since. Everything else matches the defect cases exactly — same
window, one source file, at least one test, at most six files, and the review **restricted to the
source file**, because `export` otherwise includes the test files and the two counts stop being
comparable. That mistake was made once and caught before spending.

Two amendments to the selection, both made before any run and both recorded in the script:

- **Dropped:** excluding commits that reference an issue. langchain4j appends the pull-request
  number to every subject, so the rule matched the whole repository and left two candidates. It
  was discriminating on a commit convention, not on content.
- **Added:** a wider fix vocabulary than the defect selection uses — correct, harden, guard,
  prevent, avoid, resolve, escape, validate, sanitize. `Correct ToolContext parameter detection`
  and `Harden filename handling` are repairs whose subject avoids the word "fix". Widening an
  exclusion can only shrink the corpus and only toward cleaner cases.

One case is borderline and stays in: `6bfa53a88` — *Close native resources in
TransformersEmbeddingModel* — is a leak repair whose subject avoids the vocabulary. Its three
findings may therefore be about genuinely defective code. Flagged rather than removed, because
removing a case after seeing its findings is the adjustment this whole exercise exists to avoid.

## Why the harness

This is the measurement that wants volume and needs no human verdict: the headline is a count.
3.28 million tokens against a subscription, where the same work on the API would have billed
around $7 — and the API budget is better spent on the detection cases, which need a human verdict
per case and cannot be scaled by paying more.

That split is the operational argument of ADR-0005 finally being used rather than debated: noise
on the harness, detection on the API.

Two changes it required, both committed:

- **The driver takes a list of jobs.** One job per invocation meant twelve round trips for one
  measurement. It now pipelines: a job's tasks start as soon as its own manifest is read.
- **The driver had to be rewritten with LF endings.** Editing it from Python on Windows turned
  every line ending into CRLF, and the workflow tool refuses a script containing control
  characters. Reading the file back in text mode hid it — Python converts `\r\n` to `\n`
  silently — so it took reading the bytes to see the 132 carriage returns.

## What this does not establish

- **Eight commits.** The per-case rate has an interval wide enough to be nearly useless on its
  own; the silence contrast is the part that carries weight.
- **Two repositories, one language, no context pack.**
- **"Clean" is a proxy** and the noise figure is a lower bound. Every finding above might be a
  bug report nobody has written yet.
- **Nothing about whether a reader would act on the twelve.** Acceptance rate per lens is still
  the only judge of usefulness, and it is still unmeasured.
