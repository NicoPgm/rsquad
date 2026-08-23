"""The harness transport — the same squad, run by somebody else's agent loop.

ADR-0005 asked for two transports and one core. This is the second transport, and it is
deliberately **not** "the Claude Code version": a Claude Code workflow does not run in Cursor,
and building against one harness would have produced a third implementation the first time the
editor changed.

So the seam is a **job on disk**, and it is narrow on purpose:

    rsquad export <job>      RSquad computes the units, resolves the context packs, renders
                             every prompt, and writes one task per call.
    <the harness>            reads each task, runs it, writes the JSON reply next to it.
                             Any harness. Claude Code, Cursor, a shell script, a person.
    rsquad ingest <job>      RSquad validates every reply, runs both mechanical guards, and
                             either writes the next round or the final queue.

Everything that makes the squad trustworthy stays on this side of the seam: the closed
vocabularies, the anchoring guard, "reproduction or nothing", the blindness of the lenses, the
ranking. The harness contributes exactly one thing — a model call — and cannot quietly change
what a lens was asked or what its answer had to satisfy.

**Two things this transport gives up, and they should be measured rather than argued about.**

*Mechanical constraint becomes best-effort.* A harness that supports structured output can force
the schema, and the manifest hands it the same one the API path uses. A harness that cannot will
return prose-wrapped JSON or worse. `ingest` validates every reply against the schema regardless
and drops what does not conform — the same client-side backstop already used for the numeric
bound the API rejects. So the constraint never disappears; it moves from generation time to
ingest time, where it costs a wasted call instead of a wrong finding.

*Prompt caching stops being ours.* On the API path the four lenses share a byte-identical prefix
carrying one cache write and three reads, measured. Here the harness decides. That is a real
cost difference and it points the opposite way from the billing question — which is exactly why
ADR-0005 defers the choice to a measurement.

**Refutation is inherently two rounds.** A refuter needs a finding, so it cannot be exported
alongside the lenses. `ingest` advances one round: it reads round 1, and writes round 2 rather
than a queue. Running `ingest` again on round 2 writes the queue.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import anchoring, conformance, lenses, prompts, ranking, refutation
from .chunking import Unit
from .findings import CONTRACTS, api_schema, validate

VERSION = 1

LENS_ROUND, REFUTE_ROUND = 1, 2


@dataclass
class Task:
    """One call the harness has to make."""

    id: str
    contract: str                 # which schema the reply must satisfy
    lens: str                     # a blind lens name, "conformance", or "refutation"
    file: str
    prompt: str
    finding: dict | None = None   # the claim under test, for refutation tasks only


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _task_text(system: str, user: str) -> str:
    """One file the harness can hand to an agent whole.

    System and user are concatenated because most harnesses give an agent a single prompt. The
    separation only mattered for the cache breakpoint, which the harness owns here anyway.
    """
    return "%s\n\n---\n\n%s\n" % (system, user)


def lens_tasks(units: list[Unit], lens_names: list[str],
               intent: conformance.Intent | None = None) -> list[Task]:
    tasks = []
    for unit in units:
        stem = unit.file.replace("/", "__").replace("\\", "__")
        for lens in lens_names:
            body = prompts.user_prompt(file=unit.file, diff=unit.diff, numbered=unit.numbered,
                                       elision=unit.elision, context=unit.context_block)
            tasks.append(Task(id="%s--%s" % (lens, stem), contract="finding", lens=lens,
                              file=unit.file,
                              prompt=_task_text(prompts.system_prompt()
                                                + "\n\n" + prompts.lens_prompt(lens), body)))
        if intent is not None and intent.parts:
            tasks.append(Task(
                id="conformance--%s" % stem, contract="conformance",
                lens=conformance.LENS, file=unit.file,
                prompt=_task_text(prompts.conformance_system_prompt(),
                                  prompts.conformance_user_prompt(
                                      intent.text, file=unit.file, diff=unit.diff,
                                      numbered=unit.numbered, elision=unit.elision,
                                      context=unit.context_block))))
    return tasks


def refutation_tasks(findings: list[dict], units: dict[str, Unit]) -> list[Task]:
    """One task per refutable finding. Conformance claims have no refuter (ADR-0007)."""
    tasks = []
    for position, finding in enumerate(findings, 1):
        unit = units.get(finding["file"])
        if unit is None or not refutation.refutable(finding):
            continue
        tasks.append(Task(
            id="refute--%04d" % position, contract="verdict", lens="refutation",
            file=finding["file"], finding=finding,
            prompt=_task_text(prompts.refutation_system_prompt(),
                              prompts.refutation_user_prompt(
                                  finding, file=unit.file, diff=unit.diff,
                                  numbered=unit.numbered, elision=unit.elision,
                                  context=unit.context_block))))
    return tasks


def export(job: Path, tasks: list[Task], meta: dict, round_number: int = LENS_ROUND) -> Path:
    """Write a round: the tasks, the schemas, and a manifest naming what each reply must be."""
    round_dir = job / ("round-%d" % round_number)
    for task in tasks:
        _write(round_dir / "tasks" / ("%s.md" % task.id), task.prompt)
    for contract in sorted({t.contract for t in tasks}):
        _write(job / "schema" / ("%s.json" % contract),
               json.dumps(api_schema(contract), indent=2, ensure_ascii=False))
    (round_dir / "results").mkdir(parents=True, exist_ok=True)

    manifest = dict(meta, version=VERSION, round=round_number,
                    tasks=[{k: v for k, v in asdict(t).items() if k != "prompt"}
                           for t in tasks])
    _write(job / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    return round_dir


def manifest(job: Path) -> dict:
    path = job / "manifest.json"
    if not path.exists():
        raise SystemExit("no manifest in %s — run `rsquad export` first." % job)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != VERSION:
        raise SystemExit("job written by a different version of rsquad (%s)"
                         % data.get("version"))
    return data


@dataclass
class Ingested:
    findings: list[dict] = field(default_factory=list)
    dropped: list[tuple[dict, str]] = field(default_factory=list)
    verdicts: list = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    malformed: list[tuple[str, str]] = field(default_factory=list)


def _reply(round_dir: Path, task_id: str) -> str | None:
    path = round_dir / "results" / ("%s.json" % task_id)
    return path.read_text(encoding="utf-8") if path.exists() else None


def ingest(job: Path, units: dict[str, Unit],
           intent: conformance.Intent | None = None) -> Ingested:
    """Read one round's replies. Validate everything; trust nothing the harness did."""
    data = manifest(job)
    round_dir = job / ("round-%d" % data["round"])
    out = Ingested()

    for entry in data["tasks"]:
        text = _reply(round_dir, entry["id"])
        if text is None:
            # A task with no reply is not an empty result. Saying nothing and being unable to
            # speak look identical in a queue, and only one of them means the code is fine.
            out.missing.append(entry["id"])
            continue
        unit = units.get(entry["file"])
        if unit is None:
            out.malformed.append((entry["id"], "no unit for %s" % entry["file"]))
            continue
        try:
            if entry["contract"] == "finding":
                kept, dropped = lenses.interpret(unit, entry["lens"], text)
                out.findings += kept
                out.dropped += dropped
            elif entry["contract"] == "conformance":
                if intent is None:
                    raise SystemExit("this job holds conformance replies; pass the same "
                                     "--spec arguments so the requirement anchor can run")
                kept, dropped = conformance.interpret(unit, intent, text)
                out.findings += kept
                out.dropped += dropped
            else:
                verdict = refutation.interpret(unit, entry["finding"], text)
                if not verdict.anchored:
                    verdict.error = refutation.UNANCHORED
                out.verdicts.append(verdict)
        except Exception as error:                               # noqa: BLE001
            # Malformed is reported, never silently skipped: a harness that returns prose
            # instead of JSON must show up as a number, not as a quiet absence of findings.
            out.malformed.append((entry["id"], "%s: %s" % (type(error).__name__, error)))
    return out


def queue(ingested: Ingested, footer: str = "") -> str:
    surviving, killed = refutation.survivors(ingested.verdicts)
    findings = surviving if ingested.verdicts else ingested.findings
    errors = (["%s: no reply from the harness" % t for t in ingested.missing]
              + ["%s: %s" % pair for pair in ingested.malformed])
    return ranking.render(ranking.group(findings), ingested.dropped, errors, footer,
                          refuted=killed if ingested.verdicts else None)
