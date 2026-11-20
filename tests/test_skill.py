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


def test_the_skill_declares_a_name_and_a_description():
    """Both hosts (Claude Code, Cursor) select a skill by its front matter."""
    head = SKILL.read_text(encoding="utf-8").split("---")[1]
    assert re.search(r"^name: rsquad-review$", head, re.M)
    assert re.search(r"^description: \S", head, re.M)
