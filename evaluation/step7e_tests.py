"""Step 7e — show the `tests` lens a test file, for the first time.

`rsquad evaluate` reviews **one unit per case: the changed source file**. So across the whole
Java campaign the `tests` lens was asked to judge test quality in a payload that contained no
test. It answered anyway — four findings in 190 tasks — and those four are the lens replying
off-topic, not the lens performing badly. **It has never been evaluated.**

This is not a detection measurement and cannot be: the frozen labels name a defect in a source
file, and a finding about a test has nothing to be scored against. What it measures is yield —
does the lens speak when it is finally given its subject, and is what it says worth reading. The
verdict on the second half belongs to the acceptance worksheet, which is where these findings
go.

**The selection rule, fixed here before the run.** One test file per case, never more, chosen
mechanically:

1. the test whose name is the source file's stem plus `Test` or `IT` — the test *for* the code
   under review;
2. failing that, the test whose stem contains the source stem;
3. failing that, the first in sorted order.

One per case bounds the run at 38 tasks and keeps the case the unit, so this arm lines up with
every other number in the campaign. Which rule fired is recorded per case, because "the first in
sorted order" is a much weaker claim than "the test for this class" and a reader must be able to
tell them apart.

**The model is a parameter here, and `claude-sonnet-5` is defensible for this arm alone.**
Every other measurement in the campaign compares against a half already run on `claude-opus-5`,
so there the model has to be held constant or two things move at once. This arm has no such
counterpart — it is a first look at a lens nobody has ever looked at — so a cheaper model costs
nothing but a caveat. Two conditions, both binding: the model is written into `selection.json`
and into the report, and these findings are **labelled by model** in the acceptance worksheet.
Unlabelled, they would quietly turn that corpus into a mixture of two engines.

    python evaluation/step7e_tests.py <workspace> <clones> [model]
    # then run the harness on the jobs, and: rsquad ingest <job> --path <test file>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
FREEZES = (HERE / "step7b.yaml", HERE / "step7d.yaml")


def run(args, check=True):
    done = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    if check and done.returncode != 0:
        raise SystemExit("%s\n%s%s" % (" ".join(args), done.stdout, done.stderr))
    return done


def test_files(repo: Path, commit: str) -> list[str]:
    shown = run(["git", "-C", str(repo), "show", "--name-only", "--format=", commit])
    return sorted(p for p in shown.stdout.split()
                  if "/src/test/" in p and p.endswith(".java"))


def choose(source: str, candidates: list[str]) -> tuple[str, str] | None:
    """(path, which rule fired), or None when the commit touched no test."""
    if not candidates:
        return None
    stem = Path(source).stem
    for suffix in ("Test", "IT"):
        for path in candidates:
            if Path(path).stem == stem + suffix:
                return path, "named for the class under review"
    for path in candidates:
        if stem in Path(path).stem:
            return path, "name contains the class under review"
    return candidates[0], "first in sorted order — no name relation"


def main(workspace: Path, clones: Path, model: str) -> int:
    workspace.mkdir(parents=True, exist_ok=True)
    chosen, skipped = [], []

    for freeze in FREEZES:
        frozen = yaml.safe_load(freeze.read_text(encoding="utf-8"))
        for case in frozen["cases"]:
            if case["detectable_from_diff"] == "no":
                continue
            repo = clones / case["repo"].split("/")[1]
            picked = choose(case["file"], test_files(repo, case["origin"]))
            if picked is None:
                skipped.append(case["id"])
                continue
            path, rule = picked
            chosen.append({"case": case["id"], "repo": str(repo), "origin": case["origin"],
                           "source": case["file"], "test": path, "rule": rule})

    for entry in chosen:
        out = workspace / entry["case"]
        run([sys.executable, "-m", "rsquad", "export", str(out),
             "--repo", entry["repo"], "--head", entry["origin"],
             "--path", entry["test"], "--lens", "tests", "--no-conformance",
             "--model", model])
        print("  %-24s %s" % (entry["case"], entry["test"]))

    (workspace / "selection.json").write_text(
        json.dumps({"model": model, "chosen": chosen, "skipped": skipped}, indent=2),
        encoding="utf-8")
    print("\n%d job(s) in %s, %d case(s) whose origin touched no test: %s"
          % (len(chosen), workspace, len(skipped), ", ".join(skipped) or "none"))
    print("  model: %s — recorded because this arm alone does not hold it constant" % model)
    for rule in sorted({e["rule"] for e in chosen}):
        print("  %2d  %s" % (sum(1 for e in chosen if e["rule"] == rule), rule))
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)
    sys.exit(main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(),
                  sys.argv[3] if len(sys.argv) == 4 else "claude-opus-5"))
