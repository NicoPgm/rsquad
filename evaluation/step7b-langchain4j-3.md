# Evaluation replay

**5 scorable case(s) of 17 in the set.**

This report does not contain a detection rate and cannot: the verdict line under
each case is a human judgement. Fill them in, then read the fractions below with
their denominators visible — never as a percentage. On a handful of cases a 25 %
rate and a 75 % one are the same measurement.

## `langchain4j-23098bd`

fix: Preserve binary bytes in Azure dynamic sessions file download (#5652)

| | |
|---|---|
| introduced in | `1fab3b7e4` |
| file | `code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java` |
| detectable from diff | yes |

12 finding(s) survived refutation:

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`** — correctness
  `Object result = response.get("result");`
  `getNestedMapProperty` returns null at line 314, `executeCode` returns null, and `use()` dereferences it on line 213, throwing NullPointerException instead of a diagnosable error.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:433`** — correctness
  `if (e.getMessage().contains("404")) {`
  The catch block itself throws a NullPointerException on `e.getMessage()`, so the original failure is discarded and the caller sees an NPE from the error handler rather than the wrapped RuntimeException the code intends to throw.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:91`** — correctness
  `private static final Pattern SANITIZE_PATTERN_START = Pattern.compile("^(\\s|`)*(?i:python)?\\s*");`
  The optional `python` group matches the identifier prefix, so the submitted code becomes `path = 5\nprint(pythonpath)` — silently mutated source is executed remotely and fails with a NameError instead of running the user's code.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:357`** — contract
  `String contentType = "Content-Type: application/json\r\n\r\n";`
  The multipart part declares `Content-Type: application/json` for raw binary bytes, so the upload request misdescribes every file that is not JSON.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`** — correctness
  `Object result = response.get("result");`
  use()/execute() dereferences the null map and throws NullPointerException instead of returning a JSON result or a meaningful error.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:387`** — boundary
  `Map<String, Object> fileMetadataMap = valueList.get(0);`
  IndexOutOfBoundsException (or NullPointerException for the missing-key case) is thrown, caught at line 390 and rethrown as RuntimeException("Failed to upload file: Index 0 out of bounds ..."), masking the actual API response.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:429`** — correctness
  `byte[] fileBytes = response.body().getBytes(StandardCharsets.UTF_8);`
  The body has already been decoded into a String; re-encoding with getBytes(UTF_8) replaces every invalid byte sequence with U+FFFD (0xEF 0xBF 0xBD), so the returned Base64 string decodes to corrupted content that differs from the remote file.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:478`** — boundary
  `if (valueArray.isEmpty()) {`
  NullPointerException on valueArray.isEmpty(), caught at line 505 and rethrown as RuntimeException("Failed to list files: null API URL: ...") instead of reporting no files.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:424`** — contract
  `if (response.statusCode() == 404) {`
  langchainHttpClient.execute() only ever returns a SuccessfulHttpResponse (2xx); a 404 is surfaced as a thrown exception, so this comparison can never be true. The branch is a silent no-op and the 404 handling relies entirely on the string match on the exception message below.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:429`** — correctness
  `byte[] fileBytes = response.body().getBytes(StandardCharsets.UTF_8);`
  The body was already decoded to a String; bytes that are not valid UTF-8 become U+FFFD, and re-encoding with getBytes(UTF_8) produces different bytes. The returned Base64 string does not decode back to the original file content.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:91`** — correctness
  `private static final Pattern SANITIZE_PATTERN_START = Pattern.compile("^(\\s|`)*(?i:python)?\\s*");`
  The optional group is not anchored to a word boundary or a fence, so the literal prefix "python" is stripped from the identifier: the code sent to the session becomes "ic = 5\nprint(pythonic)", which executes different code and raises NameError instead of the user's program.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`** — contract
  `Object result = response.get("result");`
  executeCode's documented map return can be null and is dereferenced unchecked here, throwing NullPointerException out of use()/execute() instead of a diagnosable error.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-575eb46`

fix: Skip search results with unresolvable URIs in GoogleCustomWebSearchEngine (#5628)

| | |
|---|---|
| introduced in | `b246cfde7` |
| file | `web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java` |
| detectable from diff | weak |

1 finding(s) survived refutation:

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — contract
  `if (!result.getPagemap().isEmpty()) {`
  NullPointerException is thrown while mapping the result, so search(...) fails entirely instead of returning organic results. The new null/empty guard on search.getItems() protects only against a missing items list, not against a null pagemap on an individual item.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-0d16d28`

fix: unanimousLastWord convergence to normalize verdict token (#5479)

| | |
|---|---|
| introduced in | `8b6aeead7` |
| file | `langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java` |
| detectable from diff | weak |

8 finding(s) survived refutation:

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — correctness
  `String text = p.toString().trim();`
  throws NullPointerException on p.toString(); the sibling strategy unanimous() handles the same input without throwing because it uses Objects.equals

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  lastIndexOf(' ') only searches for the space character, so the first element yields lastWord "CONCEDE.\nYES" instead of "YES"; the method returns false even though both positions end with the same word

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  lastIndexOf(' ') finds the space before "is", so lastWord becomes "IS\nYES" instead of "YES"; it does not equal "YES" from the second position and hasConverged returns false even though both verdicts are identical

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — boundary
  `String text = p.toString().trim();`
  p.toString() throws NullPointerException instead of returning a boolean

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:33`** — boundary
  `return firstVerdict != null;`
  unanimousLastWord() returns false while unanimous() returns true for the identical input, so a caller swapping strategies gets opposite convergence decisions on the empty case

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  lastIndexOf(' ') only recognises the ASCII space, so the extracted "last word" becomes "ARGUMENTS\nYES" instead of "YES"; hasConverged returns false even though both positions end in the same verdict

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — contract
  `String text = p.toString().trim();`
  throws NullPointerException, while unanimous() handles the same input safely via Objects.equals; the interface places no null restriction on the collection

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — correctness
  `String text = p.toString().trim();`
  throws NullPointerException, whereas unanimous() handles nulls safely via Objects.equals

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-34b8d34`

fix: Surface failed A2A tasks as exceptions instead of empty results (#5471)

| | |
|---|---|
| introduced in | `a24e4f9d3` |
| file | `langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java` |
| detectable from diff | weak |

6 finding(s) survived refutation:

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`** — correctness
  `messageResponse.complete(extractTextFromParts(
                task.artifacts().stream().flatMap(a -> a.parts().stream()).toList()));`
  isTerminalState() is true, so the guard at line 178 falls through and the future is completed normally with the empty string produced by extractTextFromParts on an empty list. invokeAgent then returns serviceOutputParser.parseText(returnType, "") — the caller receives an empty/blank result as a successful answer instead of any indication that the remote task failed.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`** — boundary
  `if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {`
  The guard falls through and `messageResponse.complete(...)` is called with only the artifacts seen so far; every later update finds the future already completed, so `invokeAgent` returns a truncated response containing only the first chunk of the agent's output.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`** — boundary
  `messageResponse.complete(extractTextFromParts(`
  `extractTextFromParts` on an empty list returns "", so the future completes normally with an empty string and `serviceOutputParser.parseText(returnType, "")` is invoked; the caller receives an empty/garbage result instead of an error for a failed or rejected task.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:164`** — resource
  `String responseText = messageResponse.get();`
  `completeFromTask` returns without completing the future for every event, nothing else completes it, and `messageResponse.get()` (no timeout) blocks the calling thread indefinitely, leaking that thread.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`** — correctness
  `if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {`
  The guard is skipped because the state is terminal, so `messageResponse.complete("")` runs with an empty joined string; `invokeAgent` then returns `serviceOutputParser.parseText(returnType, "")` and the caller silently receives an empty/blank agent result instead of an error for a failed or rejected task.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:179`** — contract
  `return;`
  `completeFromTask` returns without completing the future, nothing else ever completes it, and `messageResponse.get()` at line 164 blocks the calling thread indefinitely (no timeout), hanging the agent invocation. Previously a TaskEvent always completed the future.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-95a3aff`

Fix filtering for non-TextSegment entries in InMemoryEmbeddingStore (#5405)

| | |
|---|---|
| introduced in | `2b2c09f05` |
| file | `langchain4j/src/main/java/dev/langchain4j/store/embedding/inmemory/InMemoryEmbeddingStore.java` |
| detectable from diff | weak |

2 finding(s) survived refutation:

- **`langchain4j/src/main/java/dev/langchain4j/store/embedding/inmemory/InMemoryEmbeddingStore.java:101`** — contract
  `entries.removeIf(entry -> entry.id.equals(id));`
  silently removes nothing and returns normally, instead of rejecting the argument the way the sibling removeAll(Collection) does via ensureNotEmpty and the way the EmbeddingStore.remove default implementation does via ensureNotNull; callers get no signal that their id was invalid

- **`langchain4j/src/main/java/dev/langchain4j/store/embedding/inmemory/InMemoryEmbeddingStore.java:118`** — contradicts
  `} else if (entry.embedded == null) {`
  For entries whose embedded object is null (added via add(String, Embedding) or addAll(List<Embedding>)), the code silently keeps the entry instead of raising UnsupportedOperationException as the described strategy states; the intent does not mention this null case.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## Excluded from scoring, and why

| case | reason |
|---|---|
| `langchain4j-cc37ab3` | not findable from the diff (no) |
| `langchain4j-4aff9c9` | not findable from the diff (no) |
| `langchain4j-d5b13be` | not selected by --case |
| `langchain4j-7e622bf` | not selected by --case |
| `langchain4j-840330c` | not selected by --case |
| `langchain4j-771b0d2` | not selected by --case |
| `langchain4j-145ff45` | not selected by --case |
| `langchain4j-e59754e` | not selected by --case |
| `langchain4j-196bc5d` | not selected by --case |
| `langchain4j-96a3af9` | not selected by --case |
| `langchain4j-0626661` | not selected by --case |
| `langchain4j-f274731` | not selected by --case |

## To total it

- **detected / 5 scorable** — the headline, as a fraction.
- **findings that were not the known defect** — not errors (a genuine second bug
  is not a false positive), but the number that bounds a reader's cost, and the
  one that decides whether anyone keeps using this.

Nothing here measures a false-positive rate: every case is a diff known to
contain a defect. That needs the opposite corpus — clean commits — and it is
arguably the more useful of the two.

---

Model `claude-opus-5`, 56 call(s) across 5 case(s), 4.6962 USD billed. 0 finding(s) refused by the guards. cache read 88377 tokens against 7583 written
