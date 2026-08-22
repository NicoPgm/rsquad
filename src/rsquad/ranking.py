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
    def representative(self) -> dict:
        """One finding to show for the whole entry.

        Four blind lenses that agree describe the same defect four times, in nearly the same
        words. Printing all four turns the strongest signal in the queue — agreement — into the
        longest thing to read, which is precisely backwards. The count is already in the
        heading; the body needs one account of the defect, so take the most detailed one.
        """
        return max(self.findings, key=lambda f: len(f["consequence"]) + len(f["inputs"]))


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
           errors: list[str] | None = None, footer: str = "") -> str:
    """The queue, as Markdown. Read top-down; stop when it stops being worth your time."""
    ranked = rank(entries)
    out = ["# Review queue", ""]
    out += ["%d finding(s) after both mechanical guards, in %d place(s)."
            % (sum(len(e.findings) for e in ranked), len(ranked)), ""]
    out += ["> Ordered by severity, then by how many blind lenses agreed. **Severity is the "
            "model's own claim and nothing has checked it**; agreement between lenses is "
            "independent, because they never saw each other's output. This is a reading order, "
            "not a verdict — nothing here blocks anything.", ""]

    if not ranked:
        out += ["Nothing to report. On most diffs this is the correct answer.", ""]

    for position, entry in enumerate(ranked, 1):
        mark = " · **%d lenses agree**" % len(entry.lenses) if entry.corroborated else ""
        out += ["## %d. `%s:%d` — %s%s" % (position, entry.file, entry.line, entry.severity,
                                           mark), ""]
        out += ["_%s · seen by %s_" % (", ".join(entry.kinds), ", ".join(entry.lenses)), ""]
        finding = entry.representative
        out += ["```", finding["snippet"].rstrip(), "```", ""]
        out += ["- **Inputs** — %s" % finding["inputs"]]
        out += ["- **Consequence** — %s" % finding["consequence"], ""]
        if len(entry.findings) > 1:
            out += ["_%d further account(s) of the same defect, not repeated here._"
                    % (len(entry.findings) - 1), ""]

    if dropped:
        out += ["---", "", "## Dropped by the guards (%d)" % len(dropped), ""]
        out += ["Not noise to ignore — this is how well the lenses are behaving.", ""]
        for finding, reason in dropped:
            out += ["- `%s:%s` (%s) — %s" % (finding.get("file"), finding.get("line"),
                                             finding.get("lens", "?"), reason)]
        out += [""]

    if errors:
        out += ["---", "", "## Lenses that failed (%d)" % len(errors), ""]
        out += ["A failed lens said nothing. It did not say there was nothing.", ""]
        out += ["- %s" % e for e in errors] + [""]

    if footer:
        out += ["---", "", footer, ""]
    return "\n".join(out)
