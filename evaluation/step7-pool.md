# Step 7 — the candidate pool, and what its dates cost us

**Date:** 2026-08-23
**Produced by:** `python evaluation/step7_origin.py <full clone> <full clone>` — full clones, not
`--shallow-since`: an introducing commit can be twenty years old.

Every qualifying fix since 2026-05-01 in both repositories, traced back to where its buggy line
was **first written**. Not "is it a regression" — a scan of the same commits found none
(`docs/step7-first-run.md`).

## Yield: 42 usable of 63

| | qualifying | usable | mass-import | moved | no history |
|---|---:|---:|---:|---:|---:|
| apache/commons-lang | 36 | **27** | 5 | 1 | 3 |
| FasterXML/jackson-databind | 27 | **15** | 6 | 0 | 6 |

67 %, and 42 cases is enough for a detection rate of +/- 15 points at 95 % — about **$35** at the
$0.84 per case measured on Java. The money was never the constraint; this is the pool that makes
the labelling effort the constraint instead.

## The dates are the problem, and they are also the measurement

| When the buggy line was first written | Cases |
|---|---:|
| after the May 2026 knowledge cutoff | **1** |
| 2025 - 2026-05 | 9 |
| 2020 - 2024 | 11 |
| before 2020 | 21 |

**Requiring a post-cutoff introduction leaves one case.** The control that `step7.yaml` rule 1
bought for the *fixes* cannot be bought for the *introductions*: mature libraries were written
long ago, which is the same fact that makes their defects born-with-the-code rather than
regressions.

So it stops being an exclusion and becomes a covariate. Half the pool predates 2020 and has sat
in training data in both its broken and its fixed form; a quarter is from 2025 onward. **Report
detection split by that boundary.** A large gap in favour of the old cases is evidence of
memorisation; no gap is evidence against it. Same run, same money, one extra column.

That is a weaker instrument than excluding the confound, and it is the only one this pool
supports.

## One genuine regression exists

`0594cadc9` *"Fix regression wrt #5988"*, broken by `434d6c511` (2026-05-11). The regression scan
missed it because that test required the fixed form to have stood at the identical line, and the
repair added lines rather than restoring one. The first-written criterion catches it anyway,
which is the argument for the looser criterion in one case.

## The pool

