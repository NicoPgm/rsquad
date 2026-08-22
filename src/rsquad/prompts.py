"""Prompt templates, versioned on disk and rendered at run time.

Two rules carry this module.

**The vocabulary is never written into a prompt.** `{{VOCABULARY_BLOCK}}` is rendered from
`schema/finding.v1.json`, so the words the model is told to use and the words the schema accepts
cannot drift. A prompt that spelled them out would be a second source of truth, and the second
source is always the stale one.

**The cached prefix must stay byte-identical.** Caching is a prefix match: one changed byte
anywhere before the breakpoint and everything after it is recomputed. So the shared system text
comes first and carries the breakpoint, the per-lens instruction comes after it, and the review
unit — the only genuinely variable part — comes last, in the user turn. That layout is also why
the four lenses share one cache entry instead of paying for four.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .findings import ROOT, vocabulary_block

PROMPT_DIR = ROOT / "prompts"
LENS_DIR = PROMPT_DIR / "lenses"

#: Prompt version, per mode. Read it with the mode, never alone.
VERSIONS = {"api": "v1"}

LENSES = ("repro", "bounds", "contract", "tests")

_COMMENT = re.compile(r"<!--.*?-->", re.S)


def version(mode: str = "api") -> str:
    return VERSIONS[mode]


@lru_cache(maxsize=None)
def _load(path: Path) -> str:
    if not path.exists():
        raise SystemExit("prompt not found: %s" % path)
    return _COMMENT.sub("", path.read_text(encoding="utf-8")).strip()


def _render(template: str, **values: str) -> str:
    text = template
    for key, value in values.items():
        text = text.replace("{{%s}}" % key.upper(), value)
    left = re.search(r"\{\{[A-Z_]+\}\}", text)
    if left:
        raise SystemExit("unrendered placeholder in prompt: %s" % left.group(0))
    return text


def system_prompt() -> str:
    return _render(_load(PROMPT_DIR / "system.v1.md"), vocabulary_block=vocabulary_block())


def lens_prompt(lens: str) -> str:
    if lens not in LENSES:
        raise SystemExit("unknown lens: %s" % lens)
    return _load(LENS_DIR / ("%s.v1.md" % lens))


def user_prompt(file: str, diff: str, numbered: str, elision: str = "") -> str:
    return _render(_load(PROMPT_DIR / "user.v1.md"), file=file, diff=diff, numbered=numbered,
                   elision=elision)


def system_blocks(lens: str) -> list[dict]:
    """The system turn: shared text with the cache breakpoint, then the lens instruction.

    The breakpoint sits on the **first** block, not the last. Putting it after the lens
    instruction would give each lens its own cache entry — four writes instead of one write and
    three reads.
    """
    return [
        {"type": "text", "text": system_prompt(), "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": lens_prompt(lens)},
    ]
