"""Stack adapters. One per (language, test runner) pair.

Adding a stack means answering four questions — see `base.StackAdapter`. It does not mean
touching `core.py`; if it does, the line between portable and specific has moved and that is
worth a note in `docs/porting.md`.
"""

from .base import StackAdapter
from .python_pytest import PythonPytestAdapter

__all__ = ["StackAdapter", "PythonPytestAdapter"]
