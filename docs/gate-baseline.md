# Gate baseline — what it actually catches, measured

**Date:** 2026-08-22
**Subject:** `rsquad gate --replay 20` against `ai-video-digest@6ade3ff`.
**Supersedes:** the "47 % examined / 8 % suspect" figure published in that project. That number
came from a replay path where `--head` was overwritten by `HEAD` — see `extraction.md`.

## The corrected rate

| | Published | **Corrected** |
|---|---:|---:|
| Commits examined | 20 | 20 |
| touching tests | 15 | **14** |
| where the gate says something | 9 / 15 | **8 / 14** |
| New or modified test functions | 159 | **129** |
| **Actually examined** | 75 (47 %) | **55 (43 %)** |
| Valid | 69 | **50** |
| **Suspect** | 6 (8 %) | **5 (9 %)** |

Six of twenty commits touch no test file at all. Of the fourteen that do, six produce **no
signal whatsoever** — every new test file is uncollectable on the base because it imports
symbols that do not exist yet.

**Read the 43 % as the headline, not the 9 %.** On more than half the new tests the gate cannot
say anything, and a "0 suspect" verdict most often means "nothing could be checked".

And 43 % is itself an upper bound: a test that fails on the base with `AttributeError` on a
missing symbol is currently classed *valid*, though it carries the same information as the
`ImportError` classed *no signal*. The verdict depends on import style. Unfixed — see
`extraction.md` §3.

## The five suspects, by nature

The split is what matters for deployment, not the count.

### One genuine finding — a loosened assertion

`tests/test_discover.py::test_la_configuration_reelle_charge` at `6de3862`:

```
assert len(chaines) == 5     ->     assert len(chaines) >= 5
```

The gate sees it because the relaxed test now passes on the base. **This is the failure mode the
gate exists for** — loosening an assertion to green the CI. Nothing else signals it: the suite
stays green, coverage does not move, review sees a one-character diff.

It survives the replay correction unchanged, which is the single most important thing this
re-measurement establishes.

### Two characterization tests

- `test_en_mode_nominal_la_date_du_flux_reste_un_repli_legitime` — asserts a nominal behaviour
  is still a legitimate fallback.
- `test_une_fiche_portant_deux_graphies_n_est_comptee_qu_une_fois` — asserts a dedup property
  that already held.

Both exist to prove a change broke nothing. They *must* pass on the base. Correct signal, known
remedy: the `characterization` marker.

### Two negative guards

- `test_sans_depuis_l_absence_de_date_n_alarme_pas`
- `test_muse_seul_n_est_pas_rattache_a_meta_muse_spark`

They assert something does **not** happen. The base does not do it either, so they cannot fail
there by construction. These tests are valuable — they protect a deliberate decision — and
invisible to this gate by design. They need the same exemption, under the `guard` marker.

## What this means for deployment

**One of five suspects calls for a change to the test.** Shipped without distinguishing the three
natures, the gate produces **four false positives out of five**, and gets switched off inside a
week — taking the genuine finding with it.

So: ship both markers from day one, and budget for an annotation pass over the existing test
base. The real signal — loosened assertions — only emerges after that pass.

## Reproducing

```bash
rsquad gate --replay 20 --head 6ade3ff --repo ../ai-video-digest
```

Roughly one worktree and one partial pytest run per commit touching tests. The worktree shares
git's object store, so the cost is the test runs, not the checkouts.
