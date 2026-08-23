# Evaluation replay

**4 scorable case(s) of 17 in the set.**

This report does not contain a detection rate and cannot: the verdict line under
each case is a human judgement. Fill them in, then read the fractions below with
their denominators visible — never as a percentage. On a handful of cases a 25 %
rate and a 75 % one are the same measurement.

## `langchain4j-145ff45`

fix: treat an MCP $ref outside $defs as a plain schema, not a reference (#5790)

| | |
|---|---|
| introduced in | `632836213` |
| file | `langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java` |
| detectable from diff | weak |

7 finding(s) survived refutation:

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`** — correctness
  `if (node.has("$ref")) {
            return JsonReferenceSchema.builder()`
  jsonNodeToJsonSchemaElement returns a JsonReferenceSchema, so the cast on line 44, builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema"))), throws ClassCastException and the whole tool list conversion fails. Before this change the same input fell through to the default object-schema branch and succeeded.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:106`** — contract
  `for (Map.Entry<String, JsonNode> entry : ((ObjectNode) defsNode).properties()) {`
  node.has("$defs") is true for an explicit null, so defsNode is a NullNode (or ArrayNode) and the cast to ObjectNode throws ClassCastException, aborting conversion of the entire tool list instead of ignoring the unusable definitions block.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:106`** — boundary
  `for (Map.Entry<String, JsonNode> entry : ((ObjectNode) defsNode).properties()) {`
  Throws java.lang.ClassCastException (NullNode/ArrayNode cannot be cast to ObjectNode) while parsing the tool list, so the whole ListTools response fails instead of the empty/invalid `$defs` being ignored.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:44`** — contract
  `builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema")));`
  The cast to JsonObjectSchema throws java.lang.ClassCastException, aborting parsing of the entire tool list; previously the same input produced an (empty) object schema without throwing.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`** — contract
  `if (node.has("$ref")) {`
  jsonNodeToJsonSchemaElement returns a JsonReferenceSchema, and the unconditional cast at line 44, `builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema")))`, throws ClassCastException, aborting the whole tool-list conversion. Before this change the same input fell through to the 'no type -> object schema' default and did not throw.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:106`** — contract
  `for (Map.Entry<String, JsonNode> entry : ((ObjectNode) defsNode).properties()) {`
  the cast to ObjectNode throws ClassCastException instead of ignoring the malformed keyword, failing conversion of the entire tool list

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:77`** — correctness
  `return JsonReferenceSchema.builder()
                    .reference(extractReferenceKey(node.get("$ref").asText()))
                    .build();`
  the description (and any other sibling keyword) is silently dropped from the produced JsonReferenceSchema, so the schema handed to the model loses the property description, unlike every other branch of this method which copies "description"

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-96a3af9`

fix: Use UTF-8 when encoding Playwright page content for the document parser (#5686)

| | |
|---|---|
| introduced in | `0e7374d64` |
| file | `document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java` |
| detectable from diff | weak |

4 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  `pageContent.getBytes()` encodes the String with the platform default charset while parsers (e.g. the HTML/text document parsers) decode the stream as UTF-8, so the returned Document text contains mojibake or U+FFFD replacement characters instead of the original characters; multi-byte characters such as \u4f60 are unmappable and become '?'.

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset while the parser decodes as UTF-8, so the returned Document text contains mojibake / replacement characters instead of the original page text (non-representable characters are replaced with '?' when the default charset cannot encode them).

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — contract
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset while DocumentParser implementations decode the stream as UTF-8, so the parsed Document text contains mojibake or '?' replacement characters instead of the original page text; characters unrepresentable in the default charset are lost irrecoverably

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:84`** — undocumented
  `public String pageContent(String url) {`
  `load(String url)` was rewritten to delegate to a newly added *public* method `pageContent(String url)`, so the change also expands the public API surface of this class (a new supported entry point callers can depend on) which the intent never mentions; the observable result of `load(String url)` itself is the same, but the method body and its logging were changed rather than left as-is.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-0626661`

fix: Include failing file URL in GitHubDocumentLoader load-failure exception message (#5684)

| | |
|---|---|
| introduced in | `aaddb9226` |
| file | `document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java` |
| detectable from diff | yes |

4 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:94`** — contract
  `logger.error("Failed to read directory from GitHub: {}", ghContent.getHtmlUrl(), ioException);`
  The IOException is logged and swallowed inside the forEach lambda; scanDirectory returns normally, so loadDocuments returns a silently truncated List<Document> that is missing every file under that subtree, and the caller has no way to distinguish it from a complete result.

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`** — correctness
  `throw new RuntimeException("Failed to load document from GitHub: {}", ioException);`
  RuntimeException(String, Throwable) does no SLF4J-style substitution, so the propagated message is the literal "Failed to load document from GitHub: {}" with no file or URL information; when scanDirectory logs it at line 101 the operator sees the unsubstituted placeholder.

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:90`** — boundary
  `if (ghContent.isDirectory()) {`
  The entry falls into the else branch and is passed to fromGitHub, where content.isFile() is false, so IllegalArgumentException("Content must be a file, and not a directory: ...") is thrown. Because it is wrapped in withRetry(..., 3), the non-retryable failure is retried three times with backoff sleeps before the error is logged and the entry silently dropped from the returned list.

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`** — contract
  `throw new RuntimeException("Failed to load document from GitHub: {}", ioException);`
  RuntimeException(String,Throwable) performs no SLF4J-style interpolation, so getMessage() is literally "Failed to load document from GitHub: {}" — the placeholder is never substituted and the message carries no information about the failed file or cause

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-f274731`

fix: Encode page content as UTF-8 in SeleniumDocumentLoader (#5671)

| | |
|---|---|
| introduced in | `36c175190` |
| file | `document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java` |
| detectable from diff | weak |

8 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset, so the bytes handed to the parser are not UTF-8; the parser (which decodes as UTF-8) produces mojibake or '?' replacement characters, and the returned Document text differs from the actual page content.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  pageContent is null and line 59 throws a raw NullPointerException outside the try block, bypassing the intended "Failed to load document" RuntimeException wrapping, so callers catching that wrapper see an unhandled NPE instead.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset while the DocumentParser decodes as UTF-8, so the returned Document text contains mojibake / replacement characters instead of the original page text.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — contract
  `new ByteArrayInputStream(pageContent.getBytes())`
  pageContent is null and line 59 throws NullPointerException outside the try block, so it escapes uncaught instead of the documented RuntimeException("Failed to load document").

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:77`** — boundary
  `public Builder timeout(Duration timeout) {`
  build() succeeds (only webDriver is null-checked), and the null timeout only fails later at new WebDriverWait(webDriver, null), which is swallowed into RuntimeException("Failed to load document") — the failure is reported as a page-load failure rather than a configuration error.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:53`** — contract
  `return ((JavascriptExecutor) requireNonNull(wd)).executeScript("return document.readyState").equals("complete");`
  NullPointerException is thrown inside the wait predicate. WebDriverWait does not ignore NPE, so the wait aborts on the first poll instead of retrying until the timeout, and the NPE is caught at line 56 and rethrown as RuntimeException("Failed to load document") — a load that would have succeeded after a short wait fails immediately.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))`
  `String.getBytes()` encodes with the platform default charset while parsers such as TextDocumentParser decode as UTF-8, so the resulting Document text contains replacement/garbled characters.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:53`** — unimplemented
  `return ((JavascriptExecutor) requireNonNull(wd)).executeScript("return document.readyState").equals("complete");`
  The only readiness signal used is `document.readyState == "complete"`, which becomes true as soon as the initial document and its subresources have loaded; content injected later by asynchronous JavaScript (XHR/fetch-driven rendering) is not waited for, so `getPageSource()` may be captured before dynamically loaded elements exist.

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
| `langchain4j-e59754e` | not selected by --case |
| `langchain4j-196bc5d` | not selected by --case |
| `langchain4j-23098bd` | not selected by --case |
| `langchain4j-575eb46` | not selected by --case |
| `langchain4j-0d16d28` | not selected by --case |
| `langchain4j-34b8d34` | not selected by --case |
| `langchain4j-95a3aff` | not selected by --case |

## To total it

- **detected / 4 scorable** — the headline, as a fraction.
- **findings that were not the known defect** — not errors (a genuine second bug
  is not a false positive), but the number that bounds a reader's cost, and the
  one that decides whether anyone keeps using this.

Nothing here measures a false-positive rate: every case is a diff known to
contain a defect. That needs the opposite corpus — clean commits — and it is
arguably the more useful of the two.

---

Model `claude-opus-5`, 44 call(s) across 4 case(s), 2.9268 USD billed. 0 finding(s) refused by the guards. cache read 69736 tokens against 4030 written
