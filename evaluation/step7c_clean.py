"""Select clean commits — the corpus every campaign so far has been missing.

Each case in `step7b.yaml` is a diff **known** to contain a defect, so nothing measured there
bounds what the squad says about code nobody has complained about. 35 of 50 findings were not the
known defect, and that number is only interpretable next to what the same lenses produce on a
commit with no defect in it.

"Clean" cannot mean "contains no bug" — nobody can establish that. The operational definition,
fixed here before anything runs:

    a commit whose changed source file has NOT been touched by any later fix commit

Nobody has reported a bug in that file since. It is a proxy and it is falsifiable in one
direction only: a latent defect nobody has hit yet still counts as clean, which makes the noise
figure a **lower bound** rather than an upper one. Stated so it cannot be quietly forgotten.

Everything else matches the defect cases exactly, so the two are comparable:

    1. committed since 2026-05-01
    2. the message does NOT match a fix vocabulary, deliberately WIDER than the one used to
       select the defect cases
    3. exactly one changed .java outside the test tree, at least one inside it, <= 6 files
    4. the source diff changes at least one line that is not a comment, blank or import
    5. no later commit whose message matches the fix vocabulary touches that file
    6. the N most recent that qualify, by date. No further choice.

Two amendments to rule 2, both made before anything ran and both recorded here rather than
folded in silently.

**Dropped: excluding any commit that references an issue.** langchain4j appends the pull request
number to every commit subject — `(#5901)` — so the rule matched the entire repository and left
two candidates. It was discriminating on a commit convention, not on content.

**Added: a wider fix vocabulary than the defect selection uses.** `Correct ToolContext parameter
detection` and `Harden filename handling` are repairs whose subject avoids the word "fix", and
they survived the first pass. The exclusion list here therefore also carries correct, harden,
guard, prevent, avoid, resolve and workaround. Widening an EXCLUSION can only shrink the corpus
and only toward cleaner cases, so it is safe in the direction that matters. It is not applied
backwards to `step7b.yaml`, which is frozen.
"""

from __future__ import annotations

import re
import subprocess
import sys

#: Wider than the defect selection's vocabulary, on purpose — see the module docstring. Widening
#: an EXCLUSION can only shrink the corpus, and only toward cleaner cases.
FIX = re.compile(r"\b(fix(e[sd])?|bug|incorrect|wrong|regression|npe|fails?|broken|"
                 r"should not|no longer|correct(s|ed|ion)?|harden(s|ed|ing)?|guard(s|ed)?|"
                 r"prevent(s|ed)?|avoid(s|ed)?|resolve[sd]?|workaround|escape[sd]?|"
                 r"validate[sd]?|sanitiz(e|es|ed))\b", re.I)
NOISE = re.compile(r"^[+-]\s*(//|\*|/\*|import\s|$)")
SINCE = "2026-05-01"


def git(repo, args):
    return subprocess.run(["git", "-C", repo] + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def upstream(repo):
    heads = [line.strip() for line in git(repo, ["branch", "-r"]).splitlines()
             if "->" not in line]
    return heads[0] if heads else "HEAD"


def touched_by_a_later_fix(repo, sha, path, head):
    """Has any fix commit touched this file since? That is what disqualifies a case."""
    for later in git(repo, ["log", "%s..%s" % (sha, head), "--format=%H", "--", path]).split():
        if FIX.search(git(repo, ["log", "-1", "--format=%s%n%b", later])):
            return True
    return False


def select(repo, want):
    head = upstream(repo)
    taken = []
    for sha in git(repo, ["log", head, "--since=" + SINCE, "--format=%H"]).split():
        message = git(repo, ["log", "-1", "--format=%s%n%b", sha]).strip()
        if FIX.search(message):
            continue
        names = [n for n in git(repo, ["show", "--name-only", "--format=", sha]).split()
                 if n.endswith(".java")]
        src = [n for n in names if "/test/" not in n and "/it/" not in n]
        tests = [n for n in names if "/test/" in n or "/it/" in n]
        if len(src) != 1 or not tests or len(names) > 6:
            continue
        patch = git(repo, ["show", "--format=", sha, "--", src[0]]).splitlines()
        real = [line for line in patch if line[:1] in "+-"
                and not line.startswith(("+++", "---")) and not NOISE.match(line)]
        if not real:
            continue
        if touched_by_a_later_fix(repo, sha, src[0], head):
            continue
        taken.append((sha, message.splitlines()[0][:60], src[0], len(real)))
        if len(taken) == want:
            break
    return taken


if __name__ == "__main__":
    want = int(sys.argv[-1])
    for repo in sys.argv[1:-1]:
        rows = select(repo, want)
        print("### %s: %d clean commit(s)" % (repo, len(rows)))
        for sha, subject, path, lines in rows:
            print("  %s %-60s %4dL %s" % (sha[:9], subject, lines, path.split("/")[-1]))
