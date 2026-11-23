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


_PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")


def _render(template: str, **values: str) -> str:
    """One pass over the template only: a value is never scanned or substituted again.

    The values carry the code under review, and code may contain `{{HEAD}}` of its own. Checked
    after substitution, it failed the export; substituted in sequence, it was silently rewritten.
    """
    values = {key.upper(): value for key, value in values.items()}
    for name in _PLACEHOLDER.findall(template):
        if name not in values:
            raise SystemExit("unrendered placeholder in prompt: {{%s}}" % name)
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], template)


def system_prompt() -> str:
    return _render(_load(PROMPT_DIR / "system.v1.md"), vocabulary_block=vocabulary_block())


def lens_prompt(lens: str) -> str:
    if lens not in LENSES:
        raise SystemExit("unknown lens: %s" % lens)
    return _load(LENS_DIR / ("%s.v1.md" % lens))


def user_prompt(file: str, diff: str, numbered: str, elision: str = "",
                context: str = "") -> str:
    return _render(_load(PROMPT_DIR / "user.v1.md"), file=file, diff=diff, numbered=numbered,
                   elision=elision, context=context)


def sections(units) -> str:
    """Every file of the change, each as the per-file prompt shows one: diff, then numbered text."""
    out = []
    for unit in units:
        out.append("## `%s`\n\n### What the change did to it\n\n```diff\n%s\n```\n\n"
                   "### The file as it now stands\n\n```\n%s\n```\n%s%s"
                   % (unit.file, unit.diff, unit.numbered, unit.context_block, unit.elision))
    return "\n".join(out)


def pr_user_prompt(units) -> str:
    return _render(_load(PROMPT_DIR / "user-pr.v1.md"),
                   files=", ".join("`%s`" % u.file for u in units), sections=sections(units))


def conformance_system_prompt() -> str:
    return _render(_load(PROMPT_DIR / "conformance-system.v1.md"),
                   vocabulary_block=vocabulary_block("conformance"))


def conformance_user_prompt(intent: str, file: str, diff: str, numbered: str,
                            elision: str = "", context: str = "") -> str:
    return _render(_load(PROMPT_DIR / "conformance-user.v1.md"), intent=intent, file=file,
                   diff=diff, numbered=numbered, elision=elision, context=context)


def conformance_blocks() -> list[dict]:
    """The shared rules carry the breakpoint; the intent is variable and goes in the user turn.

    Putting the intent in the system block would look tidier and would cost a cache write on
    every change, since the intent differs per commit.
    """
    return [{"type": "text", "text": conformance_system_prompt(),
             "cache_control": {"type": "ephemeral"}}]


def refutation_system_prompt() -> str:
    return _render(_load(PROMPT_DIR / "refutation-system.v1.md"),
                   vocabulary_block=vocabulary_block("verdict"))


#: In place of a diff, for a claim about a file the change does not touch.
NO_CHANGE = "(nothing: the change does not touch this file)"


def refutation_user_prompt(finding: dict, file: str, diff: str, numbered: str,
                           elision: str = "", context: str = "") -> str:
    """The claim under test, and nothing about who made it.

    `lens`, `kind` and `severity` are deliberately absent. They are the finder's framing, and
    framing is what a refuter must not inherit — the claim to test is only "with these inputs,
    does this line produce this consequence?".
    """
    return _render(_load(PROMPT_DIR / "refutation-user.v1.md"),
                   file=file, line=str(finding["line"]), snippet=finding["snippet"],
                   inputs=finding["inputs"], consequence=finding["consequence"],
                   diff=diff or NO_CHANGE, numbered=numbered, elision=elision,
                   context=context)


def refutation_blocks() -> list[dict]:
    """One block: the shared rules carry the breakpoint, and there is no per-claim system text."""
    return [{"type": "text", "text": refutation_system_prompt(),
             "cache_control": {"type": "ephemeral"}}]


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
