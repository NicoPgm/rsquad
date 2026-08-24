"""Rule 7, made a script: does the buggy line appear as an ADDITION in the origin's diff?

`step7_origin.py` finds where a line was last written and checks the commit is reviewable. It
does not check that the commit *wrote* that line — `git log -L` reports the last commit to touch
the line, which is the same thing only when the history is clean.

So this reads the pool listing, pairs each removed line of the fix with its replacement, and
keeps a case only when at least one of those removed lines is literally added by the origin. A
case that verifies nothing is **dropped, not labelled**: the two are different statements, and
the rubric says so (rule 5).

    python evaluation/step7_origin.py --max-files 20 <repo>... > pool.txt
    python evaluation/step7_verify.py pool.txt

Written after the fact, from the version used to build `step7b.yaml`, which lived outside the
repository — so the check that decided eight drops was not reproducible. It is now.
"""
import re
import subprocess
import sys

NOISE = re.compile(r"^[+-]\s*(//|\*|/\*|import\s|$)")


def git(repo, args):
    return subprocess.run(["git", "-C", repo] + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def nows(s):
    return re.sub(r"\s+", "", s)


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


def replacements(repo, fix, path):
    """Removed lines of the fix, paired with what replaced them — same pairing as the pool scan."""
    diff = git(repo, ["diff", "%s~1" % fix, fix, "--", path]).splitlines()
    out, old, pending = [], 0, []
    for line in diff:
        m = re.match(r"^@@ -(\d+)", line)
        if m:
            old = int(m.group(1)); pending = []; continue
        if line.startswith("-") and not line.startswith("---"):
            if not NOISE.match(line):
                pending.append((old, line[1:]))
            old += 1
        elif line.startswith("+") and not line.startswith("+++"):
            if pending and not NOISE.match(line):
                n, b = pending.pop(0); out.append((n, b, line[1:]))
        elif line.startswith(" "):
            old += 1
    joined = nows("".join(a[1:] for a in diff
                          if a.startswith("+") and not a.startswith("+++")))
    return [r for r in out if nows(r[1]) not in joined]


ROW = re.compile(r"^  (\S{9}) (.{44})  <- (\S+) \((\d{4}-\d{2})-\d{2}\) (.{34}) (\d+) file")

repo = None
for line in open(sys.argv[1], encoding="utf-8"):
    head = re.match(r"^(\S+): \d+ qualifying", line)
    if head:
        repo = head.group(1)
        continue
    m = ROW.match(line)
    if not (m and repo):
        continue
    fix, subject, origin, date, osubject, nfiles = m.groups()
    src = [n for n in git(repo, ["show", "--name-only", "--format=", fix]).split()
           if n.endswith(".java") and "/test/" not in n]
    if not src:
        continue
    src = src[0]
    pairs = replacements(repo, fix, src)
    patch = git(repo, ["show", "--format=", origin, "--", src]).splitlines()
    added = {norm(l[1:]) for l in patch if l.startswith("+") and not l.startswith("+++")}
    verified = [(n, b, f) for n, b, f in pairs if norm(b) in added]
    size = sum(1 for l in patch if l[:1] in "+-" and not l.startswith(("+++", "---")))
    creates = not any(l.startswith("-") for l in patch if not l.startswith("---"))
    print("### %s | %s | %s | origin %s %s | %s files | %dL | %s"
          % (repo, fix, src.split("/")[-1], origin, date, nfiles.strip(), size,
             "NEW FILE" if creates else "modifies"))
    print("    path: %s" % src)
    print("    fix: %s" % subject.strip())
    print("    origin: %s" % osubject.strip())
    print("    VERIFIED %d/%d buggy line(s) appear as additions in the origin diff"
          % (len(verified), len(pairs)))
    for n, b, f in verified[:2]:
        print("      bug  %s" % norm(b)[:150])
        print("      fix  %s" % norm(f)[:150])
    print()
