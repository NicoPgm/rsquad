"""Prompt templates. Rendered from the schema, never written twice."""

import pytest

from rsquad.findings import glossary, vocabulary
from rsquad.prompts import (LENSES, lens_prompt, system_blocks, system_prompt, user_prompt,
                            version)


def test_every_lens_has_a_template():
    for lens in LENSES:
        assert lens_prompt(lens).strip()


def test_an_unknown_lens_is_refused():
    with pytest.raises(SystemExit):
        lens_prompt("style")


def test_the_system_prompt_carries_the_rendered_vocabulary():
    text = system_prompt()
    for name in ("kind", "severity"):
        for value, gloss in glossary(name).items():
            assert "`%s`" % value in text
            assert gloss in text


def test_no_template_leaves_a_placeholder_unrendered():
    """An unrendered `{{...}}` reaches the model as literal braces and quietly degrades it."""
    rendered = [system_prompt(), user_prompt("a.py", "diff", "1\tx")]
    rendered += [lens_prompt(lens) for lens in LENSES]
    for text in rendered:
        assert "{{" not in text


def test_a_missing_value_is_an_error_not_a_silent_gap():
    with pytest.raises(SystemExit):
        from rsquad.prompts import _load, _render, PROMPT_DIR
        _render(_load(PROMPT_DIR / "user.v1.md"), file="a.py")


def test_code_under_review_may_contain_placeholders_of_its_own():
    """Found at work: a file holding `{{HEAD}}` failed the export, so it was never reviewed."""
    code = 'url = "{{HEAD}}/{{DIFF}}"'
    text = user_prompt("a.py", diff=code, numbered="1\t" + code)
    assert text.count(code) == 2


def test_html_comments_are_stripped():
    """They are notes to whoever edits the file, not tokens anyone should pay for."""
    assert "<!--" not in system_prompt()
    assert "<!--" not in lens_prompt("repro")


def test_the_system_prompt_forbids_style_findings():
    """Left unsaid, every lens reports naming and import order and the queue becomes noise."""
    text = system_prompt().lower()
    assert "style" in text and "naming" in text


def test_the_system_prompt_asks_for_every_defect_not_the_surest():
    """ADR-0011. "An empty result is the usual answer" kept the lenses to one finding, or none,
    and on ReviewBench they covered a fifth of the golden findings."""
    text = " ".join(system_prompt().split())
    assert "Report every defect you find" in text
    assert "Keep reviewing after the first finding" in text
    assert "If you cannot name the inputs" not in text


def test_the_shared_block_comes_first_and_holds_the_breakpoint():
    blocks = system_blocks("repro")
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert blocks[0]["text"] == system_prompt()
    assert blocks[1]["text"] == lens_prompt("repro")


def test_the_user_prompt_places_the_unit_after_everything_cacheable():
    text = user_prompt("a.py", "@@ -1 +1 @@", "1\tx = 1")
    assert "a.py" in text and "@@ -1 +1 @@" in text and "1\tx = 1" in text


def test_the_elision_notice_is_optional():
    assert "not shown" not in user_prompt("a.py", "d", "n")
    assert "not shown" in user_prompt("a.py", "d", "n", elision="... lines not shown ...")


def test_the_version_is_read_per_mode():
    """`prompt_version` alone means nothing: v1 in one mode is not v1 in another."""
    assert version("api") == "v1"
    with pytest.raises(KeyError):
        version("local")
