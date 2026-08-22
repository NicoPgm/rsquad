"""The stack adapter protocol — four questions, and nothing else.

This is the line between what ports and what does not. The gate's core (worktree, merge base,
JUnit parsing, verdicts, reporting) knows no language. Everything a stack changes fits into the
four methods below.

    1. Which files in the diff are tests?
    2. Which test functions are new or modified? (by comparing bodies across revisions)
    3. How do we run that subset so it emits JUnit XML?
    4. **How do we guarantee the code under test is the base's?**

Question 4 is the trap, and it is different in every ecosystem. On Python it is the editable
install resolving back to the main checkout's `src/`. Expect the equivalent — and expect to find
it by running the thing, not by reading it. Every defect in the original implementation of this
gate was found by executing it; none by review.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

from ..core import EXEMPT_MARKERS, git


class StackAdapter(ABC):
    """One implementation per (language, test runner) pair."""

    name: str = "abstract"

    #: Default paths handed to `git diff -- <patterns>`.
    watched_paths: tuple[str, ...] = ("tests/",)

    # ------------------------------------------------------------------ question 1
    @abstractmethod
    def is_test_file(self, path: str) -> bool:
        """Does this path from the diff hold tests this adapter can run?"""

    # ------------------------------------------------------------------ question 2
    @abstractmethod
    def changed_test_functions(self, files: list[str], base: str, head: str,
                               repo: Path | None = None) -> set[str]:
        """The test functions that are **new or modified**, by comparing function bodies.

        File-level granularity is not merely coarse, it is fatal: on a touched file every
        pre-existing test gets examined and reported "suspect" because it passes on the base —
        which is its job. Measured on a real commit: 35 false positives against 6 genuine
        findings. A gate in that state is switched off within a week, and takes the real
        findings with it.
        """

    # ------------------------------------------------------------------ question 3
    @abstractmethod
    def test_command(self, files: list[str], report_path: Path) -> list[str]:
        """The command that runs exactly `files` and writes JUnit XML to `report_path`.

        It must not abort the whole run on a collection error: on the base, a brand-new test
        file is *always* uncollectable — it imports symbols that do not exist yet.
        """

    # ------------------------------------------------------------------ question 4
    @abstractmethod
    def base_environment(self, tree: Path) -> dict[str, str]:
        """The environment that forces the code under test to be the worktree's, not the
        developer's checkout.

        Get this wrong and the gate validates everything while looking green.
        """

    # ------------------------------------------------------------------ shared
    def exempt_names(self, sources: dict[str, str]) -> set[str]:
        """Test functions carrying an exemption marker.

        `sources` maps path to file text **at the revision under test** — not the working tree.
        Reading the working tree instead is correct only when head happens to be checked out,
        and silently wrong on every replay of a past commit.

        The default implementation covers any language where a marker sits on the line(s)
        directly above the test declaration. Override where that is not true.
        """
        exempt: set[str] = set()
        marked = False
        for text in sources.values():
            for line in text.splitlines():
                bare = line.strip()
                if any(m in bare for m in EXEMPT_MARKERS) and self.is_marker_line(bare):
                    marked = True
                elif self.is_test_declaration(bare):
                    if marked:
                        exempt.add(self.declared_name(bare))
                    marked = False
        return exempt

    def is_marker_line(self, line: str) -> bool:
        return line.startswith("@")

    def is_test_declaration(self, line: str) -> bool:
        return line.startswith("def test")

    def declared_name(self, line: str) -> str:
        return line[4:].split("(", 1)[0].strip()

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def file_at(revision: str, path: str, repo: Path | None = None) -> str | None:
        """The contents of `path` at `revision`, or None if it did not exist there."""
        shown = git(["show", "%s:%s" % (revision, path)], repo)
        return shown.stdout if shown.returncode == 0 else None

    @staticmethod
    def inherited_environment() -> dict[str, str]:
        return dict(os.environ)
