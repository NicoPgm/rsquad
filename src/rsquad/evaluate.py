"""Replaying the squad against defects whose label came from reality.

The only non-circular way to know whether a review squad finds anything is to replay it on
diffs known to contain a defect, where the label came from somebody hitting the bug — not from
a model's opinion. Everything else measures agreement with itself.

**This module selects and reports. It does not score.** Deciding whether a finding *is* the
known defect needs two judgements, and only one of them can be mechanised:

- does it anchor at the right place? — mechanical, and `anchoring` already does it;
- does its `consequence` describe the actual failure? — not mechanical, and pretending
  otherwise is how a detection rate becomes a number nobody can interpret.

So the report lays the evidence out per case and leaves a verdict line blank. At four scorable
cases that is a minute of reading. At four hundred it would be the reason nobody does this, and
that is a problem to have when the set is four hundred.

See `docs/evaluation.md` for the method, its cost, and what it cannot prove.
"""

from __future__ import annotations

from pathlib import Path

import yaml

#: A case belongs in a detection rate only if a careful reader of the diff could find it.
SCORABLE = ("yes", "weak")

#: The most a single case has cost, measured: 4 cases billed $7.05 on 2026-08-23 and the
#: dearest was ~$2.90 — a case pays one refuter per finding, and one of the four produced 18.
WORST_CASE_USD = 3.0


def within_budget(spent: float, cap: float | None) -> bool:
    """May another case start?

    The cap is enforced by refusing to **start** a case that could cross it, never by stopping
    one midway: what a case costs is only known once it is over, because every finding pays for
    its own refuter. So the guard reserves `WORST_CASE_USD` and declines when that would not
    fit.

    Conservative on purpose. The estimate this replaces was $4 against $7.05 billed — a 76 %
    overshoot, which is what an unbounded loop over cases does to a budget.
    """
    return cap is None or spent + WORST_CASE_USD <= cap


def load(path: Path) -> list[dict]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["defects"]


def partition(defects: list[dict]) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Split the set into what can be scored and what cannot, with the reason attached.

    Two exclusions, and both of them make the squad look *better* than the raw count would:

    - `detectable_from_diff: no` — a wrong constant looks like a right constant. Scoring
      against a case nobody could find measures nothing and drags the number down.
    - `self_found: true` — the case was found by RSquad. Scoring a squad on what it discovered
      measures that it can repeat itself, and drags the number up.

    Reporting the excluded ones with their reason is not politeness; a denominator chosen after
    seeing the result is how the source project published 47 % for two weeks.
    """
    scorable, excluded = [], []
    for defect in defects:
        if defect.get("detectable_from_diff") not in SCORABLE:
            excluded.append((defect, "not findable from the diff (%s)"
                             % defect.get("detectable_from_diff")))
        elif defect.get("self_found"):
            excluded.append((defect, "found by RSquad itself — scoring it would be circular"))
        else:
            scorable.append(defect)
    return scorable, excluded


def _case(defect: dict, findings: list[dict], failed: str | None) -> str:
    lines = ["## `%s`" % defect["id"], "",
             "%s" % " ".join(defect["summary"].split()), "",
             "| | |", "|---|---|",
             "| introduced in | `%s` |" % defect["introduced_in"],
             "| file | `%s` |" % defect["file"],
             "| detectable from diff | %s |" % defect["detectable_from_diff"]]
    # A set from another project need not carry this project's taxonomy. Absent is absent, not
    # "None" — the report is read by a human deciding a verdict, not by a parser.
    if defect.get("kind") or defect.get("severity"):
        lines.append("| kind / severity | %s / %s |"
                     % (defect.get("kind", "-"), defect.get("severity", "-")))
    lines.append("")

    if failed:
        lines += ["**The replay did not run: %s**" % failed, ""]
        return "\n".join(lines)

    if not findings:
        lines += ["**No finding survived.** Missed, and no judgement needed.", ""]
        return "\n".join(lines)

    lines += ["%d finding(s) survived refutation:" % len(findings), ""]
    for finding in findings:
        lines += ["- **`%s:%s`** — %s" % (finding["file"], finding["line"],
                                          finding.get("kind", "?")),
                  "  `%s`" % finding["snippet"].strip(),
                  # Parenthesised on purpose: `"%s" % a or b` binds as `("%s" % a) or b`, so a
                  # conformance finding — which has no `consequence` — rendered "None".
                  "  %s" % (finding.get("consequence") or finding.get("mismatch", "")), ""]

    lines += ["**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a",
              "finding above anchors at the defect **and** its consequence describes the actual",
              "failure. A finding that points at the right line for the wrong reason is a",
              "coincidence, and counting it inflates every later number.", ""]
    return "\n".join(lines)


def render(cases: list[tuple[dict, list[dict], str | None]],
           excluded: list[tuple[dict, str]], footer: str) -> str:
    """The report. It states fractions and denominators, and computes no rate."""
    parts = ["# Evaluation replay", "",
             "**%d scorable case(s) of %d in the set.**" % (len(cases),
                                                            len(cases) + len(excluded)), "",
             "This report does not contain a detection rate and cannot: the verdict line under",
             "each case is a human judgement. Fill them in, then read the fractions below with",
             "their denominators visible — never as a percentage. On a handful of cases a 25 %",
             "rate and a 75 % one are the same measurement.", ""]

    for defect, findings, failed in cases:
        parts.append(_case(defect, findings, failed))

    parts += ["## Excluded from scoring, and why", "",
              "| case | reason |", "|---|---|"]
    for defect, reason in excluded:
        parts.append("| `%s` | %s |" % (defect["id"], reason))

    parts += ["", "## To total it", "",
              "- **detected / %d scorable** — the headline, as a fraction." % len(cases),
              "- **findings that were not the known defect** — not errors (a genuine second bug",
              "  is not a false positive), but the number that bounds a reader's cost, and the",
              "  one that decides whether anyone keeps using this.", "",
              "Nothing here measures a false-positive rate: every case is a diff known to",
              "contain a defect. That needs the opposite corpus — clean commits — and it is",
              "arguably the more useful of the two.", "", "---", "", footer, ""]
    return "\n".join(parts)
