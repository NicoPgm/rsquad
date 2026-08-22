"""Step [1] — the conformance lens. No network anywhere in this file.

The test that matters is the second anchor. A blind lens can hallucinate code and the anchoring
guard catches it; this lens can hallucinate a *requirement*, and only a check against the intent
catches that.
"""

import inspect
import json

import pytest

from rsquad.chunking import Unit
from rsquad.conformance import (EFFORT, LENS, UNQUOTED, Intent, gather, interpret, request,
                                sift)

UNIT = Unit(
    file="a.py",
    diff="@@ -1,2 +1,3 @@\n+    return fiches[0]\n",
    source="def resume(fiches):\n    return fiches[0]\n",
    numbered="1\tdef resume(fiches):\n2\t    return fiches[0]",
)

INTENT = Intent(parts=[("commit message", "Return None when the corpus is empty."),
                       ("docs/specs/03.md", "The summary must never raise on an empty corpus.")])

MISMATCH = {
    "file": "a.py", "line": 2, "snippet": "return fiches[0]",
    "requirement": "Return None when the corpus is empty.",
    "mismatch": "it indexes straight into the list and raises IndexError",
    "kind": "unimplemented", "severity": "significant",
}


# ------------------------------------------------------------------ the second anchor

def test_a_requirement_must_be_quoted_from_the_intent():
    kept, dropped = sift([MISMATCH], UNIT, INTENT)
    assert kept and not dropped


def test_an_invented_requirement_is_dropped():
    """The failure mode this lens has and no other does.

    A fabricated requirement sounds authoritative and sends a reader to argue with a document
    that never said it. It is worse than a missed mismatch.
    """
    invented = dict(MISMATCH, requirement="The summary must be at most 200 words.")
    kept, dropped = sift([invented], UNIT, INTENT)
    assert kept == []
    assert dropped[0][1] == UNQUOTED


def test_a_paraphrased_requirement_is_dropped():
    """Close is not quoted. A paraphrase is where an invented requirement hides."""
    paraphrased = dict(MISMATCH, requirement="Return nothing when there are no cards.")
    assert sift([paraphrased], UNIT, INTENT)[0] == []


def test_reflowed_whitespace_still_counts_as_quoted():
    """Rejecting a true quote over line wrapping would be a false negative, not rigour."""
    wrapped = dict(MISMATCH, requirement="Return None   when the corpus\nis empty.")
    assert sift([wrapped], UNIT, INTENT)[0]


def test_a_requirement_may_come_from_any_part_of_the_intent():
    from_spec = dict(MISMATCH,
                     requirement="The summary must never raise on an empty corpus.")
    assert sift([from_spec], UNIT, INTENT)[0]


def test_the_code_side_is_still_anchored_too():
    """Both ends, or neither is worth anything."""
    ghost = dict(MISMATCH, snippet="return fiches.first()")
    assert sift([ghost], UNIT, INTENT)[0] == []


# ------------------------------------------------------------------ the intent is named

def test_the_intent_is_never_discovered_by_walking_directories(tmp_path, monkeypatch):
    """One directory walk away from undoing ADR-0002, and wrong about which file matters."""
    assert set(inspect.signature(gather).parameters) == {"head", "repo", "specs"}


def test_a_named_document_that_does_not_exist_is_an_error_not_a_silent_skip(monkeypatch):
    """Silently reviewing against a missing spec would report "conformant" for the wrong reason."""
    from rsquad import conformance
    monkeypatch.setattr(conformance, "git",
                        lambda args, repo=None: type("R", (), {"stdout": "msg"})())
    with pytest.raises(SystemExit):
        gather("head", None, ["docs/does-not-exist.md"])


def test_the_commit_message_is_always_part_of_the_intent(monkeypatch):
    """It is the author's own statement of what they meant, and it is free."""
    from rsquad import conformance
    monkeypatch.setattr(conformance, "git",
                        lambda args, repo=None: type("R", (), {"stdout": "Fix the thing\n"})())
    intent = gather("head", None, None)
    assert intent.sources == ["commit message"]
    assert intent.quotes("Fix the thing")


