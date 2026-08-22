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
SCHEMA_FILE = SCHEMA_DIR / "finding.v1.json"

VERSION = "v1"

#: Keys that mean something to us and nothing to a JSON Schema validator.
ANNOTATIONS = ("glossary",)


@lru_cache(maxsize=1)
def schema() -> dict:
    if not SCHEMA_FILE.exists():
        raise SystemExit("schema not found: %s (installed non-editable?)" % SCHEMA_FILE)
    return json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))


def _strip(node):
    if isinstance(node, dict):
        return {k: _strip(v) for k, v in node.items() if k not in ANNOTATIONS}
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def api_schema() -> dict:
    """The schema as sent to the API in `output_config.format`.

    Note for token accounting: this counts toward the cached prefix, so it belongs **before**
    the cache breakpoint, with the diff after it.
    """
    return _strip(schema())


def vocabulary(name: str) -> list[str]:
    """The closed list for `kind` or `severity`, read from the schema."""
    return list(schema()["$defs"][name]["enum"])


def glossary(name: str) -> dict[str, str]:
    return dict(schema()["$defs"][name]["glossary"])


def vocabulary_block() -> str:
    """The text rendered into `{{VOCABULARY_BLOCK}}` in every lens prompt.

    Rendered, never written by hand. A prompt that spells out the values would be a second
    source of truth, and the second source is always the one that goes stale.
    """
    lines = []
    for name in ("kind", "severity"):
        gloss = glossary(name)
        lines.append("`%s` - exactly one of:" % name)
        lines.append("")
        for value in vocabulary(name):
            lines.append("- `%s` - %s" % (value, gloss[value]))
        lines.append("")
    return "\n".join(lines).rstrip()


def validate(payload: dict) -> None:
    """Raise `jsonschema.ValidationError` if the payload is not a well-formed finding set.

    This is the shape check only. It says nothing about whether a finding is *true* - that is
    what `anchoring` and, later, the refuter are for.
    """
    jsonschema.validate(payload, schema())
