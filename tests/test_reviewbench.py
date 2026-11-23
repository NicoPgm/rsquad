"""The ReviewBench adapter: one entry per place, at head, in the bench's own shape."""

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "evaluation" / "reviewbench.py"
_spec = importlib.util.spec_from_file_location("reviewbench", _PATH)
reviewbench = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reviewbench)

PR = {"repo": "https://github.com/o/r", "pr_number": 7, "base": "b" * 40, "head": "h" * 40,
      "title": "not copied", "body": "not copied"}


def _finding(lens, line, snippet="x = f()", consequence="raises KeyError."):
    return {"file": "src/a.py", "line": line, "snippet": snippet, "kind": "crash",
            "severity": "significant", "inputs": "an empty dict", "consequence": consequence,
            "lens": lens}


def test_lenses_agreeing_on_a_place_are_one_entry():
    """The contract asks for one entry per logical issue; agreement is not three issues."""
    out = reviewbench.findings_file([_finding("repro", 10), _finding("bounds", 11),
                                     _finding("contract", 40)], PR)
    assert [(f["start_line"], f["end_line"]) for f in out["findings"]] == [(10, 11), (40, 40)]


def test_a_multi_line_snippet_extends_the_range():
    out = reviewbench.findings_file([_finding("repro", 10, snippet="a\nb\nc\n")], PR)
    assert (out["findings"][0]["start_line"], out["findings"][0]["end_line"]) == (10, 12)


def test_the_message_says_what_is_wrong_then_when():
    out = reviewbench.findings_file([_finding("repro", 10)], PR)
    assert out["findings"][0]["message"] == "raises KeyError. Inputs: an empty dict"


def test_the_message_carries_where_the_refuter_places_the_defect():
    moved = dict(_finding("contract", 10), elsewhere="It lives in delete.py:12.")
    out = reviewbench.findings_file([moved], PR)
    assert out["findings"][0]["message"] == ("raises KeyError. Inputs: an empty dict "
                                             "Where it lives: It lives in delete.py:12.")


def test_the_message_says_when_a_defect_predates_the_change():
    out = reviewbench.findings_file([dict(_finding("repro", 10), scope="pre-existing")], PR)
    assert out["findings"][0]["message"].endswith("Scope: already there.")


def test_the_pr_block_matches_the_manifest_and_nothing_more():
    out = reviewbench.findings_file([], PR)
    assert out == {"pr": {"repo": PR["repo"], "pr_number": 7, "base": PR["base"],
                          "head": PR["head"]}, "agent": "rsquad", "findings": []}
