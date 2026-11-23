"""The ranked queue. It orders attention; it does not decide."""

from rsquad.ranking import SEVERITY_ORDER, Entry, group, rank, render


def finding(file="a.py", line=10, severity="significant", lens="repro", kind="boundary"):
    return {"file": file, "line": line, "snippet": "premiere = fiches[0]", "kind": kind,
            "severity": severity, "inputs": "fiches = []", "consequence": "raises IndexError",
            "lens": lens}


# ------------------------------------------------------------------ grouping

def test_two_lenses_on_the_same_line_become_one_entry():
    entries = group([finding(lens="repro"), finding(lens="bounds")])
    assert len(entries) == 1
    assert entries[0].lenses == ["bounds", "repro"]
    assert entries[0].corroborated


def test_nearby_lines_are_the_same_defect():
    """Two lenses describing one defect rarely agree on the exact line."""
    assert len(group([finding(line=10), finding(line=12)])) == 1


def test_distant_lines_stay_separate():
    assert len(group([finding(line=10), finding(line=40)])) == 2


def test_the_same_line_in_different_files_stays_separate():
    assert len(group([finding(file="a.py"), finding(file="b.py")])) == 2


def test_an_entry_takes_the_worst_severity_reported_for_it():
    entry, = group([finding(severity="minor"), finding(severity="blocking")])
    assert entry.severity == "blocking"


def test_one_lens_reporting_twice_is_not_corroboration():
    """Agreement is only a signal because the lenses are blind to each other."""
    entry, = group([finding(lens="repro", line=10), finding(lens="repro", line=11)])
    assert entry.corroborated is False


# ------------------------------------------------------------------ ordering

def test_severity_orders_first():
    entries = group([finding(line=10, severity="minor"), finding(line=90, severity="blocking")])
    assert rank(entries)[0].severity == "blocking"


def test_agreement_breaks_ties_within_a_severity():
    entries = group([finding(line=10, lens="repro"),
                     finding(line=90, lens="repro"), finding(line=90, lens="bounds")])
    ranked = rank(entries)
    assert ranked[0].line == 90 and ranked[0].corroborated


def test_the_order_is_total_and_stable():
    """Same input, same order — a queue that reshuffles cannot be worked through."""
    entries = group([finding(line=n) for n in (10, 50, 90)])
    assert [e.line for e in rank(entries)] == [e.line for e in rank(list(reversed(entries)))]


# ------------------------------------------------------------------ rendering

def test_the_queue_says_severity_is_unverified():
    """Ranking implies confidence. The header has to say where that confidence comes from."""
    text = render(group([finding()]))
    assert "model's own claim" in text
    assert "not a verdict" in text


def test_an_empty_queue_says_so_without_apology():
    text = render([])
    assert "Nothing to report" in text
    assert "correct answer" in text


def test_dropped_findings_are_shown_not_hidden():
    """A silent drop reads as "nothing was there"; it is really a measurement of the lenses."""
    text = render(group([finding()]), dropped=[(finding(line=99), "snippet does not appear")])
    assert "Dropped by the guards (1)" in text
    assert "a.py:99" in text


def test_a_failed_lens_is_distinguished_from_a_quiet_one():
    text = render([], errors=["repro on a.py: timeout"])
    assert "did not say there was nothing" in text
    assert "timeout" in text


def test_corroboration_is_visible_in_the_entry_title():
    text = render(group([finding(lens="repro"), finding(lens="contract")]))
    assert "2 lenses agree" in text


def test_one_account_that_stood_settles_the_entry():
    """Two lenses, one defect: if one refuter confirmed it, the entry is not 'undecided'."""
    stood = dict(finding(lens="repro"), verdict="stands")
    doubted = dict(finding(lens="contract"), verdict="undecided")
    assert "could not decide" not in render(group([stood, doubted]), refuted=[])
    assert "could not decide" in render(group([doubted]), refuted=[])


def test_every_severity_has_a_rank():
    """A severity the schema allows but the ranker does not know would crash the queue."""
    from rsquad.findings import vocabulary
    assert set(vocabulary("severity")) == set(SEVERITY_ORDER)
