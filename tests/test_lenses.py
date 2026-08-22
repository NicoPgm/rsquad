"""The blind lenses. No network anywhere in this file.

The blindness test is the one that matters. It does not check that a spec happens to be absent
from one payload — it checks that there is no channel through which a spec could arrive. An
absence you observe once is a coincidence; an absence the signature forbids is a property.
"""

import inspect
import json

import anthropic
import pytest

from rsquad.chunking import Unit
from rsquad.lenses import EFFORT, LENSES, LensRun, Usage, interpret, look, request

UNIT = Unit(
    file="src/avd/indexation.py",
    diff="@@ -40,3 +40,4 @@\n+    premiere = fiches[0]\n",
    source="def resume(fiches):\n    premiere = fiches[0]\n    return premiere.summary\n",
    numbered="1\tdef resume(fiches):\n2\t    premiere = fiches[0]\n3\t    return premiere.summary",
)

FINDING = {
    "file": "src/avd/indexation.py",
    "line": 2,
    "snippet": "premiere = fiches[0]",
    "kind": "boundary",
    "severity": "significant",
    "inputs": "fiches = []",
    "consequence": "raises IndexError",
}


def _payload_text(lens="repro") -> str:
    return json.dumps(request(UNIT, lens), ensure_ascii=False)


# ------------------------------------------------------------------ blindness

def test_a_lens_request_has_no_channel_for_a_specification():
    """The structural guard. If someone later adds `spec=` or `repo=`, this fails.

    Blindness enforced by prompt instruction would be unverifiable, and unverifiable is the
    same as untrue at scale. Enforced by signature, it is a fact.
    """
    assert set(inspect.signature(request).parameters) == {"unit", "lens", "model"}


def test_the_payload_is_exactly_the_unit_and_the_prompts():
    """A complete characterisation, not a list of forbidden words.

    Naming words to exclude does not work here — the shared prompt legitimately contains
    "commit message", in the sentence explaining that the lens is not shown one. What can be
    asserted is stronger: the request is byte-for-byte the shared block, the lens block, and
    the rendered unit. There is nothing else in it, so nothing else can leak.
    """
    from rsquad.prompts import system_blocks, user_prompt

    body = request(UNIT, "repro")
    assert body["system"] == system_blocks("repro")
    assert body["messages"] == [{"role": "user", "content": user_prompt(
        file=UNIT.file, diff=UNIT.diff, numbered=UNIT.numbered, elision=UNIT.elision)}]
    assert set(body) == {"model", "max_tokens", "thinking", "output_config", "system",
                         "messages"}


def test_every_lens_gets_the_same_shared_prefix():
    """Otherwise the four lenses pay four cache writes instead of one write and three reads."""
    prefixes = {request(UNIT, lens)["system"][0]["text"] for lens in LENSES}
    assert len(prefixes) == 1


def test_the_cache_breakpoint_is_on_the_shared_block():
    blocks = request(UNIT, "repro")["system"]
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in blocks[1]


def test_each_lens_contributes_its_own_instruction():
    instructions = {request(UNIT, lens)["system"][1]["text"] for lens in LENSES}
    assert len(instructions) == len(LENSES)


# ------------------------------------------------------------------ request shape

def test_the_output_format_is_constrained_mechanically():
    """A closed vocabulary asked for in prose is not a constraint."""
    config = request(UNIT, "repro")["output_config"]
    assert config["format"]["type"] == "json_schema"
    assert config["format"]["schema"]["$defs"]["kind"]["enum"]


def test_effort_is_set_per_lens():
    for lens in LENSES:
        assert request(UNIT, lens)["output_config"]["effort"] == EFFORT[lens]


def test_thinking_is_adaptive_and_carries_no_token_budget():
    """`budget_tokens` is rejected outright on this model generation."""
    body = request(UNIT, "repro")
    assert body["thinking"] == {"type": "adaptive"}
    assert "budget_tokens" not in json.dumps(body)


def test_the_ceiling_leaves_room_for_reasoning():
    """Reasoning tokens count against `max_tokens`; the source project lost a bench run to it."""
    assert request(UNIT, "repro")["max_tokens"] >= 16000


# ------------------------------------------------------------------ interpreting a reply

def test_a_sound_reply_is_kept_and_tagged_with_its_lens():
    kept, dropped = interpret(UNIT, "bounds", json.dumps({"findings": [FINDING]}))
    assert dropped == []
    assert kept[0]["lens"] == "bounds"


def test_a_hallucinated_snippet_is_dropped_before_anyone_reads_it():
    ghost = dict(FINDING, snippet="premiere = fiches.first()")
    kept, dropped = interpret(UNIT, "repro", json.dumps({"findings": [ghost]}))
    assert kept == []
    assert len(dropped) == 1


def test_an_empty_reply_is_normal():
    assert interpret(UNIT, "repro", json.dumps({"findings": []})) == ([], [])


# ------------------------------------------------------------------ failure isolation

class _Boom:
    def __init__(self, error):
        self._error = error
        self.messages = self

    def create(self, **_):
        raise self._error


def test_an_api_failure_is_recorded_not_raised():
    """A dead lens is a lens that said nothing, not a review that collapsed."""
    import httpx

    response = httpx.Response(500, request=httpx.Request("POST", "https://api.anthropic.com"))
    error = anthropic.APIStatusError("down", response=response, body=None)
    run = look(UNIT, "repro", client=_Boom(error))
    assert isinstance(run, LensRun)
    assert run.error and run.findings == []


def test_an_unexpected_exception_is_also_contained():
    run = look(UNIT, "repro", client=_Boom(RuntimeError("socket exploded")))
    assert "RuntimeError" in run.error


def test_usage_adds_up():
    assert (Usage(1, 2, 3, 4) + Usage(10, 20, 30, 40)) == Usage(11, 22, 33, 44)
