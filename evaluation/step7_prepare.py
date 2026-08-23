"""Build the synthetic bug-introducing commits for step 7, and the defect set that replays them.

A review squad reads a diff, so the defect has to be in the diff. The commits selected in
`step7.yaml` are **fixes** — the bug is gone. Rather than hunt the commit that introduced each
one (archaeology, and `git log -S` finds when a LINE appeared, not when a DEFECT did), this
applies each fix backwards to its source file only:

    git checkout -b step7/<id> <fix>
    git revert --no-commit <fix>            # everything
    git checkout <fix> -- <test paths>      # ... except the tests
    git commit --allow-empty-message -m ""

The result is a real commit whose diff introduces a known bug, on top of real history, with the
pre-fix file at head. The tests are left as the fix wrote them, so they fail on that commit —
irrelevant here, since the lenses never run tests, but it means the GATE cannot be run on these
commits and no conclusion about step [0] may be drawn from them.

**The empty message is deliberate.** Nobody stated an intent for a change nobody wrote, and
inventing one would hand the conformance lens a contradiction that does not exist in the world.
`conformance.gather` yields no parts on an empty message, so `evaluate` skips step [1] by itself.

Usage:

    python evaluation/step7_prepare.py <workspace>
    python -m rsquad evaluate --defects <workspace>/commons-lang.defects.yaml \\
        --repo <workspace>/commons-lang --max-usd 7 --out evaluation/step7-lang.md --confirm
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
SINCE = "2026-04-01"


def run(args: list[str], cwd: Path | None = None, check: bool = True):
    # `core.longpaths` is not optional on Windows. jackson-databind has test files whose paths
    # exceed 260 characters once a workspace path is prepended, and checking one branch out
    # fails with "Filename too long" halfway through — after two cases have already been built.
    if args[0] == "git":
        args = [args[0], "-c", "core.longpaths=true"] + args[1:]
    done = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if check and done.returncode != 0:
        raise SystemExit("%s\n%s%s" % (" ".join(args), done.stdout, done.stderr))
    return done


def clone(url: str, into: Path) -> None:
    if into.exists():
        return
    print("cloning %s" % url, flush=True)
    run(["git", "clone", "--quiet", "--shallow-since=" + SINCE, "--single-branch", url,
         str(into)])


def synthesize(repo: Path, case: dict) -> str:
    """One commit whose diff reintroduces this case's defect. Returns its sha."""
    branch = "step7/%s" % case["id"]
    run(["git", "checkout", "--quiet", "-B", branch, case["fix"]], repo)
    run(["git", "revert", "--no-commit", "--no-edit", case["fix"]], repo)

    tests = [name for name in
             run(["git", "show", "--name-only", "--format=", case["fix"]], repo).stdout.split()
             if "/test/" in name or "/it/" in name]
    if tests:
        # Restore the fix's tests: only the SOURCE is reverted, so the diff under review is a
        # change to production code and nothing else.
        run(["git", "checkout", case["fix"], "--"] + tests, repo)

    run(["git", "commit", "--quiet", "--allow-empty-message", "-m", ""], repo)
    return run(["git", "rev-parse", "HEAD"], repo).stdout.strip()


def main(workspace: Path) -> int:
    frozen = yaml.safe_load((HERE / "step7.yaml").read_text(encoding="utf-8"))
    workspace.mkdir(parents=True, exist_ok=True)

    for arm in frozen["arms"]:
        name = arm["repo"].split("/")[1]
        repo = workspace / name
        clone(arm["url"], repo)

        defects = []
        for case in [c for c in frozen["cases"] if c["repo"] == arm["repo"]]:
            sha = synthesize(repo, case)
            print("  %-34s %s <- reverse of %s" % (case["id"], sha[:9], case["fix"]), flush=True)
            defects.append({
                "id": case["id"],
                "summary": case["summary"],
                "repo": arm["repo"],
                "introduced_in": sha,
                "fixed_in": case["fix"],
                "file": case["file"],
                "replayable": True,
                "self_found": False,
                "detectable_from_diff": case["detectable_from_diff"],
                "found_by": "issue %s, reported by a user" % case["issue"],
                "note": case["label_rationale"],
            })

        out = workspace / ("%s.defects.yaml" % name)
        out.write_text(yaml.safe_dump({"schema_version": 1, "defects": defects},
                                      allow_unicode=True, sort_keys=False), encoding="utf-8")
        print("  -> %s\n" % out, flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(main(Path(sys.argv[1]).resolve()))
