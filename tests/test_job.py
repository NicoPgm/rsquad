"""The harness transport. No network and no harness — the replies are written by hand.

The round trip is the test: whatever runs the tasks, everything that makes a finding
trustworthy happens on this side of the seam.
"""

import json

import pytest

from rsquad import job
from rsquad.chunking import Unit
from rsquad.context import Definition
from rsquad.conformance import Intent

UNIT = Unit(
    file="src/a.py",
    diff="@@ -1,2 +1,3 @@\n+    return fiches[0]\n",
    source="def resume(fiches):\n    return fiches[0]\n",
    numbered="1\tdef resume(fiches):\n2\t    return fiches[0]",
)
UNITS = {UNIT.file: UNIT}
INTENT = Intent(parts=[("commit message", "Return None when the corpus is empty.")])

FINDING = {"file": "src/a.py", "line": 2, "snippet": "return fiches[0]", "kind": "boundary",
           "severity": "blocking", "scope": "introduced", "inputs": "fiches = []", "consequence": "raises IndexError"}

META = {"base": "b", "head": "h", "repo": ".", "specs": [], "model": "claude-opus-5"}


def _export(tmp_path, lenses=("repro",), intent=None):
    tasks = job.lens_tasks([UNIT], list(lenses), intent)
    job.export(tmp_path, tasks, META)
    return tasks


def _answer(tmp_path, task_id, payload, round_number=1):
    path = tmp_path / ("round-%d" % round_number) / "results" / ("%s.json" % task_id)
    path.write_text(json.dumps(payload), encoding="utf-8")


# ------------------------------------------------------------------ what crosses the seam

def test_a_task_carries_the_whole_instruction(tmp_path):
    """The harness gets an agent one prompt, so system and user are already joined."""
    tasks = _export(tmp_path)
    text = (tmp_path / "round-1" / "tasks" / ("%s.md" % tasks[0].id)).read_text(encoding="utf-8")
    assert "return fiches[0]" in text          # the unit
    assert "Reproduction or nothing" not in text or "reproduction" in text.lower()
    assert "{{" not in text                     # fully rendered before it left


@pytest.mark.guard
def test_a_task_carries_the_code_it_anchors_to(tmp_path):
    """The repository is there to search (ADR-0011), not to replace the payload.

    The code under review is inline, and so is every definition of the context pack: a finding
    is anchored in the numbered text the task carries, and a reader sent to the checkout for it
    could quote a line that is not the one under review.
    """
    definition = Definition(symbol="load", file="src/other.py", line=40,
                            source="def load(path):\n    return open(path).read()")
    unit = Unit(file=UNIT.file, diff=UNIT.diff, source=UNIT.source, numbered=UNIT.numbered,
                context=[definition])
    tasks = job.lens_tasks([unit], ["repro"], INTENT)
    job.export(tmp_path, tasks, META)
    for task in tasks:
        text = (tmp_path / "round-1" / "tasks" / ("%s.md" % task.id)).read_text(encoding="utf-8")
        assert unit.numbered in text                     # the code, not a path to it
        assert "def load(path):" in text                 # the pack quotes, never cites
        assert unit.diff in text


def test_the_schema_crosses_too(tmp_path):
    """A harness that can force it should; one that cannot is caught at ingest instead."""
    _export(tmp_path)
    schema = json.loads((tmp_path / "schema" / "finding.json").read_text(encoding="utf-8"))
    assert schema["$defs"]["kind"]["enum"]
    assert "glossary" not in json.dumps(schema)


def test_the_blind_tasks_carry_no_intent(tmp_path):
    """Blindness is a property of the payload (ADR-0002), and the payload is now a file.

    A transport that leaked the intent into the blind tasks would undo the architecture
    without touching a line of `lenses.py`.
    """
    tasks = _export(tmp_path, lenses=("repro", "bounds"), intent=INTENT)
    for task in tasks:
        text = (tmp_path / "round-1" / "tasks" / ("%s.md" % task.id)).read_text(encoding="utf-8")
        if task.lens == "conformance":
            assert "Return None when the corpus is empty." in text
        else:
            assert "Return None when the corpus is empty." not in text


# ------------------------------------------------------------------ nothing is trusted back

