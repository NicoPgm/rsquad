"""Java — **question 6 only**, and the file says so rather than implying otherwise.

The other six questions of the adapter protocol are the gate's, and the gate's Java half does
not exist: it needs a JDK, a Maven invocation that emits JUnit XML, and — question 4 — whatever
this ecosystem's version of "the code under test is the base's" turns out to be. That is a
measurement to run, not a file to write, so nothing here pretends to answer it. When it is
built, it should absorb this class rather than sit beside it.

**Why question 6 alone was worth building first.** Every Java case ever reviewed by this squad
— 165 tasks across two repositories — carried an empty context pack, because the resolver was
Python's and a `.java` file is a `SyntaxError` to it. So every published Java number is a
measurement of the squad *without* the pack. The pack is the sharpest limit named in those
reports; it can now be varied while everything else stays frozen.

**What a definition is here.** Not the whole type: a Java class is usually the whole file, and
pasting it in would spend the payload on a second file to review. What a caller needs is the
*shape* — what fields exist, what a method returns, what it takes, what is private — plus the
bodies short enough to be evidence. So a definition is the declaration, then every member, with
bodies over `MAX_BODY_LINES` collapsed to `{ ... }`. A one-line getter stays whole, because
"nothing ever populates this field" is exactly the kind of finding the pack exists to enable,
and it is unprovable from a signature.

The two constraints from `base.StackAdapter.resolve_context` bind here as everywhere:
deterministic (source order, no ranking), and symbol-driven (imports and the file's own package,
never a directory walk).
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import StackAdapter

#: A member body longer than this is replaced by `{ ... }`. Short bodies are kept because a
#: getter's body is evidence and its signature is not.
MAX_BODY_LINES = 8

_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)
_IMPORT = re.compile(r"^\s*import\s+(static\s+)?([\w.]+?)(\.\*)?\s*;", re.M)
_IDENT = re.compile(r"\b[A-Za-z_$][\w$]*\b")


def _clean(source: str) -> tuple[str, str]:
    """(stripped, masked) — comments blanked in both, string and char literals in `masked` too.

    Both keep the length and the line breaks of the original, so an offset means the same thing
    in all three. `masked` is what the scanners count braces in — a `"}"` inside a string would
    otherwise close a body that never opened. `stripped` is what gets quoted, so the literals
    survive where a reader can see them.
    """
    stripped, masked = list(source), list(source)
    i, n = 0, len(source)

    def blank(start: int, end: int, both: bool) -> None:
        for j in range(start, min(end, n)):
            if source[j] != "\n":
                masked[j] = " "
                if both:
                    stripped[j] = " "

    while i < n:
        two, three = source[i:i + 2], source[i:i + 3]
        if two == "//":
            end = source.find("\n", i)
            end = n if end < 0 else end
            blank(i, end, True)
            i = end if end > i else i + 1
        elif two == "/*":
            end = source.find("*/", i + 2)
            end = n if end < 0 else end + 2
            blank(i, end, True)
            i = end
        elif three == '"""':
            end = source.find('"""', i + 3)
            end = n if end < 0 else end + 3
            blank(i, end, False)
            i = end
        elif source[i] in "\"'":
            quote, j = source[i], i + 1
            while j < n and source[j] != quote and source[j] != "\n":
                j += 2 if source[j] == "\\" else 1
            blank(i, min(j + 1, n), False)
            i = min(j + 1, n)
        else:
            i += 1
    return "".join(stripped), "".join(masked)


def _package(masked: str) -> str:
    found = _PACKAGE.search(masked)
    return found.group(1) if found else ""


def _imports(masked: str) -> tuple[dict[str, str], list[str], dict[str, str]]:
    """(type name -> dotted type, wildcard packages, bound member -> dotted type).

    A static import binds a lowercase member name, so it is the one case where an identifier
    that does not look like a type still names one: `import static a.b.Grid.of;` means a bare
    `of(...)` in the changed lines is a reference to `Grid`.
    """
    types: dict[str, str] = {}
    packages: list[str] = []
    members: dict[str, str] = {}
    for static, dotted, star in _IMPORT.findall(masked):
        parts = dotted.split(".")
        if static:
            if star:                                   # import static a.b.Grid.*;
                types.setdefault(parts[-1], dotted)
            elif len(parts) >= 2:                      # import static a.b.Grid.of;
                members.setdefault(parts[-1], ".".join(parts[:-1]))
                types.setdefault(parts[-2], ".".join(parts[:-1]))
        elif star:
            packages.append(dotted)
        else:
            types.setdefault(parts[-1], dotted)
    return types, packages, members


def _referenced(masked: str, ranges: list[tuple[int, int]],
                imports: tuple[dict[str, str], list[str], dict[str, str]],
                package: str, path: str) -> list[tuple[str, list[str]]]:
    """(name as written, candidate paths) for every symbol the changed lines name.

    Candidates are ordered the way Java itself resolves them — explicit import, then the file's
    own package, then a wildcard — and the caller keeps the first one that is tracked.
    """
    types, packages, members = imports
    directory = path.replace("\\", "/").rsplit("/", 1)[0] if "/" in path else ""
    own = Path(path).stem
    lines = masked.splitlines()

    wanted: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    for first, last in ranges:
        for number in range(max(first, 1), min(last, len(lines)) + 1):
            for name in _IDENT.findall(lines[number - 1]):
                if name in seen or name == own:
                    continue
                if name in members:
                    seen.add(name)
                    wanted.append((name, ["%s.java" % members[name].replace(".", "/")]))
                    continue
                if not name[:1].isupper():
                    continue
                seen.add(name)
                candidates = []
                if name in types:
                    candidates.append("%s.java" % types[name].replace(".", "/"))
                if directory:
                    candidates.append("%s/%s.java" % (directory, name))
                elif package:
                    candidates.append("%s/%s.java" % (package.replace(".", "/"), name))
                candidates += ["%s/%s.java" % (p.replace(".", "/"), name) for p in packages]
                wanted.append((name, candidates))
    return wanted


