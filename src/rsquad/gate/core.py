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
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from ..vcs import git, resolve, run

# A characterization test MUST pass on the base: it exists to prove a refactor changes nothing.
# A guard test asserts that something does NOT happen; the base does not do it either, so it
# cannot fail there by construction. Both need the exemption, and the exemption must stay
# visible in review — hence a marker in the code rather than a list in a config file.
EXEMPT_MARKERS = ("characterization", "guard")

VALID, SUSPECT, NO_SIGNAL = "valid", "suspect", "no-signal"


class RunnerFailed(RuntimeError):
    """The runner produced no report, so the gate verified nothing.

    Raised rather than swallowed on purpose. A gate that cannot run must say so loudly; one
    that quietly returns "nothing to report" is worse than no gate, because it is trusted.
    """


@dataclass
class Verdict:
    identifier: str
    state: str
    detail: str = ""


def merge_base(reference: str, head: str = "HEAD", repo: Path | None = None) -> str:
    """The **merge base**, not "head minus the diff".

    If the branch has diverged the two do not denote the same code, and comparing against
    anything other than the common ancestor means testing against a state that never existed.
    """
    merged = git(["merge-base", head, reference], repo)
    if merged.returncode == 0 and merged.stdout.strip():
        return merged.stdout.strip()
    return resolve(reference, repo)


def changed_files(base: str, head: str, patterns: list[str],
                  repo: Path | None = None) -> list[str]:
    """Paths touched between base and head, restricted to the watched directories.

    Filtering by extension is the adapter's job (question 1) — this only asks git.
    """
    diff = git(["diff", "--name-only", "%s...%s" % (base, head), "--", *patterns], repo)
    return [line.strip() for line in diff.stdout.splitlines() if line.strip()]


def _selects(entries: set[str], function: str, classname: str, qualified: bool) -> bool:
    """Is this JUnit case one of `entries`?

    Entries are `module::function`. JUnit's `classname` is hierarchical and dotted in every
    producer this seam targets — pytest writes `tests.test_alpha` for a module-level test and
    `tests.test_alpha.TestGrouped` for a method — so an entry matches when its module *is* the
    classname or is a dotted prefix of it.

    `qualified` is decided once per report, by `_qualified_matches`. False means the module part
    is ignored and only the name is compared, which is the behaviour that existed before files
    were tracked at all.
    """
    for entry in entries:
        module, _, name = entry.rpartition("::")
        if name != function:
            continue
        if not qualified:
            return True
        if module and (classname == module or classname.startswith(module + ".")):
            return True
    return False


def _qualified_matches(cases: list, entries: set[str]) -> bool:
    """Does this runner's `classname` follow the convention the adapter's modules assume?

    Decided once for the whole report, never per case. **The fallback is the point:** an adapter
    that has not implemented `module_name`, or a runner that names things some other way, would
    otherwise match nothing at all — and a gate that examines nothing reports "0 suspect", which
    reads as a clean bill of health. Failing back to bare-name matching is wrong in the noisy
    direction, which is the survivable one.
    """
    modules = {entry.rpartition("::")[0] for entry in entries if "::" in entry}
    classnames = {case.get("classname", "") for case in cases if case.get("classname")}
    return any(name == module or name.startswith(module + ".")
               for module in modules if module for name in classnames)


def _fit(text: str, width: int = 64) -> str:
    """Elide the middle, never the head.

    The identifier used to be truncated from the left, which kept the test name and dropped the
    module — and since question 7 the module is what tells two same-named tests apart. Reporting
    `adapter_python::test_x` where the file was `tests.test_adapter_python` is a report you have
    to decode.
    """
    if len(text) <= width:
        return text
    head = (width - 1) // 2
    return text[:head] + "…" + text[-(width - head - 1):]


