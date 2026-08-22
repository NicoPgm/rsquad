# Extracting the gate — equivalence first, then deliberate change

**Date:** 2026-08-22
**Origin:** `ai-video-digest/tools/portail_tests.py` (298 lines, French), commits `2a21282` →
`6ade3ff`.

The gate was written and measured inside a private project bound by a non-publication
constraint. Moving it here meant two changes at once — extraction and translation — and doing
both while also fixing defects would have made it impossible to say which change caused which
difference.

So: **prove nothing changed, then change things.**

## Step 1a — equivalence

The logic lives in four functions. Each was compared against its original on real data: the
20 commits behind `ai-video-digest@6ade3ff`, the same set that produced the published
measurement.

| Original | RSquad | Commits compared | Divergences |
|---|---|---:|---:|
| `base_de_comparaison` | `core.merge_base` | 20 | 0 |
| `fichiers_de_test_modifies` | `core.changed_files` + `is_test_file` | 20 | 0 |
| `tests_touches` | `PythonPytestAdapter.changed_test_functions` | 20 | 0 |
| `noms_exempts` | `StackAdapter.exempt_names` | 20 | 0 |
| `analyser_junit` | `core.parse_junit` | 14 synthetic cases | 0 |

The JUnit cases cover every branch: `<failure>`, `<error>`, pass, `<skipped>`, a parametrized
name, a classname-less collection error, and an unrelated function — each with and without an
exemption marker.

Result: **no divergence.** The translation is faithful.

## Step 1b — the deliberate changes

Two defects were found while reading the original closely enough to translate it. Both are in
this repository's version; neither is in the original.

### 1. `--head` was overwritten by `HEAD` before the work happened

`main()` resolved the requested revision, used it to pick the base and the changed file list,
and then did:

```python
tete = executer(["git", "rev-parse", "HEAD"]).stdout.strip()
```

Everything after that line — extracting changed test functions, and populating the worktree
with "tests from head" — used `HEAD` instead of the requested revision. Replaying a past commit
therefore graded *that commit's parent* against *today's tests*.

With `--head HEAD` (the default) the overwrite is inert. It bites only on replay — which is
exactly the path that produced the published rate.

Measured impact across the same 20 commits:

| | Correct | As shipped |
|---|---:|---:|
| Retained test functions | 129 | **149** |
| Commits affected | — | **5 of 14** |

The line dates from `2a21282`, the gate's first commit.

**Consequence: the published "47 % examined / 8 % suspect" is not a usable baseline.** Both the
denominator and the verdicts came from that path.

### 2. Exemption markers were read from the working tree

`noms_exempts` opened files from the current directory rather than from the revision under
test. Same failure shape as above: correct when head happens to be checked out, silently wrong
on every replay. `exempt_names` now takes the file text at the revision.

### 3. Deferred one commit, then fixed

A third defect was found independently in the source project and committed there as `b366b7d`:
a test that fails on the base with `AttributeError` on a missing symbol is classed **valid**,
while an `ImportError` on the same missing symbol is classed **no signal**. The two carry the
same epistemic content — the symbol does not exist yet — so the verdict depends on where the
symbol is referenced, i.e. on import style, not on test quality.

It was left unfixed in the import commit on purpose: fixing it would have broken the equivalence
check above. It is fixed in the commit that follows, as **question 5** of the adapter protocol —
see `gate-baseline.md` for what it cost.

The shape of the fix matters more than the fix. The classification looked portable, because
`<failure>` versus `<error>` is a JUnit distinction every runner emits. It is not: deciding
whether a failure means "nothing was there to discriminate" requires reading an exception
message, and exception vocabularies are per-language. So the seam between core and adapter was
in the wrong place, and only running the gate revealed it.

The predicate is deliberately a narrow allowlist of message shapes, each verified against real
`pytest --junitxml` output rather than assumed. The risk being managed is the false negative:

| Message | Meaning |
|---|---|
| `AttributeError: module 'x' has no attribute 'y'` | symbol absent — no signal |
| `NameError: name 'y' is not defined` | symbol absent — no signal |
| `ImportError: cannot import name 'y' from 'x'` | symbol absent — no signal |
| `AttributeError: 'NoneType' object has no attribute 'y'` | **a real defect, caught — valid** |
| `assert 4 == 5` | a real assertion — valid |

Widening this to "any `AttributeError`" would throw away tests that were doing their job.

## What this costs to know

Every defect listed here — including the four found in the original implementation
(editable-install resolution, `git checkout HEAD` in a detached worktree, collection errors
aborting the session, file-level granularity) — was found by **running the tool or reading it
line by line to port it**. None was found by using it and trusting the output.

That is the recurring lesson, and it is why `--replay` exists: a check verifies what it
verifies, and the confidence it inspires beyond that is an illusion.
