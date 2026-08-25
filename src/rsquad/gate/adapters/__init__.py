"""Stack adapters. One per (language, test runner) pair.

Adding a stack means answering the seven questions — see `base.StackAdapter`. It does not mean
touching `core.py`; if it does, the line between portable and specific has moved and that is
worth a note in `docs/porting.md`.

**Question 6 is answered per file, not per run**, which is why it has its own registry. The
other six belong to the gate, which is told which stack it is running (`rsquad gate --adapter`)
because a test command is a property of the repository. The context pack is a property of the
file being read: one change can touch a `.py` and a `.java`, and the resolver that can follow an
import in one is a `SyntaxError` in the other.

That distinction was not free. Every Java review this squad has ever run — 190 lens tasks — was
handed the Python resolver, which parsed a `.java` file, raised `SyntaxError`, and returned an
empty pack. Nothing failed and nothing said so.
"""

from pathlib import Path

from .base import StackAdapter
from .java import JavaContext
from .python_pytest import PythonPytestAdapter

#: Question 6 by file extension. The value only ever has `resolve_context` called on it.
RESOLVERS = {".py": PythonPytestAdapter(), ".java": JavaContext()}


class ByLanguage:
    """Route each file to the resolver for its language, or to no resolver at all.

    An unknown extension resolves nothing, which is the same honest behaviour as a stack nobody
    has taught: a smaller pack, never a wrong one.
    """

    def resolve_context(self, path, source, ranges, revision, repo, tracked):
        resolver = RESOLVERS.get(Path(path).suffix)
        if resolver is None:
            return []
        return resolver.resolve_context(path, source, ranges, revision, repo, tracked)


#: The one instance. `chunking` calls `resolve_context` and nothing else, so this is all a
#: caller needs to hand it.
by_language = ByLanguage()

__all__ = ["ByLanguage", "JavaContext", "PythonPytestAdapter", "RESOLVERS", "StackAdapter",
           "by_language"]