def parse_junit(path: Path, exempt: set[str], retained: set[str],
                missing_symbol=None) -> list[Verdict]:
    """Classify every test case from the JUnit report produced against the base.

    `missing_symbol` is the adapter's `signals_missing_symbol` — a predicate over a failure
    message. It exists because `<failure>` and `<error>` do not split failures the way this
    gate needs them split.

    A test whose new symbol does not exist yet fails at *collection* when the symbol is named
    in an import (`<error>`, no signal), but inside the *call phase* when it is reached through
    a module attribute (`<failure>`, which reads as a discriminating test). Same epistemic
    content — the symbol does not exist yet — opposite verdicts, decided by import style rather
    than by test quality. Measured 2026-08-22 on a commit that reported 10 valid, 0 no-signal
    while adding an entirely new test file.

    The predicate is per-stack because the exception vocabulary is: `AttributeError` here,
    `NoSuchMethodError` or `ReferenceError` elsewhere. Adapters that do not implement it keep
    the old behaviour, which over-reports `valid`.
    """
    if not path.exists():
        return []
    cases = list(ET.parse(path).getroot().iter("testcase"))
    qualified = _qualified_matches(cases, retained | exempt)
    verdicts = []
    for case in cases:
        classname = case.get("classname", "")
        identifier = "%s::%s" % (classname, case.get("name", ""))
        name = case.get("name", "")
        # JUnit emits `test_x[param]`; we key on the function, not the parametrization.
        function = name.split("[", 1)[0]
        # A collection error carries no `classname`: it covers the whole module. Filtering it
        # like an ordinary test would hide the fact that N new tests could not be examined at
        # all — the gate's most misleading silence.
        collection_error = case.find("error") is not None and not case.get("classname")
        # **No `retained and` short-circuit here.** An empty `retained` means no test function
        # was added or modified, which is a reason to say nothing — not a reason to classify
        # every pre-existing test in a touched file. With the guard, a commit that edits a
        # fixture or a module-level constant makes `tests_touched` return an empty set, the
        # filter turns into a no-op, and every passing test in the file is reported SUSPECT:
        # exactly the false-positive flood the per-function granularity exists to prevent, and
        # exit 1 under --strict. Found by the squad's own lenses on 2026-08-22.
        # `_selects`, not `in`: names alone cannot say which file a test lives in, so two
        # files each holding a `test_roundtrip` were indistinguishable and the untouched one
        # was examined and reported suspect for passing on the base — which is its job.
        if not _selects(retained, function, classname, qualified) and not collection_error:
            continue
        failure = case.find("failure")
        if case.find("error") is not None:
            verdicts.append(Verdict(identifier, NO_SIGNAL,
                                    "collection or setup error on the base"))
        elif failure is not None:
            if missing_symbol and missing_symbol(failure.get("message") or ""):
                verdicts.append(Verdict(identifier, NO_SIGNAL,
                                        "fails on a symbol that does not exist yet"))
            else:
                verdicts.append(Verdict(identifier, VALID, "fails on the base"))
        elif case.find("skipped") is not None:
            verdicts.append(Verdict(identifier, NO_SIGNAL, "skipped on the base"))
        # `function`, not `name`. JUnit reports a parametrized case as `test_x[1]` while the
        # marker scan collects the bare `test_x`, so matching on `name` silently loses the
        # exemption for every parametrized characterization or guard test.
        elif _selects(exempt, function, classname, qualified):
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
        # Clean up before leaving. The caller's `finally` only runs once this function has
        # returned a path, so raising from here used to strand the temp directory — one orphan
        # per failed run, forever.
        shutil.rmtree(work, ignore_errors=True)
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
    completed = run(adapter.test_command(files, report_path), cwd=tree, env=env)

    # **A missing report is a run that did not happen, not a run that found nothing.** The
    # return code cannot carry this: the runner exits non-zero whenever tests fail, which here
    # is the normal, desired outcome. The file's absence is the signal — the runner is not
    # installed, a path does not exist on the base, the invocation was rejected. Left
    # unchecked, the gate printed "nothing collected" and returned 0, reporting success on a
    # run that verified nothing. That is the failure mode this whole tool exists to name.
    if not report_path.exists():
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        cleanup(report_path, repo)
        raise RunnerFailed("the runner produced no report: %s"
                           % (detail[-1][:200] if detail else "no output"))
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
            out("  %-64s %s" % (_fit(v.identifier), v.detail))

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