def test_an_empty_intent_quotes_nothing():
    assert Intent().quotes("anything") is False


# ------------------------------------------------------------------ request shape

def test_the_intent_reaches_this_lens_and_only_this_lens():
    payload = json.dumps(request(UNIT, INTENT))
    assert "must never raise on an empty corpus" in payload


def test_the_intent_stays_out_of_the_cached_prefix():
    """It differs per commit. In the system block it would cost a cache write every run."""
    blocks = request(UNIT, INTENT)["system"]
    assert len(blocks) == 1
    assert "empty corpus" not in blocks[0]["text"]
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}


def test_the_conformance_vocabulary_is_its_own():
    """Shown the blind lenses' kinds, it would report bugs instead of divergences — the job
    three better-placed readers already do."""
    enum = request(UNIT, INTENT)["output_config"]["format"]["schema"]["$defs"]["kind"]["enum"]
    assert "stale-intent" in enum
    assert "boundary" not in enum


def test_findings_are_tagged_with_this_lens():
    kept, _ = interpret(UNIT, INTENT, json.dumps({"findings": [MISMATCH]}))
    assert kept[0]["lens"] == LENS


def test_it_runs_at_high_effort_not_the_highest():
    """Reading prose against code is not walking execution paths; the refuter needs more."""
    assert request(UNIT, INTENT)["output_config"]["effort"] == EFFORT


# ------------------------------------------------------------------ the queue takes both shapes

def test_the_queue_labels_a_requirement_as_a_requirement():
    """Calling a quoted requirement "Inputs" would make the strongest guard in this step read
    like a guess."""
    from rsquad.ranking import group, render
    text = render(group([dict(MISMATCH, lens=LENS)]))
    assert "**Requirement**" in text
    assert "**Inputs**" not in text


def test_the_two_shapes_rank_together():
    from rsquad.ranking import group, rank
    blind = {"file": "a.py", "line": 40, "snippet": "x", "kind": "boundary",
             "severity": "blocking", "inputs": "i", "consequence": "c", "lens": "repro"}
    ranked = rank(group([dict(MISMATCH, lens=LENS), blind]))
    assert ranked[0].severity == "blocking"
    assert len(ranked) == 2


def test_a_conformance_account_is_not_buried_by_a_blind_one():
    """When both land on the same lines, the conformance account is the only one carrying a
    quoted requirement. Picking one most-detailed representative hid it: the first real run
    reported `contradicts` on a line and showed nothing about what it contradicted.
    """
    from rsquad.ranking import group, render
    blind = {"file": "a.py", "line": 2, "snippet": "return fiches[0]", "kind": "boundary",
             "severity": "blocking", "lens": "repro",
             "inputs": "a very long description of the inputs " * 5,
             "consequence": "a very long description of the consequence " * 5}
    text = render(group([blind, dict(MISMATCH, lens=LENS)]))
    assert "**Inputs**" in text and "**Requirement**" in text


def test_a_conformance_finding_is_never_sent_to_the_refuter():
    """It was documented as unsupported and then handed one anyway, which crashed the run.

    Documenting a gap does not close it.
    """
    from rsquad.refutation import NOT_REFUTABLE, refutable, refute_all
    assert refutable(MISMATCH) is False
    verdicts = refute_all([dict(MISMATCH, lens=LENS)], {"a.py": UNIT})
    assert [v.error for v in verdicts] == [NOT_REFUTABLE]


def test_an_unrefuted_conformance_finding_still_reaches_the_reader():
    """A claim nobody could contest is not a claim nobody should see — but the run says so."""
    from rsquad.refutation import Verdict, survivors, NOT_REFUTABLE
    kept, killed = survivors([Verdict(finding=dict(MISMATCH, lens=LENS),
                                      error=NOT_REFUTABLE)])
    assert len(kept) == 1 and killed == []
