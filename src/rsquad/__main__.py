"""RSquad command line.

    rsquad gate                                  # HEAD against its parent
    rsquad gate --base master --strict           # against the merge base with master
    rsquad gate --head 4164d03                   # replay the gate on a past commit
    rsquad gate --replay 20 --repo ../other      # aggregate over the last 20 commits
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .gate import ADAPTERS, DEFAULT_ADAPTER, check, git, report


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

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
