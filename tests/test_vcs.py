"""Git helpers. One test here guards against a trap git sets deliberately."""

import os
import subprocess

import pytest

from rsquad import vcs


def test_an_invalid_revision_is_refused_on_the_return_code(monkeypatch):
    """Not on the output. `git rev-parse nonsense` exits 128 — and echoes `nonsense` on stdout.

    So the obvious guard, `if not out.strip(): raise`, never fires. The caller sails on with
    the literal string as a revision, every later git call quietly matches nothing, and the
    tool reports a clean run against a revision that does not exist. Verified against git
    before this test was written; found by a lens on the source project's copy of the pattern,
    which this code had inherited.
    """
    def echoes_back(args, repo=None):
        return type("R", (), {"returncode": 128, "stdout": args[-1] + "\n", "stderr": "fatal"})()

    monkeypatch.setattr(vcs, "git", echoes_back)
    with pytest.raises(SystemExit):
        vcs.resolve("typo_that_does_not_exist")


def test_a_valid_revision_comes_back_stripped(monkeypatch):
    sha = "b404a9392d6f0000000000000000000000000000"
    monkeypatch.setattr(vcs, "git", lambda args, repo=None: type(
        "R", (), {"returncode": 0, "stdout": sha + "\n", "stderr": ""})())
    assert vcs.resolve("HEAD") == sha


def test_a_missing_file_reads_as_absent_not_empty(monkeypatch):
    """An empty file and a deleted file mean different things to every caller downstream."""
    monkeypatch.setattr(vcs, "git", lambda args, repo=None: type(
        "R", (), {"returncode": 128, "stdout": "", "stderr": "does not exist"})())
    assert vcs.file_at("head", "gone.py") is None


def _repo(tmp_path):
    """A real repository with one commit: `src/a.py` holding `x = 1`."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "Return None when the corpus is empty.")
    return repo


def _git(repo, *args, input=None):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo,
                          check=True, capture_output=True, text=True, input=input)


@pytest.mark.guard
def test_the_snapshot_holds_the_commit_and_nothing_beside_it(tmp_path):
    """ADR-0011. The readers search the tree at head: not the working copy's uncommitted files,
    and not `.git`, which holds the commit message the blind lenses must not be handed."""
    repo = _repo(tmp_path)
    (repo / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
    (repo / "scratch.txt").write_text("not committed\n", encoding="utf-8")

    vcs.snapshot("HEAD", tmp_path / "job" / "repo", repo)
    copy = tmp_path / "job" / "repo"
    assert (copy / "src" / "a.py").read_text(encoding="utf-8") == "x = 1\n"
    assert not (copy / "scratch.txt").exists()
    assert not (copy / ".git").exists()


@pytest.mark.guard
def test_a_revision_that_cannot_be_archived_stops_the_export(tmp_path):
    """Inside a real repository: outside one, any revision would fail and prove nothing."""
    repo = _repo(tmp_path)
    vcs.snapshot("HEAD", tmp_path / "ok", repo)                 # the same call succeeds on HEAD
    with pytest.raises(SystemExit, match="no-such-revision"):
        vcs.snapshot("no-such-revision", tmp_path / "out", repo)


def test_a_second_snapshot_holds_nothing_of_the_first(tmp_path):
    repo = _repo(tmp_path)
    vcs.snapshot("HEAD", tmp_path / "job" / "repo", repo)
    _git(repo, "rm", "-q", "src/a.py")
    (repo / "b.py").write_text("y = 2\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "Move it.")
    vcs.snapshot("HEAD", tmp_path / "job" / "repo", repo)
    copy = tmp_path / "job" / "repo"
    assert (copy / "b.py").exists() and not (copy / "src" / "a.py").exists()


def test_a_link_out_of_the_tree_is_left_out_not_fatal(tmp_path):
    """A reader must not follow a link out of the copy, and one link must not stop a review.
    The link is committed as a git symlink entry, so the test needs no symlink support."""
    repo = _repo(tmp_path)
    for name, target in (("out", "../../outside"), ("abs", "/etc/hosts")):
        blob = _git(repo, "hash-object", "-w", "--stdin", input=target).stdout.strip()
        _git(repo, "update-index", "--add", "--cacheinfo", "120000,%s,%s" % (blob, name))
    _git(repo, "commit", "-q", "-m", "Two links that leave the tree.")
    vcs.snapshot("HEAD", tmp_path / "job" / "repo", repo)
    copy = tmp_path / "job" / "repo"
    assert (copy / "src" / "a.py").exists()
    assert not os.path.lexists(copy / "out") and not os.path.lexists(copy / "abs")
