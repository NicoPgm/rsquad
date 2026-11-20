"""The skill is prose a host agent follows, so it can drift from the CLI it drives.

What can be checked mechanically is checked: every option it tells the agent to pass exists.
"""

import re

import pytest

from rsquad.__main__ import main
from rsquad.findings import ROOT

SKILL = ROOT / ".claude" / "skills" / "rsquad-review" / "SKILL.md"


def _help(capsys, command):
    with pytest.raises(SystemExit):
        main([command, "--help"])
    return capsys.readouterr().out


def test_every_option_the_skill_names_exists(capsys):
    named = set(re.findall(r"(?<![\w-])--[a-z][a-z-]+", SKILL.read_text(encoding="utf-8")))
    accepted = _help(capsys, "export") + _help(capsys, "ingest")
    assert named, "the skill names no option at all - the pattern is broken"
    assert sorted(o for o in named if o not in accepted) == []


def test_the_task_agent_can_read_and_do_nothing_else():
    """Read-only is what keeps a blind lens blind on this path, as far as it goes (ADR-0010)."""
    agent = ROOT / ".claude" / "agents" / "rsquad-task.md"
    head = agent.read_text(encoding="utf-8").split("---")[1]
    assert re.search(r"^name: rsquad-task$", head, re.M)
    assert re.search(r"^tools: Read$", head, re.M)
    assert "rsquad-task" in SKILL.read_text(encoding="utf-8")


def test_the_skill_declares_a_name_and_a_description():
    """Both hosts (Claude Code, Cursor) select a skill by its front matter."""
    head = SKILL.read_text(encoding="utf-8").split("---")[1]
    assert re.search(r"^name: rsquad-review$", head, re.M)
    assert re.search(r"^description: \S", head, re.M)
