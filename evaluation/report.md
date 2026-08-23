# Evaluation replay

**4 scorable case(s) of 9 in the set.**

**Result: 1 detected out of 4 scorable cases.** The verdicts below were filled in by reading
each case and checking the defect was genuinely in the diff shown to the lenses. Four cases do
not make a rate — 1/4 and 3/4 are the same measurement at this size — but the *pattern* of the
three misses is readable, and it is at the bottom of this file.

This report contains no computed detection rate and cannot: the verdict line under
each case is a human judgement. Fill them in, then read the fractions below with
their denominators visible — never as a percentage. On a handful of cases a 25 %
rate and a 75 % one are the same measurement.

## `head-overwritten-before-use`

`main()` resolves the requested revision, uses it to pick the base and the changed file list, then reassigns the same variable to `HEAD` before the work that needs it.

| | |
|---|---|
| introduced in | `b404a93` |
| file | `tools/portail_tests.py` |
| detectable from diff | yes |
| kind / severity | correctness / significant |

8 finding(s) survived refutation:

- **`tools/portail_tests.py:272`** — correctness
  `tete = executer(["git", "rev-parse", "HEAD"]).stdout.strip()`
  the value resolved from --tete at line 258 (and used for the diff and merge-base) is silently overwritten by the SHA of HEAD, so `tests_touches` diffs 4164d03's base against HEAD and `executer_sur_la_base` checks HEAD's test files into the worktree. The replay runs the *current* tests against 4164d03's parent code instead of the tests of 4164d03, producing verdicts for the wrong revision.

- **`tools/portail_tests.py:258`** — contract
  `tete = executer(["git", "rev-parse", args.tete]).stdout.strip()
    if not tete:`
  `git rev-parse` exits 128 but echoes the unresolved argument on stdout, so `tete` is the non-empty string "pas-un-commit" and the guard never fires; the returncode is not inspected. `git diff base...pas-un-commit` then fails with empty stdout, so the tool prints "aucun fichier de test modifié" and returns 0 — a clean success for a revision that does not exist.

- **`tools/portail_tests.py:272`** — correctness
  `tete = executer(["git", "rev-parse", "HEAD"]).stdout.strip()`
  `tete` is silently overwritten with the HEAD SHA after the file list was computed, so `tests_touches` and `executer_sur_la_base` compare/check out the tests of HEAD instead of those of 4164d03: the worktree gets `git checkout <HEAD> -- <fichier>` and the retained test set comes from HEAD, producing verdicts about HEAD's tests while claiming (line 267) to report `4164d03 <- base`. The advertised replay mode measures the wrong commit.

- **`tools/portail_tests.py:259`** — contract
  `if not tete:
        raise SystemExit("révision introuvable : %s" % args.tete)`
  `git rev-parse` exits non-zero but still echoes the unresolved argument on stdout, so `tete` is the literal string "mastr" and the guard never fires; the return code is discarded. Execution continues, `git diff base...mastr` fails and yields an empty list, and the tool prints "aucun fichier de test modifié" and returns 0 — a typo'd revision is reported as a clean pass instead of an error.

- **`tools/portail_tests.py:272`** — correctness
  `tete = executer(["git", "rev-parse", "HEAD"]).stdout.strip()`
  the resolved `--tete` revision computed at line 258 is silently discarded and replaced by HEAD; `tests_touches` and `executer_sur_la_base` then diff/checkout the tests of HEAD against the base of 4164d03~1, so the replay runs today's tests against an unrelated old code state and the verdicts do not describe the requested commit at all

- **`tools/portail_tests.py:258`** — contract
  `tete = executer(["git", "rev-parse", args.tete]).stdout.strip()
    if not tete:`
  `git rev-parse` echoes the unresolvable argument on stdout while returning 128, so `tete` is the literal string "typo-sha" and the `if not tete` guard never fires; `git diff master...typo-sha` then fails, `fichiers` is empty, and the tool prints "aucun fichier de test modifié" and exits 0 as if the gate had passed

