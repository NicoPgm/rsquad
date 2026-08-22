"""The Python/pytest adapter — the four questions, answered for one stack.

No test here runs git or pytest. `file_at` is the only git call in the adapter and it is
stubbed, which keeps the interesting logic — body comparison and marker reading — under test
without a fixture repository.
"""

import sys
from pathlib import Path

from rsquad.gate.adapters.python_pytest import PythonPytestAdapter

ADAPTER = PythonPytestAdapter()


# ------------------------------------------------------------------ question 1

def test_only_python_files_are_tests():
    assert ADAPTER.is_test_file("tests/test_a.py")
    assert not ADAPTER.is_test_file("tests/fixtures/sample.vtt")
    assert not ADAPTER.is_test_file("tests/README.md")


# ------------------------------------------------------------------ question 2

BEFORE = '''
def test_kept():
    assert 1 == 1


def test_loosened():
    assert len(channels) == 5
'''

AFTER = '''
def test_kept():
    assert 1 == 1


def test_loosened():
    assert len(channels) >= 5


def test_added():
    assert True
'''


def _stub(monkeypatch, mapping):
    monkeypatch.setattr(PythonPytestAdapter, "file_at",
                        staticmethod(lambda rev, path, repo=None: mapping.get((rev, path))))


def test_only_new_or_modified_functions_are_retained(monkeypatch):
    """An untouched test teaches nothing about the change in flight.

    File-level granularity produced 35 false positives against 6 genuine findings on a real
    commit — the failure mode that gets a gate switched off.
    """
    _stub(monkeypatch, {("base", "tests/t.py"): BEFORE, ("head", "tests/t.py"): AFTER})
    assert ADAPTER.changed_test_functions(["tests/t.py"], "base", "head") \
        == {"test_loosened", "test_added"}


def test_a_relaxed_assertion_counts_as_modified(monkeypatch):
    """`== 5` becoming `>= 5` is the failure mode this gate exists to catch."""
    _stub(monkeypatch, {("base", "tests/t.py"): BEFORE, ("head", "tests/t.py"): AFTER})
    assert "test_loosened" in ADAPTER.changed_test_functions(["tests/t.py"], "base", "head")


def test_a_brand_new_file_yields_all_its_tests(monkeypatch):
    """The file does not exist on the base — `file_at` returns None, not an empty string."""
    _stub(monkeypatch, {("head", "tests/t.py"): AFTER})
    assert ADAPTER.changed_test_functions(["tests/t.py"], "base", "head") \
        == {"test_kept", "test_loosened", "test_added"}


def test_a_deleted_file_yields_nothing(monkeypatch):
    _stub(monkeypatch, {("base", "tests/t.py"): BEFORE})
    assert ADAPTER.changed_test_functions(["tests/t.py"], "base", "head") == set()


def test_decorators_are_part_of_the_body():
    """Loosening a `parametrize` case changes the test without touching its body.

    Comparing the AST alone would miss it; comparing source text from the first decorator
    onwards does not.
    """
    plain = 'def test_a():\n    assert True\n'
    decorated = '@pytest.mark.parametrize("x", [1])\ndef test_a():\n    assert True\n'
    assert ADAPTER._functions(plain)["test_a"] != ADAPTER._functions(decorated)["test_a"]


def test_a_syntax_error_yields_no_functions():
    """Half-written code must not crash the gate — it simply teaches nothing."""
    assert ADAPTER._functions("def test_a(:\n") == {}


def test_non_test_functions_are_ignored():
    source = 'def helper():\n    pass\n\n\ndef test_a():\n    pass\n'
    assert set(ADAPTER._functions(source)) == {"test_a"}


# ------------------------------------------------------------------ question 3

def test_the_command_never_aborts_on_a_collection_error():
    """On the base a new test file is *always* uncollectable — it imports what does not exist.

    Without the flag, pytest runs nothing and the gate falls silent exactly when it would
    earn its keep.
    """
    command = ADAPTER.test_command(["tests/t.py"], Path("report.xml"))
    assert "--continue-on-collection-errors" in command
    assert "--junitxml" in command
    assert command[0] == sys.executable


# ------------------------------------------------------------------ question 4

def test_the_environment_forces_the_base_sources(tmp_path):
    """The editable install points at the main checkout's `src/`.

    Without this variable pytest imports the NEW code from the worktree and the gate validates
    everything while looking green — 22 tests passed that way on 2026-08-20.
    """
    env = ADAPTER.base_environment(tmp_path)
    assert env["PYTHONPATH"] == str(tmp_path / "src")
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"


# ------------------------------------------------------------------ exemption markers

MARKED = '''
@pytest.mark.characterization
def test_preserved():
    assert True


def test_ordinary():
    assert True
'''


def test_a_marked_test_is_exempt():
    assert ADAPTER.exempt_names({"tests/t.py": MARKED}) == {"test_preserved"}


def test_the_marker_applies_only_to_the_next_test():
    """Otherwise one marker would silently exempt the rest of the file."""
    assert "test_ordinary" not in ADAPTER.exempt_names({"tests/t.py": MARKED})


def test_a_bare_mention_of_the_word_is_not_a_marker():
    """The word appears in docstrings and comments; only a decorator line counts."""
    source = 'def test_a():\n    """A characterization of nothing."""\n    assert True\n'
    assert ADAPTER.exempt_names({"tests/t.py": source}) == set()


GUARDED = '''
@pytest.mark.guard
def test_muse_alone_is_not_linked_to_meta_muse_spark():
    assert canonicalise("Muse") == "Muse"
'''


def test_a_negative_guard_is_exempt_too():
    """A guard asserts something does NOT happen.

    The base does not do it either, so the test cannot fail there by construction — it is
    invisible to this gate by design, not by defect. Two of the five suspects in the measured
    baseline were of this kind; without the marker the gate reports four false positives out
    of five and gets switched off.
    """
    assert ADAPTER.exempt_names({"tests/t.py": GUARDED}) \
        == {"test_muse_alone_is_not_linked_to_meta_muse_spark"}
