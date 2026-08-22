"""The two mechanical guards. No model, no judgement — a finding either passes or is dropped.

**Anchoring.** Every finding must quote code that literally exists, near the line it claims.
This is the direct transposition of the rule that keeps the source project's cards honest: an
entity that is not literally in the transcript is deleted, no matter how plausible it reads. It
is the only guard against hallucination that depends on no provider, no model and no prompt.

Checking the snippet *near the claimed line* rather than anywhere in the file is what makes it
bite twice: it validates the quote and the location together. A finding that quotes real code
but points at the wrong place is still a finding a human cannot act on.

**Reproduction or nothing.** `inputs` and `consequence` are required by the schema and must not
be vacuous. "This is fragile" does not ship. "If `items` is empty, line 42 raises" does — and it
is checkable, therefore refutable, therefore worth arguing about on evidence.

Be clear about what this second guard can and cannot do. It rejects the empty and the obviously
evasive; it cannot tell a specific claim from a confidently-worded vague one. That is the
refuter's job, in step [3]. A mechanical guard that pretended to judge prose quality would be
exactly the kind of check that measures its own vocabulary.
"""

from __future__ import annotations

#: How far from the claimed line the snippet may actually sit. Small on purpose: the point is
#: to validate the location, and a wide window would validate nothing.
WINDOW = 3

#: Answers that fill the field without saying anything. Matched whole, after normalisation.
VACUOUS = frozenset({
    "n/a", "na", "none", "null", "nil", "-", "--", "tbd", "todo", "unknown", "unclear",
    "any", "various", "see above", "not applicable", "as described", "same as above",
})

#: Below this, a value is punctuation rather than a claim. Deliberately low: rejecting a short
#: but real answer ("x = 0", "empty list") would cost more than letting it through to the refuter.
MINIMUM = 3

NOT_ANCHORED = "snippet does not appear within %d lines of the claimed line" % WINDOW
UNKNOWN_FILE = "file is not among the files under review"
VACUOUS_INPUTS = "inputs say nothing concrete"
VACUOUS_CONSEQUENCE = "consequence says nothing observable"


def normalise(text: str) -> str:
    """Collapse every run of whitespace to one space.

    Models reflow indentation and wrap lines; comparing raw text would reject correct quotes
    for reasons that have nothing to do with truthfulness. Collapsing is the smallest
    normalisation that survives that without letting a paraphrase through.
    """
    return " ".join(text.split())


def anchored(snippet: str, source: str, line: int, window: int = WINDOW) -> bool:
    """Does `snippet` appear in `source` within `window` lines of `line` (1-indexed)?"""
    needle = normalise(snippet)
    if not needle:
        return False
    lines = source.splitlines()
    height = max(1, len(snippet.splitlines()))
    first = max(0, line - 1 - window)
    last = min(len(lines), line - 1 + window + height)
    if first >= last:
        return False
    return needle in normalise("\n".join(lines[first:last]))


def vacuous(text: str) -> bool:
    bare = normalise(text).lower().rstrip(".!")
    return not bare or len(bare) < MINIMUM or bare in VACUOUS


def reject(finding: dict, sources: dict[str, str]) -> str | None:
    """Why this finding cannot be kept, or None if it survives both guards."""
    source = sources.get(finding["file"])
    if source is None:
        return UNKNOWN_FILE
    if not anchored(finding["snippet"], source, finding["line"]):
        return NOT_ANCHORED
    if vacuous(finding["inputs"]):
        return VACUOUS_INPUTS
    if vacuous(finding["consequence"]):
        return VACUOUS_CONSEQUENCE
    return None


def sift(findings: list[dict],
         sources: dict[str, str]) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Split findings into (kept, dropped-with-reason).

    Both halves are returned because a silent drop reads as "nothing was there". What the guards
    reject is a measurement of how well the lenses are behaving, and it belongs in the run
    report, not in a wastebasket.
    """
    kept, dropped = [], []
    for finding in findings:
        reason = reject(finding, sources)
        (dropped.append((finding, reason)) if reason else kept.append(finding))
    return kept, dropped