def _tracked_file(candidates: list[str], tracked: list[str]) -> str | None:
    """The first candidate this repository actually tracks.

    Everything else — the JDK, every dependency — falls out here, for the same reason the
    Python resolver skips them: the model knows what `Optional.map` does, and does not know
    what the class next door does.
    """
    normalised = {p.replace("\\", "/"): p for p in tracked}
    for candidate in candidates:
        if candidate in normalised:
            return normalised[candidate]
        for clean, original in normalised.items():
            if clean.endswith("/" + candidate):
                return original
    return None


def _declaration(masked: str, name: str) -> int | None:
    """Offset of the `class`/`interface`/`enum`/`record` keyword declaring `name`."""
    found = re.search(r"\b(?:class|interface|enum|record)\s+%s\b" % re.escape(name), masked)
    return found.start() if found else None


def _matching(masked: str, opening: int) -> int:
    depth = 0
    for i in range(opening, len(masked)):
        if masked[i] == "{":
            depth += 1
        elif masked[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(masked) - 1


def _header_start(stripped: str, offset: int) -> int:
    """Back up from the keyword over any annotation lines above it.

    Line-based on purpose. Backing up to the previous `;` or `}` would be exact until an
    annotation carries an array argument — `@Target({TYPE})` — whose brace is indistinguishable
    from the end of the declaration before it. Losing an annotation line is a smaller error
    than emitting half of one.
    """
    start = stripped.rfind("\n", 0, offset) + 1
    while start > 0:
        above = stripped[stripped.rfind("\n", 0, start - 1) + 1:start - 1].strip()
        if not above.startswith("@"):
            break
        start = stripped.rfind("\n", 0, start - 1) + 1
    return start


def _members(stripped: str, masked: str, first: int, last: int) -> list[str]:
    """Every member declared directly inside a body, bodies over the bound collapsed."""
    out: list[str] = []
    i, start = first + 1, first + 1
    parens = 0
    while i < last:
        char = masked[i]
        if char == "(":
            parens += 1
        elif char == ")":
            parens = max(parens - 1, 0)
        elif char == ";" and parens == 0:
            out.append(stripped[start:i + 1])
            i, start = i + 1, i + 1
            continue
        elif char == "{" and parens == 0:
            close = _matching(masked, i)
            if "=" in masked[start:i].replace("==", "").replace("!=", ""):
                # An array initializer, not a body: `int[] limits = {1, 2};` — the declaration
                # continues past the closing brace, to the semicolon.
                i = close + 1
                continue
            body = stripped[i:close + 1]
            out.append(stripped[start:i] + (body if body.count("\n") <= MAX_BODY_LINES
                                            else "{ ... }"))
            i, start = close + 1, close + 1
            continue
        i += 1
    tail = stripped[start:last].strip()
    if tail:                       # enum constants with no trailing `;`
        out.append(tail)
    return out


def _tidy(text: str) -> list[str]:
    return [line.rstrip() for line in text.strip("\n").splitlines() if line.strip()]


def skeleton(source: str, name: str) -> tuple[int, str] | None:
    """(line, text) for the declaration of `name` in `source`, or None if it is not there."""
    stripped, masked = _clean(source)
    offset = _declaration(masked, name)
    if offset is None:
        return None
    opening = masked.find("{", offset)
    if opening < 0:
        return None
    start = _header_start(stripped, offset)
    closing = _matching(masked, opening)

    lines = _tidy(stripped[start:opening + 1])
    for member in _members(stripped, masked, opening, closing):
        lines += _tidy(member)
    lines.append("}")
    return stripped.count("\n", 0, start) + 1, "\n".join(lines)


class JavaContext:
    """Question 6 for Java. Not a `StackAdapter`: it answers one of the seven questions.

    Duck-typed against `chunking.unit`, which calls `resolve_context` and nothing else. Making
    it a `StackAdapter` subclass would mean four methods that raise, and a `rsquad gate
    --adapter java` offering a gate that does not exist.
    """

    name = "java"

    def resolve_context(self, path, source, ranges, revision, repo, tracked):
        from ...context import Definition, truncate

        _, masked = _clean(source)
        imports = _imports(masked)
        found, seen = [], set()
        for symbol, candidates in _referenced(masked, ranges, imports, _package(masked), path):
            target = _tracked_file(candidates, tracked)
            if target is None or target in seen:
                continue
            seen.add(target)
            text = StackAdapter.file_at(revision, target, repo)
            if text is None:
                continue
            # The file's own name, not the symbol as written: a static import names a member,
            # and `Grid.of` is declared by the type `Grid`.
            defined = skeleton(text, Path(target).stem)
            if defined is None:
                continue
            line, body = defined
            body, cut = truncate(body)
            found.append(Definition(symbol=Path(target).stem, file=target, line=line,
                                    source=body, truncated=cut))
        return sorted(found, key=lambda d: (d.file, d.line))