- **`tools/portail_tests.py:272`** — correctness
  `tete = executer(["git", "rev-parse", "HEAD"]).stdout.strip()`
  the resolved `tete` computed at line 258 is discarded and replaced by HEAD's SHA, so `tests_touches` and `executer_sur_la_base` diff and check out tests from HEAD instead of the requested revision; the replay compares the base's code against HEAD's tests, producing verdicts for the wrong commit (and reporting a header at line 267 that names 4164d03)

- **`tools/portail_tests.py:272`** — contradicts
  `tete = executer(["git", "rev-parse", "HEAD"]).stdout.strip()`
  Après le calcul de la base et de la liste des fichiers, `tete` est réécrit en dur avec `HEAD` : la sélection des tests touchés (`tests_touches`) et l'exécution sur la base (`executer_sur_la_base`, qui fait `git checkout tete -- fichier`) utilisent donc HEAD et non la révision passée à `--tete`. Le rejeu sur un commit passé compare l'ancien code aux tests de HEAD, pas à ceux du commit examiné.

**Detected? `yes`.** Five independent accounts anchor at `:272` and every one of them names
the actual failure: the revision resolved at line 258 is overwritten by HEAD before
`tests_touches` and `executer_sur_la_base` use it. Not a coincidence of location.

## `verdict-depends-on-import-style`

A base failure on a symbol that does not exist yet is classed `valid` when the test reaches it as a module attribute and `no signal` when it imports it by name. Same missing symbol, verdict decided by how the test spells the import.

| | |
|---|---|
| introduced in | `2a21282` |
| file | `tools/portail_tests.py` |
| detectable from diff | weak |
| kind / severity | correctness / blocking |

16 finding(s) survived refutation:

- **`tools/portail_tests.py:145`** — correctness
  `elif nom in exempts:`
  `nom` still carries the `[1]` suffix (only `fonction` on line 131 strips it), so the membership test fails and the case is classified SUSPECT with "PASSE sur la base" instead of VALIDE; with `--strict` the tool exits 1 on a correctly exempted characterization test.

- **`tools/portail_tests.py:136`** — boundary
  `if retenus and fonction not in retenus and not erreur_de_collecte:`
  The `retenus and` short-circuit disables the filter entirely, so every pre-existing passing test in that file is reported SUSPECT ("PASSE sur la base"), exactly the 35-false-positives situation the docstring says the filter exists to prevent; `--strict` returns exit code 1.

- **`tools/portail_tests.py:209`** — contract
  `executer([sys.executable, "-m", "pytest", *fichiers, "-p", "no:cacheprovider",`
  The returned CompletedProcess is discarded, `analyser_junit` sees `chemin.exists()` is False and returns `[]`, and `main` prints "aucun cas exécuté — pytest n'a rien collecté sur la base." and returns 0. The gate reports success while it examined nothing, including under `--strict`.

- **`tools/portail_tests.py:165`** — correctness
  `elif nue.startswith("def test"):`
  `nue.startswith("def test")` is False for the `async def` line, so the name is never added to `exempts` (and `precedent_marque` is never reset either); the test is classified SUSPECT despite carrying the exemption marker, failing `--strict`. `tests_touches` handles `ast.AsyncFunctionDef`, so async tests do reach this path.

- **`tools/portail_tests.py:136`** — boundary
  `if retenus and fonction not in retenus and not erreur_de_collecte:`
  The `retenus and ...` guard short-circuits to False, the per-function filter is disabled, and every pre-existing test in the file is analysed. All of them pass on the base, so each is reported SUSPECT ("PASSE sur la base") and, with `--strict`, `rapporter` returns exit code 1 — exactly the mass false-positive mode the function's docstring claims to prevent.

- **`tools/portail_tests.py:145`** — correctness
  `elif nom in exempts:`
  The membership test uses `nom` (with the `[param]` suffix) instead of the already-computed `fonction`, so the exemption never matches; the passing case is classified SUSPECT and `--strict` exits 1 for a test that is explicitly marked exempt.

