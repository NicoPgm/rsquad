"""The corrected filter: where was the buggy line first written, and is that commit reviewable?

Not "is it a regression" -- a scan of ~70 qualifying fixes across two mature Java libraries
found none. Defects are born with the code far more often than they are introduced by breaking
working code, so requiring a regression empties the pool.

A first-write commit is usable when it is a normal change rather than a wholesale import, and
when it actually WROTE the line rather than moving it.
"""
import re, subprocess, sys

FIX = re.compile(r"\b(fix(e[sd])?|bug|incorrect|wrong|regression|npe|fails?|broken)\b", re.I)
ISSUE = re.compile(r"(#\d+|\b[A-Z]{2,}-\d+\b)")
MAX_FILES_IN_ORIGIN = 10
NOISE = re.compile(r"^[+-]\s*(//|\*|/\*|import\s|$)")

def git(repo, args):
    return subprocess.run(["git", "-C", repo] + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout

def nows(s):
    return re.sub(r"\s+", "", s)


def norm(s):
    return re.sub(r"\s+", " ", s.strip())

def removed(repo, fix, path):
    diff = git(repo, ["diff", "%s~1" % fix, fix, "--", path]).splitlines()
    out, old, pending = [], 0, []
    for line in diff:
        m = re.match(r"^@@ -(\d+)", line)
        if m:
            old = int(m.group(1)); pending = []; continue
        if line.startswith("-") and not line.startswith("---"):
            # **NOISE here too.** Without it, a fix that also adds an import pairs the import
            # against a removed code line, and the history traced is the IMPORT's -- so the
            # origin commit belongs to a line nobody cares about. Four of the first twelve
            # dossiers had an `import` as their buggy line before this filter was applied.
            if not NOISE.match(line):
                pending.append((old, line[1:]))
            old += 1
        elif line.startswith("+") and not line.startswith("+++"):
            if pending and not NOISE.match(line):
                out.append(pending.pop(0))
        elif line.startswith(" "):
            old += 1
    # **Reformatting is not a change.** These projects run a formatter inside fix commits, so a
    # removed line often reappears re-wrapped across two added lines. Pairing then traces the
    # history of a line that nobody edited. A removed line counts only if its content, stripped
    # of every space, does not survive in the concatenated additions.
    joined = nows("".join(a[1:] for a in diff
                          if a.startswith("+") and not a.startswith("+++")))
    return [r for r in out if nows(r[1]) not in joined]

def classify(repo, path, lineno, buggy, before):
    log = git(repo, ["log", "-L", "%d,%d:%s" % (lineno, lineno, path),
                     "--format=@@@%h|%ad|%s", "--date=short", before])
    commits = re.findall(r"@@@(\S+)\|(\S+)\|(.*)", log)
    if not commits:
        return None
    sha, date, subject = commits[-1]
    files = git(repo, ["show", "--format=", "--name-only", sha]).split()
    if len(files) > MAX_FILES_IN_ORIGIN:
        return ("mass-import", sha, date, subject, len(files))
    parent = git(repo, ["show", "%s~1:%s" % (sha, path)])
    if parent and any(norm(l) == norm(buggy) for l in parent.splitlines()):
        return ("moved", sha, date, subject, len(files))
    # **Path stability, checked instead of reconstructed.** `git log -L` follows renames, so the
    # origin is right while today's path may not have existed then -- Fraction.java was under
    # src/java/org/apache/commons/lang/ in 2002. A rename-walking resolver got some of those
    # right and some wrong. Requiring the path to resolve AT the origin is exact, conservative,
    # and needs no heuristic: if it does not, the case is dropped rather than guessed.
    import subprocess as sp
    if sp.run(["git", "-C", repo, "cat-file", "-e", "%s:%s" % (sha, path)],
              capture_output=True).returncode != 0:
        return ("renamed-since", sha, date, subject, len(files))
    changed = [l for l in git(repo, ["show", "--format=", sha, "--", path]).splitlines()
               if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    if not changed:
        return ("empty-diff", sha, date, subject, len(files))
    return ("usable", sha, date, subject, len(files))

def scan(repo):
    head = [l.strip() for l in git(repo, ["branch", "-r"]).splitlines() if "->" not in l][0]
    tally, pool = {}, []
    for fix in git(repo, ["log", head, "--since=2026-05-01", "--format=%H"]).split():
        msg = git(repo, ["log", "-1", "--format=%s%n%b", fix])
        if not (FIX.search(msg) and ISSUE.search(msg)):
            continue
        files = [n for n in git(repo, ["show", "--name-only", "--format=", fix]).split()
                 if n.endswith(".java")]
        src = [n for n in files if "/test/" not in n]
        tests = [n for n in files if "/test/" in n]
        if len(src) != 1 or not tests or len(files) > 6:
            continue
        # Rule 4, carried over: a Javadoc correction is not a defect. `pool.py` had dropped it,
        # and "Fix two Javadoc errors in StringUtils" was sitting in the pool as a case.
        patch = git(repo, ["show", "--format=", fix, "--", src[0]]).splitlines()
        if not [l for l in patch if l[:1] in "+-"
                and not l.startswith(("+++", "---")) and not NOISE.match(l)]:
            continue
        verdict = None
        for lineno, buggy in removed(repo, fix, src[0])[:4]:
            got = classify(repo, src[0], lineno, buggy, "%s~1" % fix)
            if got and got[0] == "usable":
                verdict = got; break
            verdict = verdict or got
        if verdict is None:
            tally["no-history"] = tally.get("no-history", 0) + 1
            continue
        tally[verdict[0]] = tally.get(verdict[0], 0) + 1
        if verdict[0] == "usable":
            pool.append((fix[:9], msg.splitlines()[0][:44], verdict, src[0]))
    return tally, pool

for repo in sys.argv[1:]:
    tally, pool = scan(repo)
    total = sum(tally.values())
    print("=" * 104)
    print("%s: %d qualifying fix(es) -> %s" % (repo, total, tally))
    for fix, subject, (_, sha, date, subj, nfiles), path in pool:
        print("  %s %-44s  <- %s (%s) %-34s %d file(s)"
              % (fix, subject, sha, date, subj[:34], nfiles))
