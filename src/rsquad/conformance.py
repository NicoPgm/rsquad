"""Step [1] — the conformance lens. The only reader shown what the change was supposed to do.

Every other step is deliberately kept from the intent (ADR-0002) so it answers a different
question. This one asks the question nobody else can: *does the change do what it said?*

**Its failure mode is not the others'.** A blind lens can hallucinate code, and the anchoring
guard catches that. This lens can hallucinate a *requirement* — and a fabricated requirement is
worse than a missed mismatch, because it sounds authoritative and sends a reader to argue with a
document that never said it. Two squads doing that twice is one squad nobody reads.

So both ends are anchored. `snippet` must appear in the file near its line, exactly as a
finding's must. `requirement` must appear **in the intent**, verbatim after whitespace
normalisation. If it cannot be quoted, it is not a requirement.

**The intent is named, never discovered.** The commit message is always included — it is the
author's own statement and it is free — and any further document must be passed explicitly. A
lens that went looking for "the spec" by walking directories would be one directory-walk away
from undoing the architecture in ADR-0002, and would also be wrong about which file matters.

Not built: a refuter for conformance findings. The refuter in step [3] tests reachability with
concrete inputs, which is not the shape of a conformance claim, and pointing it at one would
produce confident nonsense. What guards these findings today is the double anchor, and that is
less than the blind lenses get. Stated here rather than discovered later.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import anchoring, prompts
from .chunking import Unit
from .findings import api_schema, validate
from .lenses import MAX_TOKENS, MODEL, Usage, _usage
from .vcs import git

#: It reads prose against code, which is not the same work as walking execution paths.
EFFORT = "high"

LENS = "conformance"

UNQUOTED = "requirement does not appear in the stated intent"


@dataclass
class Intent:
    """What the change said it would do, and where each part came from."""

    parts: list[tuple[str, str]] = field(default_factory=list)   # (source, text)

    @property
    def text(self) -> str:
        return "\n\n".join("### %s\n\n%s" % (source, body) for source, body in self.parts)

    @property
    def sources(self) -> list[str]:
        return [source for source, _ in self.parts]

    def quotes(self, requirement: str) -> bool:
        """Does the intent literally contain this requirement?"""
        needle = anchoring.normalise(requirement)
        return bool(needle) and needle in anchoring.normalise(self.text)


def gather(head: str, repo: Path | None = None, specs: list[str] | None = None) -> Intent:
    """The commit message, plus any document named on the command line. Nothing discovered."""
    intent = Intent()
    message = git(["log", "-1", "--format=%B", head], repo).stdout.strip()
    if message:
        intent.parts.append(("commit message", message))
    for name in specs or []:
        path = Path(name)
        if not path.exists():
            raise SystemExit("intent document not found: %s" % path)
        intent.parts.append((str(path), path.read_text(encoding="utf-8", errors="replace")))
    return intent


@dataclass
class ConformanceRun:
    file: str
    findings: list[dict] = field(default_factory=list)
    dropped: list[tuple[dict, str]] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    latency_s: float = 0.0
    error: str | None = None


def request(unit: Unit, intent: Intent, model: str = MODEL) -> dict[str, Any]:
    """The exact request body. Pure — and the only one in the squad that carries an intent."""
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "thinking": {"type": "adaptive"},
        "output_config": {
            "format": {"type": "json_schema", "schema": api_schema("conformance")},
            "effort": EFFORT,
        },
        "system": prompts.conformance_blocks(),
        "messages": [{"role": "user", "content": prompts.conformance_user_prompt(
            intent.text, file=unit.file, diff=unit.diff, numbered=unit.numbered,
            elision=unit.elision, context=unit.context_block)}],
    }


def sift(findings: list[dict], unit: Unit,
         intent: Intent) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Both anchors: the code side in the file, the requirement side in the intent."""
    kept, dropped = [], []
    for finding in findings:
        reason = anchoring.reject(finding | {"inputs": finding["requirement"],
                                             "consequence": finding["mismatch"]},
                                  {unit.file: unit.source})
        if reason is None and not intent.quotes(finding["requirement"]):
            reason = UNQUOTED
        (dropped.append((finding, reason)) if reason else kept.append(finding))
    return kept, dropped


def interpret(unit: Unit, intent: Intent,
              text: str) -> tuple[list[dict], list[tuple[dict, str]]]:
    payload = json.loads(text)
    validate(payload, "conformance")
    for finding in payload["findings"]:
        finding["lens"] = LENS
    return sift(payload["findings"], unit, intent)


def check(unit: Unit, intent: Intent, model: str = MODEL,
          client: "anthropic.Anthropic | None" = None) -> ConformanceRun:
    """One file against the stated intent. Failure is recorded, never raised."""
    import anthropic

    run = ConformanceRun(file=unit.file)
    client = client or anthropic.Anthropic()
    started = time.monotonic()
    try:
        response = client.messages.create(**request(unit, intent, model))
        run.usage = _usage(response)
        if response.stop_reason in ("refusal", "max_tokens"):
            run.error = "stopped on %s" % response.stop_reason
            return run
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            run.error = "no text block (stop_reason=%s)" % response.stop_reason
            return run
        run.findings, run.dropped = interpret(unit, intent, text)
    except anthropic.APIStatusError as error:
        run.error = "%s: %s" % (type(error).__name__, error.message)
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        run.error = "unparsable output despite the constraint: %s" % error
    except Exception as error:                                   # noqa: BLE001
        run.error = "%s: %s" % (type(error).__name__, error)
    finally:
        run.latency_s = time.monotonic() - started
    return run


def review(units: list[Unit], intent: Intent, model: str = MODEL,
           client: "anthropic.Anthropic | None" = None, on_run=None) -> list[ConformanceRun]:
    import anthropic

    client = client or anthropic.Anthropic()
    runs = []
    for unit in units:
        run = check(unit, intent, model, client)
        runs.append(run)
        if on_run:
            on_run(run)
    return runs
