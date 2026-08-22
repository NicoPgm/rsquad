"""The mechanical gate. No test here runs git or pytest — only the classification is checked.

What is pinned below is what running the original on real commits cost to discover: the
`failure`/`error` distinction, per-test granularity, and the fact that a collection error must
stay visible instead of being filtered away with everything else.
"""

from pathlib import Path

from rsquad.gate import NO_SIGNAL, SUSPECT, VALID, Verdict, parse_junit, report, summarize


def _report(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "base.xml"
    path.write_text('<?xml version="1.0"?><testsuites><testsuite>%s</testsuite></testsuites>'
                    % body, encoding="utf-8")
    return path


FAILED = '<testcase classname="tests.t" name="test_a"><failure>boom</failure></testcase>'
ERRORED = '<testcase classname="tests.t" name="test_a"><error>import</error></testcase>'
PASSED = '<testcase classname="tests.t" name="test_a"/>'
SKIPPED = '<testcase classname="tests.t" name="test_a"><skipped/></testcase>'
COLLECTION = '<testcase classname="" name="tests.t"><error>ImportError</error></testcase>'


def test_an_assertion_failure_means_the_test_is_valid(tmp_path):
    """The only case that proves a test discriminates."""
    v, = parse_junit(_report(tmp_path, FAILED), set(), {"test_a"})
    assert v.state == VALID


def test_a_test_that_passes_on_the_base_is_suspect(tmp_path):
    v, = parse_junit(_report(tmp_path, PASSED), set(), {"test_a"})
    assert v.state == SUSPECT


def test_an_error_is_not_a_failure(tmp_path):
    """The distinction carries the whole tool.

    On new code a test file imports symbols that do not exist yet: it crashes at collection.
    Counting that as a success would validate, in bulk, tests we know nothing about — and it is
    the MOST common case, not an edge case.
    """
    v, = parse_junit(_report(tmp_path, ERRORED), set(), {"test_a"})
    assert v.state == NO_SIGNAL


def test_a_skipped_test_says_nothing(tmp_path):
    v, = parse_junit(_report(tmp_path, SKIPPED), set(), {"test_a"})
    assert v.state == NO_SIGNAL


def test_an_exempt_test_that_passes_stays_valid(tmp_path):
    """It exists to prove a refactor changes nothing: it MUST pass on the base."""
    v, = parse_junit(_report(tmp_path, PASSED), {"test_a"}, {"test_a"})
    assert v.state == VALID
    assert "exempt" in v.detail


def test_an_unmodified_test_is_not_examined(tmp_path):
    """Without this filter every pre-existing test in a touched file is flagged "suspect".

    Measured on a real commit: 35 false positives against 6 genuine findings. A gate in that
    state is switched off within a week, and takes the real findings with it.
    """
    assert parse_junit(_report(tmp_path, PASSED), set(), {"test_other"}) == []


def test_a_collection_error_stays_visible(tmp_path):
    """Filtering it away with the unmodified tests would be the most misleading silence.

    It signals that N new tests could not be examined **at all**. Hiding it makes a whole file
    look like "nothing to report".
    """
    v, = parse_junit(_report(tmp_path, COLLECTION), set(), {"test_x"})
    assert v.state == NO_SIGNAL


def test_parametrization_is_folded_back_into_its_function(tmp_path):
    """JUnit emits `test_a[case]`; the filter keys on the function, not the parametrization."""
    body = '<testcase classname="tests.t" name="test_a[Grok]"><failure>x</failure></testcase>'
    v, = parse_junit(_report(tmp_path, body), set(), {"test_a"})
    assert v.state == VALID


# ------------------------------------------------------------------- missing symbols

ABSENT = ('<testcase classname="tests.t" name="test_a"><failure message="AttributeError: '
          "module 'pkg' has no attribute 'nope'\"/></testcase>")


def test_a_failure_on_an_absent_symbol_is_no_signal(tmp_path):
    """`<failure>` versus `<error>` does not split failures the way this gate needs.

    A symbol that does not exist yet fails at collection when imported by name, and inside the
    test body when reached as a module attribute. Same missing symbol, and without this the
    second one reads as a discriminating test.
    """
    v, = parse_junit(_report(tmp_path, ABSENT), set(), {"test_a"},
                     missing_symbol=lambda m: "has no attribute" in m)
    assert v.state == NO_SIGNAL
    assert "does not exist yet" in v.detail


def test_without_a_predicate_every_failure_still_counts_as_valid(tmp_path):
    """The default has to be the old behaviour: over-count `valid`, never discard a finding.

    An adapter that has not answered question 5 must not silently start dropping tests.
    """
    v, = parse_junit(_report(tmp_path, ABSENT), set(), {"test_a"})
    assert v.state == VALID


def test_the_predicate_never_sees_a_collection_error(tmp_path):
    """Collection errors are already no-signal; running the predicate there would be noise."""
    seen = []
    parse_junit(_report(tmp_path, COLLECTION), set(), {"test_x"},
                missing_symbol=lambda m: seen.append(m) or False)
    assert seen == []


# ------------------------------------------------------------------- overall verdict

def test_strict_fails_only_on_a_suspect():
    quiet = []
    valid = [Verdict("t", VALID)]
    suspect = [Verdict("t", SUSPECT)]
    assert report(valid, strict=True, out=quiet.append) == 0
    assert report(suspect, strict=True, out=quiet.append) == 1
    assert report(suspect, strict=False, out=quiet.append) == 0


def test_no_signal_never_blocks():
    """A gate that blocks on what it cannot judge gets routed around."""
    quiet = []
    assert report([Verdict("t", NO_SIGNAL)], strict=True, out=quiet.append) == 0


def test_the_summary_counts_functions_not_junit_cases():
    """A parametrized function yields N cases but is ONE new test.

    Mixing the units produced aggregate rows with 4 new tests and 10 "valid".
    """
    verdicts = [Verdict("tests.t::test_a[x]", VALID), Verdict("tests.t::test_a[y]", VALID),
                Verdict("tests.t::test_b", SUSPECT)]
    s = summarize(verdicts)
    assert (s.examined, s.valid, s.suspect, s.junit_cases) == (2, 1, 1, 3)


def test_the_summary_is_printed_next_to_the_verdict():
    """"0 suspect" very often means "nothing could be checked" — the count must be visible."""
    lines = []
    report([Verdict("tests.t::test_a", NO_SIGNAL)], strict=False, out=lines.append)
    assert any("0 function(s) examined" in line for line in lines)
