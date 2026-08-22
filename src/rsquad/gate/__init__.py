"""Step [0] — the mechanical gate. No agent, no model, no judgement.

It runs first and it does not negotiate: having a model comment on code that does not compile
produces confident noise. It is also the only step allowed to block.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..vcs import resolve
from .adapters.base import StackAdapter
from .adapters.python_pytest import PythonPytestAdapter
from .core import (EXEMPT_MARKERS, NO_SIGNAL, SUSPECT, VALID, RunnerFailed, Summary, Verdict,
                   changed_files, cleanup, git, merge_base, parse_junit, report,
                   run_against_base, summarize)

ADAPTERS = {a.name: a for a in (PythonPytestAdapter(),)}
DEFAULT_ADAPTER = "python-pytest"


@dataclass
class Outcome:
    """What one gate run learned. `summary` is None when there was nothing to check."""
    head: str
    base: str
    files: list[str]
    changed_functions: set[str]
    verdicts: list[Verdict]
    summary: Summary | None

    @property
    def has_signal(self) -> bool:
        return self.summary is not None and self.summary.examined > 0


def check(base: str | None = None, head: str = "HEAD", repo: Path | None = None,
          adapter: StackAdapter | None = None, patterns: list[str] | None = None) -> Outcome:
    """Run the gate for one revision and return what it found.

    `head` is honoured throughout. The original implementation of this gate resolved `head`,
    used it to pick the base and the file list, then **overwrote it with `HEAD`** before
    extracting test functions and populating the worktree. Replaying a past commit therefore
    graded that commit's parent against *today's* tests. Measured across the 20 commits behind
    ai-video-digest@6ade3ff: 149 retained functions instead of 129, 5 of 14 commits affected.
    The published "47 % examined / 8 % suspect" came from that path and is not a usable
    baseline.
    """
    adapter = adapter or ADAPTERS[DEFAULT_ADAPTER]
    head_sha = resolve(head, repo)
    base_sha = merge_base(base or "%s~1" % head_sha, head_sha, repo)
    watched = patterns or list(adapter.watched_paths)
    files = [p for p in changed_files(base_sha, head_sha, watched, repo)
             if adapter.is_test_file(p)]
    if not files:
        return Outcome(head_sha, base_sha, [], set(), [], None)

    changed = adapter.changed_test_functions(files, base_sha, head_sha, repo)

    # Exemption markers are read at `head_sha`, never from the working tree — see
    # `StackAdapter.exempt_names`.
    sources = {p: text for p in files
               if (text := adapter.file_at(head_sha, p, repo)) is not None}

    report_path = run_against_base(base_sha, head_sha, files, adapter, repo)
    try:
        verdicts = parse_junit(report_path, adapter.exempt_names(sources), changed,
                               missing_symbol=adapter.signals_missing_symbol)
    finally:
        cleanup(report_path, repo)

    return Outcome(head_sha, base_sha, files, changed, verdicts,
                   summarize(verdicts) if verdicts else None)


__all__ = ["ADAPTERS", "DEFAULT_ADAPTER", "EXEMPT_MARKERS", "NO_SIGNAL", "SUSPECT", "VALID",
           "Outcome", "RunnerFailed", "StackAdapter", "Summary", "Verdict", "check", "report",
           "summarize"]