- **`tools/portail_tests.py:117`** — correctness
  `touches |= {nom for nom, corps in nouvelles.items()`
  `retenus` holds only the bare name `test_roundtrip`, so the untouched `tests/test_b.py::test_roundtrip` also passes the filter at line 136; it passes on the base and is reported SUSPECT, failing `--strict` for a test the PR never touched.

- **`tools/portail_tests.py:145`** — contract
  `elif nom in exempts:`
  The membership test compares the parametrized JUnit name against a set that only ever holds bare function names, so it is always false; the already-computed `fonction` (`nom.split("[", 1)[0]`) is never used here. Every parametrized characterization test that passes on the base is reported SUSPECT and, with `--strict`, makes the gate exit 1.

- **`tools/portail_tests.py:209`** — contract
  `executer([sys.executable, "-m", "pytest", *fichiers, "-p", "no:cacheprovider",`
  The CompletedProcess (and its returncode/stderr) is discarded; `analyser_junit` sees a missing file, returns `[]`, and `main` prints "aucun cas exécuté" and returns 0. A completely failed gate run reports success, so no test is ever checked and CI stays green.

- **`tools/portail_tests.py:136`** — boundary
  `if retenus and fonction not in retenus and not erreur_de_collecte:`
  The `retenus and` guard disables filtering entirely, so every pre-existing test in the file is classified. All of them pass on the base and are reported SUSPECT — the mass false-positive case the function's docstring says it exists to prevent — and with `--strict` the gate exits 1.

- **`tools/portail_tests.py:165`** — correctness
  `elif nue.startswith("def test"):`
  `async def test_...` does not match `startswith("def test")`, so the async test is never added to `exempts` and is reported SUSPECT, while `precedent_marque` stays True and wrongly exempts the next plain `def test_*` encountered — a genuinely non-discriminating test is silently marked VALIDE.

- **`tools/portail_tests.py:145`** — correctness
  `elif nom in exempts:`
  `nom` still carries `[cas1]`, so the membership test fails and the exempted characterization test is reported as SUSPECT (exit code 1 under --strict), even though the same function name was already normalised into `fonction` two lines above

- **`tools/portail_tests.py:165`** — correctness
  `elif nue.startswith("def test"):`
  `precedent_marque` is never reset by the intervening lines, so `test_nouveau` is added to `exempts` and a test that passes on the base is reported VALIDE instead of SUSPECT — the gate silently approves a non-discriminating test

- **`tools/portail_tests.py:136`** — boundary
  `if retenus and fonction not in retenus and not erreur_de_collecte:`
  the filter is skipped entirely and every pre-existing test in the file is classified, all of them reported SUSPECT because they pass on the base — reproducing exactly the mass false-positive failure the docstring says the function exists to prevent, and returning exit 1 under --strict

- **`tools/portail_tests.py:184`** — resource
  `raise SystemExit("worktree impossible : %s" % (ajout.stderr or "")[:200])`
  the temporary directory created by `tempfile.mkdtemp` at line 180 is never removed (nettoyer is never reached), leaking a directory under the system temp dir on every failed invocation

- **`tools/portail_tests.py:145`** — undocumented
  `elif nom in exempts:`
  Le code introduit une echappatoire non mentionnee dans l'intention : un test portant le marqueur `characterization` qui PASSE sur la base est neanmoins classe VALIDE (au lieu de SUSPECT), ce qui permet de faire taire le portail — y compris son code de sortie `--strict` — sans que le message de commit evoque ce mecanisme d'exemption.

**Detected? `no`.** Nothing here is the import-style defect. `<failure>` versus `<error>` is
never questioned, and no finding observes that a symbol which does not exist yet lands on
either side depending on how the test spells the import. The lenses found six other things in
the same file — four of them already in this set — and walked past this one.

The `weak` label is doing real work: finding it requires knowing pytest reports an exception in
a test body as `<failure>` and a collection failure as `<error>`, then noticing both mean the
same thing here. That is domain reasoning, not reading.

**Two of the six are new, and both are live in RSquad today** — see `:165` and `:117`.

## `words-per-video-invented`

`MOTS_PAR_VIDEO = 2400`, used to price a batch before spending, was a guess. The measured median was 3238, so the estimate ran 2.3x low.

