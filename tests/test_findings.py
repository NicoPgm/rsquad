"""The finding schema and its closed vocabularies.

What is pinned here is the doctrine, not the current word list: the vocabulary exists once, the
prompt text is derived from it, and nothing a validator would have to forgive reaches the API.
"""

import jsonschema
import pytest

from rsquad.findings import (api_schema, glossary, schema, validate, vocabulary,
                             vocabulary_block)

GOOD = {
    "findings": [{
        "file": "src/avd/indexation.py",
        "line": 42,
        "snippet": "return fiches[0]",
        "kind": "boundary",
        "severity": "significant",
        "inputs": "an empty corpus, so `fiches` is []",
        "consequence": "raises IndexError instead of returning None",
    }]
}


# ------------------------------------------------------------------ one source of truth

@pytest.mark.parametrize("name", ["kind", "severity"])
def test_every_value_has_a_gloss(name):
    """The gloss is what the lens prompt shows. A value without one is invisible to the model."""
    assert set(vocabulary(name)) == set(glossary(name))


@pytest.mark.parametrize("name", ["kind", "severity"])
def test_the_prompt_block_is_rendered_from_the_schema(name):
    """A prompt that spelled out the values would be a second source, and it would go stale."""
    block = vocabulary_block()
    for value, gloss in glossary(name).items():
        assert "`%s`" % value in block
        assert gloss in block


def test_the_vocabularies_are_closed():
    """`enum`, not a sentence asking the model nicely. A value outside the list is a failure."""
    for name in ("kind", "severity"):
        assert "enum" in schema()["$defs"][name]


# ------------------------------------------------------------------ what reaches the API

def test_the_api_schema_carries_no_annotation():
    """`glossary` is ours, not JSON Schema's. Strict output formats get the standard shape."""
    def walk(node):
        if isinstance(node, dict):
            assert "glossary" not in node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(api_schema())
    assert "glossary" in schema()["$defs"]["kind"]      # still present in the source


def test_the_api_schema_still_validates_the_same_payloads():
    """Stripping annotations must not weaken the constraint it is sent to enforce."""
    jsonschema.validate(GOOD, api_schema())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"findings": [dict(GOOD["findings"][0], kind="style")]},
                            api_schema())


# ------------------------------------------------------------------ shape

def test_a_well_formed_finding_validates():
    validate(GOOD)


def test_no_findings_is_valid():
    """Empty is the common honest answer. A schema that forbade it would manufacture findings."""
    validate({"findings": []})


@pytest.mark.parametrize("field", ["file", "line", "snippet", "kind", "severity",
                                   "inputs", "consequence"])
def test_every_field_is_required(field):
    """`inputs` and `consequence` included - that is 'reproduction or nothing', in the schema."""
    finding = {k: v for k, v in GOOD["findings"][0].items() if k != field}
    with pytest.raises(jsonschema.ValidationError):
        validate({"findings": [finding]})


@pytest.mark.parametrize("field,value", [
    ("kind", "style"),
    ("severity", "nitpick"),
    ("line", 0),
    ("snippet", ""),
    ("inputs", ""),
])
def test_out_of_range_values_are_refused(field, value):
    with pytest.raises(jsonschema.ValidationError):
        validate({"findings": [dict(GOOD["findings"][0], **{field: value})]})


def test_an_extra_field_is_refused():
    """`additionalProperties: false` - otherwise a model invents its own confidence score."""
    with pytest.raises(jsonschema.ValidationError):
        validate({"findings": [dict(GOOD["findings"][0], confidence=0.9)]})
