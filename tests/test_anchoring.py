"""The two mechanical guards: quoted code must exist where it is claimed, and a finding must
carry concrete inputs and an observable consequence.

No model is involved anywhere in this file, which is the point.
"""

import pytest

from rsquad.anchoring import (NOT_ANCHORED, UNKNOWN_FILE, VACUOUS_CONSEQUENCE, VACUOUS_INPUTS,
                             anchored, reject, sift, vacuous)

SOURCE = """def resume(fiches):
    if not fiches:
        return None
    premiere = fiches[0]
    return premiere.summary
"""

FINDING = {
    "file": "a.py",
    "line": 4,
    "snippet": "premiere = fiches[0]",
    "kind": "boundary",
    "severity": "significant",
    "inputs": "fiches = []",
    "consequence": "raises IndexError",
}
SOURCES = {"a.py": SOURCE}


# ------------------------------------------------------------------ anchoring

def test_a_verbatim_quote_at_the_right_line_anchors():
    assert anchored("premiere = fiches[0]", SOURCE, 4)


def test_indentation_and_reflow_do_not_break_the_anchor():
    """Models reflow code. Rejecting a true quote over whitespace would be a false negative."""
    assert anchored("    premiere   =  fiches[0]", SOURCE, 4)
    assert anchored("if not fiches:\n        return None", SOURCE, 2)


def test_a_paraphrase_does_not_anchor():
    """This is the whole guard: plausible-but-not-present is exactly what must be dropped."""
    assert not anchored("premiere = fiches.first()", SOURCE, 4)


def test_a_real_quote_at_the_wrong_line_does_not_anchor():
    """The line is checked too. A finding pointing at the wrong place is not actionable.

    `premiere = fiches[0]` is genuinely in the file - just not within the window of line 40.
    """
    assert not anchored("premiere = fiches[0]", SOURCE, 40)


def test_a_line_past_the_end_of_the_file_does_not_anchor():
    assert not anchored("anything", SOURCE, 999)


def test_the_window_is_forgiving_but_narrow():
    """Off by one or two is a model counting lines; off by ten is a model guessing."""
    assert anchored("premiere = fiches[0]", SOURCE, 2)          # two lines early, accepted
    assert anchored("premiere = fiches[0]", SOURCE, 4, window=0)  # exact line, no slack needed
    assert not anchored("return None", SOURCE, 4, window=0)     # really line 3, refused at 0


def test_an_empty_snippet_never_anchors():
    """Otherwise the substring test passes against anything and the guard is decorative."""
    assert not anchored("", SOURCE, 1)
    assert not anchored("   \n  ", SOURCE, 1)


# ------------------------------------------------------------------ reproduction or nothing

@pytest.mark.parametrize("text", ["", "  ", "N/A", "none", "unknown", "TBD", "-",
                                  "see above", "Various."])
def test_evasive_answers_are_vacuous(text):
    assert vacuous(text)


@pytest.mark.parametrize("text", ["fiches = []", "x = 0", "an empty caption file",
                                  "duration_s = 0 and no captions"])
def test_short_but_concrete_answers_survive(text):
    """Rejecting a true short answer costs more than passing it to the refuter."""
    assert not vacuous(text)


# ------------------------------------------------------------------ the two guards together

def test_a_sound_finding_survives():
    assert reject(FINDING, SOURCES) is None


def test_a_finding_about_a_file_not_under_review_is_dropped():
    """A lens may only speak about what it was shown."""
    assert reject(dict(FINDING, file="ailleurs.py"), SOURCES) == UNKNOWN_FILE


def test_a_hallucinated_quote_is_dropped():
    assert reject(dict(FINDING, snippet="premiere = fiches.first()"), SOURCES) == NOT_ANCHORED


def test_a_finding_with_empty_inputs_is_dropped():
    assert reject(dict(FINDING, inputs="N/A"), SOURCES) == VACUOUS_INPUTS


def test_a_confidently_vague_answer_still_gets_through():
    """The honest limit of this guard, pinned so nobody mistakes it for a quality check.

    "certain conditions" is not concrete, and no mechanical rule separates it from a real short
    answer without also rejecting "x = 0". Judging that is the refuter's job in step [3]. A
    guard that pretended to do it would be measuring its own vocabulary.
    """
    assert reject(dict(FINDING, inputs="certain conditions"), SOURCES) is None


def test_a_finding_without_an_observable_consequence_is_dropped():
    assert reject(dict(FINDING, consequence="unknown"), SOURCES) == VACUOUS_CONSEQUENCE


def test_sift_returns_both_halves_with_reasons():
    """A silent drop reads as "nothing was there". What the guards reject is a measurement."""
    bad = dict(FINDING, snippet="jamais ecrit")
    kept, dropped = sift([FINDING, bad], SOURCES)
    assert kept == [FINDING]
    assert dropped == [(bad, NOT_ANCHORED)]