```
commons-lang: 36 qualifying fix(es) -> {'no-history': 3, 'usable': 27, 'mass-import': 5, 'moved': 1}
  4ee32aa56 Fix low surrogate false match in containsAny  <- 18f71280b (2003-07-14) Add and rework isEmpty, isNotEmpty 1 file(s)
  10f442145 Fix spurious overflow in Fraction.multiplyBy  <- 8d72d2195 (2002-12-22) Add Fraction class and associated  3 file(s)
  9288e2c95 Fix the overflow bound direction in Instants  <- 6e02b0a4d (2026-06-05) Add and use Instants.toInstant(Ins 2 file(s)
  a1c12e6d4 Fix two Javadoc errors in StringUtils (#1763  <- 9da3c6aa4 (2025-11-28) Javadoc                            1 file(s)
  b1aba6833 fix StrBuilder.lastIndexOf(String) start ind  <- 1ae0107b3 (2004-10-16) Add initial version of StrBuilder, 1 file(s)
  1d1044848 Fix int overflow in FluentBitSet.setInclusiv  <- 6e1c33667 (2021-11-30) Add FluentBitSet.                  4 file(s)
  98dc24990 Fix sign extension in BitField.getValue for   <- ef292354c (2002-12-18) BitField moved over from the [util 3 file(s)
  c99f2ddfe Fix ArrayUtils.reverse range underflow on In  <- d31f3d3f8 (2002-10-13) Initial version of ArrayUtils, inc 1 file(s)
  35d652e9e Fix Strings.CI.indexOf returning out-of-rang  <- 6941f81cd (2024-09-21) Add Strings and refactor StringUti 9 file(s)
  aafee70bf fix NumberUtils min/max varargs dropping the  <- 2d06a7ce8 (2003-06-24) NumberUtils moved to math subpacka 9 file(s)
  7e29cde71 fix StringUtils.getDigits dropping supplemen  <- 91ac16e0b (2009-12-17) Applying Niall's patch from LANG-5 2 file(s)
  6c4269eb8 fix WordUtils.containsAllWords missing words  <- 47367eb9a (2003-08-17) Rename WordWrapUtils to WordUtils  5 file(s)
  6334440d5 Fold supplementary code points in CharSequen  <- 2541a62de (2011-04-07) Moving the CharSequence specific m 4 file(s)
  581ce79c4 [LANG-1824] Fix Strings.replace overflow on   <- 6941f81cd (2024-09-21) Add Strings and refactor StringUti 9 file(s)
  13d93944f [LANG-1824] Fix Strings.replace overflow on   <- 6941f81cd (2024-09-21) Add Strings and refactor StringUti 9 file(s)
  13d25e059 Fix int overflow in DurationFormatUtils.form  <- 177d40989 (2004-09-27) removed the weak assumptions for n 3 file(s)
  a0ffef035 fix silent int overflow in Fraction.getFract  <- 8d72d2195 (2002-12-22) Add Fraction class and associated  3 file(s)
  ddf5625d5 Fix int mask sign extension in BitField long  <- ef292354c (2002-12-18) BitField moved over from the [util 3 file(s)
  46d9a80e5 Fix spurious overflow in Fraction.add/subtra  <- 8d72d2195 (2002-12-22) Add Fraction class and associated  3 file(s)
  8e0dd9df1 fix substringAfter(Last) for supplementary c  <- d68a7a418 (2020-06-27) Add org.apache.commons.lang3.Strin 3 file(s)
  86ed42da5 Fix RandomStringUtils.random() false rejecti  <- f382d61a0 (2024-07-06) Reimplement RandomStringUtils on t 4 file(s)
  bdd674f7c fix CharSequenceUtils.lastIndexOf for supple  <- 2541a62de (2011-04-07) Moving the CharSequence specific m 4 file(s)
  0b4a9d95d LocaleUtils.parseLocale(String) operator pre  <- 04e1537d3 (2005-08-16) Initial version of LocaleUtils for 1 file(s)
  9f7d3b5ec Fix `WordUtils.wrap` for `wrapOn` matches di  <- 54facb4fd (2015-05-05) DOC: StringUtils.containsAny. ADD: 3 file(s)
  552d7d07d ToStringStyle.appendDetail(StringBuffer,Stri  <- 12c325974 (2002-09-17) Initial checkin of ToStringBuilder 3 file(s)
  313d877d5 Two fixes in RandomStringUtils.random(int, i  <- f382d61a0 (2024-07-06) Reimplement RandomStringUtils on t 4 file(s)
  c07bc828f Fix typo in SystemProperties.JDK_XML_ENTITY_  <- 9a313ed46 (2024-05-01) Add SystemProperties constants for 3 file(s)
========================================================================================================
jackson-databind: 27 qualifying fix(es) -> {'no-history': 6, 'mass-import': 6, 'usable': 15}
  7d114f50a Fix DefaultCacheProvider.Builder cache defau  <- 341f8d360 (2023-09-05) Add a way to configure `Deserializ 7 file(s)
  f3c3296a2 Fix QName object deserialization to reject n  <- 70511f029 (2025-02-14) Fix #4771: Support OBJECT shape fo 5 file(s)
  6a17bd06b Fix #4762: @JsonValue should honor @JsonIncl  <- f4441ecc7 (2012-01-31) Convert JsonValueSerializer to Con 2 file(s)
  728a2950a Fix #6059 (#6061)                             <- 43ef2bc5f (2021-03-02) Start implementing #2411; complete 5 file(s)
  eced97ee4 Fix #1803: `TreeTraversingParser` should all  <- 6a66bb99e (2021-02-01) Fix #3002                          5 file(s)
  93a315d52 Fix #6040 (#6042)                             <- 73f858441 (2026-01-11) Fix #2124 (or edge case thereof) ( 5 file(s)
  434bb7d6c Fix #6031, @JsonAlias/@JsonIgnore (#6035)     <- 4c0ef09ee (2013-01-12) Rename creator properties in _rena 1 file(s)
  a7062a263 Fix #6028: improve error message for unwrapp  <- ebdc36fdc (2026-04-18) Fix #2883: detect and report on co 5 file(s)
  f302386c9 Fix #5980: current value wrong for parser wi  <- d16420f35 (2025-03-15) Fix #4938 Allow `@JsonCreator` to  5 file(s)
  43f53b48b Fix #6001: custom `@JsonUnwrapped` deseriali  <- 118fba4bb (2025-12-20) Fix #650: @JsonUnwrapped prevents  8 file(s)
  26a8c70bd Part 2 of #5988 fix (allow Enum types as par  <- 434d6c511 (2026-05-11) `PolymorphicTypeValidator` needs t 6 file(s)
  0594cadc9 Fix regression wrt #5988 (#5990)              <- 434d6c511 (2026-05-11) `PolymorphicTypeValidator` needs t 6 file(s)
  01d1692c8 Backport fix for #5981 in 2.18 branch (#5984  <- 533fe319a (2019-11-06) Fix #2534                          3 file(s)
  24529da29 Fix #5981: `BasicPolymorphicTypeValidator` s  <- 2c94ecc19 (2025-02-13) Fix Javadoc errors                 9 file(s)
  6d028931a Apply per-property DYNAMIC typing override t  <- 67942a586 (2012-01-31) ...                                4 file(s)
