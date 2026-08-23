"""Turn the frozen step 7b selection into one defect set per arm, ready for `rsquad evaluate`.

No synthetic commits here, unlike `step7_prepare.py`: the commit under review is a real one from
the repository's own history — the commit that first wrote the buggy line. So this only reshapes
`step7b.yaml` into the schema `evaluate` reads, and clones the repositories if needed.

    python evaluation/step7b_prepare.py <workspace>
    python -m rsquad evaluate --defects <workspace>/langchain4j.defects.yaml \\
        --repo <workspace>/langchain4j --max-usd 8 --out evaluation/step7b-langchain4j.md --confirm
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent


def run(args, check=True):
    if args[0] == "git":
        args = [args[0], "-c", "core.longpaths=true"] + args[1:]
    done = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    if check and done.returncode != 0:
        raise SystemExit("%s\n%s%s" % (" ".join(args), done.stdout, done.stderr))
    return done


def main(workspace: Path) -> int:
    frozen = yaml.safe_load((HERE / "step7b.yaml").read_text(encoding="utf-8"))
    workspace.mkdir(parents=True, exist_ok=True)

    for arm in frozen["arms"]:
        name = arm["repo"].split("/")[1]
        repo = workspace / name
        if not repo.exists():
            print("cloning %s" % arm["url"], flush=True)
            run(["git", "clone", "--quiet", "--single-branch", arm["url"], str(repo)])

        defects = []
        for case in [c for c in frozen["cases"] if c["repo"] == arm["repo"]]:
            defects.append({
                "id": case["id"],
                "summary": case["fix_subject"].strip(),
                "repo": arm["repo"],
                # The commit that FIRST WROTE the buggy line — a real commit, verified to carry
                # that line as an addition. Not a reverse patch and not a regression.
                "introduced_in": case["origin"],
                "fixed_in": case["fix"],
                "file": case["file"],
                "replayable": True,
                "self_found": False,
                "detectable_from_diff": case["detectable_from_diff"],
                "found_by": "reported by a user; fixed in %s" % case["fix"],
                "note": case["label_rationale"].strip(),
            })

        out = workspace / ("%s.defects.yaml" % name)
        out.write_text(yaml.safe_dump({"schema_version": 1, "defects": defects},
                                      allow_unicode=True, sort_keys=False), encoding="utf-8")
        scorable = sum(1 for d in defects if d["detectable_from_diff"] != "no")
        print("  %-14s %d case(s), %d scorable -> %s" % (name, len(defects), scorable, out),
              flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(main(Path(sys.argv[1]).resolve()))
