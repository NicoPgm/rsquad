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

3 finding(s) survived refutation:

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:71`** — correctness
  `if (createOrUpdateIndex && index != null) {`
  The && short-circuits to the else branch, so this.indexName becomes getOrDefault(null, DEFAULT_INDEX_NAME) = "vectorsearch"; the SearchClient built at lines 85-89 / 98-102 is bound to "vectorsearch" instead of "my-index", so every add/addAll upload and findRelevant query silently targets the wrong (default) index — the supplied index is never used at all on this path.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:71`** — correctness
  `if (createOrUpdateIndex && index != null) {`
  The && short-circuits to the else branch, so this.indexName becomes getOrDefault(null, DEFAULT_INDEX_NAME) = "vectorsearch" and the searchClient built at lines 85-89/98-102 is bound to "vectorsearch" instead of "my-index". Every subsequent add/addAll writes documents into, and findRelevant queries, the default index rather than the index the caller supplied - silently, with no exception.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:71`** — contract
  `if (createOrUpdateIndex && index != null) {
            this.indexName = index.getName();`
  The && guard fails, so the else branch sets this.indexName = DEFAULT_INDEX_NAME ("vectorsearch"), and the searchClient built at lines 88/101 is bound to "vectorsearch" instead of the caller's index. Every subsequent addAllInternal upload and findRelevant query silently targets the wrong index: documents are written into "vectorsearch" and searches return results from it (or fail with a missing-index error), never touching "my-index". The caller's index name is accepted and then discarded without any error.

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

6 finding(s) survived refutation:

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — correctness
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  The guard on line 21 does not fire (size is 2), and the loop never skips metadataTextKey, so the returned map is {"text_segment": "hello world", "author": "bob"} instead of {"author": "bob"} — the segment text is injected into the metadata of every retrieved segment that carries at least one real metadata field. The pre-sized capacity filedsMap.size() - 1 on line 25 shows one fewer entry was expected than the loop actually writes.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — correctness
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  The loop calls putFields with key equal to metadataTextKey, overwriting the field set on line 43, so the Struct stored in Pinecone holds "bob" as the segment text and "hello world" is lost; retrieval returns a TextSegment whose text is the metadata value.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:25`** — boundary
  `Map<String, Object> metadataMap = new HashMap<>(filedsMap.size() - 1);
        for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  The loop never skips metadataTextKey, so the returned map is {"text": "hello world", "author": "bob"} instead of {"author": "bob"}: the segment text is duplicated into the metadata of every retrieved match. The exclusion works only at exactly size == 1 (the early return), which is also why the capacity is sized size() - 1.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — correctness
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  putFields overwrites the field written at line 43, so the Struct stored in Pinecone carries "text" -> "bob" instead of the segment text; on retrieval the embedded segment's text is "bob" and the original text "hello world" is lost.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:25`** — correctness
  `Map<String, Object> metadataMap = new HashMap<>(filedsMap.size() - 1);
        for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  The loop copies every entry, including the metadataTextKey entry, so the returned metadata map is {"text": "the whole segment body", "author": "bob"}: the segment text is duplicated into the reconstructed TextSegment's metadata. The initial capacity filedsMap.size() - 1 and the size==1 early return both exclude that key, so the two paths disagree — a one-field struct yields no "text" entry while a two-field struct yields one.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — contract
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  putFields overwrites the text field written at line 43, so the Struct stores "some caption" instead of "real body". The segment text is silently lost at write time and every later retrieval returns the metadata value as the segment text; nothing in the method detects or reports the collision.

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

4 finding(s) survived refutation:

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — contract
  `state.replaceAll(this::readStateBlocking);`
  ConcurrentHashMap.replaceAll rejects a null return value and throws NullPointerException out of rootCallEnded, before the kind checks that follow. The EPHEMERAL branch never calls registry.evict(memoryId) and the PERSISTENT branch never calls flush(registry), so the scope is left in the registry unevicted and unpersisted, and the exception surfaces to the caller ending the root call.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — boundary
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking first removes the key via writeState(key, null) (line 82), then returns null; ConcurrentHashMap.replaceAll throws NullPointerException on a null remapping result, so rootCallEnded aborts before reaching the eviction/flush branch. The EPHEMERAL scope is never evicted from the registry and the PERSISTENT scope is never flushed to the store, while the state map is left half-resolved.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — contract
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null, and ConcurrentHashMap.replaceAll rejects a null result: rootCallEnded throws NullPointerException before reaching the kind switch, so registry.evict(memoryId) is never called for EPHEMERAL and flush(registry) is never called for PERSISTENT. The map has already been mutated by the nested writeState(key, null), which removed the key, so the scope is left half-updated, unevicted and unpersisted, and the NPE propagates to the caller of the root agent. That null values are expected here is shown by writeState's own null branch (state.remove(key)).

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — correctness
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null, and ConcurrentHashMap.replaceAll rejects a null remapping result, so rootCallEnded throws NullPointerException at line 143. The exception propagates to the caller and the rest of the method never runs: an EPHEMERAL scope is never evicted from the registry (it stays in inMemoryAgenticScope) and a PERSISTENT scope is never flushed, so its final state is not saved to the store.

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

- **`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:28`** — resource
  `this.session = this.environment.createSession(modelPath, options);`
  The OrtSession created on line 28 is already holding the loaded model's native memory; the catch on line 37 rethrows as RuntimeException without calling session.close(), and the partially built object is discarded, so that native allocation is leaked for the lifetime of the JVM. Each retry with a bad tokenizer path leaks another session.

- **`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:28`** — resource
  `this.session = this.environment.createSession(modelPath, options);`
  The OrtSession opened on line 28 is never closed: the constructor throws, the object is discarded, and the class exposes no close()/AutoCloseable, so the session's native model memory is held until JVM exit. Each retried construction with a bad tokenizer path leaks another session.

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

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`** — correctness
  `if (node.has("$ref")) {
            return JsonReferenceSchema.builder()`
  The new $ref branch fires before the type/default-object branch, so jsonNodeToJsonSchemaElement returns a JsonReferenceSchema; line 44's cast (JsonObjectSchema) then throws ClassCastException, aborting toolSpecificationListFromMcpResponse so no tool from that server is registered. Before the change the same input fell through to typeNode == null and produced a JsonObjectSchema.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`** — contract
  `if (node.has("$ref")) {
            return JsonReferenceSchema.builder()`
  Line 44, builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema"))), throws ClassCastException: JsonReferenceSchema cannot be cast to JsonObjectSchema. The exception escapes toolSpecificationListFromMcpResponse, so the entire tool list fails to load, not just the one tool. Before this change the same input produced an empty JsonObjectSchema (typeNode == null path) and loaded without error.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`** — contract
  `if (node.has("$ref")) {
            return JsonReferenceSchema.builder()`
  jsonNodeToJsonSchemaElement now returns a JsonReferenceSchema for that node, and the unconditional cast at line 44, builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema"))), throws ClassCastException: JsonReferenceSchema cannot be cast to JsonObjectSchema. The exception escapes toolSpecificationListFromMcpResponse, so every tool from that server is lost, not just the offending one. Before this change the same input fell through to the typeNode == null branch and produced an (empty) JsonObjectSchema without throwing.

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

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:565`** — correctness
  `stmt.setDouble(4, minScore);`
  The bound parameter feeds `WHERE ranked.score >= ?`, but `score` here is the RRF sum `1.0/(60+v.rnk) + 1.0/(60+k.rnk)`, whose maximum possible value is 2/61 = 0.0328. minScore is validated by EmbeddingSearchRequest to be in [0.0, 1.0], so any value above 0.0328 filters out every row: search() returns an empty match list even for an exact vector-and-keyword match, whereas the same request in VECTOR mode (where minScore is compared against the normalized cosine score) returns the row.

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`** — correctness
  `WHERE ranked.score >= ?`
  Returns an empty EmbeddingSearchResult every time. minScore is validated into [0.0, 1.0] and in VECTOR mode it is compared to a cosine similarity on that same scale, but here it is bound (stmt.setDouble(4, minScore)) against the RRF score COALESCE(1.0/(60+v.rnk),0.0)+COALESCE(1.0/(60+k.rnk),0.0), whose maximum possible value is 1/61+1/61 = 0.0328 for a row ranked first in both branches. Every row is therefore filtered out at any minScore above 0.0328, silently, with no error and no log.

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`** — contract
  `WHERE ranked.score >= ?`
  The bound parameter is minScore, which EmbeddingSearchRequest validates as a similarity in [0.0, 1.0] and which embeddingOnlySearch compares against (2 - distance)/2 in [0,1]. Here it is compared against the RRF score COALESCE(1.0/(60 + v.rnk), 0.0) + COALESCE(1.0/(60 + k.rnk), 0.0), whose maximum possible value is 2/61 = 0.0328. Every row is filtered out and search() returns an empty EmbeddingSearchResult even when the top-ranked document matches both the vector and the full-text query — a silent no-op rather than an error.

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
  discover() runs inside the static initializer of LazyHolder, so the RuntimeException("Duplicate agent name across registries: writer") thrown at line 82 escapes as ExceptionInInitializerError on the first get(). LazyHolder is then permanently marked erroneous: every later AgentsRegistry.get() AND AgentsRegistry.refresh() throws NoClassDefFoundError: Could not initialize class ...AgentsRegistry$LazyHolder, because refresh() must touch the same class to reassign INSTANCE. The documented recovery path ("Call refresh() to force re-discovery") can never run for the whole life of the JVM, and the original cause is no longer reported.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  allAgents() hands back the live mutable HashMap field instead of the unmodifiable map the interface javadoc promises (line 24: "an unmodifiable map"), and EmptyAgentsRegistry honours by returning Map.of(). The clear()/put() succeeds instead of raising UnsupportedOperationException, permanently corrupting the cached singleton: a subsequent AgentsRegistry.get().getAgent("writer") throws RuntimeException("No agent found with name: writer") for an agent that is still registered by its provider.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — contract
  `private static volatile AgentsRegistry INSTANCE = discover();`
  The exception escapes the static initializer, so get() throws ExceptionInInitializerError and the JVM permanently marks LazyHolder erroneous. Every later call to get() throws NoClassDefFoundError: Could not initialize class ...AgentsRegistry$LazyHolder, and the documented recovery path refresh() throws the same NoClassDefFoundError at LazyHolder.INSTANCE = LazyHolder.discover() instead of re-discovering. The registry cannot be recovered for the life of the JVM even after the duplicate/failing provider is removed.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  The mutation silently succeeds on the live internal HashMap: subsequent getAgent("x") returns the injected agent and cleared entries throw "No agent found with name: ...". The same caller code throws UnsupportedOperationException with 0 providers and corrupts the registry with 2+ providers, so behaviour depends on how many providers happen to be on the classpath.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — contract
  `private static volatile AgentsRegistry INSTANCE = discover();`
  discover() runs inside LazyHolder's static initializer, so the CompositeAgentsRegistry constructor's RuntimeException("Duplicate agent name across registries: writer") is wrapped: the first AgentsRegistry.get() throws ExceptionInInitializerError, not the RuntimeException the class javadoc promises. LazyHolder is then permanently in erroneous state, so every later call to get() AND to refresh() throws NoClassDefFoundError, making the documented re-discovery recovery path unreachable for the life of the classloader.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  The mutation silently succeeds instead of throwing UnsupportedOperationException as the allAgents() javadoc ("an unmodifiable map") and the sibling EmptyAgentsRegistry (Map.of()) both promise, and it edits the live HashMap backing the cached process-wide registry, so every subsequent getAgent("writer") on the singleton throws RuntimeException("No agent found with name: writer").

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

4 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() with no argument encodes with the JVM default charset while the parser decodes the stream as UTF-8, so the returned Document's text() contains mojibake ('cafÃ©') or '?' replacement characters instead of the original page text; the same URL yields different document text depending on the JVM's platform charset.

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — correctness
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))`
  String.getBytes() encodes with the platform default charset while the DocumentParser decodes as UTF-8, so the parsed Document text is mojibake, and characters unmappable in the default charset are replaced by '?' and lost irrecoverably; load(url) on the same page returns the correct text, so the two overloads disagree on identical input.

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — contract
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset while DocumentParser implementations decode the InputStream as UTF-8 (TextDocumentParser's default), so the parsed Document's text contains mojibake or '?' replacement characters instead of the original page text; characters unmappable in the default charset are lost irreversibly. load(String) is unaffected, so the same URL yields different text through the two overloads.

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:42`** — contradicts
  `public Document load(String url) {`
  The body of load(String url) was rewritten: the Playwright navigation and error handling were extracted into a newly added public method pageContent(String url), which load(String url) now delegates to. The observable contract is preserved, but the method did not remain unchanged, and the extraction adds a new public method to the class that the intent's list of changes does not mention.

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

3 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`** — correctness
  `throw new RuntimeException("Failed to load document from GitHub: {}", ioException);`
  The RuntimeException surfaced to the caller carries the literal message "Failed to load document from GitHub: {}" — the SLF4J placeholder is not substituted by java.lang.RuntimeException(String, Throwable), so the two-arg call binds ioException as the cause and no URL is ever interpolated. The failing file is unidentifiable from the message; only the wrapped IOException's own text remains.

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`** — correctness
  `throw new RuntimeException("Failed to load document from GitHub: {}", ioException);`
  The thrown RuntimeException's message is the literal string "Failed to load document from GitHub: {}"; RuntimeException(String, Throwable) does no SLF4J-style substitution, so the content URL the placeholder was meant to carry never appears, and the caller/log sees an unfilled "{}".

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`** — contract
  `throw new RuntimeException("Failed to load document from GitHub: {}", ioException);`
  RuntimeException(String message, Throwable cause) does no brace substitution, so the thrown exception carries the literal message "Failed to load document from GitHub: {}" with no URL; the offending file is unidentifiable from the message, and in scanDirectory it is logged that way and the document is silently skipped

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

5 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  getPageSource() returns a correct Java String, but getBytes() encodes it with the platform default charset while the parser decodes with UTF-8, so the returned Document text holds mojibake or '?' replacements instead of the page characters ("caf?" / "cafÃ©"); the same URL yields different document text on different machines.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:53`** — correctness
  `return ((JavascriptExecutor) requireNonNull(wd)).executeScript("return document.readyState").equals("complete");`
  The lambda throws NullPointerException on .equals instead of returning false and retrying; WebDriverWait does not ignore NPE, so it propagates immediately and load() aborts with RuntimeException("Failed to load document") without ever waiting out the timeout or reading the page source.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))`
  String.getBytes() encodes with the platform default charset while the downstream DocumentParser decodes the stream as UTF-8, so every non-Latin-1 character is written as '?' and every accented character becomes a replacement/mojibake sequence in Document.text(). The loader silently returns a corrupted document.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — contract
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() with no explicit Charset encodes with the platform default, while DocumentParser.parse(InputStream) decodes the byte stream with its own charset (UTF-8 for the default text parser). Characters unrepresentable in the platform charset are replaced by '?' before the parser ever sees them, and representable non-ASCII bytes are re-decoded under the wrong charset, so the returned Document.text() holds mojibake or lost characters. The same URL yields different document text on two machines that differ only in default locale.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:53`** — unimplemented
  `return ((JavascriptExecutor) requireNonNull(wd)).executeScript("return document.readyState").equals("complete");`
  The only readiness condition is document.readyState == "complete", which is reached at the load event, before content that JavaScript injects asynchronously afterwards (XHR/fetch-driven rendering, SPA hydration) exists in the DOM. getPageSource() therefore captures a snapshot that can omit exactly the dynamically loaded elements the intent says are captured, and no other wait or hook is offered to cover it.

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

11 finding(s) survived refutation:

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:91`** — correctness
  `private static final Pattern SANITIZE_PATTERN_START = Pattern.compile("^(\\s|`)*(?i:python)?\\s*");`
  sanitizeInput() strips the leading "python" because the optional group is not anchored to a word boundary or fence, so the code actually POSTed to code/execute is "_version = 3" (resp. "ic = 1"). The session silently executes different code than the caller asked for, and the returned result belongs to that mutated code.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:314`** — correctness
  `return getNestedMapProperty(responseJson, "properties");`
  getNestedMapProperty returns null (line 519), executeCode returns null, and use() then dereferences it at line 213 (response.get("result")), throwing a bare NullPointerException out of use()/execute(). The null return is never checked by either caller, so the failure surfaces as an unhelpful NPE instead of the "Failed to execute code." wrapper.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:424`** — correctness
  `if (response.statusCode() == 404) {`
  The branch is unreachable: SuccessfulHttpResponse's constructor runs ensureBetween(statusCode, 200, 299), so a value of 404 can never be constructed and langchainHttpClient.execute() throws instead of returning. "File not found: missing.txt" is therefore never produced by this branch; the method's behaviour for a missing file depends entirely on whether the thrown exception's message text happens to contain the substring "404" (line 433), and it throws a RuntimeException when it does not.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:433`** — correctness
  `if (e.getMessage().contains("404")) {`
  Line 429 (response.body().getBytes(...)) throws a NullPointerException whose getMessage() is null; the catch block then calls e.getMessage().contains("404") and throws a second NullPointerException from inside the handler. The original failure and the "Failed to download file: ... API URL: ..." context are both lost.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:387`** — boundary
  `Map<String, Object> fileMetadataMap = valueList.get(0);`
  valueList.get(0) throws IndexOutOfBoundsException (empty array) or NullPointerException (missing key); both are swallowed by the surrounding catch and rethrown as RuntimeException("Failed to upload file: null API URL: ..."), hiding the actual API response.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`** — correctness
  `Object result = response.get("result");`
  use() dereferences the null map outside any try block and throws a raw NullPointerException instead of the wrapped "Failed to execute code." error the rest of the method produces.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:272`** — correctness
  `input = SANITIZE_PATTERN_START.matcher(input).replaceAll("");`
  The optional `(?i:python)?` group matches even with no backticks present, so the leading "python" is stripped and `_version = 3` / `ic = 1` is sent to the session — different code than the caller supplied, failing with a syntax/name error or silently binding the wrong variable.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:424`** — contract
  `if (response.statusCode() == 404) {`
  The branch is unreachable: SuccessfulHttpResponse's constructor runs ensureBetween(builder.statusCode, 200, 299), so statusCode() can never be 404 and the langchain4j client never returns such a response at all. The documented "File not found: ..." result is therefore only ever produced by the fallback at line 433, which depends on the literal text "404" appearing in the exception message; with any client whose exception message omits that digit string, downloadFile throws RuntimeException instead of returning the not-found string.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:429`** — correctness
  `byte[] fileBytes = response.body().getBytes(StandardCharsets.UTF_8);`
  The body was already decoded into a String by the HTTP client; re-encoding it with getBytes(UTF_8) replaces every byte sequence that is not valid UTF-8 with U+FFFD (EF BF BD). The returned Base64 string does not decode back to the original file, so binary downloads are silently corrupted rather than failing.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:314`** — contract
  `return getNestedMapProperty(responseJson, "properties");`
  getNestedMapProperty returns null (line 519), executeCode returns that null, and use() dereferences it at line 213 (response.get("result")), throwing a bare NullPointerException outside any try block instead of an error naming the malformed response. Callers of the public executeCode also receive null, which nothing documents or checks.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:357`** — contract
  `String contentType = "Content-Type: application/json\r\n\r\n";`
  The multipart part is sent declaring Content-Type: application/json while carrying arbitrary bytes, so the declared media type contradicts the payload for every file that is not JSON. A server that honours the part's declared type rejects the upload or stores it with the wrong type.

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

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — boundary
  `if (!result.getPagemap().isEmpty()) {`
  `result.getPagemap().isEmpty()` throws NullPointerException inside the stream at line 190, so `toWebSearchOrganicResults` propagates it and the whole `search(...)` call fails instead of returning results — the same no-data shape the change set out to tolerate.

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — boundary
  `if (!result.getPagemap().isEmpty()) {`
  `result.getPagemap()` returns null and `.isEmpty()` throws NullPointerException, aborting the whole `search(...)` call — the non-empty-items path the change just opened up still fails on the missing-vs-empty edge for a single item, discarding every other result in the batch.

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — contract
  `if (!result.getPagemap().isEmpty()) {`
  `toResultMetadataMap` throws NullPointerException on `getPagemap().isEmpty()`. The exception propagates out of the stream `map` in `toWebSearchOrganicResults` (line 190-197) and out of `search(...)`, so the whole search fails even though every other result was well formed. The new `isNullOrEmpty(search.getItems())` guard does not cover this: it only protects the null-items case, and the failure happens per item once items are present.

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

5 finding(s) survived refutation:

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  hasConverged returns false although both verdicts are YES: for the second element lastIndexOf(' ') is -1, so lastWord becomes the whole string "DEFINITELY\nYES" instead of "YES", and it fails the equals check against "YES". The same happens for "reasoning\nAGREE" vs "other reasoning\nAGREE", where the extracted tokens are "REASONING\nAGREE" and "REASONING\nAGREE" only by accident and differ as soon as the word before the newline differs. Splitting on the literal space character only, instead of on any whitespace, makes unanimous agreement read as non-convergence.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  Only ' ' is treated as a word separator (trim() removes surrounding whitespace but leaves interior '
' and '	'), so the first position yields lastWord "SHIP IT.
YES" instead of "YES". It does not equal the second position's "YES", so hasConverged returns false even though both verdicts are identical, and the debate keeps running to its round limit.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — contract
  `String text = p.toString().trim();`
  p.toString() throws NullPointerException out of hasConverged instead of returning a boolean, aborting the caller rather than reporting non-convergence.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  lastIndexOf(' ') only splits on the ASCII space, and the following trim() removes no interior whitespace, so the extracted "last words" are "PROCEED.\nAGREE" and "YES.\nAGREE"; they differ and hasConverged returns false even though every position ends with the same verdict, so the debate never reports convergence and runs to its round limit

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — contract
  `String text = p.toString().trim();`
  p.toString() throws NullPointerException out of hasConverged, so the same input that unanimous() evaluates without error aborts the caller when unanimousLastWord() is the configured strategy

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

7 finding(s) survived refutation:

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`** — resource
  `if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {
            return;`
  completeFromTask returns without completing messageResponse, no further event ever arrives, and no error is raised, so the streamingErrorHandler never fires either. The calling thread parks forever on messageResponse.get() at line 164 (an untimed CompletableFuture.get), hanging the agent invocation. Before this change every task event completed the future, so the call returned instead of blocking.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`** — correctness
  `messageResponse.complete(extractTextFromParts(
                task.artifacts().stream().flatMap(a -> a.parts().stream()).toList()));`
  isTerminalState is true, so the early return is skipped and the future is completed normally with extractTextFromParts over an empty stream, i.e. the empty string "". messageResponse.get() returns "" and serviceOutputParser.parseText hands the caller an empty result as though the remote agent had succeeded; the remote failure is never surfaced as an exception.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`** — boundary
  `messageResponse.complete(extractTextFromParts(
                task.artifacts().stream().flatMap(a -> a.parts().stream()).toList()));`
  isTerminalState() is true, so the guard on line 178 short-circuits and does not return; the stream over an empty artifact list joins to "" and the future is completed successfully with the empty string. invokeAgent then returns serviceOutputParser.parseText(returnType, "") - the empty string for a String-returning agent, or an output-parser failure for any other return type - so a failed/canceled/rejected remote task is reported to the caller as a successful empty answer instead of an error.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`** — boundary
  `if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {`
  completeFromTask returns without completing the future, and no later event arrives to complete it; messageResponse.get() on line 164 blocks the calling thread forever, since it is an untimed get and the error handler is never invoked. The pre-change TaskEvent branch always completed the future, so this path could not hang.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`** — contract
  `messageResponse.complete(extractTextFromParts(
                task.artifacts().stream().flatMap(a -> a.parts().stream()).toList()));`
  isTerminalState() is true, so the early return is skipped and messageResponse is completed normally with the empty string. invokeAgent() then returns serviceOutputParser.parseText(returnType, "") as a successful result: the caller sees an empty answer instead of an exception, and the remote failure is silently swallowed. For a non-String returnType the empty text is handed to an output parser that has no valid value to parse.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`** — contract
  `if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {`
  The guard only returns early when the task is non-terminal AND artifacts are empty, so a working task with a partial artifact falls through and completes messageResponse with the partial text. CompletableFuture.complete() is one-shot, so every later update - including the final terminal task carrying the full artifacts - is discarded and invokeAgent() returns a truncated response.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:71`** — undocumented
  `.withTransport(JSONRPCTransport.class, new JSONRPCTransportConfigBuilder())`
  Beyond porting to the new SDK package and builder types, the change drops the explicit `ClientConfig` with `setStreaming(false)` that previously disabled streaming, so the client now runs in the SDK's default (streaming) mode. The accompanying rework of the event consumers (terminal-state handling in `completeFromTask`) and of the error handler (swallowing SSE errors once the future is done) is the consequence of that behaviour switch, which the intent describes only as a version bump.

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
  `} else if (entry.embedded == null) {`
  The intent describes a two-way strategy: a TextSegment is filtered, anything else raises UnsupportedOperationException. The code adds an undescribed third branch: an entry whose embedded is null is neither filtered nor rejected, it is silently kept. Such entries are reachable via add(String, Embedding) and addAll(List<Embedding>), so removeAll(Filter) can silently leave rows behind instead of raising as the intent states.

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
