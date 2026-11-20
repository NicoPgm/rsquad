"""Step [3] — refutation. One reader per finding, in a separate context, trying to kill it.

Finding is free. An agent asked for problems supplies some, and most of what a review produces
is plausible rather than true. The asymmetry is the mechanism: a claim reaches a human only
after somebody tried to destroy it and failed.

**The refuter inherits no framing.** It is given the line, the snippet, the inputs and the
claimed consequence — never the lens that produced them, never the severity somebody assigned,
never the other findings. Those are the finder's opinions, and a refuter that saw them would be
grading a colleague instead of reading code. `request()` is pure, and a test asserts that none
of the three leaks into the payload.

**Doubt means refuted.** There is no confidence field, because a scale is where a refuter
hedges. The burden is on the claim; the reader's time gets the benefit of the doubt.
Doubt is also *named*: `undecided` kills a finding like any other cause, so the `Refuted`
section can tell "shown wrong" from "not shown right" (ADR-0009). With six causes only, a
refuter that could not decide had to borrow one that might not hold.

**A refutation is held to the standard it enforces.** `evidence_snippet` must anchor in the file
exactly as a finding's snippet must — quote real code near a real line, or be discarded.

And one asymmetry inside the asymmetry, which matters: **an unanchored verdict does not refute
anything.** "Doubt means refuted" governs the refuter's reasoning, not its malfunctions. A
verdict whose evidence does not exist in the file is not a doubt, it is a broken response, and
letting one kill a finding would mean hallucinated evidence silently destroying real work. Those
verdicts are recorded and ignored, and the finding survives to be read.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from . import anchoring, prompts
from .chunking import Unit
from .findings import api_schema, validate
from .lenses import MAX_TOKENS, MODEL, Usage, _usage

#: The hardest reading in the squad, and the one whose mistakes are least visible: a wrong
#: refutation deletes a real finding and leaves no trace in the queue.
EFFORT = "xhigh"

#: The only verdict that lets a finding through.
STANDS = "stands"

UNANCHORED = "evidence does not appear near the line it cites"

NOT_REFUTABLE = "no refuter exists for this claim shape"

#: What this refuter can test. It walks concrete inputs to a concrete consequence, which is the
#: shape a blind lens produces and **not** the shape of a conformance mismatch — that claim is
#: "the intent says X and the code does Y", and testing it needs the intent and a different
#: question. Pointing this refuter at one produced a crash on the first real run, which is the
#: honest outcome: it was documented as missing and then handed one anyway.
REQUIRED_FIELDS = ("inputs", "consequence")


def refutable(finding: dict) -> bool:
    return all(field in finding for field in REQUIRED_FIELDS)


@dataclass
class Verdict:
    """One refuter's answer about one finding."""

    finding: dict
    verdict: str = ""
    reason: str = ""
    evidence_line: int = 0
    evidence_snippet: str = ""
    anchored: bool = False
    usage: Usage = field(default_factory=Usage)
    latency_s: float = 0.0
    error: str | None = None

    @property
    def refutes(self) -> bool:
        """Does this verdict actually remove the finding from the queue?

        Three things must all hold: a verdict was produced, it is not `stands`, and its evidence
        is real. A broken refutation is not a refutation.
        """
        return bool(self.verdict) and self.verdict != STANDS and self.anchored and not self.error


def request(unit: Unit, finding: dict, model: str = MODEL) -> dict[str, Any]:
    """The exact request body. Pure — no client, no network, no clock, no other findings."""
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "thinking": {"type": "adaptive"},
        "output_config": {
            "format": {"type": "json_schema", "schema": api_schema("verdict")},
            "effort": EFFORT,
        },
        "system": prompts.refutation_blocks(),
        "messages": [{"role": "user", "content": prompts.refutation_user_prompt(
            finding, file=unit.file, diff=unit.diff, numbered=unit.numbered,
            elision=unit.elision, context=unit.context_block)}],
    }


def interpret(unit: Unit, finding: dict, text: str) -> Verdict:
    payload = json.loads(text)
    validate(payload, "verdict")
    return Verdict(
        finding=finding,
        verdict=payload["verdict"],
        reason=payload["reason"],
        evidence_line=payload["evidence_line"],
        evidence_snippet=payload["evidence_snippet"],
        anchored=anchoring.anchored(payload["evidence_snippet"], unit.source,
                                    payload["evidence_line"]),
    )


def refute(unit: Unit, finding: dict, model: str = MODEL,
           client: "anthropic.Anthropic | None" = None) -> Verdict:
    """Try to kill one finding. Failure is recorded, never raised.

    A refuter that dies leaves the finding standing. That is the safe direction: the cost is a
    reader's minute, where the other direction costs a real defect.
    """
    import anthropic

    result = Verdict(finding=finding)
    client = client or anthropic.Anthropic()
    started = time.monotonic()
    try:
        response = client.messages.create(**request(unit, finding, model))
        result.usage = _usage(response)
        if response.stop_reason in ("refusal", "max_tokens"):
            result.error = "stopped on %s" % response.stop_reason
            return result
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            result.error = "no text block (stop_reason=%s)" % response.stop_reason
            return result
        parsed = interpret(unit, finding, text)
        parsed.usage, parsed.error = result.usage, None
        result = parsed
        if not result.anchored:
            result.error = UNANCHORED
    except anthropic.APIStatusError as error:
        result.error = "%s: %s" % (type(error).__name__, error.message)
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        result.error = "unparsable verdict despite the constraint: %s" % error
    except Exception as error:                                   # noqa: BLE001
        result.error = "%s: %s" % (type(error).__name__, error)
    finally:
        result.latency_s = time.monotonic() - started
    return result


def refute_all(findings: list[dict], units: dict[str, Unit], model: str = MODEL,
               client: "anthropic.Anthropic | None" = None, on_verdict=None) -> list[Verdict]:
    """One call per finding. Order follows the findings, so a run is replayable."""
    import anthropic

    client = client or anthropic.Anthropic()
    verdicts = []
    for finding in findings:
        unit = units.get(finding["file"])
        if unit is None:
            continue
        if not refutable(finding):
            # Recorded, not skipped silently, and not spent on. A broken verdict leaves the
            # finding standing, so the claim still reaches the reader — uncontested, and the
            # run report says so.
            verdict = Verdict(finding=finding, error=NOT_REFUTABLE)
            verdicts.append(verdict)
            if on_verdict:
                on_verdict(verdict)
            continue
        verdict = refute(unit, finding, model, client)
        verdicts.append(verdict)
        if on_verdict:
            on_verdict(verdict)
    return verdicts


def survivors(verdicts: list[Verdict]) -> tuple[list[dict], list[Verdict]]:
    """(findings that survived, verdicts that killed one).

    Both halves are returned. What the refuter removed is the measurement of how well the lenses
    are behaving, and burying it would hide the most useful number in the run.
    """
    kept, killed = [], []
    for verdict in verdicts:
        if verdict.refutes:
            killed.append(verdict)
        else:
            finding = dict(verdict.finding)
            finding["verdict"] = verdict.verdict or "not refuted"
            kept.append(finding)
    return kept, killed
