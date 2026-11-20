"""RSquad command line.

    rsquad gate                                  # HEAD against its parent
    rsquad gate --base master --strict           # against the merge base with master
    rsquad gate --head 4164d03                   # replay the gate on a past commit
    rsquad gate --replay 20 --repo ../other      # aggregate over the last 20 commits

    rsquad review                                # what would be sent, and to how many lenses
    rsquad review --confirm                      # actually spend
    rsquad review --base master --lens repro --confirm
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import (budget, chunking, conformance, config, evaluate, job, lenses, ranking,
               refutation)
from .gate import ADAPTERS, DEFAULT_ADAPTER, by_language, check, git, merge_base, report
from .vcs import resolve


def _gate(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve() if args.repo else None
    adapter = ADAPTERS[args.adapter]
    if args.replay:
        return _replay(args, repo, adapter)

    outcome = check(base=args.base, head=args.head, repo=repo, adapter=adapter,
                    patterns=args.path)
    if not outcome.files:
        print("no test file changed since %s — nothing to check." % outcome.base[:12])
        return 0

    print("%s <- %s | %d changed test file(s)"
          % (outcome.head[:12], outcome.base[:12], len(outcome.files)))
    for path in outcome.files:
        print("  %s" % path)
    print("  %d new or modified test(s)" % len(outcome.changed_functions))

    if not outcome.verdicts:
        print("\nno case ran — the runner collected nothing on the base.")
        return 0
    return report(outcome.verdicts, args.strict)


def _replay(args: argparse.Namespace, repo: Path | None, adapter) -> int:
    """Replay the gate across the last N commits and aggregate the real rate.

    Units must stay coherent: `new` counts test FUNCTIONS, so the summary must count functions
    too — a parametrized function yields N JUnit cases.
    """
    log = git(["log", "--format=%h", "-%d" % args.replay, args.head], repo).stdout.split()
    commits = [c for c in log if c]
    print("%d commit(s) examined\n" % len(commits))
    print("%-9s %-44s %5s %5s %5s %5s" % ("commit", "subject", "new", "vald", "susp", "none"))
    print("-" * 80)

    total = dict(new=0, valid=0, suspect=0, no_signal=0, with_tests=0, with_signal=0)
    for commit in commits:
        subject = git(["log", "--format=%s", "-1", commit], repo).stdout.strip()[:44]
        outcome = check(head=commit, repo=repo, adapter=adapter, patterns=args.path)
        if not outcome.files:
            print("%-9s %-44s %5s %5s %5s %5s" % (commit, subject, "-", "-", "-", "-"))
            continue
        total["with_tests"] += 1
        total["new"] += len(outcome.changed_functions)
        s = outcome.summary
        if s:
            total["valid"] += s.valid
            total["suspect"] += s.suspect
            total["no_signal"] += s.no_signal
        if outcome.has_signal:
            total["with_signal"] += 1
        print("%-9s %-44s %5d %5d %5d %5d"
              % (commit, subject, len(outcome.changed_functions),
                 s.valid if s else 0, s.suspect if s else 0, s.no_signal if s else 0))

    examined = total["valid"] + total["suspect"]
    print("-" * 80)
    print("%-54s %5d %5d %5d %5d"
          % ("TOTAL", total["new"], total["valid"], total["suspect"], total["no_signal"]))
    print("\ncommits touching tests            : %d / %d" % (total["with_tests"], len(commits)))
    print("commits where the gate says something : %d / %d"
          % (total["with_signal"], total["with_tests"]))
    if total["new"]:
        print("test functions examined           : %d / %d  (%.0f %%)"
              % (examined, total["new"], 100 * examined / total["new"]))
    if examined:
        print("among those examined              : %d valid, %d suspect  (%.0f %% suspect)"
              % (total["valid"], total["suspect"], 100 * total["suspect"] / examined))
    return 1 if (args.strict and total["suspect"]) else 0


def _require_api() -> None:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        raise SystemExit("the API transport is optional and frozen (ADR-0009): "
                         "pip install 'rsquad[api]'") from None


def _adapter(context: bool):
    """The context pack is off unless asked for (ADR-0009): 14/19 with it and without it, the
    same fourteen cases, for 30 % more payload (`docs/step7b-context-pack.md`)."""
    return by_language if context else None


def _round_two(data: dict) -> dict:
    """What the refutation round must remember of the first.

    Jobs written before 2026-11-20 carry neither key: they all had the pack, and one model.
    """
    meta = {k: data[k] for k in ("base", "head", "repo", "specs", "model")}
    meta["path"] = data.get("path")
    meta["context"] = data.get("context", True)
    meta["refute_model"] = data.get("refute_model", data["model"])
    return meta


def _show_excluded(excluded) -> None:
    for path, reason in excluded:
        print("  %-52s not reviewed: %s" % (path, reason))


@dataclass
class Outcome:
    """What steps [1] to [3] produced on one set of units."""

    runs: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    dropped: list = field(default_factory=list)
    verdicts: list = field(default_factory=list)
    killed: list = field(default_factory=list)
    errors: list = field(default_factory=list)


def _run_squad(units, chosen, model, intent, refute: bool, quiet: bool = False) -> Outcome:
    """Steps [1] to [3] over already-computed units.

    `review` and `evaluate` both call this. Duplicating it would let the measured pipeline drift
    from the deployed one, and a measurement of a pipeline nobody runs is worse than none — the
    same argument that keeps both transports on one core (ADR-0005).

    `intent` of None skips step [1] deliberately; `refute` of False skips step [3].
    """
    def say(*parts):
        # `flush=True` is not cosmetic here. Piped or redirected, Python buffers stdout, so a
        # command that spends money for minutes looks hung until it is finished — and the one
        # moment you want to see it is while it is still cancellable.
        if not quiet:
            print(*parts, flush=True)

    def told(run):
        say("  %-10s %-40s %s" % (getattr(run, "lens", conformance.LENS), run.file[-40:],
                                  run.error or "%d finding(s)" % len(run.findings)))

    out = Outcome(runs=lenses.review(units, chosen, model, on_run=told))

    if intent is not None:
        say("\nconformance, against %s" % ", ".join(intent.sources))
        out.runs += conformance.review(units, intent, model, on_run=told)

    for run in out.runs:
        out.findings += run.findings
        out.dropped += run.dropped
        if run.error:
            out.errors.append("%s on %s: %s" % (getattr(run, "lens", conformance.LENS),
                                                run.file, run.error))

    if refute and out.findings:
        say("\n%d finding(s) to refute" % len(out.findings))
        out.verdicts = refutation.refute_all(
            out.findings, {u.file: u for u in units}, model,
            on_verdict=lambda v: say("  %-46s %s"
                                     % ("%s:%s" % (v.finding["file"][-30:], v.finding["line"]),
                                        v.error or v.verdict)))
        out.findings, out.killed = refutation.survivors(out.verdicts)
    return out


def _review(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve() if args.repo else None
    head = resolve(args.head, repo)
    base = merge_base(args.base or "%s~1" % head, head, repo)
    units, excluded = chunking.units(base, head, repo, args.path,
                                     adapter=_adapter(args.context))
    chosen = args.lens or list(lenses.LENSES)
    _show_excluded(excluded)

    if not units:
        print("nothing readable changed between %s and %s." % (base[:12], head[:12]))
        return 0

    calls = sum(lenses.applies(lens, u.file) for u in units for lens in chosen)
    print("%s <- %s | %d file(s), %d lens call(s)" % (head[:12], base[:12], len(units), calls))
    for unit in units:
        print("  %-52s %6d chars%s" % (unit.file, len(unit.numbered),
                                       "  (elided)" if unit.elided else ""))

    if args.confirm:
        _require_api()
    if args.confirm and not config.credential_available():
        raise SystemExit(
            "no %s in the environment or in %s.\n"
            "Export it, or source the .env you already keep for another project - do not copy "
            "the key into a second file." % (config.KEY, config.ENV))

    if not args.confirm:
        # No estimate is printed on purpose. Two invented cost constants in the source project
        # are in `evaluation/defects.yaml`; this tool reports what was billed, not what it
        # guessed. Pass --confirm to find out.
        print("\ndry run. --confirm to spend."
              + ("" if args.no_refute else " Plus one further call per finding, to refute it."))
        return 0

    intent = conformance.gather(head, repo, args.spec)
    if not args.no_conformance and not intent.parts:
        raise SystemExit(
            "no stated intent: the commit message is empty and no --spec was given.\n"
            "Pass --spec, or --no-conformance to skip step [1] deliberately.")

    outcome = _run_squad(units, chosen, args.model, None if args.no_conformance else intent,
                         refute=not args.no_refute)
    findings, dropped, verdicts = outcome.findings, outcome.dropped, outcome.verdicts
    killed, errors, runs = outcome.killed, outcome.errors, outcome.runs

    usages = [r.usage for r in runs] + [v.usage for v in verdicts]
    spend = budget.total(args.model, usages)
    footer = ("Model `%s`, %d lens call(s) + %d refutation(s), %.4f USD billed. %s"
              % (args.model, len(runs), len(verdicts), spend.total,
                 budget.cache_verdict(usages)))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(ranking.render(ranking.group(findings), dropped, errors, footer,
                                  refuted=killed if not args.no_refute else None,
                                  excluded=excluded),
                   encoding="utf-8")
    print("\n%s" % footer)
    print("%d survived refutation, %d refuted, %d dropped by the guards, %d lens failure(s)"
          " -> %s" % (len(findings), len(killed), len(dropped), len(errors), out))
    # Always 0. Only the gate blocks; opinions comment.
    return 0


def _case_units(defect: dict, repo: Path, context: bool):
    """The one unit a case is reviewed on: its file, at the commit that introduced the defect."""
    head = resolve(defect["introduced_in"], repo)
    base = merge_base("%s~1" % head, head, repo)
    units, excluded = chunking.units(base, head, repo, [defect["file"]],
                                     adapter=_adapter(context))
    if not units:
        # ValueError and not SystemExit: the callers catch Exception so that one case never
        # ends the replay of the others, and SystemExit is not an Exception.
        raise ValueError("%s not reviewed in %s: %s"
                         % (defect["file"], head[:12],
                            excluded[0][1] if excluded else "it did not change"))
    return head, base, units


def _evaluate_export(args, scorable, excluded, repo: Path, chosen) -> int:
    """Write one job per case, for a harness to run.

    The same selection, the same scoring rule and the same report as the API path — only the
    transport differs, which is ADR-0005 applied to the measurement rather than to the review.
    It matters here for a reason the ADR did not anticipate: **scaling the case count costs
    tokens on this path and dollars on the other**, and a detection rate wants cases.
    """
    workspace = Path(args.jobs)
    written = 0
    for defect in scorable:
        try:
            head, base, units = _case_units(defect, repo, args.context)
            intent = conformance.gather(head, repo, None)
            tasks = job.lens_tasks(units, chosen, intent if intent.parts else None, args.model)
        except Exception as error:                                   # noqa: BLE001
            print("  %-44s not exported: %s" % (defect["id"], error))
            continue
        # `path` rides in the manifest so ingest rebuilds the SAME unit. Without it the review
        # would be one file and the ingest a whole commit, and the two would stop lining up.
        job.export(workspace / defect["id"], tasks,
                   {"base": base, "head": head, "repo": str(repo), "specs": [],
                    "model": args.model, "refute_model": args.refute_model or args.model,
                    "context": args.context, "path": defect["file"], "case": defect["id"]})
        written += 1
        print("  %-44s %d task(s)" % (defect["id"], len(tasks)))

    print("\n%d job(s) in %s. Run them, then: rsquad evaluate --ingest --jobs %s ..."
          % (written, workspace, workspace))
    return 0


def _evaluate_ingest(args, scorable, excluded, repo: Path, chosen) -> int:
    """Read the harness's replies for every case, advancing one round or writing the report."""
    workspace = Path(args.jobs)
    cases, advanced, dropped = [], 0, []
    for defect in scorable:
        folder = workspace / defect["id"]
        if not (folder / "manifest.json").exists():
            cases.append((defect, [], "no job in %s" % folder))
            continue
        data = job.manifest(folder)
        here = Path(data["repo"])
        units = {u.file: u for u in chunking.units(
            data["base"], data["head"], here,
            [data["path"]] if data.get("path") else None,
            adapter=_adapter(data.get("context", True)))[0]}
        intent = conformance.gather(data["head"], here, data["specs"])
        result = job.ingest(folder, units, intent)
        dropped += result.dropped

        if data["round"] == job.LENS_ROUND and not args.no_refute and result.findings:
            meta = _round_two(data)
            meta["carried"] = job.carried(result.findings, units)
            job.export(folder, job.refutation_tasks(result.findings, units,
                                                    meta["refute_model"]),
                       meta, round_number=job.REFUTE_ROUND)
            advanced += 1
            continue

        surviving = (refutation.survivors(result.verdicts)[0] if result.verdicts
                     else result.findings)
        note = None
        if result.missing:
            note = "%d task(s) had no reply from the harness" % len(result.missing)
        cases.append((defect, surviving, note))

    if advanced:
        print("%d case(s) advanced to the refutation round. Run the harness again, then ingest "
              "again." % advanced)
        return 0

    footer = ("Harness transport, %d case(s), %d finding(s) refused by the guards. **No dollar "
              "cost**: the tokens are the harness's. That is the point of running the scaling "
              "measurement here." % (len(cases), len(dropped)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(evaluate.render(cases, excluded, footer), encoding="utf-8")
    print("%d case(s) ingested -> %s. The verdicts are yours to fill in." % (len(cases), out))
    return 0


def _evaluate(args: argparse.Namespace) -> int:
    """Replay the squad on diffs known to contain a defect, and lay the evidence out.

    It reports fractions with their denominators and computes no rate: on a handful of cases a
    25 % detection rate and a 75 % one are the same measurement, and a percentage printed from
    them would be believed. `docs/evaluation.md`.
    """
    defects = evaluate.load(Path(args.defects))
    scorable, excluded = evaluate.partition(defects)
    if args.case:
        wanted = set(args.case)
        excluded += [(d, "not selected by --case") for d in scorable if d["id"] not in wanted]
        scorable = [d for d in scorable if d["id"] in wanted]

    print("%d case(s) in the set: %d scorable, %d excluded"
          % (len(defects), len(scorable), len(excluded)))
    for defect, why in excluded:
        print("  skip  %-44s %s" % (defect["id"], why))
    if not scorable:
        print("\nnothing to replay.")
        return 0

    repo = Path(args.repo).resolve()
    chosen = list(lenses.LENSES)
    print("\n%d case(s) to replay against %s, %d lens(es) each"
          % (len(scorable), repo, len(chosen)))
    for defect in scorable:
        print("  %-44s %s @ %s" % (defect["id"], defect["file"], defect["introduced_in"]))

    if args.export or args.ingest:
        if not args.jobs:
            raise SystemExit("--export and --ingest need --jobs <workspace>")
        handler = _evaluate_export if args.export else _evaluate_ingest
        return handler(args, scorable, excluded, repo, chosen)

    if args.max_usd is not None and args.max_usd < evaluate.WORST_CASE_USD:
        raise SystemExit(
            "--max-usd %.2f is below the worst single case measured (%.2f), so nothing would "
            "run at all. Raise it, or narrow the set with --case."
            % (args.max_usd, evaluate.WORST_CASE_USD))

    if not args.confirm:
        print("\ndry run. --confirm to spend. Plus one further call per finding, to refute it.")
        return 0
    _require_api()
    if not config.credential_available():
        raise SystemExit("no %s in the environment or in %s." % (config.KEY, config.ENV))

    cases, usages, dropped = [], [], []
    for defect in scorable:
        spent = budget.total(args.model, usages).total
        if not evaluate.within_budget(spent, args.max_usd):
            # Not a miss. A case that never ran and a case that found nothing look identical in
            # a total, and only one of them says anything about the squad.
            reason = ("not started — %.4f USD spent, and one more case could cross the "
                      "--max-usd %.2f cap" % (spent, args.max_usd))
            print("\n--- %s\n  %s" % (defect["id"], reason), flush=True)
            cases.append((defect, [], reason))
            continue
        print("\n--- %s" % defect["id"], flush=True)
        try:
            head, base, units = _case_units(defect, repo, args.context)
            intent = conformance.gather(head, repo, None)
            outcome = _run_squad(units, chosen, args.model,
                                 intent if intent.parts else None, refute=not args.no_refute)
        except Exception as error:                                   # noqa: BLE001
            # One case must never end the replay of the others — the same rule the pipeline
            # applies to a batch. A case that could not run is reported as such, never as a miss.
            print("  did not run: %s" % error, flush=True)
            cases.append((defect, [], str(error)))
            continue
        usages += [r.usage for r in outcome.runs] + [v.usage for v in outcome.verdicts]
        # What the guards refuse is a measurement of how the lenses are behaving, so it is
        # reported rather than discarded — `review` has always done this and `evaluate` did not,
        # which came to light only when a finished run could not answer "how many were dropped?".
        dropped += outcome.dropped
        cases.append((defect, outcome.findings, None))

    spend = budget.total(args.model, usages)
    footer = ("Model `%s`, %d call(s) across %d case(s), %.4f USD billed. "
              "%d finding(s) refused by the guards. %s"
              % (args.model, len(usages), len(cases), spend.total, len(dropped),
                 budget.cache_verdict(usages)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(evaluate.render(cases, excluded, footer), encoding="utf-8")
    print("\n%s\n%d case(s) replayed -> %s. The verdicts are yours to fill in."
          % (footer, len(cases), out))
    return 0


def _units_and_intent(args, repo):
    head = resolve(args.head, repo)
    base = merge_base(args.base or "%s~1" % head, head, repo)
    units, excluded = chunking.units(base, head, repo, args.path,
                                     adapter=_adapter(args.context))
    return head, base, units, excluded, conformance.gather(head, repo, args.spec)


def _export(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve() if args.repo else None
    head, base, units, excluded, intent = _units_and_intent(args, repo)
    _show_excluded(excluded)
    if not units:
        print("nothing readable changed between %s and %s." % (base[:12], head[:12]))
        return 0

    tasks = job.lens_tasks(units, args.lens or list(lenses.LENSES),
                           None if args.no_conformance else intent, args.model)
    out = Path(args.job)
    meta = {"base": base, "head": head, "repo": str(repo or Path.cwd()),
            "specs": args.spec or [], "model": args.model,
            "refute_model": args.refute_model or args.model, "context": args.context}
    round_dir = job.export(out, tasks, meta)

    print("%s <- %s | %d task(s) written to %s"
          % (head[:12], base[:12], len(tasks), round_dir / "tasks"))
    print("\nRun each task and write its JSON reply to %s/<task id>.json."
          % (round_dir / "results"))
    print("Schemas the replies must satisfy are in %s." % (out / "schema"))
    print("Then: rsquad ingest %s" % out)
    return 0


def _ingest(args: argparse.Namespace) -> int:
    out = Path(args.job)
    data = job.manifest(out)
    repo = Path(data["repo"])
    # Units are recomputed from the manifest rather than carried in it. They are a pure
    # function of (base, head, repo), so recomputing is both cheaper and a check: if the
    # revisions moved under the job, the anchors stop matching and the guards say so.
    selected, excluded = chunking.units(data["base"], data["head"], repo, args.path,
                                        adapter=_adapter(data.get("context", True)))
    units = {u.file: u for u in selected}
    intent = conformance.gather(data["head"], repo, data["specs"])
    result = job.ingest(out, units, intent)

    print("round %d: %d finding(s), %d dropped by the guards, %d missing, %d malformed"
          % (data["round"], len(result.findings), len(result.dropped),
             len(result.missing), len(result.malformed)))

    if data["round"] == job.LENS_ROUND and not args.no_refute and result.findings:
        meta = _round_two(data)
        tasks = job.refutation_tasks(result.findings, units, meta["refute_model"])
        # Findings with no refuter ride in the manifest rather than falling off the edge of the
        # round. The queue must show every finding that survived the guards, contested or not.
        meta["carried"] = job.carried(result.findings, units)
        round_dir = job.export(out, tasks, meta, round_number=job.REFUTE_ROUND)
        print("\n%d refutation task(s) written to %s (%d finding(s) carried, no refuter)"
              % (len(tasks), round_dir / "tasks", len(meta["carried"])))
        print("Run them, then: rsquad ingest %s" % out)
        return 0

    queue = Path(args.out)
    queue.parent.mkdir(parents=True, exist_ok=True)
    queue.write_text(job.queue(result, "Harness transport, job %s." % out, excluded),
                     encoding="utf-8")
    surviving, killed = refutation.survivors(result.verdicts)
    print("%d survived, %d refuted -> %s"
          % (len(surviving) if result.verdicts else len(result.findings), len(killed), queue))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rsquad", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    gate = sub.add_parser("gate", help="step [0] — a new test must fail on the code as it was")
    gate.add_argument("--base", default=None,
                      help="reference branch or commit (default: the parent of --head)")
    gate.add_argument("--head", default="HEAD",
                      help="revision to examine (default: HEAD). Replaying a past commit is "
                           "how you measure what the gate would have caught, on data nobody "
                           "arranged.")
    gate.add_argument("--repo", default=None, help="repository to run against (default: cwd)")
    gate.add_argument("--path", action="append", default=None,
                      help="test paths to watch; repeatable")
    gate.add_argument("--adapter", default=DEFAULT_ADAPTER, choices=sorted(ADAPTERS),
                      help="stack adapter (default: %s)" % DEFAULT_ADAPTER)
    gate.add_argument("--replay", type=int, default=0, metavar="N",
                      help="replay across the last N commits and aggregate")
    gate.add_argument("--strict", action="store_true",
                      help="exit 1 if any suspect remains")
    gate.set_defaults(handler=_gate)

    review = sub.add_parser("review", help="steps [2] and [4] - blind lenses, ranked queue")
    review.add_argument("--base", default=None,
                        help="reference branch or commit (default: the parent of --head)")
    review.add_argument("--head", default="HEAD", help="revision to review (default: HEAD)")
    review.add_argument("--repo", default=None, help="repository to review (default: cwd)")
    review.add_argument("--path", action="append", default=None,
                        help="restrict to these paths; repeatable")
    review.add_argument("--lens", action="append", default=None, choices=list(lenses.LENSES),
                        help="run only this lens; repeatable (default: all four)")
    review.add_argument("--model", default=lenses.MODEL, help="default: %s" % lenses.MODEL)
    review.add_argument("--out", default="review/queue.md", help="where to write the queue")
    review.add_argument("--spec", action="append", default=None,
                        help="a document stating what this change should do; repeatable. The "
                             "commit message is always included. Nothing is discovered by "
                             "walking directories - step [1] reads what you name, and the other "
                             "steps read none of it")
    review.add_argument("--no-conformance", action="store_true",
                        help="skip step [1]")
    review.add_argument("--context", action="store_true",
                        help="add the context pack: definitions the changed lines use, from "
                             "other files. Off by default (ADR-0009)")
    review.add_argument("--no-refute", action="store_true",
                        help="skip step [3]. Cheaper, and the queue becomes a list of "
                             "suspicions nobody contested")
    review.add_argument("--confirm", action="store_true",
                        help="actually call the API and spend; without it, a dry run")
    review.set_defaults(handler=_review)

    ev = sub.add_parser("evaluate", help="replay the squad on defects labelled by reality")
    ev.add_argument("--defects", default="evaluation/defects.yaml",
                    help="the ground-truth set (default: %(default)s)")
    ev.add_argument("--repo", required=True,
                    help="the repository the cases were recorded against")
    ev.add_argument("--case", action="append", default=None,
                    help="replay only this case id; repeatable. Bounds the spend")
    ev.add_argument("--model", default=lenses.MODEL, help="default: %s" % lenses.MODEL)
    ev.add_argument("--out", default="evaluation/report.md", help="where the report is written")
    ev.add_argument("--no-refute", action="store_true", help="skip step [3]")
    ev.add_argument("--context", action="store_true",
                    help="add the context pack (off by default, ADR-0009)")
    ev.add_argument("--refute-model", default=None,
                    help="harness only: the model for the refutation round (default: --model)")
    ev.add_argument("--max-usd", type=float, default=None, metavar="USD",
                    help="do not start a case that could cross this. Checked between cases and "
                         "never mid-case: what a case costs is known only once it is over, "
                         "since every finding pays for its own refuter")
    ev.add_argument("--confirm", action="store_true",
                    help="actually call the API and spend; without it, a dry run")
    ev.add_argument("--jobs", default=None, metavar="DIR",
                    help="workspace for the harness transport, one job directory per case")
    ev.add_argument("--export", action="store_true",
                    help="write a job per case for a harness to run, instead of calling the "
                         "API. Same selection, same scoring rule, same report — scaling the "
                         "case count then costs tokens rather than dollars")
    ev.add_argument("--ingest", action="store_true",
                    help="read the harness's replies for every case; run it twice, once for "
                         "the lenses and once for the refutations")
    ev.set_defaults(handler=_evaluate)

    for name, help_text in (("export", "write a job any harness can run"),
                            ("ingest", "read a harness's replies and advance one round")):
        sub_parser = sub.add_parser(name, help=help_text)
        sub_parser.add_argument("job", help="the job directory")
        sub_parser.add_argument("--path", action="append", default=None,
                                help="restrict to these paths; repeatable")
        sub_parser.add_argument("--out", default="review/queue.md",
                                help="where the final queue is written (ingest)")
        sub_parser.add_argument("--no-refute", action="store_true",
                                help="do not write a refutation round")
        if name == "export":
            sub_parser.add_argument("--base", default=None)
            sub_parser.add_argument("--head", default="HEAD")
            sub_parser.add_argument("--repo", default=None)
            sub_parser.add_argument("--spec", action="append", default=None)
            sub_parser.add_argument("--lens", action="append", default=None,
                                    choices=list(lenses.LENSES))
            sub_parser.add_argument("--no-conformance", action="store_true")
            sub_parser.add_argument("--model", default=job.LENS_MODEL,
                                    help="the lenses' model, recorded per task for the harness "
                                         "to honour (default: %(default)s, step 8)")
            sub_parser.add_argument("--refute-model", default=job.REFUTE_MODEL,
                                    help="the refuter's model (default: %(default)s)")
            sub_parser.add_argument("--context", action="store_true",
                                    help="add the context pack (off by default, ADR-0009)")
        sub_parser.set_defaults(handler=_export if name == "export" else _ingest)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
