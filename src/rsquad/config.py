"""Run-time settings: the API credential, and nothing else for now.

The key is read from the environment first, and only then from a `.env` at the repository root.
That order matters: it means the credential can live in exactly one place on a machine — an
exported variable, or the sibling project's own `.env` sourced before the run — instead of being
copied into a second file. A secret duplicated is a secret with two places to leak from and two
places to forget when it rotates.

`.env` is never committed. Nothing in this module returns, logs, or formats the value.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: Point this at the `.env` you already keep elsewhere rather than copying the key here.
#: Reading the file directly also survives CRLF line endings, which sourcing it in a shell
#: would not — a trailing carriage return inside a credential fails as an authentication error
#: and looks nothing like a line-ending problem.
ENV_VAR = "RSQUAD_ENV_FILE"

ENV = Path(os.environ.get(ENV_VAR) or ROOT / ".env")

KEY = "ANTHROPIC_API_KEY"


def load(path: Path | None = None) -> list[str]:
    """Put any key from `.env` that is not already set into the environment.

    Returns the names it set — names only. An existing environment variable always wins, so a
    deliberate override on the command line is never silently replaced by a stale file.
    """
    path = path or Path(os.environ.get(ENV_VAR) or ROOT / ".env")
    if not path.exists():
        return []
    placed = []
    for line in path.read_text(encoding="utf-8").splitlines():
        bare = line.strip()
        if not bare or bare.startswith("#") or "=" not in bare:
            continue
        name, _, value = bare.partition("=")
        name, value = name.strip(), value.strip().strip('"').strip("'")
        if not name or not value or name in os.environ:
            continue
        os.environ[name] = value
        placed.append(name)
    return placed


def credential_available() -> bool:
    """Whether a key is reachable, without reading or returning it."""
    load()
    return bool(os.environ.get(KEY))
