# Evaluation replay

**15 scorable case(s) of 17 in the set.**

This report does not contain a detection rate and cannot: the verdict line under
each case is a human judgement. Fill them in, then read the fractions below with
their denominators visible — never as a percentage. On a handful of cases a 25 %
rate and a 75 % one are the same measurement.

## `langchain4j-d5b13be`

fix: Use the name of the provided Azure AI Search index when index creation is disabled (#5901)

| | |
|---|---|
| introduced in | `b099922a1` |
| file | `langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java` |
| detectable from diff | weak |

1 finding(s) survived refutation:

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:74`** — boundary
  `this.indexName = getOrDefault(indexName, DEFAULT_INDEX_NAME);`
  The provided index's name is ignored; indexName falls back to "vectorsearch", so searchClient reads and writes the default index instead of "my-index".

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-7e622bf`

Fix Pinecone segment text being overwritten by reserved metadata key (#6033)

| | |
|---|---|
| introduced in | `e848e6a88` |
| file | `langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java` |
| detectable from diff | yes |

4 finding(s) survived refutation:

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — correctness
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  The loop never skips metadataTextKey, so the segment text is copied into the returned metadata map as an entry under "text_segment". The rebuilt segment's metadata then holds a duplicate of its own text, and it differs from the metadata that was stored. The initial capacity of size-1 shows the text key was meant to be excluded.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — boundary
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  The loop never skips metadataTextKey, so the returned metadata map contains the segment text under the text key (size 2 instead of the 1 the HashMap capacity size()-1 implies). The text leaks into the reconstructed Metadata for every segment that has any metadata.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — correctness
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  The early return only covers a map made solely of the text key. With any other field present, the loop never skips metadataTextKey, so the segment text is copied into the returned metadata map as a string entry (map capacity size-1 shows it was meant to be excluded). The reconstructed segment's metadata contains a spurious text_segment entry.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — correctness
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  putFields replaces the segment text stored under that key, so the stored text becomes "foo" and the real text is lost with no error.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-840330c`

Avoid NullPointerException when an async agent returns null (#5864)

| | |
|---|---|
| introduced in | `9443ad9b2` |
| file | `langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java` |
| detectable from diff | yes |

3 finding(s) survived refutation:

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — correctness
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null after writeState has removed the key. ConcurrentHashMap.replaceAll throws NullPointerException on a null result. rootCallEnded aborts before registry.evict (EPHEMERAL) or flush (PERSISTENT), so the scope is leaked or not persisted. Any exception thrown by blockingGet has the same effect.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — boundary
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null; ConcurrentHashMap.replaceAll throws NullPointerException for a null replacement value. rootCallEnded aborts before evict (EPHEMERAL) or flush (PERSISTENT), so the scope is never evicted or persisted.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — contract
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null, and ConcurrentHashMap.replaceAll throws NullPointerException when the function returns null. rootCallEnded aborts before registry.evict (EPHEMERAL) or flush (PERSISTENT). The ephemeral scope stays in the registry and the persistent scope is not saved, and the NPE propagates to the caller of the root call.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-771b0d2`

fix: support 3D logit output in OnnxScoringBertCrossEncoder (#5739)

| | |
|---|---|
| introduced in | `1c0671617` |
| file | `langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java` |
| detectable from diff | weak |

2 finding(s) survived refutation:

- **`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:36`** — resource
  `this.tokenizer = HuggingFaceTokenizer.newInstance(Paths.get(pathToTokenizer), tokenizerOptions);`
  The constructor throws RuntimeException and the object is never returned, so the already-created native OrtSession cannot be closed (no close/try-catch cleanup). Its native memory and model weights leak for each failed construction.

- **`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:28`** — resource
  `this.session = this.environment.createSession(modelPath, options);`
  The native OrtSession already created is never closed, because the catch block only wraps the exception and the class has no close method. Each failed construction leaks the loaded model's native memory.

**Detected?** `no` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-145ff45`

fix: treat an MCP $ref outside $defs as a plain schema, not a reference (#5790)

| | |
|---|---|
| introduced in | `632836213` |
| file | `langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java` |
| detectable from diff | weak |

3 finding(s) survived refutation:

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:44`** — contract
  `builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema")));`
  jsonNodeToJsonSchemaElement now returns a JsonReferenceSchema instead of falling through to the object branch (before the change, a node with no type became an empty object schema). The unconditional cast to JsonObjectSchema throws ClassCastException, so toolSpecificationListFromMcpResponse fails and the whole tool list from that server cannot be loaded.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`** — contract
  `if (node.has("$ref")) {`
  The root now returns a JsonReferenceSchema and its $defs are never read, because the $ref branch returns before the definitions code. The unchanged cast at line 44, (JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema")), then throws ClassCastException, so the whole tools/list conversion fails. Before the change this root was treated as an object schema.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:103`** — correctness
  `JsonNode defsNode = node.has("$defs") ? node.get("$defs") : node.get("definitions");`
  Only $defs is read; the "definitions" entries are silently dropped. extractReferenceKey maps the ref to "B", which has no entry in the resulting definitions map, so the JsonReferenceSchema points at a missing definition.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-e59754e`

fix: pass builder skipCreateVectorExtension to PgVectorEmbeddingStore (#5788)

| | |
|---|---|
| introduced in | `313452c49` |
| file | `langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java` |
| detectable from diff | weak |

3 finding(s) survived refutation:

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`** — contract
  `WHERE ranked.score >= ?`
  The score is an RRF sum, COALESCE(1.0/(60+v.rnk),0)+COALESCE(1.0/(60+k.rnk),0), so its maximum is 2/61, about 0.0328. The filter `ranked.score >= 0.5` then rejects every row and the search returns an empty result, even for an exact match. The same minScore gives sensible results in VECTOR mode, so switching modes silently empties the results.

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`** — boundary
  `WHERE ranked.score >= ?`
  Any minScore above 2/(rrfK+1) makes the filter reject every row, so the search returns an empty result. The minScore contract is a 0..1 similarity threshold, but the RRF scale tops out near 0.033. Even a document ranked first by both searches cannot pass.

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`** — contract
  `WHERE ranked.score >= ?`
  The hybrid score is a sum of RRF terms 1/(k+rank), at most about 2/(rrfK+1) (about 0.033 with the default k=60), so any minScore above that bound filters out every row and the search returns an empty result. The same minScore means a different scale in each mode, and the EmbeddingSearchRequest minScore contract is silently broken.

**Detected?** `no` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-196bc5d`

Follow up on AgentsRegistry implementation (#5719)

| | |
|---|---|
| introduced in | `ff9dfc1c7` |
| file | `langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java` |
| detectable from diff | yes |

6 finding(s) survived refutation:

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — correctness
  `private static volatile AgentsRegistry INSTANCE = discover();`
  discover() runs in LazyHolder's static initializer and CompositeAgentsRegistry throws RuntimeException, so the first get() fails with ExceptionInInitializerError. LazyHolder is then permanently in an erroneous state: every later get() and refresh() (which calls LazyHolder.discover()) throws NoClassDefFoundError, so refresh() cannot recover even after the duplicate provider is fixed. The documented 'exception at discovery time' becomes an unrecoverable class-init failure.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  allAgents() is documented to return an unmodifiable map, but it returns the internal mutable HashMap, so the mutation succeeds and silently changes the shared cached registry, removing or adding agents for all later getAgent() lookups.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — correctness
  `private static volatile AgentsRegistry INSTANCE = discover();`
  The first get() throws ExceptionInInitializerError and LazyHolder is marked erroneous. Every later get() and every refresh() throws NoClassDefFoundError, because refresh() touches LazyHolder.INSTANCE too. A refresh() after the duplicate is fixed cannot recover, which contradicts the Javadoc ('Call refresh() to force re-discovery'). The failure is also not the documented plain exception at discovery time.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  The shared internal HashMap is mutated, so getAgent() and later allAgents() see the change and the process-wide cached registry is corrupted. The interface Javadoc promises an unmodifiable map, and EmptyAgentsRegistry returns an immutable Map.of() while this returns a mutable HashMap. Concurrent readers of a mutated HashMap are also unsafe.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — contract
  `private static volatile AgentsRegistry INSTANCE = discover();`
  discover() runs inside LazyHolder's static initializer, so the RuntimeException surfaces as ExceptionInInitializerError and every later get() or refresh() fails with NoClassDefFoundError. The documented duplicate-name exception is never seen again, and refresh() cannot recover the class.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  allAgents() is documented as returning an unmodifiable map, but it returns the internal mutable HashMap. The call succeeds and changes the cached singleton registry for every consumer, so getAgent() then finds or loses agents. It does not throw UnsupportedOperationException.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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

3 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — correctness
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset while the parser decodes as UTF-8, so non-ASCII characters are corrupted (mojibake or '?' replacement; characters not representable in the default charset are lost) in the parsed Document text.

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — correctness
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset, so the parser decodes those bytes differently and the document text comes out with mojibake or replacement characters; characters outside the default charset become '?'

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — contract
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset while the parser reads the stream as UTF-8, so non-ASCII text is garbled or replaced with U+FFFD in the parsed Document. Characters not representable in the default charset become '?'. The result depends on the host JVM.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`** — correctness
  `throw new RuntimeException("Failed to load document from GitHub: {}", ioException);`
  RuntimeException.getMessage() is the literal text 'Failed to load document from GitHub: {}'; RuntimeException does not substitute placeholders, so the URL/path is never in the message and the failing file cannot be identified from it.

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:99`** — resource
  `document = withRetry(() -> fromGitHub(parser, ghContent), 3);`
  fromGitHub throws a deterministic IllegalArgumentException; withRetry retries it 3 times (each attempt logs 'Loading document' and incurs retry delay), then the error is logged and the entry skipped. Retries cannot succeed and slow the scan.

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:99`** — boundary
  `document = withRetry(() -> fromGitHub(parser, ghContent), 3);`
  fromGitHub throws a deterministic IllegalArgumentException for the entry. withRetry treats it as transient and calls it 3 times with backoff delays and 3 info logs. The entry is then logged as an error and skipped, so each such entry adds retry delay to the whole scan.

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`** — correctness
  `throw new RuntimeException("Failed to load document from GitHub: {}", ioException);`
  The RuntimeException message contains a literal unformatted '{}' placeholder, because RuntimeException does not interpolate. The URL of the failing content is never included in the message.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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

3 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))`
  String.getBytes() encodes with the platform default charset while the parser decodes the stream as UTF-8, so the text is mojibake. Characters the default charset cannot represent become '?' and are lost. The Document ends up with corrupted content, and the result depends on the machine the code runs on.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))`
  String.getBytes() encodes with the platform default charset, but the parser reads UTF-8. Non-ASCII text is mangled into replacement characters or mojibake in the returned Document, and the result depends on the host JVM.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — contract
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))`
  String.getBytes() encodes with the platform default charset, but parsers read the stream as UTF-8 by default. Non-ASCII characters are mangled into replacement or garbled characters, and the document text depends on the host JVM instead of on the page.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-23098bd`

fix: Preserve binary bytes in Azure dynamic sessions file download (#5652)

| | |
|---|---|
| introduced in | `1fab3b7e4` |
| file | `code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java` |
| detectable from diff | yes |

8 finding(s) survived refutation:

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:91`** — correctness
  `Pattern.compile("^(\\s|`)*(?i:python)?\\s*")`
  The optional (?i:python) group has no word boundary, so the leading 'python' is stripped from the identifier. The code sent to the session becomes "_version = 3\nprint(python_version)", which is a different program and raises NameError (or silently computes something else).

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`** — boundary
  `Object result = response.get("result");`
  getNestedMapProperty returns null, executeCode returns null, and use() throws NullPointerException here instead of reporting the malformed response.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:478`** — boundary
  `if (valueArray.isEmpty()) {`
  json.get("value") returns null, so valueArray.isEmpty() throws NullPointerException. It is wrapped as "Failed to list files: null" with no indication of the real problem.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:91`** — boundary
  `Pattern.compile("^(\\s|`)*(?i:python)?\\s*");`
  The optional (?i:python) has no word boundary, so it strips the prefix off the identifier. The code sent is "_version = 3\nprint(python_version)", which raises NameError or silently changes semantics.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:429`** — correctness
  `byte[] fileBytes = response.body().getBytes(StandardCharsets.UTF_8);`
  The body has already been decoded to a String, so invalid byte sequences became U+FFFD. Re-encoding and Base64-ing returns corrupted bytes, not the original file.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`** — contract
  `Object result = response.get("result");`
  executeCode returns null and use() throws a NullPointerException at response.get("result") instead of a meaningful error.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:429`** — correctness
  `byte[] fileBytes = response.body().getBytes(StandardCharsets.UTF_8);`
  Invalid byte sequences are replaced by U+FFFD during decoding, so the returned Base64 does not match the remote file and the binary content is silently corrupted.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:433`** — contract
  `if (e.getMessage().contains("404")) {`
  NullPointerException inside the catch block hides the original failure and the 'Failed to download file' RuntimeException is never thrown.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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

3 finding(s) survived refutation:

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — correctness
  `if (!result.getPagemap().isEmpty()) {`
  toResultMetadataMap is called from the new toWebSearchOrganicResults for every item, so result.getPagemap().isEmpty() raises NullPointerException and the whole search() call fails instead of returning the results. The new empty-items guard does not cover this path.

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — boundary
  `if (!result.getPagemap().isEmpty()) {`
  NullPointerException in toResultMetadataMap, called from the new toWebSearchOrganicResults. The whole search() call fails even though the new empty-items guard was meant to make it tolerant of sparse responses.

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — contract
  `if (!result.getPagemap().isEmpty()) {`
  NullPointerException in toResultMetadataMap, called from the new toWebSearchOrganicResults, so the whole search() call fails instead of returning the results; the null-guard added for items does not cover this.

**Detected?** `no` — replace with `yes` or `no`. It counts as detected only if a
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

4 finding(s) survived refutation:

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  The word is split only on ' ', so the first position's lastWord is "PLAN.\nAPPROVE" and the second's is "APPROVE". They differ, so hasConverged returns false even though both end with the same verdict word, and the debate keeps running until its round limit.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — boundary
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  Only a space is treated as a word separator, so the first position yields "RAISED.
YES" while the second yields "YES". The verdicts compare unequal and hasConverged returns false even though both end in YES. A multi-line debate never converges.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  The extracted 'last word' is "DONE.
APPROVE" for the first and "FINISHED.
APPROVE" for the second. They compare unequal, so unanimousLastWord() returns false although every agent gave the same verdict, and the debate never converges.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — contract
  `String text = p.toString().trim();`
  p.toString() throws NullPointerException from unanimousLastWord().hasConverged instead of returning a boolean.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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

3 finding(s) survived refutation:

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`** — correctness
  `messageResponse.complete(extractTextFromParts(
                task.artifacts().stream().flatMap(a -> a.parts().stream()).toList()));`
  isTerminalState is true, so the future completes normally with an empty string. invokeAgent returns the parsed empty text as a successful result instead of throwing, and the failure is silently lost.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`** — contract
  `messageResponse.complete(extractTextFromParts(`
  The future is completed normally with an empty string instead of exceptionally. invokeAgent returns an empty or parsed-empty result as if the call succeeded, so a failed remote task is reported as success with empty output.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`** — undocumented
  `if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {`
  Beyond the dependency bump, the change alters response-completion behaviour: non-terminal tasks without artifacts are now ignored instead of completing the future, and the explicit setStreaming(false) client configuration is dropped. The intent describes only a version bump.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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

1 finding(s) survived refutation:

- **`langchain4j/src/main/java/dev/langchain4j/store/embedding/inmemory/InMemoryEmbeddingStore.java:118`** — contradicts
  `} else if (entry.embedded == null) {
                return false;`
  An entry whose embedded value is null is not a TextSegment, yet it is silently kept instead of raising UnsupportedOperationException; only non-null non-TextSegment values raise.

**Detected?** `no` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## Excluded from scoring, and why

| case | reason |
|---|---|
| `langchain4j-cc37ab3` | not findable from the diff (no) |
| `langchain4j-4aff9c9` | not findable from the diff (no) |

## To total it

- **detected / 15 scorable** — the headline, as a fraction.
- **findings that were not the known defect** — not errors (a genuine second bug
  is not a false positive), but the number that bounds a reader's cost, and the
  one that decides whether anyone keeps using this.

Nothing here measures a false-positive rate: every case is a diff known to
contain a defect. That needs the opposite corpus — clean commits — and it is
arguably the more useful of the two.

---

Harness transport, 15 case(s), 0 finding(s) refused by the guards. **No dollar cost**: the tokens are the harness's. That is the point of running the scaling measurement here.
