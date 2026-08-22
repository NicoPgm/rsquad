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
from pathlib import Path

from . import budget, chunking, config, lenses, ranking, refutation
from .gate import ADAPTERS, DEFAULT_ADAPTER, check, git, merge_base, report
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


def _review(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve() if args.repo else None
    head = resolve(args.head, repo)
    base = merge_base(args.base or "%s~1" % head, head, repo)
    units = chunking.units(base, head, repo, args.path,
                           adapter=ADAPTERS[DEFAULT_ADAPTER])
    chosen = args.lens or list(lenses.LENSES)

    if not units:
        print("nothing readable changed between %s and %s." % (base[:12], head[:12]))
        return 0

    print("%s <- %s | %d file(s), %d lens(es) = %d call(s)"
          % (head[:12], base[:12], len(units), len(chosen), len(units) * len(chosen)))
    for unit in units:
        print("  %-52s %6d chars%s" % (unit.file, len(unit.numbered),
                                       "  (elided)" if unit.elided else ""))

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

    errors: list[str] = []

    def progress(run):
        # `flush=True` is not cosmetic here. Piped or redirected, Python buffers stdout, so a
        # command that spends money for minutes looks hung until it is finished — and the one
        # moment you want to see it is while it is still cancellable.
        print("  %-10s %-40s %s" % (run.lens, run.file[-40:],
                                    run.error or "%d finding(s)" % len(run.findings)),
              flush=True)

    runs = lenses.review(units, chosen, args.model, on_run=progress)
    findings, dropped = [], []
    for run in runs:
        findings += run.findings
        dropped += run.dropped
        if run.error:
            errors.append("%s on %s: %s" % (run.lens, run.file, run.error))

    verdicts = []
    if not args.no_refute and findings:
        print("\n%d finding(s) to refute" % len(findings), flush=True)

        def told(verdict):
            print("  %-46s %s" % ("%s:%s" % (verdict.finding["file"][-30:],
                                             verdict.finding["line"]),
                                  verdict.error or verdict.verdict), flush=True)

        verdicts = refutation.refute_all(findings, {u.file: u for u in units}, args.model,
                                         on_verdict=told)
        findings, killed = refutation.survivors(verdicts)
    else:
        killed = []

    usages = [r.usage for r in runs] + [v.usage for v in verdicts]
    spend = budget.total(args.model, usages)
    footer = ("Model `%s`, %d lens call(s) + %d refutation(s), %.4f USD billed. %s"
              % (args.model, len(runs), len(verdicts), spend.total,
                 budget.cache_verdict(usages)))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(ranking.render(ranking.group(findings), dropped, errors, footer,
                                  refuted=killed if not args.no_refute else None),
                   encoding="utf-8")
    print("\n%s" % footer)
    print("%d survived refutation, %d refuted, %d dropped by the guards, %d lens failure(s)"
          " -> %s" % (len(findings), len(killed), len(dropped), len(errors), out))
    # Always 0. Only the gate blocks; opinions comment.
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
    review.add_argument("--no-refute", action="store_true",
                        help="skip step [3]. Cheaper, and the queue becomes a list of "
                             "suspicions nobody contested")
    review.add_argument("--confirm", action="store_true",
                        help="actually call the API and spend; without it, a dry run")
    review.set_defaults(handler=_review)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
