"""Step [4] — the ranked queue. It orders human attention; it does not decide.

This is the lesson the source project paid for in its layer-2 clustering: no threshold separated
well enough to decide alone, but the top of the ranking was good. A system that ranks beats one
that claims to replace the reader, and presenting a ranking as a verdict would be a mistake that
only shows up once somebody trusts it.

So: no pass/fail, no exit code, no gate. Only step [0] blocks. Opinions comment.

Two signals order the queue, and only one of them is trustworthy.

**Corroboration is earned.** The lenses are blind to each other, so two of them landing on the
same lines is independent agreement, not an echo. That is a real signal.

**Severity is self-reported.** The model chose it, nothing validated it, and it is ranked first
anyway because a claim of "blocking" deserves a human glance even alone. The queue says so in
its own header rather than letting the order imply a confidence nobody measured.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SEVERITY_ORDER = {"blocking": 0, "significant": 1, "minor": 2}

#: The queue renders two finding shapes. A blind lens states the inputs that trigger a defect and
#: the consequence that follows; the conformance lens quotes a requirement and says what the code
#: does instead. Same location, same severity, different claim — and labelling a quoted
#: requirement "Inputs" would make the strongest guard in step [1] read like a guess.
SHAPES = (("inputs", "consequence", "Inputs", "Consequence"),
          ("requirement", "mismatch", "Requirement", "Mismatch"))


def _shape(finding: dict) -> tuple[str, str, str, str]:
    for first, second, left, right in SHAPES:
        if first in finding:
            return first, second, left, right
    raise KeyError("finding matches no known shape: %s" % sorted(finding))


def detail(finding: dict) -> tuple[str, str, str, str]:
    """(left label, left text, right label, right text) for whichever shape this is."""
    first, second, left, right = _shape(finding)
    return left, finding[first], right, finding[second]

#: Two findings this close, in the same file, are treated as the same defect seen twice.
NEAR = 3


@dataclass
class Entry:
    """One defect, as reported by one or more lenses."""

    file: str
    line: int
    findings: list[dict] = field(default_factory=list)

    @property
    def lenses(self) -> list[str]:
        return sorted({f.get("lens", "?") for f in self.findings})

    @property
    def severity(self) -> str:
        return min((f["severity"] for f in self.findings), key=lambda s: SEVERITY_ORDER[s])

    @property
    def kinds(self) -> list[str]:
        return sorted({f["kind"] for f in self.findings})

    @property
    def corroborated(self) -> bool:
        return len(self.lenses) > 1

    @property
    def representatives(self) -> list[dict]:
        """One account per shape, most detailed first.

        Four blind lenses that agree describe the same defect four times in nearly the same
        words; printing all four turns the strongest signal in the queue — agreement — into the
        longest thing to read. So one account per shape, not per finding.

        **Per shape, not one overall.** When the conformance lens lands on the same lines as the
        blind ones, its account is the only one carrying a quoted requirement, and picking a
        single most-detailed representative buried it: the first real run reported
        `contradicts` on a line and showed nothing about what it contradicted.
        """
        def weight(finding: dict) -> int:
            first, second, _, _ = _shape(finding)
            return len(finding[first]) + len(finding[second])

        best: dict[str, dict] = {}
        for finding in self.findings:
            key = _shape(finding)[0]
            if key not in best or weight(finding) > weight(best[key]):
                best[key] = finding
        return [best[key] for key, *_ in SHAPES if key in best]

    @property
    def representative(self) -> dict:
        return self.representatives[0]


def group(findings: list[dict], near: int = NEAR) -> list[Entry]:
    """Fold findings that name the same place into one entry.

    Deliberately positional rather than semantic: two lenses describing the same defect in
    different words still land on the same lines, and judging whether two *descriptions* mean
    the same thing would need a model — which would put an unverified judgement inside the
    mechanism that is supposed to be the trustworthy half.
    """
    entries: list[Entry] = []
    for finding in sorted(findings, key=lambda f: (f["file"], f["line"])):
        for entry in entries:
            if entry.file == finding["file"] and abs(entry.line - finding["line"]) <= near:
                entry.findings.append(finding)
                break
        else:
            entries.append(Entry(file=finding["file"], line=finding["line"],
                                 findings=[finding]))
    return entries


def rank(entries: list[Entry]) -> list[Entry]:
    return sorted(entries, key=lambda e: (SEVERITY_ORDER[e.severity], -len(e.lenses),
                                          e.file, e.line))


def render(entries: list[Entry], dropped: list[tuple[dict, str]] | None = None,
           errors: list[str] | None = None, footer: str = "", refuted=None) -> str:
    """The queue, as Markdown. Read top-down; stop when it stops being worth your time."""
    ranked = rank(entries)
    out = ["# Review queue", ""]
    out += ["%d finding(s) after both mechanical guards, in %d place(s)."
            % (sum(len(e.findings) for e in ranked), len(ranked)), ""]
    out += ["> Ordered by severity, then by how many blind lenses agreed. **Severity is the "
            "model's own claim and nothing has checked it**; agreement between lenses is "
            "independent, because they never saw each other's output. This is a reading order, "
            "not a verdict — nothing here blocks anything.", ""]
    if refuted is not None:
        out += ["> Every finding below **survived a refuter** that was given the claim without "
                "its author, its severity or the other findings, and told to kill it. %d claim(s) "
                "did not survive." % len(refuted), ""]

    if not ranked:
        out += ["Nothing to report. On most diffs this is the correct answer.", ""]

    for position, entry in enumerate(ranked, 1):
        mark = " · **%d lenses agree**" % len(entry.lenses) if entry.corroborated else ""
        out += ["## %d. `%s:%d` — %s%s" % (position, entry.file, entry.line, entry.severity,
                                           mark), ""]
        out += ["_%s · seen by %s_" % (", ".join(entry.kinds), ", ".join(entry.lenses)), ""]
        shown = entry.representatives
        out += ["```", shown[0]["snippet"].rstrip(), "```", ""]
        for finding in shown:
            left, left_text, right, right_text = detail(finding)
            out += ["- **%s** — %s" % (left, left_text)]
            out += ["- **%s** — %s" % (right, right_text), ""]
        remaining = len(entry.findings) - len(shown)
        if remaining:
            out += ["_%d further account(s) of the same defect, not repeated here._"
                    % remaining, ""]

    if dropped:
        out += ["---", "", "## Dropped by the guards (%d)" % len(dropped), ""]
        out += ["Not noise to ignore — this is how well the lenses are behaving.", ""]
        for finding, reason in dropped:
            out += ["- `%s:%s` (%s) — %s" % (finding.get("file"), finding.get("line"),
                                             finding.get("lens", "?"), reason)]
        out += [""]

    if refuted:
        out += ["---", "", "## Refuted (%d)" % len(refuted), ""]
        out += ["Not noise. This is the measurement of how much of what the lenses produce is "
                "plausible rather than true.", ""]
        for verdict in refuted:
            finding = verdict.finding
            out += ["- `%s:%s` (%s) — **%s** — %s"
                    % (finding.get("file"), finding.get("line"), finding.get("lens", "?"),
                       verdict.verdict, verdict.reason)]
        out += [""]

    if errors:
        out += ["---", "", "## Lenses that failed (%d)" % len(errors), ""]
        out += ["A failed lens said nothing. It did not say there was nothing.", ""]
        out += ["- %s" % e for e in errors] + [""]

    if footer:
        out += ["---", "", footer, ""]
    return "\n".join(out)
