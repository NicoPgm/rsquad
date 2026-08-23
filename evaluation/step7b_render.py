"""Render the frozen pre-registration from the case data plus the labels assigned by hand."""
import json

LABELS = {
 1: ("weak", "The guard ties two unrelated concerns: whether the index is created or updated, and "
             "which name identifies it. A supplied `index` object has its name ignored under a flag "
             "about creation. The smell fits in six lines; confirming it needs to know that supplying "
             "an index without creating it is a supported path, which the file does not state."),
 2: ("yes",  "Two writers to one Struct.Builder inside the diff: the segment text under "
             "`metadataTextKey`, then a loop putting arbitrary metadata keys into the same builder. "
             "A metadata key equal to metadataTextKey overwrites the text. Nothing outside the file "
             "is needed."),
 3: ("yes",  "`state.replaceAll(this::readStateBlocking)` mutates the map through a function that "
             "blocks on pending async writes to that same map. Both the call and `readStateBlocking` "
             "are in the file, so the hazard is reachable without leaving it."),
 4: ("weak", "An unchecked `(float[][])` cast of a generic `getValue()` is visible as a cast nobody "
             "guards. Knowing that some ONNX scoring models emit a 3D tensor is domain knowledge the "
             "file does not carry."),
 5: ("weak", "`extractReferenceKey(...)` flows straight into the builder with no null check, and that "
             "method is in the same class. What makes it a defect — that MCP permits a `$ref` outside "
             "`$defs` — is not in the file."),
 6: ("weak", "The new constructor delegates a long positional argument list built from `builder.*`, "
             "and one field is missing from it. The builder's fields are enumerable in the same file, "
             "so it is findable in principle — but it is an omission with no anchor to quote, inside "
             "292 changed lines."),
 7: ("yes",  "`allAgents()` returns the internal `mergedAgents` map directly. An accessor handing out "
             "mutable internal state is a contradiction in place; the field and the accessor are both "
             "in the diff."),
 8: ("weak", "`pageContent.getBytes()` with no charset, feeding a parser. The call is visible; that "
             "the platform default varies is a Java convention the file does not state."),
 9: ("yes",  "`new RuntimeException(\"Failed to load document from GitHub: {}\", ioException)` uses an "
             "SLF4J placeholder in an exception message, which is never substituted — and two lines "
             "below, the sibling `IllegalArgumentException` builds its message by concatenation. The "
             "diff contradicts itself."),
 10: ("weak", "Identical to case 8 in another loader: `pageContent.getBytes()` with no charset."),
 11: ("yes",  "`response.body().getBytes(StandardCharsets.UTF_8)` then Base64 — a file download routed "
              "bytes → String → bytes. The comment above says \"Convert response body to Base64\", and "
              "the surrounding method downloads a file, so the lossy round trip is visible in place."),
 12: ("weak", "`URI.create(result.getLink())` inside a stream over external search results, with no "
              "guard. The unguarded call is visible; that `URI.create` throws rather than returning "
              "null is an API contract outside the file."),
 13: ("no",   "The type chain handles String, Boolean, Integer and Long and throws otherwise, and the "
              "error message enumerates exactly that set. The code is self-consistent: nothing in the "
              "diff says Float and Double ought to be supported."),
 14: ("weak", "`text.lastIndexOf(' ')` where a word separator is meant, in a method named "
              "`unanimousLastWord`. The narrowing to one whitespace character is visible; that the "
              "inputs contain other whitespace is not in the file."),
 15: ("weak", "`isTerminalState(...)` gates an unconditional `complete(...)`, so a terminal state is "
              "treated as a successful one. The conflation is visible; that FAILED is terminal lives "
              "in an enum outside the file."),
 16: ("no",   "The arguments are swapped in a constructor call. The call site reads plausibly and the "
              "parameter order lives in `AzureBlobStorageSource`, another file — which the Java "
              "adapter cannot resolve into a context pack. Nothing in the diff distinguishes it from "
              "a correct call."),
 17: ("weak", "An if / else-if chain over `entry.embedded` covering TextSegment and null, with the "
              "general case unhandled. The exhaustiveness gap is visible; what the fallthrough then "
              "returns decides whether it is a defect."),
 18: ("weak", "`Flux.create(sink -> ...subscribe(...))` starts an async subscription and registers no "
              "dispose or cancel hook. The pattern is visible; that `Flux.create` requires one to "
              "avoid leaking is a Reactor contract outside the file."),
 19: ("no",   "Rejecting {MINIMAL, MEDIUM} while the message says the supported levels are LOW and "
              "HIGH is internally consistent. That MEDIUM is in fact supported is a fact about the "
              "model, not about the code."),
 20: ("no",   "The fix merges streaming tool-call deltas by index; the defect is that no index is "
              "used. An omission with no anchor, inside 389 changed lines, and knowing the delta type "
              "exposes an index requires the type."),
 21: ("no",   "The origin adds a null assertion on `hit.source()`, which reads as a correct hardening. "
              "Nothing in the diff reveals the deserialization problem the fix addresses."),
 22: ("weak", "A `Map<String, Object>` round-tripped through `new Gson()` — `toJson` then `fromJson` "
              "on the same object is visibly wasteful, which is the anchor. That default Gson widens "
              "every number to Double is a library behaviour outside the file."),
 23: ("weak", "`getOrDefault(KEY, null)` produces a parent observation that is then used as a parent. "
              "Defaulting to null and using the result is visible in seven lines; whether a null "
              "parent is legal needs the observation API."),
 24: ("weak", "A delete-by-filter enumerates matches with a single `ftSearch` call and no pagination. "
              "The mismatch between \"delete everything matching\" and one unbounded search is visible; "
              "that Redis returns ten results by default is outside the file."),
}

import subprocess
def subject(repo, sha):
    return subprocess.run(["git", "-C", repo, "log", "-1", "--format=%s", sha],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace").stdout.strip()

cases = json.load(open("cases.json", encoding="utf-8"))
for c in cases:
    c["fix_subject"] = subject(c["repo"], c["fix"])
rows = []
for c in cases:
    label, why = LABELS[c["n"]]
    rows.append("""
  - id: %s-%s
    repo: %s
    fix: %s
    fix_subject: >
      %s
    origin: %s
    file: %s
    detectable_from_diff: "%s"
    label_rationale: >
      %s
    origin_date: "%s"
    origin_lines: %d
    origin_creates_file: %s""" % (
        c["repo"], c["fix"][:7],
        "langchain4j/langchain4j" if c["repo"] == "langchain4j" else "spring-projects/spring-ai",
        c["fix"], c["fix_subject"].replace("\n", " ").strip(),
        c["origin"], c["file"], label,
        "\n      ".join(why[i:i+92] for i in range(0, len(why), 92)) if False else why,
        c["origin_date"], c["origin_lines"], str(c["origin_creates_file"]).lower()))

open("cases.yaml", "w", encoding="utf-8").write("".join(rows))
import collections
print(collections.Counter(LABELS[c["n"]][0] for c in cases))
print(collections.Counter((c["repo"], LABELS[c["n"]][0]) for c in cases))
strata = collections.Counter()
for c in cases:
    y, m = int(c["origin_date"][:4]), int(c["origin_date"][5:7])
    s = "post-cutoff" if (y == 2026 and m > 5) else "2025-2026.05" if y >= 2025 else "2024-"
    if LABELS[c["n"]][0] != "no":
        strata[s] += 1
print("scorable by stratum:", dict(strata))
