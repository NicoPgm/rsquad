"""Build the blind acceptance worksheet, and the key that stays shut until it is filled.

Acceptance is the only number in this project a machine cannot produce. Everything else --
detection, noise, silence -- is a count. Whether a reader would *act* on a finding is a judgement,
and it is the judgement that decides whether anyone keeps the tool: below roughly 30 % a lens
earns its removal, and a lens kept below that teaches the reader to skim the others too.

So the worksheet is built to protect that judgement from everything that would bias it:

  - **the lens is hidden.** Per-lens acceptance is the whole point, so the judge must not know
    which lens spoke. `kind` and `severity` are hidden with it: `boundary` and `contract` name
    their lenses out loud, and `severity` is the lens grading its own homework.
  - **the case is hidden.** Whether a finding is the defect the case was selected for, whether
    the commit was a clean one, and whether the refuter killed it -- all in the key, none in the
    worksheet.
  - **the order is shuffled**, with a fixed seed so it reproduces. Shuffling matters twice: it
    keeps one lens's items from arriving in a block, and it makes *any prefix* of the worksheet a
    random sample -- so a run that stops early is still unbiased about which findings were seen.

What stays is what makes the claim checkable: the file, the line, the quoted code, the inputs and
the consequence. That is the finding schema minus the parts that are about the finder.

    python evaluation/acceptance/build.py <scratch-with-job-dirs>
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 7  # fixed, so the worksheet reproduces exactly

# Every job directory the campaign left behind. `origin` is recorded in the key, never shown.
SETS = {
    "step7b": ["h40/lc", "hjobs"],
    "step7d": ["h40/d7lc", "h40/d7sa"],
    "clean": ["clean2"],
}

HEADER = """# Acceptance worksheet — one word per finding

Below are claims a code reviewer made about specific lines of Java. Each one names a file and a
line, quotes the code, states the inputs that trigger the problem and the consequence that
follows.

## What to do

Read each block. Write one word after `**verdict:**`, replacing the `?`. Nothing else. Do not
edit any other part of the file.

| word | means |
|---|---|
| `act` | I would change this code, or file it. |
| `note` | True, and I would not act on it — too minor, out of scope, a known trade-off. |
| `wrong` | The claim is false, or the consequence does not follow from the inputs. |
| `unsure` | I cannot tell without more work than this finding deserves. |

**`unsure` is a real answer, not a skip.** A forced verdict is invented data.

You are not auditing correctness. The question is only: **was this worth reading?**

Judge each block on its own. Some claims resemble each other; that is expected, and each still
costs a reader a block to read.

Answer every block in order, and do not skip one because it is hard — a skipped block is the one
whose answer mattered.

---
"""

BLOCK = """
### %03d

`%s:%s`

```java
%s
```

**Given** %s

**Then** %s

**verdict:** ?

---
"""


def collect(scratch: Path):
    """Every finding that reached the refutation round, with the lens that produced it.

    The round-2 manifest carries one task per finding with the whole `finding` inside it, and
    `lenses.interpret` stamps each finding with the lens that produced it — so nothing has to be
    re-derived and no ordering has to be guessed. (The task's own `lens` field says "refutation";
    reading that instead is a mistake worth naming, because it fails silently: every item gets a
    plausible lens and the per-lens table becomes one row.)
    """
    items = []
    for name, dirs in SETS.items():
        for rel in dirs:
            root = scratch / rel
            if not root.exists():
                print("  (absent, skipped) %s" % root)
                continue
            for job in sorted(p for p in root.iterdir() if p.is_dir()):
                manifest = json.loads((job / "manifest.json").read_text(encoding="utf-8"))
                if manifest["round"] != 2:
                    continue                       # never advanced: it found nothing
                for task in manifest["tasks"]:
                    reply = job / "round-2" / "results" / ("%s.json" % task["id"])
                    verdict = None
                    if reply.exists():
                        verdict = json.loads(reply.read_text(encoding="utf-8")).get("verdict")
                    items.append({
                        "set": name,
                        "case": job.name,
                        # The task's own `lens` is "refutation" — the lens that FOUND it rides
                        # inside the finding, which `lenses.interpret` stamps.
                        "lens": task["finding"].get("lens", "conformance"),
                        "refuter": verdict,
                        "finding": task["finding"],
                    })
    return items


def main(scratch: Path) -> int:
    items = collect(scratch)
    random.Random(SEED).shuffle(items)

    lines, key = [HEADER.replace("{N}", str(len(items)))], []
    for n, item in enumerate(items, start=1):
        f = item["finding"]
        lines.append(BLOCK % (n, f["file"], f["line"], f["snippet"],
                              f["inputs"].strip(), f["consequence"].strip()))
        key.append({"n": n, "set": item["set"], "case": item["case"], "lens": item["lens"],
                    "refuter": item["refuter"], "file": f["file"], "line": f["line"]})

    (HERE / "worksheet.md").write_text("".join(lines), encoding="utf-8")
    (HERE / "key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    print("%d finding(s) -> %s" % (len(items), HERE / "worksheet.md"))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(main(Path(sys.argv[1]).resolve()))
