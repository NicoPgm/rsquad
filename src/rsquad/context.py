"""The context pack — what a blind lens is allowed to know about the rest of the repository.

The squad's sharpest limit was that a lens sees one file. A defect whose cause lives across an
import — a filter reading a field nothing populates, a call whose signature changed on the other
side — is invisible from a single diff. The obvious fix is to hand the lens file-reading tools.

**This is the other fix, and it keeps two properties the tools would cost.**

*Reproducible.* The pack is computed, not fetched. Same revision, same diff, same pack, byte for
byte — so a replay against `evaluation/defects.yaml` measures the lens rather than whatever the
lens felt like reading that day. An agent that browses cannot be replayed, and a squad that
cannot be replayed cannot be measured.

*Still blind.* The resolver only ever follows **code symbols the change actually references**.
There is no path from it to a specification, a ticket or a commit message, because it walks
imports, not directories. Blindness stays a property of the mechanism rather than a promise in
a prompt.

The cost is coverage: it resolves what the diff names, not what a curious reader would have
gone looking for. That is a real gap, and the honest place to compare the two designs is a
measurement, not an argument.

Resolution is per-language, so it is **question 6** of the adapter protocol — the one
`adapters/base.py` predicted would exist and said only execution would surface. It surfaced in
conversation instead, which was cheaper.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Lines kept per definition before it is truncated.
MAX_DEFINITION_LINES = 60

#: Lines kept across the whole pack. Past this the payload stops being context and starts being
#: a second file to review.
MAX_PACK_LINES = 400

NOTICE = (
    "These are definitions from elsewhere in the repository that the change **references**. "
    "They are provided so you can check how this code uses them. Two rules:\n\n"
    "- They are **not under review**. Report findings in the file under review only, and quote "
    "`snippet` from its numbered listing — never from this section.\n"
    "- This section holds what the change names, not everything that exists. **Absence here "
    "is not evidence of absence in the repository.**\n"
)


@dataclass(frozen=True)
class Definition:
    """One resolved symbol: where it lives and what it says."""

    symbol: str
    file: str
    line: int
    source: str
    truncated: bool = False

    def render(self) -> str:
        head = "### `%s` — `%s:%d`%s" % (self.symbol, self.file, self.line,
                                         " (truncated)" if self.truncated else "")
        return "%s\n\n```\n%s\n```" % (head, self.source.rstrip())


def truncate(source: str, limit: int = MAX_DEFINITION_LINES) -> tuple[str, bool]:
    lines = source.splitlines()
    if len(lines) <= limit:
        return source, False
    kept = lines[:limit]
    kept.append("... %d more lines of this definition not shown ..." % (len(lines) - limit))
    return "\n".join(kept), True


def cap(definitions: list[Definition], limit: int = MAX_PACK_LINES) -> list[Definition]:
    """Keep definitions until the pack reaches `limit` lines.

    Order is the resolver's, which is source order — deterministic, and not a relevance
    ranking, because ranking relevance would need a model and would put an unverified judgement
    inside the reproducible half.
    """
    kept, spent = [], 0
    for definition in definitions:
        height = len(definition.source.splitlines())
        if spent + height > limit and kept:
            break
        kept.append(definition)
        spent += height
    return kept


def render(definitions: list[Definition]) -> str:
    """The `{{CONTEXT}}` block, or an empty string when nothing resolved."""
    if not definitions:
        return ""
    dropped = ""
    body = "\n\n".join(d.render() for d in definitions)
    return "## Referenced definitions\n\n%s\n%s%s\n" % (NOTICE, dropped, body)
