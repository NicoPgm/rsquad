"""The context pack — question 6 of the adapter protocol.

No git, no network. What is pinned here is the pair of properties that make a computed pack
worth having instead of file-reading tools: it is deterministic, and it can only ever reach
code the change references.
"""

import pytest

from rsquad.context import (MAX_DEFINITION_LINES, Definition, cap, render, truncate)
from rsquad.gate.adapters.python_pytest import PythonPytestAdapter

ADAPTER = PythonPytestAdapter()

SOURCE = '''from __future__ import annotations

import os
from pathlib import Path

from avd.verify import reparable
from . import prompts
from .schema import ROOT


def run(fiche):
    if reparable(fiche):
        return prompts.system_prompt()
    return os.path.join(ROOT, "x")
'''

NEIGHBOUR = '''SEUIL = 3


def reparable(fiche):
    """Whether this card can be replayed."""
    return fiche.genre in GENRES
'''

TRACKED = ["src/avd/verify.py", "src/avd/prompts.py", "src/avd/schema.py", "src/avd/run.py"]


def _stub(monkeypatch, sources):
    monkeypatch.setattr(PythonPytestAdapter, "file_at",
                        staticmethod(lambda rev, path, repo=None: sources.get(path)))


# ------------------------------------------------------------------ what it reaches

def test_it_resolves_a_first_party_symbol_the_change_references(monkeypatch):
    _stub(monkeypatch, {"src/avd/verify.py": NEIGHBOUR})
    found = ADAPTER.resolve_context("src/avd/run.py", SOURCE, [(11, 14)], "head", None, TRACKED)
    assert [d.symbol for d in found] == ["reparable"]
    assert "Whether this card can be replayed" in found[0].source


def test_standard_library_is_deliberately_skipped(monkeypatch):
    """A model knows `os.path.join`. Pasting it in spends payload to teach nothing."""
    _stub(monkeypatch, {"src/avd/verify.py": NEIGHBOUR})
    found = ADAPTER.resolve_context("src/avd/run.py", SOURCE, [(11, 14)], "head", None, TRACKED)
    assert all("os" not in d.symbol for d in found)


def test_a_symbol_outside_the_changed_lines_is_not_resolved(monkeypatch):
    """The pack follows what the change touches, not everything the file imports.

    This is also what keeps it blind: it walks imports, never directories, so there is no path
    from it to a specification.
    """
    _stub(monkeypatch, {"src/avd/verify.py": NEIGHBOUR})
    assert ADAPTER.resolve_context("src/avd/run.py", SOURCE, [(1, 3)], "head", None,
                                   TRACKED) == []


def test_relative_imports_resolve_against_the_package(monkeypatch):
    """`from . import prompts` is how a package names its own neighbours.

    Skipping relative imports would blind the resolver to exactly the modules a change is most
    likely to have just started calling.
    """
    _stub(monkeypatch, {"src/avd/prompts.py": "def system_prompt():\n    return 'x'\n"})
    found = ADAPTER.resolve_context("src/avd/run.py", SOURCE, [(11, 14)], "head", None, TRACKED)
    assert [d.symbol for d in found] == ["prompts.system_prompt"]


def test_a_module_the_repository_does_not_track_resolves_to_nothing():
    assert ADAPTER._module_file("requests.adapters", TRACKED) is None
    assert ADAPTER._module_file("avd.verify", TRACKED) == "src/avd/verify.py"


def test_a_package_resolves_through_its_init():
    assert ADAPTER._module_file("avd", ["src/avd/__init__.py"]) == "src/avd/__init__.py"


def test_unparsable_source_resolves_to_nothing_rather_than_crashing():
    assert ADAPTER.resolve_context("a.py", "def f(:\n", [(1, 1)], "head", None, TRACKED) == []


# ------------------------------------------------------------------ determinism

def test_the_order_is_stable(monkeypatch):
    """A pack that varies between runs cannot be replayed, and a squad that cannot be replayed
    cannot be measured. Sorting by (file, line) makes the order a fact about the repository."""
    _stub(monkeypatch, {"src/avd/verify.py": NEIGHBOUR,
                        "src/avd/prompts.py": "def system_prompt():\n    return 'x'\n"})
    twice = [ADAPTER.resolve_context("src/avd/run.py", SOURCE, [(11, 14)], "head", None,
                                     TRACKED) for _ in range(2)]
    assert twice[0] == twice[1]
    assert [d.file for d in twice[0]] == sorted(d.file for d in twice[0])


def test_a_symbol_referenced_twice_appears_once(monkeypatch):
    _stub(monkeypatch, {"src/avd/verify.py": NEIGHBOUR})
    source = SOURCE + "\n\ndef again(f):\n    return reparable(f)\n"
    found = ADAPTER.resolve_context("src/avd/run.py", source, [(11, 20)], "head", None, TRACKED)
    assert len(found) == 1


# ------------------------------------------------------------------ size

def test_a_long_definition_is_truncated_and_says_so():
    body = "\n".join("    line %d" % n for n in range(200))
    text, cut = truncate(body)
    assert cut and "not shown" in text
    assert len(text.splitlines()) == MAX_DEFINITION_LINES + 1


def test_the_pack_stops_before_becoming_a_second_file_to_review():
    big = [Definition("s%d" % n, "f%d.py" % n, 1, "x\n" * 300) for n in range(5)]
    assert len(cap(big, limit=400)) < len(big)


def test_at_least_one_definition_survives_any_cap():
    """A cap that can return nothing would silently turn the feature off on large symbols."""
    huge = [Definition("s", "f.py", 1, "x\n" * 10_000)]
    assert len(cap(huge, limit=10)) == 1


# ------------------------------------------------------------------ how it is presented

def test_the_block_says_the_definitions_are_not_under_review():
    text = render([Definition("reparable", "src/avd/verify.py", 4, "def reparable(f): ...")])
    assert "not under review" in text
    assert "src/avd/verify.py" in text


def test_the_block_warns_that_absence_proves_nothing():
    """Same reflex as the elision marker: an unmarked gap invents a statement nobody made."""
    assert "not evidence of absence" in render([Definition("x", "f.py", 1, "x")])


def test_an_empty_pack_renders_to_nothing_at_all():
    """No empty heading in the prompt — it would read as "this file references nothing"."""
    assert render([]) == ""
