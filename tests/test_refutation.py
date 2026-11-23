"""Step [3] — refutation. No network anywhere in this file.

The tests that matter are the two asymmetries: the refuter inherits no framing from the finder,
and a broken refutation does not get to kill anything.
"""

import inspect
import json

import pytest

from rsquad.chunking import Unit
from rsquad.refutation import (EFFORT, STANDS, UNANCHORED, Verdict, interpret, refute,
                               refute_all, request, survivors)

UNIT = Unit(
    file="a.py",
    diff="@@ -1,3 +1,4 @@\n+    premiere = fiches[0]\n",
    source="def resume(fiches):\n    premiere = fiches[0]\n    return premiere.summary\n",
    numbered="1\tdef resume(fiches):\n2\t    premiere = fiches[0]\n3\t    return premiere.summary",
)

FINDING = {
    "file": "a.py", "line": 2, "snippet": "premiere = fiches[0]",
    "kind": "boundary", "severity": "blocking", "lens": "repro",
    "inputs": "fiches = []", "consequence": "raises IndexError",
}


def _reply(verdict=STANDS, snippet="premiere = fiches[0]", line=2):
    return json.dumps({"verdict": verdict, "reason": "because", "evidence_line": line,
                       "evidence_snippet": snippet})


# ------------------------------------------------------------------ no inherited framing

def test_the_refuter_is_told_the_claim_and_not_who_made_it():
    """`lens`, `severity` and `kind` are the finder's opinions, and opinions are not evidence.

    A refuter that saw "blocking, from the repro lens" would be grading a colleague instead of
    reading code — and would inherit exactly the confidence it exists to test.
    """
    payload = json.dumps(request(UNIT, FINDING))
    assert "repro" not in payload
    assert "blocking" not in payload
    assert "boundary" not in payload


def test_the_claim_itself_does_reach_the_refuter():
    """Refuting requires knowing what is claimed: the line, the code, the inputs, the effect."""
    payload = json.dumps(request(UNIT, FINDING))
    for part in ("premiere = fiches[0]", "fiches = []", "raises IndexError"):
        assert part in payload


def test_no_other_finding_can_reach_it():
    """One claim per context. Findings judged together would stop being independent."""
    assert set(inspect.signature(request).parameters) == {"unit", "finding", "model"}


def test_the_verdict_vocabulary_is_closed_and_constrained_mechanically():
    fmt = request(UNIT, FINDING)["output_config"]["format"]
    assert fmt["type"] == "json_schema"
    assert STANDS in fmt["schema"]["$defs"]["verdict"]["enum"]


def test_refutation_runs_at_the_highest_effort():
    """Its mistakes are the least visible in the squad: a wrong refutation deletes a real
    finding and leaves nothing in the queue to notice."""
    assert request(UNIT, FINDING)["output_config"]["effort"] == EFFORT


# ------------------------------------------------------------------ a refutation is checkable

def test_evidence_must_anchor_like_any_finding():
    verdict = interpret(UNIT, FINDING, _reply(verdict="already-handled"))
    assert verdict.anchored and verdict.refutes


@pytest.mark.guard
def test_invented_evidence_does_not_refute_anything():
    """The asymmetry inside the asymmetry.

    The rule on doubt governs the refuter's reasoning, not its malfunctions. A verdict whose
    evidence is not in the file is a broken response, and letting one through would mean
    hallucinated evidence silently deleting real work.
    """
    verdict = interpret(UNIT, FINDING, _reply(verdict="misread", snippet="fiches.first()"))
    assert verdict.anchored is False
    assert verdict.refutes is False


def test_evidence_at_the_wrong_line_does_not_refute_either():
    verdict = interpret(UNIT, FINDING, _reply(verdict="not-reachable", line=99))
    assert verdict.refutes is False


def test_stands_never_refutes_however_well_evidenced():
    assert interpret(UNIT, FINDING, _reply(verdict=STANDS)).refutes is False


# ------------------------------------------------------------------ failure isolation

class _Boom:
    def __init__(self, error):
        self._error = error
        self.messages = self

    def create(self, **_):
        raise self._error


def test_a_dead_refuter_leaves_the_finding_standing():
    """The safe direction: the cost is a reader's minute, where the other costs a real defect."""
    verdict = refute(UNIT, FINDING, client=_Boom(RuntimeError("socket exploded")))
    assert verdict.error and verdict.refutes is False


def test_an_unparsable_verdict_does_not_refute():
    class _Garbage:
        messages = property(lambda self: self)

        def create(self, **_):
            return type("R", (), {"stop_reason": "end_turn", "usage": type(
                "U", (), {"input_tokens": 1, "output_tokens": 1})(),
                "content": [type("B", (), {"type": "text", "text": "not json"})()]})()

    assert refute(UNIT, FINDING, client=_Garbage()).refutes is False


def test_a_finding_about_an_unknown_file_is_skipped_not_crashed():
    assert refute_all([dict(FINDING, file="ailleurs.py")], {"a.py": UNIT}) == []


# ------------------------------------------------------------------ what comes out

def test_survivors_splits_and_keeps_both_halves():
    """What the refuter removed is the measurement of how much of the output was plausible
    rather than true. Burying it would hide the most useful number in the run."""
    killed = Verdict(finding=FINDING, verdict="misread", anchored=True)
    stood = Verdict(finding=dict(FINDING, line=3), verdict=STANDS, anchored=True)
    kept, removed = survivors([killed, stood])
    assert [f["line"] for f in kept] == [3]
    assert removed == [killed]


def test_a_surviving_finding_carries_the_verdict_it_survived():
    stood = Verdict(finding=FINDING, verdict=STANDS, anchored=True)
    kept, _ = survivors([stood])
    assert kept[0]["verdict"] == STANDS


def test_a_broken_verdict_leaves_its_finding_in_the_queue():
    broken = Verdict(finding=FINDING, verdict="misread", anchored=False, error=UNANCHORED)
    kept, removed = survivors([broken])
    assert len(kept) == 1 and removed == []


# ------------------------------------------------------------------ a named doubt (ADR-0009)

def test_undecided_lets_the_finding_through_and_says_so():
    """ADR-0011 reverses ADR-0006 on doubt: a claim falls on evidence only. The finding reaches
    the queue carrying the verdict, so the reader can see the refuter could not decide."""
    verdict = interpret(UNIT, FINDING, _reply("undecided"))
    assert not verdict.refutes
    kept, killed = survivors([verdict])
    assert killed == [] and kept[0]["verdict"] == "undecided"


@pytest.mark.guard
def test_an_undecided_verdict_must_still_quote_real_code():
    """Naming doubt is not a way around the anchoring guard."""
    verdict = interpret(UNIT, FINDING, _reply("undecided", snippet="nowhere in the file"))
    assert verdict.anchored is False
    assert not verdict.refutes