def test_a_reply_that_ignores_the_schema_is_dropped(tmp_path):
    """The constraint moves from generation time to ingest time; it does not disappear."""
    tasks = _export(tmp_path)
    _answer(tmp_path, tasks[0].id, {"findings": [dict(FINDING, kind="style")]})
    result = job.ingest(tmp_path, UNITS, INTENT)
    assert result.findings == []
    assert result.malformed and "ValidationError" in result.malformed[0][1]


def test_a_hallucinated_snippet_is_dropped_here_too(tmp_path):
    tasks = _export(tmp_path)
    _answer(tmp_path, tasks[0].id, {"findings": [dict(FINDING, snippet="fiches.first()")]})
    result = job.ingest(tmp_path, UNITS, INTENT)
    assert result.findings == [] and len(result.dropped) == 1


def test_a_missing_reply_is_reported_not_read_as_silence(tmp_path):
    """Saying nothing and being unable to speak look identical in a queue, and only one of
    them means the code is fine."""
    _export(tmp_path)
    result = job.ingest(tmp_path, UNITS, INTENT)
    assert result.missing and result.findings == []
    assert "no reply from the harness" in job.queue(result)


def test_prose_instead_of_json_shows_up_as_a_number(tmp_path):
    tasks = _export(tmp_path)
    path = tmp_path / "round-1" / "results" / ("%s.json" % tasks[0].id)
    path.write_text("Sure! Here are the findings I found:", encoding="utf-8")
    result = job.ingest(tmp_path, UNITS, INTENT)
    assert result.malformed and result.findings == []


# ------------------------------------------------------------------ two rounds

def test_ingesting_round_one_yields_a_refutation_round(tmp_path):
    """A refuter needs a finding, so it cannot be exported alongside the lenses."""
    tasks = _export(tmp_path)
    _answer(tmp_path, tasks[0].id, {"findings": [FINDING]})
    result = job.ingest(tmp_path, UNITS, INTENT)
    assert len(result.findings) == 1

    second = job.refutation_tasks(result.findings, UNITS)
    job.export(tmp_path, second, META, round_number=job.REFUTE_ROUND)
    assert job.manifest(tmp_path)["round"] == job.REFUTE_ROUND
    assert (tmp_path / "round-2" / "tasks" / ("%s.md" % second[0].id)).exists()


def test_a_refutation_reply_still_has_to_anchor_its_evidence(tmp_path):
    tasks = job.refutation_tasks([dict(FINDING, lens="repro")], UNITS)
    job.export(tmp_path, tasks, META, round_number=job.REFUTE_ROUND)
    _answer(tmp_path, tasks[0].id,
            {"verdict": "misread", "reason": "no", "evidence_line": 2,
             "evidence_snippet": "return fiches.first()"}, round_number=2)
    result = job.ingest(tmp_path, UNITS, INTENT)
    assert result.verdicts[0].refutes is False


def test_a_conformance_finding_gets_no_refutation_task():
    """ADR-0007: no refuter exists for that claim shape, on either transport."""
    mismatch = {"file": "src/a.py", "line": 2, "snippet": "return fiches[0]",
                "requirement": "Return None when the corpus is empty.",
                "mismatch": "it indexes", "kind": "unimplemented", "severity": "minor"}
    assert job.refutation_tasks([mismatch], UNITS) == []


# ------------------------------------------------------------------ the manifest

def test_a_job_from_another_version_is_refused(tmp_path):
    _export(tmp_path)
    path = tmp_path / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(dict(data, version=999)), encoding="utf-8")
    with pytest.raises(SystemExit):
        job.manifest(tmp_path)


def test_the_manifest_records_what_the_units_were_built_from(tmp_path):
    """Units are recomputed at ingest rather than carried. They are a pure function of
    (base, head, repo), so recomputing is also a check: if the revisions moved under the job,
    the anchors stop matching and the guards say so."""
    _export(tmp_path)
    data = job.manifest(tmp_path)
    assert data["base"] == "b" and data["head"] == "h"


def test_the_manifest_carries_no_prompt(tmp_path):
    """The prompts are on disk once. A second copy in the manifest would be the stale one."""
    _export(tmp_path)
    assert "prompt" not in json.dumps(job.manifest(tmp_path))


