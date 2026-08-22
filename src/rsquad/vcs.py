"""Shell and git helpers, shared by every step.

They started inside the gate, which was the wrong home: the gate is a step, not a utility, and
the lenses need the same two calls.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def run(command: list[str], cwd: Path | None = None,
        env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def git(args: list[str], repo: Path | None = None) -> subprocess.CompletedProcess:
    return run(["git", *args], cwd=repo)


def resolve(revision: str, repo: Path | None = None) -> str:
    """The SHA for `revision`, or exit with a clear message.

    **Check the return code, never the output.** `git rev-parse nonsense` exits 128, writes its
    complaint to stderr — and echoes the argument back on *stdout*. So the obvious guard,
    `if not out.strip(): raise`, never fires: the caller sails on with the literal string
    "nonsense" as a revision, every later git call quietly finds nothing, and the tool reports
    a clean run on a revision that does not exist.

    Verified against git on 2026-08-22 after a lens claimed it; reported as a finding on the
    source project's copy of the same pattern, and true of this one at the time.
    """
    resolved = git(["rev-parse", revision], repo)
    if resolved.returncode != 0:
        raise SystemExit("unknown revision: %s" % revision)
    return resolved.stdout.strip()


def file_at(revision: str, path: str, repo: Path | None = None) -> str | None:
    """Contents of `path` at `revision`, or None if it is not there."""
    shown = git(["show", "%s:%s" % (revision, path)], repo)
    return shown.stdout if shown.returncode == 0 else None


def tracked_files(revision: str, repo: Path | None = None) -> list[str]:
    """Every file the repository tracks at `revision`.

    Read from the revision, not from disk: the working tree may hold untracked scratch files,
    and a resolver that saw them would produce a context pack that cannot be reproduced.
    """
    listed = git(["ls-tree", "-r", "--name-only", revision], repo)
    return [line.strip() for line in listed.stdout.splitlines() if line.strip()]
