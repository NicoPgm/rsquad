"""The finding schema — what a lens is allowed to say.

`schema/finding.v1.json` is normative. The vocabularies are **closed**: `kind` and `severity`
are enumerations, constrained mechanically by the API's structured-output format, not by a line
of prompt asking nicely. A value outside the list is a generation failure, not a warning.

The vocabulary exists **once**, in the schema, together with the gloss that explains each value.
Nothing here or in `prompts/` may restate it: `vocabulary_block()` renders the prompt text from
the schema at run time, so the two cannot drift. A test asserts every enum value has a gloss and
no gloss names a value that is gone.

`glossary` is not a JSON Schema keyword. Validators ignore it, but `api_schema()` strips it
anyway — a strict structured-output format should carry nothing a validator would have to
forgive.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schema"
#: The three contracts. A finding is what a blind lens may say; a verdict is what a refuter may
#: say about one; a conformance mismatch is what the one lens that reads the intent may say. All
#: three are normative, all carry closed vocabularies, and all are read from disk so no prompt
#: ever restates them.
#:
#: `severity` is declared separately in the finding and conformance contracts rather than shared
#: by `$ref` across files, because a cross-file reference in a strict output format is a risk
#: nobody has measured. A test asserts the two lists stay identical — the sibling project's
#: discipline: a mechanical consistency check beats a clever schema.
CONTRACTS = {"finding": "finding.v1.json", "verdict": "verdict.v1.json",
             "conformance": "conformance.v1.json"}

VERSION = "v1"

#: Keys that mean something to us and nothing to a JSON Schema validator.
ANNOTATIONS = ("glossary",)

#: Keys a strict `output_config.format` schema rejects outright.
#:
#: Measured against the live API on 2026-08-22, one keyword at a time, not taken from
#: documentation:
#:
#:     minimum on an integer   -> 400 "property 'minimum' is not supported"
#:     minLength on a string   -> accepted
#:
#: So the string floors still bind at generation time and only the numeric bound falls back to
#: the client. `validate()` keeps the full schema, which is where `line >= 1` is still enforced
#: — the same division the source project states as its eleventh constraint: cardinality is not
#: guaranteed by structured outputs, so it is checked client-side, at the same place as the
#: literal verification.
UNSUPPORTED = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum")


@lru_cache(maxsize=None)
def schema(contract: str = "finding") -> dict:
    path = SCHEMA_DIR / CONTRACTS[contract]
    if not path.exists():
        raise SystemExit("schema not found: %s (installed non-editable?)" % path)
    return json.loads(path.read_text(encoding="utf-8"))


_REMOVED = ANNOTATIONS + UNSUPPORTED


def _strip(node):
    if isinstance(node, dict):
        return {k: _strip(v) for k, v in node.items() if k not in _REMOVED}
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def api_schema(contract: str = "finding") -> dict:
    """The schema as sent to the API in `output_config.format`.

    Note for token accounting: this counts toward the cached prefix, so it belongs **before**
    the cache breakpoint, with the diff after it.
    """
    return _strip(schema(contract))


def vocabulary(name: str, contract: str = "finding") -> list[str]:
    """The closed list for a field, read from the schema that owns it."""
    return list(schema(contract)["$defs"][name]["enum"])


def glossary(name: str, contract: str = "finding") -> dict[str, str]:
    return dict(schema(contract)["$defs"][name]["glossary"])


def vocabularies(contract: str = "finding") -> list[str]:
    """The `$defs` entries that are closed vocabularies, in a stable order.

    A `$defs` entry **is** a vocabulary when it carries a glossary — the object shapes live
    there too, and iterating all of them was a real bug: `finding` has no glossary, and asking
    for one crashed every prompt in the project at once.
    """
    return sorted(name for name, node in schema(contract)["$defs"].items()
                  if "glossary" in node)


def vocabulary_block(contract: str = "finding") -> str:
    """The text rendered into `{{VOCABULARY_BLOCK}}` in every lens prompt.

    Rendered, never written by hand. A prompt that spells out the values would be a second
    source of truth, and the second source is always the one that goes stale.
    """
    lines = []
    for name in vocabularies(contract):
        gloss = glossary(name, contract)
        lines.append("`%s` - exactly one of:" % name)
        lines.append("")
        for value in vocabulary(name, contract):
            lines.append("- `%s` - %s" % (value, gloss[value]))
        lines.append("")
    return "\n".join(lines).rstrip()


def validate(payload: dict, contract: str = "finding") -> None:
    """Raise `jsonschema.ValidationError` if the payload is not a well-formed finding set.

    This is the shape check only. It says nothing about whether a finding is *true* - that is
    what `anchoring` and, later, the refuter are for.
    """
    jsonschema.validate(payload, schema(contract))
