"""The ground-truth set. Data, not code — so the tests here guard against rot, not regression.

An evaluation set that quietly loses a field, or labels a defect with a `kind` the schema no
longer has, produces a number nobody can interpret. That is worse than having no set.
"""

from pathlib import Path

import pytest
import yaml

from rsquad.findings import vocabulary

DEFECTS_FILE = Path(__file__).resolve().parents[1] / "evaluation" / "defects.yaml"

REQUIRED = {"id", "summary", "repo", "introduced_in", "fixed_in", "file", "kind", "severity",
            "replayable", "self_found", "detectable_from_diff", "found_by", "note"}

DETECTABILITY = {"yes", "weak", "no"}


@pytest.fixture(scope="module")
def defects():
    return yaml.safe_load(DEFECTS_FILE.read_text(encoding="utf-8"))["defects"]


def test_the_set_is_not_empty(defects):
    assert defects


def test_identifiers_are_unique(defects):
    ids = [d["id"] for d in defects]
    assert len(ids) == len(set(ids))


def test_every_entry_is_complete(defects):
    for defect in defects:
        assert REQUIRED <= set(defect), "%s is missing %s" % (defect.get("id"),
                                                              REQUIRED - set(defect))


def test_labels_use_the_finding_vocabulary(defects):
    """The ground truth and the lenses must speak the same closed language.

    If they drift, a detection cannot be matched to its label and the whole set goes quiet.
    """
    for defect in defects:
        assert defect["kind"] in vocabulary("kind"), defect["id"]
        assert defect["severity"] in vocabulary("severity"), defect["id"]


def test_detectability_is_one_of_three_strings(defects):
    """Guards a real YAML trap: unquoted `yes` and `no` parse as booleans, not strings.

    Left unquoted, `detectable_from_diff: no` becomes `False`, every membership test below
    fails open, and a scoring script silently treats the field as missing.
    """
    for defect in defects:
        value = defect["detectable_from_diff"]
        assert isinstance(value, str), "%s: %r parsed as %s" % (defect["id"], value,
                                                                type(value).__name__)
        assert value in DETECTABILITY, defect["id"]


def test_replayable_entries_name_both_commits(defects):
    """Replaying needs the diff that introduced the defect, not the one that fixed it."""
    for defect in defects:
        if defect["replayable"]:
            assert defect["introduced_in"], defect["id"]
            assert defect["fixed_in"], defect["id"]


def test_at_least_one_case_is_plainly_detectable(defects):
    """A set of only hard cases cannot distinguish a broken squad from a hard problem."""
    assert any(d["detectable_from_diff"] == "yes" for d in defects)


def test_the_scorable_subset_is_identified(defects):
    """`no` cases are documentation, not scoring material — counting them would understate."""
    scorable = [d for d in defects if d["detectable_from_diff"] in ("yes", "weak")]
    assert scorable
    assert len(scorable) < len(defects) or all(
        d["detectable_from_diff"] != "no" for d in defects)


def test_the_set_is_not_all_self_found(defects):
    """A ground truth made only of what the squad already found measures self-consistency.

    It would report a rising detection rate while learning nothing, which is the most
    comfortable way for an evaluation to become useless.
    """
    independent = [d for d in defects if not d["self_found"]]
    assert independent, "every case was found by the squad itself - the set proves nothing"


def test_self_found_cases_declare_themselves(defects):
    for defect in defects:
        assert isinstance(defect["self_found"], bool), defect["id"]


# ------------------------------------------------------------------ the step 7 pre-registration

STEP7 = Path(__file__).resolve().parents[1] / "evaluation" / "step7.yaml"


@pytest.fixture(scope="module")
def step7():
    return yaml.safe_load(STEP7.read_text(encoding="utf-8"))


def test_every_case_carries_a_label_and_its_reasoning(step7):
    """A label with no rationale cannot be audited afterwards, and being auditable afterwards is
    the entire point of freezing this file before the run."""
    for case in step7["cases"]:
        assert case["detectable_from_diff"] in DETECTABILITY
        assert case["label_rationale"].strip()


def test_the_arms_stay_interleaved(step7):
    """`--max-usd` stops between cases. If one arm ran first as a block, a budget truncation
    would delete the comparison rather than shorten it."""
    repos = [c["repo"] for c in step7["cases"]]
    assert all(a != b for a, b in zip(repos, repos[1:])), repos


def test_both_arms_carry_the_same_number_of_cases(step7):
    counts = {arm["repo"]: sum(c["repo"] == arm["repo"] for c in step7["cases"])
              for arm in step7["arms"]}
    assert len(set(counts.values())) == 1, counts


def test_the_hard_bound_does_not_drift_from_the_caps(step7):
    """The bound is the number that gets quoted, so it must stay derived rather than typed."""
    budget = step7["budget"]
    assert budget["hard_bound_usd"] == budget["cap_usd_per_arm"] * len(step7["arms"])
