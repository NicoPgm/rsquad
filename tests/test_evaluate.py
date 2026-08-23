"""Replaying against ground truth. No network — the findings are written by hand.

What is worth testing here is not arithmetic, it is the discipline: which cases are allowed
into a denominator, and that the report never hands anybody a number it has not earned.
"""

from rsquad import evaluate

REAL = {"id": "a-real-one", "summary": "resolves the revision then overwrites it",
        "repo": "x", "introduced_in": "abc1234", "file": "tools/x.py",
        "kind": "correctness", "severity": "significant",
        "detectable_from_diff": "yes", "self_found": False}

WEAK = dict(REAL, id="a-weak-one", detectable_from_diff="weak")
INVISIBLE = dict(REAL, id="not-in-the-diff", detectable_from_diff="no")
CIRCULAR = dict(REAL, id="found-by-us", self_found=True)

FINDING = {"file": "tools/x.py", "line": 272, "snippet": "tete = HEAD", "kind": "correctness",
           "severity": "blocking", "inputs": "--tete on a past commit",
           "consequence": "grades today's tests against an old base"}


# ------------------------------------------------------------------ who gets a denominator

def test_a_defect_nobody_could_find_is_excluded():
    """Scoring against it drags the number down and measures nothing."""
    scorable, excluded = evaluate.partition([REAL, INVISIBLE])
    assert [d["id"] for d in scorable] == ["a-real-one"]
    assert excluded[0][0]["id"] == "not-in-the-diff" and "diff" in excluded[0][1]


def test_a_defect_the_squad_found_itself_is_excluded():
    """It drags the number the other way, and measures only that it can repeat itself."""
    scorable, excluded = evaluate.partition([REAL, CIRCULAR])
    assert [d["id"] for d in scorable] == ["a-real-one"]
    assert "circular" in excluded[0][1]


def test_weak_still_counts():
    """Findable only as a smell is still findable. Excluding it would flatter the result."""
    scorable, _ = evaluate.partition([WEAK])
    assert [d["id"] for d in scorable] == ["a-weak-one"]


def test_every_exclusion_carries_its_reason():
    """A denominator chosen after seeing the result is how the source project published 47 %."""
    _, excluded = evaluate.partition([INVISIBLE, CIRCULAR])
    assert all(reason for _, reason in excluded)


# ------------------------------------------------------------------ what the report will not do

def test_the_report_states_a_denominator_and_no_rate():
    text = evaluate.render([(REAL, [FINDING], None)], [(INVISIBLE, "why")], "billed")
    assert "1 scorable case(s) of 2" in text
    assert "does not contain a detection rate" in text


def test_a_case_leaves_its_verdict_to_a_human():
    """Anchoring is mechanical; whether the consequence is the actual failure is not."""
    text = evaluate.render([(REAL, [FINDING], None)], [], "billed")
    assert "**Detected?** `?`" in text
    assert "tools/x.py:272" in text and "grades today's tests" in text


def test_a_case_that_could_not_run_is_not_reported_as_a_miss():
    """Saying nothing and being unable to speak look identical in a total, and only one of
    them means the squad failed to find the defect."""
    text = evaluate.render([(REAL, [], "abc1234 does not exist here")], [], "billed")
    assert "did not run" in text
    assert "**Detected?**" not in text


def test_a_case_with_nothing_surviving_needs_no_judgement():
    text = evaluate.render([(REAL, [], None)], [], "billed")
    assert "No finding survived" in text and "**Detected?**" not in text


def test_the_report_says_what_it_cannot_measure():
    """Every case is a diff known to contain a defect, so there is no false-positive rate in
    here at all — and that is the more useful of the two measurements."""
    text = evaluate.render([(REAL, [FINDING], None)], [], "billed")
    assert "false-positive rate" in text and "clean commits" in text


def test_a_conformance_finding_renders_its_mismatch():
    """It has no `consequence`, and `"%s" % a or b` binds as `("%s" % a) or b` — so the report
    said "None" where the account should have been."""
    mismatch = {"file": "tools/x.py", "line": 272, "snippet": "tete = HEAD",
                "kind": "unimplemented", "severity": "minor",
                "requirement": "--tete runs it on a past commit",
                "mismatch": "the resolved revision is overwritten"}
    text = evaluate.render([(REAL, [mismatch], None)], [], "billed")
    assert "the resolved revision is overwritten" in text
    assert "None" not in text


# ------------------------------------------------------------------ the spend cap

def test_without_a_cap_every_case_runs():
    assert evaluate.within_budget(999.0, None) is True


def test_a_case_that_could_cross_the_cap_does_not_start():
    """What a case costs is known only once it is over — a finding pays for its own refuter —
    so the guard reserves the worst case measured rather than stopping midway."""
    assert evaluate.within_budget(10.0, 12.0) is False
    assert evaluate.within_budget(9.0, 12.0) is True


def test_the_reserve_is_the_worst_cost_actually_measured():
    """Not a round number picked to feel safe: 4 cases billed $7.05 and the dearest was ~$2.90."""
    assert evaluate.within_budget(0.0, evaluate.WORST_CASE_USD) is True
    assert evaluate.within_budget(0.01, evaluate.WORST_CASE_USD) is False
