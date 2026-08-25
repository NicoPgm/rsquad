"""Question 6 for Java — the context pack every Java review so far went without.

No git, no network, no JDK. Two things are pinned: what the resolver reaches (imports and the
file's own package, never a directory), and what a definition looks like once it gets there — a
skeleton, with short bodies kept because a getter's body is evidence and its signature is not.
"""

from rsquad.gate.adapters.base import StackAdapter
from rsquad.gate.adapters.java import (JavaContext, MAX_BODY_LINES, _clean, _imports,
                                       _referenced, skeleton)

RESOLVER = JavaContext()

STORE = """package dev.example.store;

import java.util.List;
import dev.example.filter.Filter;
import dev.example.filter.comparison.*;

import static dev.example.util.Guards.ensureBetween;

/** A store. */
public class EmbeddingStore {

    private final Filter filter;

    public List<String> search(double minScore) {
        ensureBetween(minScore, 0.0, 1.0, "minScore");
        return new IsEqualTo(filter).apply();
    }
}
"""

FILTER = """package dev.example.filter;

public interface Filter {
    boolean test(Object value);
}
"""

IS_EQUAL_TO = """package dev.example.filter.comparison;

public class IsEqualTo implements Filter {
    private final String key;

    public IsEqualTo(String key) {
        this.key = key;
    }

    public boolean test(Object value) {
        return key.equals(value);
    }
}
"""

GUARDS = """package dev.example.util;

public class Guards {
    public static double ensureBetween(double v, double lo, double hi, String name) {
        return v;
    }
}
"""

NEIGHBOUR = """package dev.example.store;

public class SearchRequest {
    private final int maxResults;
}
"""

TRACKED = ["src/main/java/dev/example/store/EmbeddingStore.java",
           "src/main/java/dev/example/store/SearchRequest.java",
           "src/main/java/dev/example/filter/Filter.java",
           "src/main/java/dev/example/filter/comparison/IsEqualTo.java",
           "src/main/java/dev/example/util/Guards.java"]

SOURCES = {"src/main/java/dev/example/filter/Filter.java": FILTER,
           "src/main/java/dev/example/filter/comparison/IsEqualTo.java": IS_EQUAL_TO,
           "src/main/java/dev/example/util/Guards.java": GUARDS,
           "src/main/java/dev/example/store/SearchRequest.java": NEIGHBOUR}

UNDER_REVIEW = "src/main/java/dev/example/store/EmbeddingStore.java"


def _stub(monkeypatch, sources=None):
    monkeypatch.setattr(StackAdapter, "file_at",
                        staticmethod(lambda rev, path, repo=None:
                                     (sources or SOURCES).get(path)))


def _resolve(monkeypatch, ranges, source=STORE, path=UNDER_REVIEW, tracked=None):
    _stub(monkeypatch)
    return RESOLVER.resolve_context(path, source, ranges, "head", None,
                                    tracked if tracked is not None else TRACKED)


# ------------------------------------------------------------------ what it reaches

def test_an_explicitly_imported_type_resolves(monkeypatch):
    found = _resolve(monkeypatch, [(12, 12)])   # the field declaration, whose type is imported
    assert "Filter" in [d.symbol for d in found]


def test_a_wildcard_import_resolves(monkeypatch):
    """`import dev.example.filter.comparison.*` is how half of Java names its neighbours."""
    found = _resolve(monkeypatch, [(14, 17)])
    assert "IsEqualTo" in [d.symbol for d in found]


def test_a_static_import_reaches_the_type_that_declares_the_member(monkeypatch):
    """`ensureBetween` is lowercase and names no type. The import says which one declares it."""
    found = _resolve(monkeypatch, [(14, 17)])
    assert "Guards" in [d.symbol for d in found]


def test_the_jdk_is_skipped_because_it_is_not_tracked(monkeypatch):
    found = _resolve(monkeypatch, [(14, 17)])
    assert all(d.symbol != "List" for d in found)


def test_a_same_package_type_resolves_without_an_import(monkeypatch):
    """Java needs no import for a sibling, so a resolver that only reads imports is blind."""
    source = STORE.replace("return new IsEqualTo(filter).apply();",
                           "return new SearchRequest().all();")
    found = _resolve(monkeypatch, [(14, 17)], source=source)
    assert "SearchRequest" in [d.symbol for d in found]


