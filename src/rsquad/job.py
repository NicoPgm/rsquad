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

from . import anchoring, chunking, conformance, lenses, prompts, ranking, refutation
from .chunking import Unit
from .findings import CONTRACTS, api_schema, validate

VERSION = 1

LENS_ROUND, REFUTE_ROUND = 1, 2

#: The default tiers on this transport. Step 8 put the lenses on Sonnet (30/38 against 31/38 for
#: Opus, `docs/step8-tiered-models.md`), when a lens read one file and reported only what it
#: could trigger. Under the recipe of ADR-0011 the model matters more: on five unseen ReviewBench
#: pull requests, the recipe covered 10 golden findings on Sonnet and 19 on Opus
#: (`docs/reviewbench-pilot.md`, arm D taken apart, variant V4).
LENS_MODEL = "claude-opus-5"
REFUTE_MODEL = "claude-opus-5"


#: A task over every file of the change, in place of one file's name (ADR-0011).
WHOLE = "*"

#: Where `export` writes the tree at head, inside the job. The prompts name it.
REPOSITORY = "repo"


@dataclass
class Task:
    """One call the harness has to make."""

    id: str
    contract: str                 # which schema the reply must satisfy
    lens: str                     # a blind lens name, "conformance", or "refutation"
    file: str
    prompt: str
    model: str = ""               # which model the driver should run it on (ADR-0009)
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
               intent: conformance.Intent | None = None, model: str = "") -> list[Task]:
    tasks = []
    for lens in lens_names:
        # `docs` is shown the whole change, code included: documentation goes stale when the
        # code it describes moves, and the code is where that shows. It still reports only in
        # documentation. It runs when no documentation changed for the same reason.
        read = units if lens == "docs" else [u for u in units if lenses.applies(lens, u.file)]
        if not read:
            continue
        prompt = _task_text(prompts.system_prompt() + "\n\n" + prompts.lens_prompt(lens),
                            prompts.pr_user_prompt(read))
        tasks.append(Task(id="%s--PR" % lens, contract="finding", lens=lens, file=WHOLE,
                          model=model, prompt=prompt))
    for unit in units:
        stem = unit.file.replace("/", "__").replace("\\", "__")
        # Not on documentation, for now: one task per file, and the `docs` lens already reads
        # documentation against the code (ADR-0013).
        if intent is not None and intent.parts and not chunking.is_doc(unit.file):
            tasks.append(Task(
                id="conformance--%s" % stem, contract="conformance",
                lens=conformance.LENS, file=unit.file, model=model,
                prompt=_task_text(prompts.conformance_system_prompt(),
                                  prompts.conformance_user_prompt(
                                      intent.text, file=unit.file, diff=unit.diff,
                                      numbered=unit.numbered, elision=unit.elision,
                                      context=unit.context_block))))
    return tasks


def carried(findings: list[dict], units: dict[str, Unit]) -> list[dict]:
    """Findings that get no refutation task and must ride to the queue anyway.

    Conformance claims have no refuter (ADR-0007). On the API path they still reach the reader,
    because `refute_all` emits a "no refuter for this claim shape" verdict and the finding
    survives. Across a job boundary there is no memory: the second round's manifest holds only
    what it asked for, so anything without a task simply vanished — nine findings in, eight in
    the queue, and the missing one was the only conformance account in the run.

    Found by running the transport end to end. It is the same shape of mistake as documenting a
    gap and not closing it: the rule existed, and the new path around it did not know.
    """
    return [f for f in findings
            if units.get(f["file"]) is not None and not refutation.refutable(f)]


def refutation_tasks(findings: list[dict], units: dict[str, Unit],
                     model: str = "") -> list[Task]:
    """One task per refutable finding. The rest ride in the manifest — see `carried`."""
    tasks = []
    for position, finding in enumerate(findings, 1):
        unit = units.get(finding["file"])
        if unit is None or not refutation.refutable(finding):
            continue
        tasks.append(Task(
            id="refute--%04d" % position, contract="verdict", lens="refutation",
            file=finding["file"], finding=finding, model=model,
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


def outside_unit(repository: Path, path: str) -> Unit | None:
    """A file of the job's `repo/` the change does not touch, as a unit with no diff.

    None when the path leaves the copy, is not a file, or is not text: a finding there has
    nothing to anchor against and the guard drops it.
    """
    root = repository.resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        return None
    try:
        source = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    numbered, _ = chunking.number(source)
    return Unit(file=path, diff="", source=source, numbered=numbered)


@dataclass
class Ingested:
    findings: list[dict] = field(default_factory=list)
    dropped: list[tuple[dict, str]] = field(default_factory=list)
    verdicts: list = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    malformed: list[tuple[str, str]] = field(default_factory=list)
    #: The units passed in, plus one per file outside the change that a finding landed in.
    #: Round 2 needs them to write and read the refutations of those findings.
    units: dict[str, Unit] = field(default_factory=dict)


def _reply(round_dir: Path, task_id: str) -> str | None:
    path = round_dir / "results" / ("%s.json" % task_id)
    return path.read_text(encoding="utf-8") if path.exists() else None


def ingest(job: Path, units: dict[str, Unit],
           intent: conformance.Intent | None = None) -> Ingested:
    """Read one round's replies. Validate everything; trust nothing the harness did."""
    data = manifest(job)
    round_dir = job / ("round-%d" % data["round"])
    out = Ingested(units=dict(units))

    def outside(path: str) -> Unit | None:
        if path not in out.units:
            unit = outside_unit(job / REPOSITORY, path)
            if unit is None:
                return None
            out.units[path] = unit
        return out.units[path]

    for entry in data["tasks"]:
        text = _reply(round_dir, entry["id"])
        if text is None:
            # A task with no reply is not an empty result. Saying nothing and being unable to
            # speak look identical in a queue, and only one of them means the code is fine.
            out.missing.append(entry["id"])
            continue
        if entry["contract"] == "finding" and entry["file"] == WHOLE:
            try:
                kept, dropped = lenses.interpret_pr(units, entry["lens"], text, outside)
                out.findings += kept
                out.dropped += dropped
            except Exception as error:                           # noqa: BLE001
                out.malformed.append((entry["id"], "%s: %s" % (type(error).__name__, error)))
            continue
        unit = units.get(entry["file"]) or (outside(entry["file"])
                                            if entry["contract"] == "verdict" else None)
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
            # noqa keeps the broad catch: a harness can return anything, and one bad reply
            # must not end the ingest of every other.
            # Malformed is reported, never silently skipped: a harness that returns prose
            # instead of JSON must show up as a number, not as a quiet absence of findings.
            out.malformed.append((entry["id"], "%s: %s" % (type(error).__name__, error)))

    # Findings that had no task still reach the queue, uncontested and marked as such.
    for finding in data.get("carried", []):
        out.verdicts.append(refutation.Verdict(finding=finding,
                                               error=refutation.NOT_REFUTABLE))
    return out


def queue(ingested: Ingested, footer: str = "",
          excluded: list[tuple[str, str]] | None = None) -> str:
    surviving, killed = refutation.survivors(ingested.verdicts)
    findings = surviving if ingested.verdicts else ingested.findings
    errors = (["%s: no reply from the harness" % t for t in ingested.missing]
              + ["%s: %s" % pair for pair in ingested.malformed])
    return ranking.render(ranking.group(findings), ingested.dropped, errors, footer,
                          refuted=killed if ingested.verdicts else None, excluded=excluded)
