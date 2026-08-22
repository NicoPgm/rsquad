"""Python + pytest.

Every comment below marks a defect that cost a real run to find. None of them was visible on
reading; each made the gate silently useless, which is the most expensive failure mode because
it produces a reassuring green.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from .base import StackAdapter


class PythonPytestAdapter(StackAdapter):

    name = "python-pytest"
    watched_paths = ("tests/",)

    # ------------------------------------------------------------------ question 1
    def is_test_file(self, path: str) -> bool:
        return path.endswith(".py")

    # ------------------------------------------------------------------ question 2
    def changed_test_functions(self, files: list[str], base: str, head: str,
                               repo: Path | None = None) -> set[str]:
        touched: set[str] = set()
        for name in files:
            before = self.file_at(base, name, repo)
            after = self.file_at(head, name, repo)
            old = self._functions(before) if before is not None else {}
            new = self._functions(after) if after is not None else {}
            touched |= {n for n, body in new.items() if old.get(n) != body}
        return touched

    @staticmethod
    def _functions(source: str) -> dict[str, str]:
        """Every `test*` function in `source`, keyed by name, valued by its source text.

        Comparing source text rather than an AST dump keeps decorators in scope: loosening a
        `@pytest.mark.parametrize` case changes the test without changing its body.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {}
        lines = source.splitlines()
        found: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name.startswith("test"):
                start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
                found[node.name] = "\n".join(lines[start:node.end_lineno])
        return found

    # ------------------------------------------------------------------ question 3
    def test_command(self, files: list[str], report_path: Path) -> list[str]:
        # **`--continue-on-collection-errors` is not a convenience.** By default a single
        # collection error aborts the entire session: pytest runs nothing and reports only the
        # error. On the base, a new test file is *always* uncollectable — it imports symbols
        # that do not exist yet. Without this flag the gate falls silent the moment a change
        # adds a test file, which is precisely when it would earn its keep.
        return [sys.executable, "-m", "pytest", *files, "-p", "no:cacheprovider",
                "--continue-on-collection-errors", "--junitxml", str(report_path), "-q"]

    # ------------------------------------------------------------------ question 4
    def base_environment(self, tree: Path) -> dict[str, str]:
        # **`PYTHONPATH` on the base's sources, and it has to win.** The package is installed
        # in editable mode and points at the main checkout's `src/`: without this variable
        # pytest imports the NEW code from the worktree and the gate validates everything.
        # Measured 2026-08-20 — 22 tests green while running against the code from after.
        env = self.inherited_environment()
        env["PYTHONPATH"] = str(tree / "src")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return env