def test_a_type_named_outside_the_changed_lines_is_not_reached(monkeypatch):
    """Symbol-driven means the *changed* lines. Otherwise it is a file-driven pack."""
    found = _resolve(monkeypatch, [(11, 11)])
    assert [d.symbol for d in found] == []


def test_the_file_under_review_never_appears_in_its_own_pack(monkeypatch):
    found = _resolve(monkeypatch, [(10, 17)])
    assert all(d.file != UNDER_REVIEW for d in found)


def test_a_reference_the_repository_does_not_track_resolves_to_nothing(monkeypatch):
    found = _resolve(monkeypatch, [(14, 17)], tracked=[UNDER_REVIEW])
    assert found == []


def test_the_order_is_deterministic_and_is_not_a_ranking(monkeypatch):
    found = _resolve(monkeypatch, [(10, 17)])
    assert [d.file for d in found] == sorted(d.file for d in found)
    assert _resolve(monkeypatch, [(10, 17)]) == found


# ------------------------------------------------------------------ what a definition is

def test_a_definition_is_a_skeleton_with_every_member(monkeypatch):
    line, text = skeleton(IS_EQUAL_TO, "IsEqualTo")
    assert line == 3
    assert "public class IsEqualTo implements Filter {" in text
    assert "private final String key;" in text
    assert "public boolean test(Object value) {" in text


def test_a_short_body_is_kept_because_it_is_the_evidence():
    """"Nothing ever populates this field" is unprovable from a signature."""
    _, text = skeleton(IS_EQUAL_TO, "IsEqualTo")
    assert "return key.equals(value);" in text


def test_a_long_body_is_collapsed():
    long_method = ("public class Big {\n    public void run() {\n"
                   + "        step();\n" * (MAX_BODY_LINES + 4) + "    }\n}\n")
    _, text = skeleton(long_method, "Big")
    assert "{ ... }" in text
    assert "step();" not in text


def test_javadoc_is_dropped_so_the_pack_is_shape_not_prose():
    documented = "/** Long prose about the type. */\npublic class Doc {\n    int x;\n}\n"
    _, text = skeleton(documented, "Doc")
    assert "Long prose" not in text


def test_an_annotation_above_the_declaration_is_kept():
    annotated = "@Deprecated\npublic class Old {\n    int x;\n}\n"
    line, text = skeleton(annotated, "Old")
    assert line == 1 and text.startswith("@Deprecated")


def test_a_brace_inside_a_string_does_not_close_the_type():
    """The masked copy exists for this. A `"}"` would otherwise end the class early."""
    tricky = 'public class S {\n    String s = "}";\n    int after;\n}\n'
    _, text = skeleton(tricky, "S")
    assert "int after;" in text
    assert '"}"' in text


def test_an_array_initializer_is_not_mistaken_for_a_body():
    arrays = "public class A {\n    int[] limits = {1, 2};\n    int after;\n}\n"
    _, text = skeleton(arrays, "A")
    assert "int after;" in text
    assert "{ ... }" not in text


def test_an_enum_without_a_semicolon_still_lists_its_constants():
    enumeration = "public enum Kind {\n    ONE,\n    TWO\n}\n"
    _, text = skeleton(enumeration, "Kind")
    assert "ONE," in text and "TWO" in text


def test_a_type_that_is_not_in_the_file_yields_nothing():
    assert skeleton(FILTER, "Absent") is None


# ------------------------------------------------------------------ the scanners

def test_comments_are_blanked_in_place_so_offsets_still_line_up():
    stripped, masked = _clean(STORE)
    assert len(stripped) == len(STORE) == len(masked)
    assert stripped.count("\n") == STORE.count("\n")
    assert "A store." not in stripped


def test_a_commented_out_import_is_not_an_import():
    types, packages, members = _imports(_clean("// import dev.example.Gone;\n")[1])
    assert types == {} and packages == [] and members == {}


def test_a_type_named_only_in_a_comment_is_not_referenced():
    source = "package p;\n\npublic class C {\n    // uses Filter here\n    int x;\n}\n"
    _, masked = _clean(source)
    assert _referenced(masked, [(4, 4)], _imports(masked), "p", "p/C.java") == []
