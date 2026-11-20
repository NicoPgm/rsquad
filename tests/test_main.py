"""The command line's own decisions — only what no other module owns."""

from rsquad.__main__ import _adapter, _round_two
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
    """Sonnet lenses, Opus refuter: the split step 8 measured, not a guess."""
    from rsquad import __main__ as cli

    seen = {}
    monkeypatch.setattr(cli, "_export", lambda args: seen.update(vars(args)) or 0)
    cli.main(["export", "job"])
    assert (seen["model"], seen["refute_model"]) == ("claude-sonnet-5", "claude-opus-5")


def test_the_refutation_round_keeps_its_own_model():
    data = {"base": "b", "head": "h", "repo": ".", "specs": [], "model": "claude-sonnet-5",
            "refute_model": "claude-opus-5", "context": False}
    meta = _round_two(data)
    assert (meta["model"], meta["refute_model"], meta["context"]) == (
        "claude-sonnet-5", "claude-opus-5", False)
