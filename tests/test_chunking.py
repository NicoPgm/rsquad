"""Cutting a change into review units. No git, no network — the two git calls are stubbed."""

import pytest

from rsquad import chunking
from rsquad.chunking import ELISION_NOTICE, Unit, hunk_ranges, number, unit

DIFF = """diff --git a/a.py b/a.py
@@ -10,3 +10,4 @@ def f():
     pass
+    return 1
@@ -100,2 +101,6 @@ def g():
-    old()
+    new()
"""


def test_hunk_ranges_reads_the_new_side():
    """The old-side numbers are useless here: findings point into the file as it now stands."""
    assert hunk_ranges(DIFF) == [(10, 13), (101, 106)]


def test_a_hunk_without_a_length_covers_one_line():
    assert hunk_ranges("@@ -1 +7 @@\n+x\n") == [(7, 7)]


def test_a_short_file_is_shown_whole_with_line_numbers():
    text, elided = number("un\ndeux\ntrois", [(2, 2)])
    assert text == "1\tun\n2\tdeux\n3\ttrois"
    assert elided is False


def test_line_numbers_start_at_one():
    """Off by one here would make every finding miss its anchor, and look like hallucination."""
    text, _ = number("premiere", [(1, 1)])
    assert text.startswith("1\tpremiere")


def test_a_long_file_is_windowed_around_its_hunks():
    source = "\n".join("ligne %d" % n for n in range(1, 501))
    text, elided = number(source, [(250, 250)], max_lines=100, context=5)
    assert elided is True
    assert "245\tligne 245" in text
    assert "255\tligne 255" in text
    assert "1\tligne 1" not in text


def test_every_gap_is_announced():
    """An unmarked cut lets a lens conclude "nothing releases this handle" from a file where
    the release was simply not shown. Same reflex as the `[...]` seam in caption stripping.
    """
    source = "\n".join("ligne %d" % n for n in range(1, 501))
    text, _ = number(source, [(250, 250)], max_lines=100, context=5)
    assert "lines not shown" in text
    assert text.count("lines not shown") == 2      # before and after the single window


def test_adjacent_windows_merge_instead_of_repeating_context():
    source = "\n".join("ligne %d" % n for n in range(1, 501))
    text, _ = number(source, [(100, 100), (104, 104)], max_lines=10, context=5)
    assert text.count("lines not shown") == 2
    assert "102\tligne 102" in text                # the gap between them is kept, not cut


def test_the_elision_notice_only_appears_when_something_was_cut():
    assert Unit("a", "d", "s", "n", elided=True).elision == ELISION_NOTICE
    assert Unit("a", "d", "s", "n", elided=False).elision == ""


# ------------------------------------------------------------------ unit assembly

def _stub(monkeypatch, source, diff=DIFF):
    monkeypatch.setattr(chunking, "file_at", lambda rev, path, repo=None: source)
    monkeypatch.setattr(chunking, "git",
                        lambda args, repo=None: type("R", (), {"stdout": diff})())


def test_a_deleted_file_yields_no_unit(monkeypatch):
    """There is no "file as it now stands" to quote, so no finding about it could anchor."""
    _stub(monkeypatch, None)
    assert unit("a.py", "base", "head") is None


def test_a_binary_file_yields_no_unit(monkeypatch):
    _stub(monkeypatch, "PK\x00\x03garbage")
    assert unit("a.bin", "base", "head") is None


def test_a_file_with_no_diff_yields_no_unit(monkeypatch):
    _stub(monkeypatch, "x = 1\n", diff="")
    assert unit("a.py", "base", "head") is None


def test_the_unit_carries_the_raw_source_for_anchoring(monkeypatch):
    """Anchoring checks against the raw text, never the numbered rendering."""
    source = "def f():\n    return 1\n"
    _stub(monkeypatch, source)
    built = unit("a.py", "base", "head")
    assert built.source == source
    assert "1\tdef f():" in built.numbered
