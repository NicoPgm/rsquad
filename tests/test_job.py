"""The harness transport. No network and no harness — the replies are written by hand.

The round trip is the test: whatever runs the tasks, everything that makes a finding
trustworthy happens on this side of the seam.
"""

import json

import pytest

from rsquad import job
from rsquad.chunking import Unit
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
           "severity": "blocking", "inputs": "fiches = []", "consequence": "raises IndexError"}

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
