# Gate baseline — what it actually catches, measured

**Date:** 2026-08-22
**Subject:** `rsquad gate --replay 20 --head 6ade3ff --repo ../ai-video-digest`.
**Supersedes:** the "47 % examined / 8 % suspect" figure published in the source project.

Three defects sat between that number and the truth. Each was fixed separately, and the table
below is the point of this document: **the published coverage was more than double the real
one.**

## The rate, corrected twice

| | Published | After the `--head` fix | **After question 5** |
|---|---:|---:|---:|
| Commits touching tests | 15 / 20 | 14 / 20 | **14 / 20** |
| where the gate says something | 9 / 15 | 8 / 14 | **8 / 14** |
| New or modified test functions | 159 | 129 | **129** |
| **Actually examined** | 75 (**47 %**) | 55 (43 %) | **27 (21 %)** |
| Valid | 69 | 50 | **22** |
| **Suspect** | 6 (8 %) | 5 (9 %) | **5 (19 %)** |
| No signal | — | 6 | **41** |

- **`--head` was overwritten by `HEAD`** before the work happened, so replays graded a commit's
  parent against today's tests. Inflated the denominator: 149 retained functions instead of 129.
  See `extraction.md` §1.
- **Question 5** — a base failure on a symbol that does not exist yet was classed *valid* when
  the test reached it as a module attribute, and *no signal* when it imported it by name. Same
  missing symbol, verdict decided by import style. `extraction.md` §3.

The second fix is the brutal one. **28 of the 50 "valid" tests proved nothing** — they failed on
the base because the symbol was not there, which is exactly what a new test does. One commit
tells the whole story: `22a9680` reported 17 valid and now reports 1 valid, 17 no signal.

The rising suspect percentage — 8 % to 19 % — is not a deterioration. The suspect count never
moved past 5; the denominator collapsed underneath it.

## The 21 % is the headline. Not the 19 %.

On **four out of five** new test functions the gate can say nothing at all. A "0 suspect" verdict
almost always means "nothing could be checked".

This also resizes a limitation that was already known but badly measured. The gate covers
*modifications*; it is blind to *additions*, because a test for a function that did not exist can
only fail by not finding it. An earlier three-commit sample put real coverage near 30 %. Over
twenty commits it is 21 %, and the no-signal bucket — 41 of 129 — is now the largest single
outcome after "never examined".

The complement remains **mutation testing**: not "does the test fail without the module?"
(trivially yes) but "does it fail if the logic is subtly wrong?". Named, not built.

## What survived all three corrections

**Every genuine finding.** The suspect set is identical before and after: five, of three kinds.
Not one of them depended on any defect. That is the strongest thing this re-measurement
establishes — the gate's value was real, only its self-reported coverage was inflated.

### One genuine finding — a loosened assertion

`tests/test_discover.py::test_la_configuration_reelle_charge` at `6de3862`:

```
assert len(chaines) == 5     ->     assert len(chaines) >= 5
```

The gate sees it because the relaxed test now passes on the base. **This is the failure mode the
gate exists for** — loosening an assertion to green the CI. Nothing else signals it: the suite
stays green, coverage does not move, review sees a one-character diff.

### Two characterization tests

`test_en_mode_nominal_la_date_du_flux_reste_un_repli_legitime` and
`test_une_fiche_portant_deux_graphies_n_est_comptee_qu_une_fois` — both assert a change broke
nothing, so both *must* pass on the base. Correct signal, known remedy: the `characterization`
marker.

### Two negative guards

`test_sans_depuis_l_absence_de_date_n_alarme_pas` and
`test_muse_seul_n_est_pas_rattache_a_meta_muse_spark` — they assert something does **not** happen.
The base does not do it either, so they cannot fail there by construction. Valuable tests,
invisible to this gate by design. They need the `guard` marker.

## What this means for deployment

**One of five suspects calls for a change to the test.** Shipped without distinguishing the three
natures, the gate produces four false positives out of five and is switched off inside a week —
taking the genuine finding with it. Ship both markers from day one and budget for an annotation
pass over the existing test base.

And publish the examined count beside every verdict. A gate that reassures precisely when it
knows nothing is worse than no gate — this document is what that failure mode looks like when it
runs for two weeks unnoticed.

## Reproducing

```bash
rsquad gate --replay 20 --head 6ade3ff --repo ../ai-video-digest
```

Roughly one worktree and one partial test run per commit touching tests. The worktree shares
git's object store, so the cost is the test runs, not the checkouts.
