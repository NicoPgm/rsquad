"""Cutting a change into review units.

**One unit is one file.** A lens sees the diff for that file and the file as it now stands, and
nothing else. That is a real limit, stated here rather than discovered later: a defect that only
exists in the interaction between two changed files is invisible to this squad. Widening the
unit to the whole change would trade that for a worse problem — attention spread thin over a
payload where most of the text is irrelevant to any given finding.

**The file is presented with line numbers.** Without them the model guesses, `line` lands a few
lines off, and the anchoring guard discards a true finding for a reason that has nothing to do
with truthfulness. Numbering makes the location producible, and therefore checkable.

**Long files are windowed around the hunks, and the elision is announced.** Silently cutting
text would let a lens conclude "nothing releases this handle" from a file where the release was
simply not shown. The marker is the same reflex as the `[...]` seam in the source project's
caption stripping: an unmarked cut invents a statement nobody made.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .context import Definition, cap, render as render_context
from .vcs import file_at, git, tracked_files

#: Above this many lines, a file is windowed around its hunks rather than shown whole.
MAX_LINES = 1200

#: Lines of untouched context kept on each side of a hunk when windowing.
CONTEXT = 40

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.M)

ELISION_NOTICE = (
    "**This file is long, so only the regions around the change are shown.** Gaps are marked "
    "`... N lines not shown ...`. Do not conclude that something is absent from the file "
    "because it is absent from what you were given.\n\n"
)


@dataclass
class Unit:
    """One file's worth of review material."""

    file: str
    diff: str
    source: str                 # the file at head, verbatim — what anchoring checks against
    numbered: str               # the same, with line numbers, possibly windowed
    elided: bool = False
    context: list[Definition] = field(default_factory=list)

    @property
    def elision(self) -> str:
        return ELISION_NOTICE if self.elided else ""

    @property
    def context_block(self) -> str:
        return render_context(self.context)


def changed_paths(base: str, head: str, repo: Path | None = None,
                  paths: list[str] | None = None) -> list[str]:
    diff = git(["diff", "--name-only", "%s...%s" % (base, head), "--", *(paths or [])], repo)
    return [line.strip() for line in diff.stdout.splitlines() if line.strip()]


def hunk_ranges(diff: str) -> list[tuple[int, int]]:
    """(first, last) line ranges in the *new* file, one per hunk, 1-indexed inclusive."""
    ranges = []
    for match in _HUNK.finditer(diff):
        start = int(match.group(1))
        length = int(match.group(2) or 1)
        ranges.append((start, start + max(length, 1) - 1))
    return ranges


def _merge(windows: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for first, last in sorted(windows):
        if merged and first <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], last))
        else:
            merged.append((first, last))
    return merged


def number(source: str, ranges: list[tuple[int, int]] | None = None,
           max_lines: int = MAX_LINES, context: int = CONTEXT) -> tuple[str, bool]:
    """Render `source` with line numbers. Returns (text, whether anything was elided)."""
    lines = source.splitlines()
    if len(lines) <= max_lines or not ranges:
        return "\n".join("%d\t%s" % (n, line) for n, line in enumerate(lines, 1)), False

    windows = _merge([(max(1, first - context), min(len(lines), last + context))
                      for first, last in ranges])
    out: list[str] = []
    cursor = 1
    for first, last in windows:
        if first > cursor:
            out.append("... %d lines not shown ..." % (first - cursor))
        out += ["%d\t%s" % (n, lines[n - 1]) for n in range(first, last + 1)]
        cursor = last + 1
    if cursor <= len(lines):
        out.append("... %d lines not shown ..." % (len(lines) - cursor + 1))
    return "\n".join(out), True


def unit(path: str, base: str, head: str, repo: Path | None = None,
         adapter=None, tracked: list[str] | None = None) -> Unit | None:
    """One review unit, or None when there is nothing a lens could read.

    Deleted files and binaries are skipped rather than reported: there is no "file as it now
    stands" to quote from, so no finding about them could ever anchor.
    """
    source = file_at(head, path, repo)
    if source is None or "\x00" in source:
        return None
    diff = git(["diff", "%s...%s" % (base, head), "--", path], repo).stdout
    if not diff.strip():
        return None
    ranges = hunk_ranges(diff)
    numbered, elided = number(source, ranges)
    context: list[Definition] = []
    if adapter is not None:
        context = cap(adapter.resolve_context(path, source, ranges, head, repo,
                                              tracked if tracked is not None
                                              else tracked_files(head, repo)))
    return Unit(file=path, diff=diff, source=source, numbered=numbered, elided=elided,
                context=context)


def units(base: str, head: str, repo: Path | None = None, paths: list[str] | None = None,
          adapter=None) -> list[Unit]:
    """Every reviewable file in the change.

    `tracked` is read once and shared: it is the same list for every unit, and asking git per
    file would be both slower and — if the revision moved underneath — inconsistent.
    """
    listing = tracked_files(head, repo) if adapter is not None else None
    found = [unit(path, base, head, repo, adapter, listing)
             for path in changed_paths(base, head, repo, paths)]
    return [u for u in found if u is not None]