def test_a_finding_with_no_refuter_still_reaches_the_queue(tmp_path):
    """It fell off the edge of the round, and the missing one was the only conformance account.

    On the API path `refute_all` emits a "no refuter for this claim shape" verdict and the
    finding survives. Across a job boundary there is no memory: round 2's manifest holds only
    what it asked for. Nine findings in, eight in the queue, found by running it end to end.
    """
    mismatch = {"file": "src/a.py", "line": 2, "snippet": "return fiches[0]",
                "requirement": "Return None when the corpus is empty.",
                "mismatch": "it indexes", "kind": "unimplemented", "severity": "minor",
                "lens": "conformance"}
    tasks = job.refutation_tasks([FINDING, mismatch], UNITS)
    riding = job.carried([FINDING, mismatch], UNITS)
    assert len(tasks) == 1 and riding == [mismatch]

    job.export(tmp_path, tasks, dict(META, carried=riding), round_number=job.REFUTE_ROUND)
    _answer(tmp_path, tasks[0].id,
            {"verdict": "stands", "reason": "holds", "evidence_line": 2,
             "evidence_snippet": "return fiches[0]"}, round_number=2)

    result = job.ingest(tmp_path, UNITS, INTENT)
    text = job.queue(result)
    assert len(result.verdicts) == 2
    assert "**Requirement**" in text, "the conformance account vanished between rounds"


def test_extra_meta_rides_in_the_manifest(tmp_path):
    """`evaluate --export` records the reviewed path there, and `--ingest` rebuilds the unit
    from it. Without that the review is one file and the ingest is the whole commit, and the
    two stop lining up — silently, since both halves succeed."""
    tasks = _export(tmp_path)
    job.export(tmp_path, tasks, dict(META, path="src/a.py", case="some-case"))
    data = job.manifest(tmp_path)
    assert data["path"] == "src/a.py" and data["case"] == "some-case"


# ------------------------------------------------------------------ routing and models (ADR-0009)

TEST_UNIT = Unit(file="tests/test_a.py", diff="@@ -1 +1 @@\n+    assert resume([]) is None\n",
                 source="def test_empty():\n    assert resume([]) is None\n",
                 numbered="1\tdef test_empty():\n2\t    assert resume([]) is None")
OTHER_UNIT = Unit(file="src/b.py", diff="@@ -1,2 +1,2 @@\n+    return rows[-1]\n",
                  source="def last(rows):\n    return rows[-1]\n",
                  numbered="1\tdef last(rows):\n2\t    return rows[-1]")


@pytest.mark.guard
def test_lens_tasks_are_routed_by_file_kind():
    tasks = {t.lens: t for t in job.lens_tasks([UNIT, TEST_UNIT], ["repro", "tests"])}
    assert "`src/a.py`" in tasks["repro"].prompt and "`tests/test_a.py`" not in tasks["repro"].prompt
    assert "`tests/test_a.py`" in tasks["tests"].prompt and "`src/a.py`" not in tasks["tests"].prompt


def test_a_lens_reads_the_whole_change_in_one_task_on_one_model():
    """ADR-0011: one task per lens over every file it reads, so a defect spanning files is
    visible. One pass: a second, on another model, added two golden findings out of 21."""
    tasks = job.lens_tasks([UNIT, OTHER_UNIT], ["repro"], model="claude-opus-5")
    assert [(t.id, t.file, t.model) for t in tasks] == [("repro--PR", job.WHOLE, "claude-opus-5")]
    assert UNIT.numbered in tasks[0].prompt and OTHER_UNIT.numbered in tasks[0].prompt
    assert "repo/" in tasks[0].prompt


def test_a_whole_change_reply_is_anchored_file_by_file(tmp_path):
    """Each finding is held to the file it names. One that quotes code from another file of the
    change, or names a file outside it, is dropped by the guard, not trusted."""
    units = {UNIT.file: UNIT, OTHER_UNIT.file: OTHER_UNIT}
    tasks = job.lens_tasks(list(units.values()), ["repro"])
    job.export(tmp_path, tasks, META)
    elsewhere = dict(FINDING, file="src/b.py", line=2, snippet="return rows[-1]")
    misplaced = dict(FINDING, file="src/b.py")                # a.py's line, b.py's name
    outside = dict(FINDING, file="src/c.py")
    _answer(tmp_path, "repro--PR", {"findings": [FINDING, elsewhere, misplaced, outside]})
    result = job.ingest(tmp_path, units)
    assert sorted((f["file"], f["line"]) for f in result.findings) == [("src/a.py", 2),
                                                                      ("src/b.py", 2)]
    assert len(result.dropped) == 2 and not result.malformed


