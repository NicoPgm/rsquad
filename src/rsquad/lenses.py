"""Step [2] — the blind lenses.

Several lenses read the same unit independently. They do not see each other's output, and they
do not see the specification.

**The blindness is a fact about the payload, not an instruction in the prompt.** `request()` is
a pure function of a `Unit` and a lens name: the diff, the numbered file, the shared rules and
the lens instruction. There is no parameter through which a spec could arrive, so "did not look
at the spec" is something a test can assert rather than something a model can be asked to
promise. A prompt saying *do not read the spec* would be unverifiable, and unverifiable is the
same as untrue at scale.

Everything a lens returns then passes the two mechanical guards before anyone reads it.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from . import anchoring, prompts
from .chunking import Unit, is_doc, is_test
from .findings import api_schema, validate

#: A starting point, not a bench result. The source project's `claude-sonnet-5` was fixed by a
#: measurement on entity survival, a criterion with nothing to do with reading code. Re-run the
#: choice against `evaluation/defects.yaml` before treating this as settled.
MODEL = "claude-opus-5"

#: Findings are short; the ceiling exists for the reasoning, which counts against it. 16 000 is
#: the practical non-streaming limit before HTTP timeouts become the dominant risk.
MAX_TOKENS = 16000

#: Effort per lens. `tests` reads assertions and needs less depth than walking execution paths.
EFFORT = {"repro": "high", "bounds": "high", "contract": "high", "tests": "medium",
          "docs": "high"}

LENSES = prompts.LENSES


#: The lenses that own a kind of file. The others read whatever neither of them owns.
OWNED = {"docs": is_doc, "tests": is_test}


def owner(path: str) -> str | None:
    """`docs` or `tests`, or None for code. Documentation wins: `tests/README.md` is prose."""
    return next((lens for lens, owns in OWNED.items() if owns(path)), None)


def applies(lens: str, path: str) -> bool:
    """Where a lens may report: `docs` in documentation, `tests` in test files, the other blind
    lenses in everything else (ADR-0009, ADR-0013).

    Measured both ways: across the whole Java campaign the `tests` lens was never shown a test
    and still answered four times in 190 tasks; shown one, it spoke
    (`docs/step7e-tests-lens.md`). A lens asked about something absent from its payload is
    paid to invent it.
    """
    return owner(path) == (lens if lens in OWNED else None)


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(*[getattr(self, f) + getattr(other, f) for f in
                       ("input_tokens", "output_tokens", "cache_creation_input_tokens",
                        "cache_read_input_tokens")])


@dataclass
class LensRun:
    """What one lens saw in one file. Never raises — a dead lens must not kill the review."""

    lens: str
    file: str
    findings: list[dict] = field(default_factory=list)
    dropped: list[tuple[dict, str]] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    latency_s: float = 0.0
    error: str | None = None


def request(unit: Unit, lens: str, model: str = MODEL) -> dict[str, Any]:
    """The exact request body. Pure — no client, no network, no clock.

    Order matters for caching: `output_config` and `system` render before `messages`, so the
    schema and the shared rules sit in the cached prefix and the unit lands after it.
    """
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "thinking": {"type": "adaptive"},
        "output_config": {
            "format": {"type": "json_schema", "schema": api_schema()},
            "effort": EFFORT.get(lens, "high"),
        },
        "system": prompts.system_blocks(lens),
        "messages": [{"role": "user", "content": prompts.user_prompt(
            file=unit.file, diff=unit.diff, numbered=unit.numbered, elision=unit.elision,
            context=unit.context_block)}],
    }


def _usage(response) -> Usage:
    raw = response.usage
    return Usage(
        input_tokens=raw.input_tokens,
        output_tokens=raw.output_tokens,
        cache_creation_input_tokens=getattr(raw, "cache_creation_input_tokens", 0) or 0,
        cache_read_input_tokens=getattr(raw, "cache_read_input_tokens", 0) or 0,
    )


def interpret(unit: Unit, lens: str, text: str) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Parse, validate against the schema, then run both mechanical guards."""
    payload = json.loads(text)
    validate(payload)
    for finding in payload["findings"]:
        finding["lens"] = lens
    return anchoring.sift(payload["findings"], {unit.file: unit.source})


