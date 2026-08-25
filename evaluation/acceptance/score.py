"""Join the filled worksheet to the key, and print acceptance with its denominators.

Refuses to print a rate for a lens with fewer than MINIMUM verdicts. A rate over eight items is
not a rate, and this project has spent four campaigns learning that a number printed is a number
believed.

    python evaluation/acceptance/score.py [worksheet.md]
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALUES = ("act", "note", "wrong", "unsure")
MINIMUM = 25          # below this, the fraction is printed and the rate is not
RETIREMENT = 0.30     # the line below which a lens earns its removal


def wilson(k: int, n: int) -> tuple[float, float]:
    if not n:
        return 0.0, 1.0
    p, z = k / n, 1.96
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def read(path: Path) -> dict[int, str]:
    text = path.read_text(encoding="utf-8")
    out = {}
    for block in re.finditer(r"^### (\d+)(.*?)(?=^### |\Z)", text, re.S | re.M):
        m = re.search(r"^\*\*verdict:\*\*\s*(\S+)", block.group(2), re.M)
        if not m or m.group(1) == "?":
            continue
        word = m.group(1).strip("`").lower()
        if word not in VALUES:
            raise SystemExit("item %s: %r is not one of %s"
                             % (block.group(1), word, ", ".join(VALUES)))
        out[int(block.group(1))] = word
    return out


def table(title: str, rows: list[tuple[str, Counter]]) -> None:
    print("\n%s" % title)
    print("%-22s %5s %5s %5s %6s %6s   %s" % ("", "act", "note", "wrong", "unsure", "n", "acceptance"))
    for name, c in rows:
        n = sum(c.values())
        if not n:
            continue
        cell = "%d/%d — too few" % (c["act"], n)
        if n >= MINIMUM:
            lo, hi = wilson(c["act"], n)
            cell = "%d/%d = %2.0f %%  [%2.0f, %2.0f]" % (c["act"], n, 100 * c["act"] / n,
                                                         100 * lo, 100 * hi)
            if hi < RETIREMENT:
                cell += "  BELOW the 30 % line"
            elif lo > RETIREMENT:
                cell += "  above"
        print("%-22s %5d %5d %5d %6d %6d   %s"
              % (name, c["act"], c["note"], c["wrong"], c["unsure"], n, cell))


def main(path: Path) -> int:
    verdicts = read(path)
    key = {x["n"]: x for x in json.loads((HERE / "key.json").read_text(encoding="utf-8"))}
    if not verdicts:
        raise SystemExit("no verdict filled in %s — every item still says `?`." % path)

    done = sorted(verdicts)
    prefix = [n for n in done if n <= max(done)]
    print("%d of %d item(s) judged." % (len(verdicts), len(key)))
    gaps = [n for n in range(1, max(done) + 1) if n not in verdicts]
    if gaps:
        # Skipping items inside the prefix breaks the one property shuffling bought.
        print("**%d item(s) skipped inside the range judged** (%s%s). The prefix is no longer a "
              "random sample: a skipped item is a judgement too, and it is usually the hard one."
              % (len(gaps), ", ".join(str(g) for g in gaps[:8]), " ..." if len(gaps) > 8 else ""))

    by = defaultdict(Counter)
    for n, word in verdicts.items():
        by[key[n]["lens"]][word] += 1
    table("Acceptance per lens", sorted(by.items(), key=lambda kv: -sum(kv[1].values())))

    corpus = defaultdict(Counter)
    for n, word in verdicts.items():
        corpus["clean commits" if key[n]["set"] == "clean" else "defect cases"][word] += 1
    table("Acceptance by corpus", sorted(corpus.items()))

    ref = defaultdict(Counter)
    for n, word in verdicts.items():
        ref["refuter killed it" if key[n]["refuter"] != "stands" else "refuter let it stand"][word] += 1
    table("What the refuter cost", sorted(ref.items()))

    # A lens is worth keeping for what only it says, so acceptance is read beside solitude.
    place = defaultdict(set)
    for x in key.values():
        place[(x["case"], x["file"], x["line"])].add(x["lens"])
    alone = Counter(next(iter(ls)) for ls in place.values() if len(ls) == 1)
    print("\nPlaces reported by exactly one lens (all %d items, no judgement needed)" % len(key))
    for lens, count in alone.most_common():
        print("  %-14s %d of %d distinct place(s)" % (lens, count, len(place)))
    print("\nA lens earns its place by acceptance AND by what only it finds. A high rate on "
          "claims\nanother lens also made is a lens that could be removed for free.")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "worksheet.md"))
