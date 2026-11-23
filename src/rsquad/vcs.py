"""Shell and git helpers, shared by every step.

They started inside the gate, which was the wrong home: the gate is a step, not a utility, and
the lenses need the same two calls.
"""

from __future__ import annotations

import shutil
import subprocess
import tarfile
import tempfile
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


def _keep(member: tarfile.TarInfo, dest: str) -> tarfile.TarInfo | None:
    """The `data` filter, except that a member it refuses is left out instead of fatal.

    A link to an absolute path or out of the tree must not land in the copy, where a reader
    could follow it out; it must not stop the review either, for one link in a whole tree.
    """
    try:
        return tarfile.data_filter(member, dest)
    except tarfile.FilterError:
        return None


def snapshot(revision: str, dest: Path, repo: Path | None = None) -> None:
    """The tree at `revision`, written to `dest`: the repository a reader may search.

    An archive, not a worktree. It leaves nothing to clean up in the reviewed repository, and it
    carries no `.git`: no history, and no commit message, which is the conformance lens's intent
    and nothing a blind lens should find lying beside the code. `dest` is emptied first, so a
    second export into the same job holds no file of the first one. The archive is streamed,
    never held whole in memory. Paths marked `export-ignore` are left out, as `git archive`
    does for any export.
    """
    shutil.rmtree(dest, ignore_errors=True)
    # Both of git's outputs must keep flowing. stderr goes to a file: a partial clone fetching
    # blobs writes there, and a pipe nobody reads fills and stalls git. stdout is drained after
    # tarfile stops at the end-of-archive marker, for the same reason. Either stall hung the
    # export of a 69-file pull request on ReviewBench, once every file was already written.
    with tempfile.TemporaryFile() as errors, subprocess.Popen(
            ["git", "archive", "--format=tar", revision], cwd=repo,
            stdout=subprocess.PIPE, stderr=errors) as archive:
        unreadable = None
        try:
            with tarfile.open(fileobj=archive.stdout, mode="r|") as tar:
                tar.extractall(dest, filter=_keep)
        except tarfile.ReadError as error:
            unreadable = error                  # no archive at all: git's status says why
        archive.stdout.read()
        if archive.wait() != 0:
            errors.seek(0)
            raise SystemExit("cannot snapshot %s: %s"
                             % (revision, errors.read().decode("utf-8", "replace").strip()))
        if unreadable is not None:
            raise unreadable
