"""The command line's own decisions — only what no other module owns."""

import argparse

import pytest

from rsquad import __main__ as cli
from rsquad.__main__ import _adapter, _round_two
from rsquad.chunking import Unit
from rsquad.conformance import Intent
from rsquad.gate import by_language


def test_the_context_pack_is_off_unless_asked_for():
    assert _adapter(False) is None
    assert _adapter(True) is by_language


def test_a_job_written_before_the_change_keeps_its_pack_and_its_model():
    """Every job on disk before 2026-11-20 had the pack and one model for both rounds."""
    old = {"base": "b", "head": "h", "repo": ".", "specs": [], "model": "claude-opus-5"}
    meta = _round_two(old)
    assert meta["context"] is True
    assert meta["refute_model"] == "claude-opus-5"


def test_export_defaults_to_the_measured_tiers(monkeypatch):
    """Opus lenses and refuter: under ADR-0011 the lenses found 19 golden findings on Opus
    against 10 on Sonnet, on five unseen pull requests. Measured, not a guess."""
    from rsquad import __main__ as cli

    seen = {}
    monkeypatch.setattr(cli, "_export", lambda args: seen.update(vars(args)) or 0)
    cli.main(["export", "job"])
    assert (seen["model"], seen["refute_model"]) == ("claude-opus-5", "claude-opus-5")


def test_the_refutation_round_keeps_its_own_model():
    data = {"base": "b", "head": "h", "repo": ".", "specs": [], "model": "claude-sonnet-5",
            "refute_model": "claude-opus-5", "context": False}
    meta = _round_two(data)
    assert (meta["model"], meta["refute_model"], meta["context"]) == (
        "claude-sonnet-5", "claude-opus-5", False)


UNIT = Unit(file="src/a.py", diff="+x\n", source="x\n", numbered="1\tx")


def _no_repository(monkeypatch):
    """Units without git: these tests are about what the command line does when the copy fails."""
    monkeypatch.setattr(cli, "_case_units", lambda defect, repo, context: ("h", "b", [UNIT]))
    monkeypatch.setattr(cli, "_units_and_intent",
                        lambda args, repo: ("h", "b", [UNIT], [], Intent(parts=[])))
    monkeypatch.setattr(cli.conformance, "gather", lambda *args: Intent(parts=[]))


def test_a_failed_snapshot_leaves_no_job_that_looks_complete(tmp_path, monkeypatch):
    _no_repository(monkeypatch)

    def fails(head, dest, repo):
        raise SystemExit("cannot snapshot h: boom")

    monkeypatch.setattr(cli, "snapshot", fails)
    args = argparse.Namespace(repo=None, lens=None, no_conformance=True, model="m",
                              refute_model=None, job=str(tmp_path / "job"), spec=None,
                              context=False)
    with pytest.raises(SystemExit):
        cli._export(args)
    assert not (tmp_path / "job" / "manifest.json").exists()


def test_one_case_that_cannot_be_copied_does_not_end_the_export(tmp_path, monkeypatch):
    _no_repository(monkeypatch)

    def snapshot(head, dest, repo):
        if dest.parent.name == "first":
            raise SystemExit("cannot snapshot h: boom")

    monkeypatch.setattr(cli, "snapshot", snapshot)
    args = argparse.Namespace(jobs=str(tmp_path), context=False, model="m", refute_model=None)
    cases = [{"id": "first", "file": "src/a.py"}, {"id": "second", "file": "src/a.py"}]
    cli._evaluate_export(args, cases, [], tmp_path, ["repro"])
    assert not (tmp_path / "first" / "manifest.json").exists()
    assert (tmp_path / "second" / "manifest.json").exists()
