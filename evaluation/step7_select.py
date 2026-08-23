"""Pre-registered selection for step 7 — the script that produced `step7.yaml`.

Kept so the selection can be reproduced, and so a later reader can check that no commit
was chosen by hand:

    git clone --shallow-since=2026-04-01 --single-branch <url> <dir>
    python evaluation/step7_select.py <dir> <other-dir> 3

Original header: Mechanical: no commit is chosen by reading its subject.

RULES, fixed before any diff was read:
  1. commits since 2026-05-01 (after the model's knowledge cutoff, so a memorised fix cannot
     masquerade as a detection)
  2. subject or body matches a fix vocabulary AND references an issue
  3. exactly 1-2 changed .java files outside the test tree, at least one inside it, <= 6 files
  4. the source diff changes at least one line that is not a comment, blank or import
     (a Javadoc correction is not a defect)
  5. the source diff REMOVES at least one non-comment line. The squad is shown the fix
     reversed, and reversing an addition-only fix deletes a guard together with the javadoc
     explaining why it is needed -- far more conspicuous than the original omission ever was.
     Only fixes that MODIFY existing logic reverse into a realistic change.
  6. the source diff adds NO net-new comment line. Reversing a fix that explains itself deletes
     that explanation, and a deleted comment naming the defect puts the answer in the diff --
     a leak, not merely an easier task. Comments that are only MOVED (removed and re-added
     unchanged) are fine: reversing restores them.
     Known bias: this selects against fixes whose author documented the subtlety.
  7. take the N most recent that qualify, by date. No further choice.
"""
import re, subprocess, sys

FIX = re.compile(r"\b(fix(e[sd])?|bug|incorrect|wrong|regression|npe|fails?|broken|"
                 r"should not|no longer)\b", re.I)
ISSUE = re.compile(r"(#\d+|\b[A-Z]{2,}-\d+\b)")
NOISE = re.compile(r"^[+-]\s*(//|\*|/\*|import\s|$)")
COMMENT = re.compile(r"^\s*(//|\*|/\*)")

def git(repo, args):
    return subprocess.run(["git", "-C", repo] + args, capture_output=True,
                          text=True, encoding="utf-8", errors="replace").stdout

def qualifies(repo, sha):
    message = git(repo, ["log", "-1", "--format=%s%n%b", sha]).strip()
    if not (FIX.search(message) and ISSUE.search(message)):
        return None
    names = [n for n in git(repo, ["show", "--name-only", "--format=", sha]).splitlines() if n]
    java = [n for n in names if n.endswith(".java")]
    src = [n for n in java if "/test/" not in n and "/it/" not in n]
    tst = [n for n in java if "/test/" in n or "/it/" in n]
    if not (1 <= len(src) <= 2 and tst and len(names) <= 6):
        return None
    diff = git(repo, ["show", "--format=", sha, "--", *src]).splitlines()
    real = [l for l in diff
            if l[:1] in "+-" and not l.startswith(("+++", "---")) and not NOISE.match(l)]
    if not real:
        return None                      # rule 4: comments only
    if not any(l.startswith("-") for l in real):
        return None                      # rule 5: addition-only reverses into a giveaway
    added = {l[1:].strip() for l in diff if COMMENT.match(l[1:]) and l.startswith("+")}
    removed = {l[1:].strip() for l in diff if COMMENT.match(l[1:]) and l.startswith("-")}
    if added - removed:
        return None                      # rule 6: the reverse would delete an explanation
    return dict(sha=sha, subject=message.splitlines()[0], src=src, tests=tst,
                issue=ISSUE.search(message).group(0), changed_lines=len(real))

def upstream(repo):
    """Walk the remote branch, never the checkout.

    `step7_prepare.py` leaves the repository on a `step7/<case>` branch, and a selection run
    afterwards then walks that branch instead of history — silently returning older commits.
    Found by running the two scripts in sequence and not recognising the result.
    """
    heads = [l.strip() for l in git(repo, ["branch", "-r"]).splitlines() if "->" not in l]
    return heads[0] if heads else "HEAD"


for repo in sys.argv[1:-1]:
    want, taken = int(sys.argv[-1]), []
    for sha in git(repo, ["log", upstream(repo), "--since=2026-05-01", "--format=%H"]).split():
        case = qualifies(repo, sha)
        if case:
            taken.append(case)
        if len(taken) == want:
            break
    print("### %s" % repo)
    for c in taken:
        print("  %s  %-3d lines  %s" % (c["sha"][:9], c["changed_lines"], c["subject"][:70]))
        print("      src: %s" % ", ".join(c["src"]))