def test_a_lens_finding_counts_only_in_the_files_that_lens_was_shown(tmp_path):
    """The lens can read every file in `repo/`; it is under review only in its own. A blind lens
    reporting in a test file is what the routing by file kind keeps out."""
    test_unit = Unit(file="tests/test_a.py", diff="@@ -0,0 +1 @@\n+assert resume([1]) == 1\n",
                     source="assert resume([1]) == 1\n", numbered="1\tassert resume([1]) == 1")
    units = {UNIT.file: UNIT, test_unit.file: test_unit}
    job.export(tmp_path, job.lens_tasks(list(units.values()), ["repro"]), META)
    in_a_test = dict(FINDING, file="tests/test_a.py", line=1, snippet="assert resume([1]) == 1")
    _answer(tmp_path, "repro--PR", {"findings": [FINDING, in_a_test]})
    result = job.ingest(tmp_path, units)
    assert [f["file"] for f in result.findings] == ["src/a.py"]
    assert len(result.dropped) == 1


def test_a_file_named_like_the_whole_change_still_gets_its_conformance(tmp_path):
    """`*` is a legal file name on POSIX. Its conformance reply must not be read as a lens's.
    The task keeps a name Windows can write; only the file it reviews is `*`."""
    star = Unit(file="*", diff=UNIT.diff, source=UNIT.source, numbered=UNIT.numbered)
    task = job.Task(id="conformance--star", contract="conformance", lens="conformance",
                    file="*", prompt="")
    job.export(tmp_path, [task], META)
    mismatch = {"file": "*", "line": 2, "snippet": "return fiches[0]",
                "requirement": "Return None when the corpus is empty.",
                "mismatch": "it indexes", "kind": "unimplemented", "severity": "minor"}
    _answer(tmp_path, task.id, {"findings": [mismatch]})
    result = job.ingest(tmp_path, {"*": star}, INTENT)
    assert result.malformed == [] and [f["file"] for f in result.findings] == ["*"]


def test_every_task_names_its_model_in_the_manifest(tmp_path):
    """The driver reads the model per task: lenses on one tier, the refuter on another."""
    job.export(tmp_path, job.lens_tasks([UNIT], ["repro"], model="claude-sonnet-5"), META)
    first = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert [t["model"] for t in first["tasks"]] == ["claude-sonnet-5"]

    job.export(tmp_path, job.refutation_tasks([FINDING], UNITS, "claude-opus-5"), META,
               round_number=job.REFUTE_ROUND)
    second = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert [t["model"] for t in second["tasks"]] == ["claude-opus-5"]


@pytest.mark.guard
def test_the_queue_names_what_no_lens_read(tmp_path):
    tasks = _export(tmp_path)
    _answer(tmp_path, tasks[0].id, {"findings": []})
    result = job.ingest(tmp_path, UNITS)
    assert result.missing == []
    text = job.queue(result, excluded=[("docs/a.md", "documentation")])
    assert "## Not reviewed (1)" in text
    assert "`docs/a.md` — documentation" in text


def test_the_queue_marks_a_finding_the_refuter_could_not_decide(tmp_path):
    """Doubt lets a finding through (ADR-0011); the reader must still see that it was doubt."""
    tasks = _export(tmp_path)
    _answer(tmp_path, tasks[0].id, {"findings": [FINDING]})
    first = job.ingest(tmp_path, UNITS)
    job.export(tmp_path, job.refutation_tasks(first.findings, UNITS), META,
               round_number=job.REFUTE_ROUND)
    _answer(tmp_path, "refute--0001",
            {"verdict": "undecided", "reason": "nothing here shows whether fiches can be empty",
             "evidence_line": 2, "evidence_snippet": "return fiches[0]"}, round_number=2)
    text = job.queue(job.ingest(tmp_path, UNITS))
    assert "`src/a.py:2`" in text and "the refuter could not decide" in text


# ------------------------------------------------------------------ outside the change

DELETE = "class DeleteNote:\n    def execute(self, model):\n        return 'Deleted'\n"
STUB = dict(FINDING, file="src/delete.py", line=3, snippet="return 'Deleted'", scope="exposed",
            inputs="note d-/2026-03-24 after a note on that date",
            consequence="the note survives the reported deletion")


def _repository(tmp_path):
    (tmp_path / job.REPOSITORY / "src").mkdir(parents=True)
    (tmp_path / job.REPOSITORY / "src" / "delete.py").write_text(DELETE, encoding="utf-8")


