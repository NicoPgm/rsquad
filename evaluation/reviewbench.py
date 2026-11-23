"""A finished RSquad job, written as ReviewBench's findings file.

ReviewBench (github.com/review-bench/ReviewBench) judges one JSON file per pull request: a file,
a line range at head, and a message (its `AGENT_CONTRACT.md` and `docs/JUDGING_INPUT.md`). This
reads a job after its last `ingest`, keeps what survived refutation, and writes one entry per
place, the way the queue shows it: lenses agreeing on a place are one logical issue, and the
contract asks for one entry per logical issue.

    python evaluation/reviewbench.py <job> --pr <pr.json> --out <findings.json>

`<pr.json>` is the bench's own metadata for the pull request: `repo`, `pr_number`, `base`,
`head`. Nothing here calls a model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rsquad import chunking, conformance, job, ranking, refutation
from rsquad.__main__ import _adapter

AGENT = "rsquad"


def message(entry: ranking.Entry) -> str:
    """What is wrong and why, from each shape's most detailed account."""
    parts = []
    for finding in entry.representatives:
        left, left_text, right, right_text = ranking.detail(finding)
        parts.append("%s. %s: %s" % (right_text.rstrip("."), left, left_text))
    # What the queue shows under "the refuter places it elsewhere": the reader gets it, so the
    # judge does too.
    for reason in dict.fromkeys(f["elsewhere"] for f in entry.findings if "elsewhere" in f):
        parts.append("Where it lives: %s" % reason)
    return " ".join(parts)


def span(entry: ranking.Entry) -> tuple[int, int]:
    """The lines the grouped findings quote, at head."""
    starts = [f["line"] for f in entry.findings]
    ends = [f["line"] + f["snippet"].rstrip("\n").count("\n") for f in entry.findings]
    return min(starts), max(ends)


def findings_file(survived: list[dict], pr: dict) -> dict:
    findings = []
    for entry in ranking.rank(ranking.group(survived)):
        start, end = span(entry)
        findings.append({"file": entry.file, "start_line": start, "end_line": end,
                         "message": message(entry), "producer": AGENT})
    return {"pr": {k: pr[k] for k in ("repo", "pr_number", "base", "head")},
            "agent": AGENT, "findings": findings}


def survived(job_dir: Path) -> list[dict]:
    """What `ingest` would put in the queue, recomputed the same way."""
    data = job.manifest(job_dir)
    repo = Path(data["repo"])
    selected, _ = chunking.units(data["base"], data["head"], repo, None,
                                 adapter=_adapter(data.get("context", True)))
    units = {u.file: u for u in selected}
    result = job.ingest(job_dir, units, conformance.gather(data["head"], repo, data["specs"]))
    if result.missing or result.malformed:
        raise SystemExit("job %s is incomplete: %d missing, %d malformed"
                         % (job_dir, len(result.missing), len(result.malformed)))
    if not result.verdicts:
        return result.findings
    return refutation.survivors(result.verdicts)[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("job", type=Path)
    parser.add_argument("--pr", type=Path, required=True, help="the bench's pr.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    pr = json.loads(args.pr.read_text(encoding="utf-8"))
    out = findings_file(survived(args.job), pr)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("%d finding(s) -> %s" % (len(out["findings"]), args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