| | |
|---|---|
| introduced in | `22a9680` |
| file | `src/avd/__main__.py` |
| detectable from diff | weak |
| kind / severity | correctness / significant |

3 finding(s) survived refutation:

- **`src/avd/__main__.py:430`** — correctness
  `if not videos:
        print("\nAucune vidéo à rattraper dans ces bornes.")
        return 0`
  The command prints "Aucune vidéo à rattraper dans ces bornes." on stdout — asserting the bounds were scanned and are empty — and exits with status 0, even though not a single channel was listed. The only trace is the `ECHEC …` lines on stderr, so a user (or a wrapper script checking the return code) concludes the backfill is complete when nothing was fetched. `_cmd_discover` returns 1 in the same situation (`return 1 if decouverte.echecs else 0`).

- **`src/avd/__main__.py:431`** — correctness
  `print("\nAucune vidéo à rattraper dans ces bornes.")`
  the command prints "Aucune vidéo à rattraper dans ces bornes." — attributing a total listing failure to the bounds — and returns 0, so a caller sees a successful, empty backfill while nothing was actually listed (`_cmd_discover` returns 1 in the same situation)

- **`src/avd/__main__.py:431`** — contract
  `print("\nAucune vidéo à rattraper dans ces bornes.")
        return 0`
  the command prints "Aucune vidéo à rattraper dans ces bornes." — which is false, nothing was listed at all — and exits 0, so a script or cron wrapper treats a completely failed rattrapage as a successful no-op; `_cmd_discover` returns 1 on the same `echecs` condition

**Detected? `no`.** `MOTS_PAR_VIDEO = 2400` is in the diff (added at line 19 of the patch)
and drives a spend estimate shown to a human before payment. No lens flagged it. The three
surviving findings are all about a listing failure being printed as "no videos in these
bounds" — a real defect, and a different one.

No lens could know the true median is 3238. The actionable half — *a magic constant with no
stated provenance is pricing a spend* — was available from the diff alone and was not taken.

## `since-flag-never-bit`

`--depuis` filtered on a publication date that `yt-dlp --flat-playlist` never returns without `--extractor-args youtubetab:approximate_date`, so the flag silently matched everything.

| | |
|---|---|
| introduced in | `22a9680` |
| file | `src/avd/discover.py` |
| detectable from diff | yes |
| kind / severity | contract / significant |

4 finding(s) survived refutation:

- **`src/avd/discover.py:376`** — contract
  `return analyser_onglet(acheve.stdout or "", chaine)`
  `acheve.returncode` is never inspected, so the failure is swallowed: `analyser_onglet("")` returns `[]` and `rattraper` records a successful `Couverture` with `entrees=0` and detail "onglet /videos, 0 entrée(s) listée(s)" while `resultat.echecs` stays empty. The channel is silently treated as having no videos to catch up on, instead of appearing as a failure like `recuperer_flux` does.

- **`src/avd/discover.py:376`** — contract
  `return analyser_onglet(acheve.stdout or "", chaine)`
  The returncode and stderr of the completed process are never inspected, so the total failure is turned into an empty list. `rattraper` then records `Couverture(entrees=0, detail="onglet /videos, 0 entrée(s) listée(s), 0 retenue(s) après bornes")` and appends nothing to `resultat.echecs`, so the channel silently contributes zero candidates and the run reports success.

- **`src/avd/discover.py:376`** — contract
  `return analyser_onglet(acheve.stdout or "", chaine)`
  `acheve.returncode` and `acheve.stderr` are never inspected, so `lister_onglet` returns `[]` as if the channel genuinely had no videos. `rattraper` then appends a normal `Couverture` reading "onglet /videos, 0 entrée(s) listée(s), 0 retenue(s) après bornes" and records nothing in `resultat.echecs`, so a total failure is reported to the user as a successful, empty catch-up.

