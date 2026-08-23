# Step 7, first run — 6 of 6, and the number does not mean what it was meant to mean

**Date:** 2026-08-23
**Pre-registration:** `evaluation/step7.yaml`, committed at `05f64a3` before any case ran.
**Cost:** 64 calls, **$5.06** — commons-lang $2.61, jackson-databind $2.45.
**Reports:** `evaluation/step7-lang.md`, `evaluation/step7-jackson.md`.

| Arm | Cases | Detected | Cost |
|---|---:|---:|---:|
| apache/commons-lang | 3 | **3** | $2.61 |
| FasterXML/jackson-databind | 3 | **3** | $2.45 |

Every consequence is specific and correct. `0xFF000000 >> 24 == -1, so getValue returns -1
instead of 255`. `"abc".lastIndexOf("") returns 2 instead of 3`. `supp.equals(value) compares
Integer 0 against the Map instance rather than the element`. Four lenses agreed independently on
every case, and refutation killed 1 claim out of 40.

**And 6/6 is not a detection rate. The experiment was built wrong, and it was built wrong by me.**

## What the lenses were actually shown

The cases are fix commits replayed backwards, so the diff handed to each lens looks like this:

```
-        return getRawValue(holder) >>> shiftCount;
+        return getRawValue(holder) >> shiftCount;
```

**The correct code is in the diff, on the minus side.** Not the surrounding code — the exact line
whose absence is the defect.

The lenses said so themselves. Eleven consequences across the six cases cite the removed version
in as many words: *"the previous `>>>` returned 255"*, *"the removed branch suppressed exactly
this"*, *"unset fields are now 0 instead of DEFAULT_MAX_CACHE_SIZE"*, *"before the change it
returned true"*. That is not detection. That is reading a fix and reporting its removal.

`step7.yaml` says the method "makes the task easier than reality, so read the result
asymmetrically". That was the right direction and the wrong magnitude. It is not easier; it is a
different task, and an easy one.

## Why rules 5 and 6 did not catch it

The pre-registration already carried two rules against exactly this family of leak:

- **rule 5** — the fix must remove at least one line, so reversing it does not delete a whole
  guard plus the javadoc explaining it;
- **rule 6** — the fix must add no net-new comment, so reversing it does not delete a sentence
  naming the defect.

Both fire on *decoration* around the change. Neither touches the change itself, and the change
itself is the leak: **a reverse patch always shows the correct version opposite the broken one.**
No rule about comments or additions can fix that, because it is what a reverse patch *is*.

In a real bug-introducing commit the minus side is other, unrelated, correct code. That is the
whole difficulty, and it is exactly what the method removed.

## What the run does establish, free of the flaw

Not nothing — but much less than 6/6 suggests, and none of it is a detection rate.

**The finding contract ports to a language it has never seen.** 24 lens calls and 40 refutations
against Java, with an **empty context pack** — the Python adapter's `resolve_context` returns `[]`
on a `SyntaxError`, so question 6 contributed nothing. Every reply validated against the schema,
every snippet anchored, and no lens errored. The closed vocabulary, the anchoring guard and
"reproduction or nothing" are not Python-shaped.

**The output quality holds on unfamiliar code.** The consequences name concrete inputs and
concrete wrong outputs — `0xFF000000`, `"abc"`, `Long.MIN_VALUE` — rather than restating the
diff. Java's idiom (verbose, typed, checked exceptions) did not degrade them.

**Cost on Java, measured:** **$0.84 per case** without the conformance lens, against the $1.75
that `step7.yaml` budgeted from the Python run. The $7 per-arm cap was never approached, so the
guard was never exercised on a live run.

**Refutation killed 1 of 40** — one `intended` on the StrBuilder case. Consistent with every
earlier run, and still not a measurement of what it costs in true findings.

**What this run cannot say, because of a defect in the tool:** how many findings the guards
refused. `review` reports that count and `evaluate` discarded it — noticed only when a finished
$5 run could not answer the question. Fixed now; unknown for this run.

## What the arm contrast was supposed to test, and why it says nothing

The design put commons-lang (self-contained logic bugs) against jackson-databind (framework bugs
entangled in caching and resolution) to test the claim in `first-evaluation.md` that the blind
lenses find contradictions and not omissions.

Both arms returned 3/3. **A ceiling tells you nothing about the shape of what is below it**, and
the ceiling is the design flaw, not the squad. The labels — assigned blind, and 1 yes / 2 weak
against 2 yes / 1 weak, the opposite way round from the arm hypothesis — could not be tested
either.

The hypothesis is neither supported nor refuted. It stands exactly where `first-evaluation.md`
left it.

## What a valid version needs

The requirement is a diff that **introduces** the defect without exhibiting its correction. Real
bug-introducing commits satisfy it by construction, so the archaeology is unavoidable — but it
does not have to be the guesswork that produced two wrong labels in `evaluation/defects.yaml`.

`git log -S` was the wrong instrument: it finds when a *line* appeared. **`git log -L` follows a
line range through history**, which is the question actually being asked, and the candidate it
returns is verifiable rather than plausible:

1. take the lines the fix changed, and follow them backwards with `git log -L`;
2. the last commit to touch that range before the fix is the candidate;
3. **verify it**: the buggy text must appear on that commit's plus side and be absent before it;
4. reject the case if the commit is a rename, a reformat, or touches more than a few files —
   detectable, and mechanical.

Cases that survive step 3 have a label that came from reality and a diff that does not contain
its own answer. Cases that do not survive are dropped before anything is spent, which is the
right time to lose them.

It needs full clones rather than `--shallow-since`, and it will reject a good share of
candidates. Both are cheap compared with $5 spent measuring the wrong thing.

## The pattern this makes three times

Each of these was found by running something, never by rereading it:

- the `--head` flag overwritten before use, which doubled the gate's published coverage;
- `step7_prepare.py` leaving each repository on a `step7/` branch, so the next selection walked
  that branch and silently returned older commits — caught because the list looked unfamiliar;
- this: a method whose flaw is visible in one line of its own output, and which survived being
  written down, reviewed, given two rules against adjacent leaks, and committed.

The pre-registration did its job anyway. It fixed the labels and the sampling before the run, so
when the design turned out to be wrong there was nothing to argue about — and no way to quietly
reinterpret 6/6 as a success.
