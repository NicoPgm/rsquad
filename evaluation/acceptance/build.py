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

**This is the measurement no machine can make.** Every other number in this project is a count.
This one asks a reader whether the finding was worth their time, and it is the one that decides
whether a lens stays.

## What to do

Read each block. Write one word after `**verdict:**`, replacing the `?`. Nothing else.

| word | means |
|---|---|
| `act` | I would change this code, or file it. |
| `note` | True, and I would not act on it — too minor, out of scope, a known trade-off. |
| `wrong` | The claim is false, or the consequence does not follow from the inputs. |
| `unsure` | I cannot tell without more work than this finding deserves. |

**`unsure` is a real answer, not a skip.** Forcing a verdict manufactures data. And it counts
*against* the lens in the headline rate, because the reader still paid the time.

You are not auditing correctness. The question is only: **was this worth reading?**

If you want to check one, the repositories are on disk and the file and line are given.

## The same defect may appear two or three times

Different lenses reach the same line independently and say nearly the same thing. Those are
separate items on purpose, and shuffling spreads them apart. **Judge each on its own** — a lens
that only ever restates another lens's finding still costs a reader a block to read, and the
whole question is whether it earns that.

## Where to stop

The order is shuffled, so any prefix is a random sample. Three checkpoints are declared here,
before any verdict is written:

| after | per big lens | what it can answer |
|---|---|---|
| **90 items** | ~30 | whether the three big lenses differ from each other by a lot (+/- 17 pts) |
| **150 items** | ~50 | whether a lens sits above or below the 30 % retirement line (+/- 13 pts) |
| **{N} items (all)** | ~68 | the same, tighter, plus clean-commit and refuted-finding acceptance |

**Stop at a checkpoint, not when the numbers look good.** Choosing where to stop after seeing
results is the one bias shuffling cannot fix.

## What is not in here

**Three lenses can be measured: `contract` (73 findings), `bounds` (65), `repro` (65).**

`tests` produced **4** findings in 46 reviews and `conformance` **8**. Neither has an acceptance
rate to measure — they have a yield problem first, and that is the answer about them.

`conformance` is absent from the worksheet entirely, for a second reason: its findings carry a
different schema — a quoted `requirement` and a `mismatch`, not `inputs` and `consequence` — so
every one of its blocks would announce its own lens. It cannot be shown blind beside the others,
and showing it labelled would bias every judgement in the file.

## Then

    python evaluation/acceptance/score.py

It joins these verdicts to `key.json` — which nobody should open before finishing — and prints
acceptance per lens, with denominators.

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