def test_a_defect_outside_the_change_reaches_the_queue_through_its_refuter(tmp_path):
    """The pull request made an untouched command reachable; the defect lives in that command.
    It anchors against the copy in `repo/`, gets a refuter, and stands in the queue."""
    _repository(tmp_path)
    tasks = _export(tmp_path)
    _answer(tmp_path, tasks[0].id, {"findings": [FINDING, STUB]})
    first = job.ingest(tmp_path, UNITS)
    assert sorted(f["file"] for f in first.findings) == ["src/a.py", "src/delete.py"]

    second = job.refutation_tasks(first.findings, first.units)
    job.export(tmp_path, second, META, round_number=job.REFUTE_ROUND)
    assert len(second) == 2
    stub_task = next(t for t in second if t.file == "src/delete.py")
    prompt = (tmp_path / "round-2" / "tasks" / ("%s.md" % stub_task.id)).read_text(
        encoding="utf-8")
    assert "the change does not touch this file" in prompt
    _answer(tmp_path, stub_task.id,
            {"verdict": "stands", "reason": "execute never touches the model",
             "evidence_line": 3, "evidence_snippet": "return 'Deleted'"}, round_number=2)
    result = job.ingest(tmp_path, UNITS)
    assert result.malformed == []
    assert "`src/delete.py:3`" in job.queue(result)


def test_a_defect_outside_the_change_cannot_be_introduced_by_it(tmp_path):
    _repository(tmp_path)
    tasks = _export(tmp_path)
    _answer(tmp_path, tasks[0].id, {"findings": [dict(STUB, scope="introduced")]})
    result = job.ingest(tmp_path, UNITS)
    assert result.findings == []
    assert [reason for _, reason in result.dropped] == [
        "says introduced, in a file the change does not touch"]


@pytest.mark.guard
def test_outside_the_change_the_routing_still_holds(tmp_path):
    """A blind lens may not report in an untouched test file any more than in a changed one."""
    (tmp_path / job.REPOSITORY / "tests").mkdir(parents=True)
    (tmp_path / job.REPOSITORY / "tests" / "test_a.py").write_text("assert True\n",
                                                                  encoding="utf-8")
    tasks = _export(tmp_path)
    in_a_test = dict(STUB, file="tests/test_a.py", line=1, snippet="assert True")
    _answer(tmp_path, tasks[0].id, {"findings": [in_a_test]})
    assert job.ingest(tmp_path, UNITS).findings == []


def test_a_path_that_leaves_the_copy_anchors_nothing(tmp_path):
    _repository(tmp_path)
    (tmp_path / "secret.py").write_text("return 'Deleted'\n", encoding="utf-8")
    assert job.outside_unit(tmp_path / job.REPOSITORY, "../secret.py") is None
    assert job.outside_unit(tmp_path / job.REPOSITORY, "src/delete.py").diff == ""


# ------------------------------------------------------------------ documentation (ADR-0013)

README = Unit(file="README.md", diff="@@ -1 +1 @@\n+Run `resume --all`.\n",
              source="Run `resume --all`.\n", numbered="1\tRun `resume --all`.")


def test_the_docs_lens_is_shown_the_code_and_runs_without_a_changed_document():
    """Documentation goes stale when the code moves, and the code is where that shows."""
    tasks = job.lens_tasks([UNIT], ["docs"])
    assert [t.id for t in tasks] == ["docs--PR"]
    assert "return fiches[0]" in tasks[0].prompt


def test_documentation_gets_no_conformance_task():
    tasks = job.lens_tasks([UNIT, README], [], INTENT)
    assert [t.file for t in tasks] == ["src/a.py"]


def test_a_stale_document_outside_the_change_reaches_the_queue(tmp_path):
    (tmp_path / job.REPOSITORY).mkdir()
    (tmp_path / job.REPOSITORY / "GUIDE.md").write_text("Call `resume` on any list.\n",
                                                        encoding="utf-8")
    job.export(tmp_path, job.lens_tasks([UNIT], ["docs"]), META)
    stale = {"file": "GUIDE.md", "line": 1, "snippet": "Call `resume` on any list.",
             "kind": "documentation", "severity": "minor", "scope": "exposed",
             "inputs": "a reader calls resume on an empty list, as the guide allows",
             "consequence": "IndexError"}
    _answer(tmp_path, "docs--PR", {"findings": [stale, FINDING]})       # FINDING is in code
    result = job.ingest(tmp_path, UNITS)
    assert [f["file"] for f in result.findings] == ["GUIDE.md"]