#: Why a finding outside the change is dropped although it anchors.
INTRODUCED_OUTSIDE = "says introduced, in a file the change does not touch"


def interpret_pr(units: dict, lens: str, text: str,
                 outside=None) -> tuple[list[dict], list[tuple[dict, str]]]:
    """`interpret`, over every file of the change: each finding is anchored in its own file.

    **A defect may live outside the change.** `outside(path)` returns a unit for a file of
    `repo/` the change does not touch, and a finding there anchors against it: on ReviewBench
    the most severe defect of a pull request was a command, untouched by it, that the pull
    request made reachable. Such a finding cannot be `introduced`; that much of its `scope` is
    checked, the rest is the lens's word.

    The routing still holds, in or out of the change: a blind lens in a test file, or the
    `tests` lens in production code, is what it exists to keep out. A changed file this lens
    was not shown stays closed to it.
    """
    payload = json.loads(text)
    validate(payload)
    sources = {f: u.source for f, u in units.items() if applies(lens, f)}
    for finding in payload["findings"]:
        finding["lens"] = lens
        path = finding["file"]
        if outside is not None and path not in units and applies(lens, path):
            unit = outside(path)
            if unit is not None:
                sources[path] = unit.source
    anchored, dropped = anchoring.sift(payload["findings"], sources)
    kept = []
    for finding in anchored:
        if finding["file"] in units or finding["scope"] != "introduced":
            kept.append(finding)
        else:
            dropped.append((finding, INTRODUCED_OUTSIDE))
    return kept, dropped


def look(unit: Unit, lens: str, model: str = MODEL,
         client: "anthropic.Anthropic | None" = None) -> LensRun:
    """Run one lens over one unit. Failure is recorded, never raised.

    A lens that dies is a lens that said nothing, not a review that collapsed. The same rule
    the source project applies to a failed video: mark it and carry on.

    `anthropic` is imported here and not at the top: the API transport is frozen and optional
    (ADR-0009), and the harness path must import this module without it.
    """
    import anthropic

    run = LensRun(lens=lens, file=unit.file)
    client = client or anthropic.Anthropic()
    started = time.monotonic()
    try:
        response = client.messages.create(**request(unit, lens, model))
        run.usage = _usage(response)
        if response.stop_reason == "refusal":
            run.error = "declined (%s)" % getattr(response.stop_details, "category", None)
            return run
        if response.stop_reason == "max_tokens":
            run.error = "truncated at max_tokens=%d, the JSON is incomplete" % MAX_TOKENS
            return run
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            run.error = "no text block (stop_reason=%s)" % response.stop_reason
            return run
        run.findings, run.dropped = interpret(unit, lens, text)
    except anthropic.APIStatusError as error:
        run.error = "%s: %s" % (type(error).__name__, error.message)
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        run.error = "unparsable output despite the constraint: %s" % error
    except Exception as error:                                   # noqa: BLE001
        run.error = "%s: %s" % (type(error).__name__, error)
    finally:
        run.latency_s = time.monotonic() - started
    return run


def review(units: list[Unit], lens_names: list[str] | None = None, model: str = MODEL,
           client: "anthropic.Anthropic | None" = None,
           on_run=None) -> list[LensRun]:
    """Every lens that applies to each unit. One call per (unit, lens) pair."""
    import anthropic

    client = client or anthropic.Anthropic()
    runs = []
    for unit in units:
        for lens in (lens_names or LENSES):
            if not applies(lens, unit.file):
                continue
            run = look(unit, lens, model, client)
            runs.append(run)
            if on_run:
                on_run(run)
    return runs
