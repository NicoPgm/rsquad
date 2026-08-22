"""The mechanical gate: a new test MUST FAIL against the code as it was.

A test that passes both before and after a change does not test that change. Coverage does not
see it — it rises either way — and neither does a green suite. This is the only test-quality
check that needs no judgement, and therefore no model.

The full rule has two halves, and keeping only one lets broken tests through:

    a valid test FAILS on the base  AND  PASSES on head

The second half is free: the suite already runs on head.

Three verdicts, and the distinction carries the whole tool:

    assertion failure on the base  -> the test discriminates        VALID
    passes on the base             -> it does not test the change   SUSPECT
    collection or setup error      -> the module does not exist yet NO_SIGNAL

The third case is the most common one on new code, and counting it as a success would validate,
in bulk, tests we know nothing about. `--junitxml` gives the distinction natively: `<failure>`
for an assertion, `<error>` for a crash. Nothing to guess.

**What this gate does NOT check:** that a test covers something anyone needs. A test can
discriminate perfectly and prove a property nobody cares about. It measures falsifiability,
not relevance.

Nothing in this module knows about any language. Everything stack-specific goes through a
`StackAdapter` — see `adapters/base.py`.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

# A characterization test MUST pass on the base: it exists to prove a refactor changes nothing.
# A guard test asserts that something does NOT happen; the base does not do it either, so it
# cannot fail there by construction. Both need the exemption, and the exemption must stay
# visible in review — hence a marker in the code rather than a list in a config file.
EXEMPT_MARKERS = ("characterization", "guard")

VALID, SUSPECT, NO_SIGNAL = "valid", "suspect", "no-signal"


@dataclass
class Verdict:
    identifier: str
    state: str
    detail: str = ""


def run(command: list[str], cwd: Path | None = None,
        env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def git(args: list[str], repo: Path | None = None) -> subprocess.CompletedProcess:
    return run(["git", *args], cwd=repo)


def merge_base(reference: str, head: str = "HEAD", repo: Path | None = None) -> str:
    """The **merge base**, not "head minus the diff".

    If the branch has diverged the two do not denote the same code, and comparing against
    anything other than the common ancestor means testing against a state that never existed.
    """
    merged = git(["merge-base", head, reference], repo)
    if merged.returncode == 0 and merged.stdout.strip():
        return merged.stdout.strip()
    resolved = git(["rev-parse", reference], repo)
    if resolved.returncode != 0:
        raise SystemExit("unknown revision: %s" % reference)
    return resolved.stdout.strip()


def changed_files(base: str, head: str, patterns: list[str],
                  repo: Path | None = None) -> list[str]:
    """Paths touched between base and head, restricted to the watched directories.

    Filtering by extension is the adapter's job (question 1) — this only asks git.
    """
    diff = git(["diff", "--name-only", "%s...%s" % (base, head), "--", *patterns], repo)
    return [line.strip() for line in diff.stdout.splitlines() if line.strip()]


def parse_junit(path: Path, exempt: set[str], retained: set[str]) -> list[Verdict]:
    """Classify every test case from the JUnit report produced against the base."""
    if not path.exists():
        return []
    verdicts = []
    for case in ET.parse(path).getroot().iter("testcase"):
        identifier = "%s::%s" % (case.get("classname", ""), case.get("name", ""))
        name = case.get("name", "")
        # JUnit emits `test_x[param]`; we key on the function, not the parametrization.
        function = name.split("[", 1)[0]
        # A collection error carries no `classname`: it covers the whole module. Filtering it
        # like an ordinary test would hide the fact that N new tests could not be examined at
        # all — the gate's most misleading silence.
        collection_error = case.find("error") is not None and not case.get("classname")
        if retained and function not in retained and not collection_error:
            continue
        if case.find("error") is not None:
            verdicts.append(Verdict(identifier, NO_SIGNAL,
                                    "collection or setup error on the base"))
        elif case.find("failure") is not None:
            verdicts.append(Verdict(identifier, VALID, "fails on the base"))
        elif case.find("skipped") is not None:
            verdicts.append(Verdict(identifier, NO_SIGNAL, "skipped on the base"))
        elif name in exempt:
            verdicts.append(Verdict(identifier, VALID,
                                    "passes on the base, but marked exempt"))
        else:
            verdicts.append(Verdict(identifier, SUSPECT,
                                    "PASSES on the base — does not test this change"))
    return verdicts


def run_against_base(base: str, head: str, files: list[str], adapter,
                     repo: Path | None = None) -> Path:
    """Build a "code from before + tests from after" tree and run the targeted tests in it.

    The tests come from head, the code from the base: that is the whole point of the check. The
    worktree shares git's object store, so it costs next to nothing — the real expense of a gate
    like this is installing dependencies, which the adapter avoids (question 4).
    """
    work = Path(tempfile.mkdtemp(prefix="rsquad-gate-"))
    tree = work / "base"
    added = git(["worktree", "add", "--detach", str(tree), base], repo)
    if added.returncode != 0:
        raise SystemExit("cannot create worktree: %s" % (added.stderr or "")[:200])

    # **The head SHA, never the literal `HEAD`.** In a worktree detached on the base, `HEAD`
    # denotes the base: `git checkout HEAD -- tests/` would bring back the OLD tests, and the
    # gate would compare old code against old tests. The command also fails as a whole as soon
    # as one file does not exist on the base, and then nothing is updated.
    for path in files:
        restored = run(["git", "checkout", head, "--", path], cwd=tree)
        if restored.returncode != 0:
            print("  (not restored: %s)" % path, file=sys.stderr)

    report_path = work / "base.xml"
    env = adapter.base_environment(tree)
    run(adapter.test_command(files, report_path), cwd=tree, env=env)
    return report_path


def cleanup(report_path: Path, repo: Path | None = None) -> None:
    tree = report_path.parent / "base"
    git(["worktree", "remove", "--force", str(tree)], repo)
    shutil.rmtree(report_path.parent, ignore_errors=True)


def _functions(batch: list[Verdict]) -> set[str]:
    """Distinct test functions behind a batch of JUnit cases.

    **Count functions, not JUnit cases.** A parametrized function yields N cases
    (`test_x[a]`, `test_x[b]`, ...) but is still ONE new test. Mixing the two units produces
    summaries where "valid" exceeds "examined" — seen on the 20-commit aggregate: 4 new tests
    against 10 "valid".
    """
    return {v.identifier.rsplit("::", 1)[-1].split("[", 1)[0] for v in batch}


@dataclass
class Summary:
    examined: int
    valid: int
    suspect: int
    no_signal: int
    junit_cases: int


def summarize(verdicts: list[Verdict]) -> Summary:
    by_state = {s: [v for v in verdicts if v.state == s] for s in (VALID, SUSPECT, NO_SIGNAL)}
    valid, suspect = _functions(by_state[VALID]), _functions(by_state[SUSPECT])
    return Summary(examined=len(valid | suspect), valid=len(valid), suspect=len(suspect),
                   no_signal=len(by_state[NO_SIGNAL]), junit_cases=len(verdicts))


def report(verdicts: list[Verdict], strict: bool, out=print) -> int:
    by_state = {s: [v for v in verdicts if v.state == s] for s in (VALID, SUSPECT, NO_SIGNAL)}
    for state, title in ((SUSPECT, "SUSPECT — pass against the code as it was"),
                         (NO_SIGNAL, "NO SIGNAL — the gate cannot say anything"),
                         (VALID, "VALID — fail against the code as it was")):
        batch = by_state[state]
        if not batch:
            continue
        out("\n%s (%d)" % (title, len(batch)))
        for v in batch:
            out("  %-64s %s" % (v.identifier[-64:], v.detail))

    s = summarize(verdicts)
    out("")
    # **Always print what was examined next to the verdict.** "0 suspect" very often means
    # "nothing could be checked at all", and a gate that reassures exactly when it knows
    # nothing is worse than no gate.
    out("%d function(s) examined: %d valid, %d suspect; %d no signal (%d JUnit case(s))."
        % (s.examined, s.valid, s.suspect, s.no_signal, s.junit_cases))
    if by_state[SUSPECT]:
        out("A test that passes before AND after does not test the change. Fix it, or mark it "
            "with one of %s if it guards preserved behaviour." % ", ".join(EXEMPT_MARKERS))
    return 1 if (strict and by_state[SUSPECT]) else 0