```

## Correction, same day: the pool is not 41. It is about 10, and 6 distinct diffs.

Two defects in the classifier above, both found by running it:

**Rule 4 was missing** — a Javadoc-only fix ("Fix two Javadoc errors in StringUtils") sat in the
pool as a case. One entry removed; 41 usable.

**And the paths are wrong.** `git log -L` follows renames, so it returns the right origin commit
— but every check made afterwards used **today's** path. `Fraction.java` lived under
`src/java/org/apache/commons/lang/` in 2002; `DefaultCacheProvider.java` under
`com/fasterxml/jackson/` before the 3.x repackaging. Half the pool reported "0 lines changed",
which reads as *nothing to review* rather than *wrong path*.

A rename-walking resolver recovered some of them and misfired on others — two repackagings
(`lang` → `lang3`, `com.fasterxml.jackson` → `tools.jackson`) across twenty years of history is
not a problem to solve by iterating on a heuristic at the end of a long day.

**What survives with certainty** — the path unchanged between origin and fix, and a non-empty
diff:

| repo | cases | distinct origin commits |
|---|---:|---:|
| apache/commons-lang | 8 | 4 |
| FasterXML/jackson-databind | 2 | 2 |
| | **10** | **6** |

Three commons-lang cases share `6941f81cd`, two share `2541a62de`. So the independent sample is
smaller than ten.

**Ten cases give +/- 30 points.** That is the smoke test we were trying to escape, and freezing
it would produce another number nobody can act on. The pool is not frozen.

### This is the third distinct obstacle, and they share one cause

1. defects are born with the code, so there are no regressions to replay;
2. the introductions predate the knowledge cutoff by years, so the memorisation control is lost;
3. the paths have been repackaged since, so the diff cannot be reconstructed reliably.

All three are consequences of **the repositories being old**. A project a few years old has its
introductions inside its own recent history, at paths that never moved, after the cutoff.

The deferred question — *add a younger repository?* — is no longer an improvement to consider.
It is the precondition.