- **`src/avd/discover.py:401`** — contract
  `resultat.echecs.append("%s : %s" % (chaine.handle, erreur))
            continue`
  No `Couverture` is appended for the failing channel, unlike `decouvrir` which appends one with `detail="flux en échec"`. `resume()` derives its channel count from `len(decouverte.couvertures)`, so the header reads "0 vidéo(s) nouvelle(s) sur 2 chaîne(s)" for a three-channel run and the failing channel is missing from the per-channel table entirely.

**Detected? `no`.** Both halves of the defect are inside the diff and sixteen lines apart:
the yt-dlp command at line 363 has no `--extractor-args youtubetab:approximate_date`, and the
`--depuis` filter at line 379 compares against a `published` that will therefore always be
empty — so `not v.published` makes the filter match everything.

Verified before scoring: the flag is genuinely absent at `22a9680`, and a docstring twelve
lines up already discusses `approximate_date` precision. The code documents a precision it
never requests, which should have made this *easier*, not harder.

The four surviving findings are all about unchecked return codes on the same function.

## Excluded from scoring, and why

| case | reason |
|---|---|
| `usd-per-word-underestimate` | not findable from the diff (no) |
| `empty-retained-disables-the-filter` | found by RSquad itself — scoring it would be circular |
| `exemption-lost-on-parametrized-tests` | found by RSquad itself — scoring it would be circular |
| `missing-report-reads-as-nothing-found` | found by RSquad itself — scoring it would be circular |
| `temp-directory-stranded-on-worktree-failure` | found by RSquad itself — scoring it would be circular |

## To total it

- **detected / 4 scorable** — the headline, as a fraction. **1 / 4** on this run.
- **findings that were not the known defect** — not errors (a genuine second bug
  is not a false positive), but the number that bounds a reader's cost, and the
  one that decides whether anyone keeps using this.

Nothing here measures a false-positive rate: every case is a diff known to
contain a defect. That needs the opposite corpus — clean commits — and it is
arguably the more useful of the two.

---

Model `claude-opus-5`, 56 call(s) across 4 case(s), 7.0507 USD billed. cache read 68552 tokens against 23226 written

## The pattern of the three misses

All three misses share a shape, and it is not "the lenses are weak".

**Every miss is a defect whose wrongness is invisible in the text.** A yt-dlp command missing a
flag looks like a yt-dlp command. `MOTS_PAR_VIDEO = 2400` looks exactly like a correct constant.
`<failure>` versus `<error>` is a distinction the code makes correctly and means wrongly. In each
case the code says what it does; what it does is not what it should do, and only knowledge from
outside the file says so.

**The one hit is the opposite shape.** At `:272` a variable is assigned, used, and reassigned
before its use — self-contradictory *within the diff*. Five lenses found it independently and one
call refuted nothing.

That is a sharper limit than "it reads a diff, not a system": **the blind lenses find
contradictions, not omissions.** An omission has no anchor to quote, and `snippet` — the guard
that makes findings checkable — requires one. The contract that stops hallucination may also be
what stops this class of finding, and nothing here separates the two.

**It also relocates the conformance lens.** Two of the three misses are exactly what a stated
intent would catch: the commit message for `22a9680` announces a bounded backfill, and a filter
that matches everything contradicts it. Step [1] ran on both cases against the commit message and
produced **zero findings**. Either the commit messages are too thin to constrain, or the
conformance lens is weaker than the blind ones — and one paid run per case would tell them apart.

## What the run produced that is not in this set

On `verdict-depends-on-import-style` the lenses returned six findings on the file. Four are
already in `defects.yaml` as `self_found`. **Two were not, and both are live in RSquad's own gate
today**, verified by running it:

- **`:165` — a marker above `async def test_x` is lost, and stolen by the next test.**
  `is_test_declaration` matches `def test`, so an `async def` line matches neither branch:
  `marked` stays `True` and lands on the following plain test. Reproduced against
  `PythonPytestAdapter.exempt_names` — the async guard is not exempt and an unmarked test is.
- **`:117` — exemptions and the changed-function filter match bare names across files.**
  Two files with a `test_roundtrip` and only one of them touched: the untouched one is examined
  and reported suspect.

Both were found on the *ancestor* code and survived the extraction. This is the second time a
paid run has found live defects in the tool that made it.
