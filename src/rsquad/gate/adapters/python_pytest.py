"""Python + pytest.

Every comment below marks a defect that cost a real run to find. None of them was visible on
reading; each made the gate silently useless, which is the most expensive failure mode because
it produces a reassuring green.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

from .base import StackAdapter

# Verified against real `pytest --junitxml` output on 2026-08-22, one probe per shape. The
# `message` attribute carries the exception repr, and the shapes separate cleanly:
#
#   AttributeError: module 'os' has no attribute 'nope'      <- symbol not there yet
#   NameError: name 'nope' is not defined                    <- symbol not there yet
#   ImportError: cannot import name 'nope' from 'os'         <- symbol not there yet
#   assert 4 == 5                                            <- a real assertion
#   AttributeError: 'NoneType' object has no attribute 'x'   <- a REAL defect, caught
#
# The last row is why this is a narrow allowlist of shapes and not "any AttributeError". A test
# that trips over a None is a test doing its job, and discarding it would be the false negative
# this whole mechanism has to avoid.
_MISSING_SYMBOL = re.compile(
    r"""^\s*(?:
          ModuleNotFoundError:
        | ImportError:
        | NameError:\s*name\s+'[^']+'\s+is\s+not\s+defined
        | AttributeError:\s*module\s+'[^']+'\s+has\s+no\s+attribute\s+'[^']+'
    )""",
    re.VERBOSE,
)


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

    # ------------------------------------------------------------------ question 5
    def signals_missing_symbol(self, message: str) -> bool:
        return bool(_MISSING_SYMBOL.match(message))

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

    # ------------------------------------------------------------------ question 6
    def resolve_context(self, path, source, ranges, revision, repo, tracked):
        """Follow the first-party symbols the changed lines name, and nothing else.

        First-party means: the module resolves to a file this repository tracks. Standard
        library and third-party imports are deliberately skipped — a model already knows what
        `os.path.join` does, and pasting it in would spend payload to teach it nothing. What it
        cannot know is the function next door that this change just started calling.
        """
        from ...context import Definition, truncate

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        bindings = self._import_bindings(tree, path)
        wanted = self._referenced(tree, ranges, bindings)

        found, seen = [], set()
        for symbol, module, name in wanted:
            path = self._module_file(module, tracked)
            if path is None or (path, name) in seen:
                continue
            seen.add((path, name))
            text = self.file_at(revision, path, repo)
            if text is None:
                continue
            defined = self._top_level(text).get(name)
            if defined is None:
                continue
            line, body = defined
            body, cut = truncate(body)
            found.append(Definition(symbol=symbol, file=path, line=line, source=body,
                                    truncated=cut))
        return sorted(found, key=lambda d: (d.file, d.line))

    @classmethod
    def _import_bindings(cls, tree, path: str) -> dict[str, tuple[str, str | None]]:
        """local name -> (module, symbol). `symbol` is None when the module itself is bound.

        Relative imports are resolved against the file's own package, because `from . import
        prompts` is how a package actually refers to itself — skipping them would leave the
        resolver blind to exactly the neighbours a change is most likely to have just started
        calling.
        """
        bindings: dict[str, tuple[str, str | None]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = cls._absolute(node.module, node.level, path)
                if module is None:
                    continue
                for alias in node.names:
                    # `from . import prompts` binds a MODULE, not a symbol of one.
                    if node.level and not node.module:
                        bindings[alias.asname or alias.name] = (
                            "%s.%s" % (module, alias.name), None)
                    else:
                        bindings[alias.asname or alias.name] = (module, alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    bindings[alias.asname or alias.name.split(".")[0]] = (alias.name, None)
        return bindings

    @staticmethod
    def _absolute(module: str | None, level: int, path: str) -> str | None:
        """Turn a possibly-relative import into a dotted path rooted at the repository."""
        if not level:
            return module
        parts = path.replace("\\", "/").split("/")[:-1]        # the file's own directory
        if level > 1:
            parts = parts[:-(level - 1)]
        if not parts:
            return None
        return ".".join(parts + ([module] if module else []))

    @staticmethod
    def _referenced(tree, ranges, bindings) -> list[tuple[str, str, str]]:
        """(as written, module, symbol) for every binding named inside the changed ranges."""
        def inside(node) -> bool:
            line = getattr(node, "lineno", None)
            return line is not None and any(a <= line <= b for a, b in ranges)

        wanted: list[tuple[str, str, str]] = []
        for node in ast.walk(tree):
            if not inside(node):
                continue
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                bound = bindings.get(node.value.id)
                if bound and bound[1] is None:
                    wanted.append(("%s.%s" % (node.value.id, node.attr), bound[0], node.attr))
            elif isinstance(node, ast.Name):
                bound = bindings.get(node.id)
                if bound and bound[1] is not None:
                    wanted.append((node.id, bound[0], bound[1]))
        return wanted

    @staticmethod
    def _module_file(module: str, tracked: list[str]) -> str | None:
        """The tracked file for a dotted module, or None when it is not ours to read."""
        parts = module.split(".")
        endings = ("/".join(parts) + ".py", "/".join(parts + ["__init__.py"]))
        for path in tracked:
            normalised = path.replace("\\", "/")
            for ending in endings:
                if normalised == ending or normalised.endswith("/" + ending):
                    return path
        return None

    @staticmethod
    def _top_level(source: str) -> dict[str, tuple[int, str]]:
        """Top-level definitions by name: functions, classes, and simple assignments."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {}
        lines = source.splitlines()
        found: dict[str, tuple[int, str]] = {}

        def segment(node, first_line: int) -> str:
            return "\n".join(lines[first_line - 1:node.end_lineno])

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                first = min([node.lineno] + [d.lineno for d in node.decorator_list])
                found[node.name] = (first, segment(node, first))
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        found[target.id] = (node.lineno, segment(node, node.lineno))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                found[node.target.id] = (node.lineno, segment(node, node.lineno))
        return found
