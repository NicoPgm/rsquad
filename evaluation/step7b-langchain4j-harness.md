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

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:74`** — correctness
  `this.indexName = getOrDefault(indexName, DEFAULT_INDEX_NAME);`
  The `createOrUpdateIndex && index != null` guard on line 71 is false, so this.indexName becomes "vectorsearch" instead of index.getName() = "products". The SearchClient built at line 88/101 is bound to "vectorsearch", so every subsequent add/addAll/findRelevant reads and writes the wrong index - and if "vectorsearch" does not exist, Azure returns an index-not-found error even though the caller named an existing index.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:71`** — boundary
  `if (createOrUpdateIndex && index != null) {`
  The condition is false, so this.indexName becomes getOrDefault(null, DEFAULT_INDEX_NAME) = "vectorsearch" and the SearchClient built at line 88/101 is bound to "vectorsearch" instead of "my-index"; every add and findRelevant then reads and writes the wrong index (or fails against a nonexistent one), while the caller-supplied index name is silently discarded — line 66 forbids passing indexName alongside index, so there is no way to reach the intended name on this path.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:71`** — contract
  `if (createOrUpdateIndex && index != null) {
            this.indexName = index.getName();`
  The `index` argument is silently discarded: the else branch sets this.indexName to DEFAULT_INDEX_NAME ("vectorsearch") because indexName is null, so searchClient at lines 85-89 / 98-102 is bound to "vectorsearch" instead of "my-custom-index", and lines 105-111 never use `index` either. Subsequent addAll/findRelevant calls read and write the wrong Azure index (findRelevant returns an empty list, or results from an unrelated index) with no error or log line.

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

7 finding(s) survived refutation:

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — correctness
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  The loop never skips metadataTextKey, so the returned map is {"text_segment"="hello world", "author"="bob"} instead of {"author"="bob"}: the segment text is re-injected as a metadata entry. The code contradicts itself — the guard on line 21 and the capacity filedsMap.size() - 1 on line 25 both assume the text key is excluded, and it is excluded only when it is the sole field.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — correctness
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  The loop calls putFields with the same key that line 43 used for the text, so the struct field "text_segment" ends up holding "bob" and the segment text "hello world" is silently lost before the vector is stored; a later read back returns the metadata value as the segment text.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — boundary
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  returns {"text": "hello world", "index": 3.0} — the segment text is copied into the returned metadata map, while the size == 1 case on line 21 returns {} for the very same key; the loop never skips metadataTextKey, so the text field leaks into the metadata of every retrieved segment that has at least one other field

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — correctness
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  putFields overwrites the field written on line 43, so the Struct stored in Pinecone carries "foo" as the text field instead of "the real content"; the segment text is silently lost and reads back wrong

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — correctness
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  The loop never skips metadataTextKey, so the returned map is {"text_segment": "hello world", "author": "bob"} - the segment text is returned as a metadata entry. The early return at line 21 and the capacity hint `filedsMap.size() - 1` at line 25 both assume that key is excluded, so behaviour is inconsistent: with one field the text key is dropped, with two or more it is kept, and the text is duplicated into TextSegment metadata on every retrieval.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — contract
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  putFields overwrites the field written at line 43, so the Struct stored in Pinecone carries "anything" as the text field instead of "hello world"; the segment text is silently lost and retrieval returns the metadata value as the segment content. Nothing in the method rejects or renames a metadata key that collides with metadataTextKey.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — correctness
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  The loop never skips metadataTextKey, so the returned map is {"text": "hello world", "author": "bob"} — the segment text is duplicated into the metadata as a field. The one-entry early return at line 21 and the capacity hint filedsMap.size() - 1 at line 25 show the text key is meant to be excluded, and it is excluded only when it is the sole field.

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

5 finding(s) survived refutation:

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — correctness
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null (it even calls writeState(key, null), which removes the entry), and ConcurrentHashMap.replaceAll throws NullPointerException on a null remapping result. rootCallEnded aborts at line 143, so registry.evict(memoryId) is never reached for EPHEMERAL scopes and flush(registry) is never reached for PERSISTENT ones, and the NPE propagates to the caller of the root agent invocation. Before this change the same value was reachable via readState(key), which returned null without throwing.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — resource
  `state.replaceAll(this::readStateBlocking);`
  blockingGet() throws inside the replaceAll mapping function, so rootCallEnded exits at line 143 before the kind dispatch: an EPHEMERAL scope is never evicted from the AgenticScopeRegistry (it stays in the registry map for the process lifetime) and a PERSISTENT scope is never flushed, so its final state is never written. The exception also surfaces from a root call that previously succeeded.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — boundary
  `state.replaceAll(this::readStateBlocking);`
  `ConcurrentHashMap.replaceAll` rejects a null remapping result (`if (newValue == null) throw new NullPointerException();`), so `rootCallEnded` throws NPE before reaching the `kind` dispatch below: an EPHEMERAL scope is never `registry.evict(memoryId)`-ed (it stays in the registry) and a PERSISTENT scope is never `flush`-ed (the final state is never persisted), and the NPE propagates to the caller that ended the root call.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — contract
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null for that key, and Map.replaceAll forbids a null remapping result: ConcurrentHashMap.replaceAll throws NullPointerException out of rootCallEnded. The key has already been removed from state by the nested writeState(key, null), later entries are never resolved, and the EPHEMERAL eviction / PERSISTENT flush below never runs, so the scope stays in the registry and is never persisted while the exception propagates to the workflow caller.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — contract
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null, and ConcurrentHashMap.replaceAll rejects a null remapping value, so rootCallEnded throws NullPointerException before eviction/flush ever runs — the ephemeral scope is never evicted and the persistent scope is never flushed

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

3 finding(s) survived refutation:

- **`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:37`** — resource
  `} catch (Exception e) {
            throw new RuntimeException(e);`
  The catch on line 37 rethrows as RuntimeException without calling session.close(); the partially built object is discarded, so the native OrtSession and the model weights it loaded (typically hundreds of MB off-heap) stay allocated until JVM exit. Repeating the failing construction, e.g. in a retry or per-request factory, grows native memory each time since OrtSession is only released by an explicit close().

- **`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:36`** — resource
  `this.tokenizer = HuggingFaceTokenizer.newInstance(Paths.get(pathToTokenizer), tokenizerOptions);`
  the OrtSession created on line 28 has already loaded the model into native memory and is never closed: the exception is converted to RuntimeException, the partially built instance is discarded, and no reference to the session survives, so its native memory is leaked for the life of the process (and leaks again on every retried construction).

- **`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:36`** — resource
  `this.tokenizer = HuggingFaceTokenizer.newInstance(Paths.get(pathToTokenizer), tokenizerOptions);
        } catch (Exception e) {
            throw new RuntimeException(e);`
  The catch rethrows as RuntimeException while the already-created OrtSession is never closed; the constructed object is discarded, so nothing can ever call session.close() and the native model memory stays allocated for the JVM lifetime (OrtSession releases native memory only via close(), it has no finalizer). Repeated construction attempts, e.g. a retry loop around model loading, accumulate one leaked model per attempt.

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

5 finding(s) survived refutation:

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`** — contract
  `if (node.has("$ref")) {
            return JsonReferenceSchema.builder()`
  The new $ref branch is tested before the type/no-type branch, so jsonNodeToJsonSchemaElement returns a JsonReferenceSchema for the root node, and line 44 `builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema")))` throws ClassCastException: JsonReferenceSchema cannot be cast to JsonObjectSchema. The exception escapes the loop, so toolSpecificationListFromMcpResponse yields no tools at all - every other tool of that server is lost too. Before this change the same schema fell into the typeNode == null branch and produced a (degraded but valid) JsonObjectSchema. The root $defs are also dropped, since the $ref return happens before the $defs collection at line 103.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`** — contract
  `if (node.has("$ref")) {`
  jsonNodeToJsonSchemaElement now returns a JsonReferenceSchema for that node, so the cast at line 44, builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema"))), throws ClassCastException and the whole toolSpecificationListFromMcpResponse call aborts, losing every tool in the response. Before this change the same input fell through to the typeNode == null branch and produced a JsonObjectSchema without crashing. The early return also skips the new $defs block below, so the sibling $defs is discarded.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:106`** — boundary
  `for (Map.Entry<String, JsonNode> entry : ((ObjectNode) defsNode).properties()) {`
  node.has("$defs") is true for an explicitly-null field and node.get(...) returns a NullNode rather than Java null, so the guard defsNode != null passes and the cast to ObjectNode throws ClassCastException, aborting conversion of the entire tool list instead of skipping the empty definitions block.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:44`** — contract
  `builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema")));`
  The new $ref branch at line 76 returns a JsonReferenceSchema, so the unchecked cast to JsonObjectSchema throws ClassCastException out of toolSpecificationListFromMcpResponse, aborting the whole tool list rather than one tool. Before this change the same input fell through to the typeNode == null branch and produced a JsonObjectSchema.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:237`** — contract
  `return ref;`
  extractReferenceKey returns the whole pointer "#/components/schemas/Foo" as the reference name, while the definitions map built at line 107 is keyed by bare names ("Foo"), so the produced JsonReferenceSchema points at a definition key that does not exist and the argument schema handed to the model contains an unresolvable reference.

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

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`** — correctness
  `WHERE ranked.score >= ?`
  Returns an empty EmbeddingSearchResult. minScore is a cosine-similarity threshold in [0,1] (embeddingOnlySearch compares it against (2 - distance)/2), but here it is compared against the RRF score built at line 542, whose maximum is 1.0/(rrfK+1) + 1.0/(rrfK+1) = 2/61 = 0.0328 with the default rrfK=60. Every row is filtered out, so the best-matching document is silently dropped instead of returned.

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`** — boundary
  `WHERE ranked.score >= ?`
  Returns an empty result list for every query. The RRF score assembled two lines above is COALESCE(1.0/(60+v.rnk),0.0)+COALESCE(1.0/(60+k.rnk),0.0), whose maximum possible value is 1/61+1/61 = 0.0328 for a document ranked first in both CTEs, so the >= comparison against minScore filters out every row at any minScore above 0.0328. The same request against the VECTOR path (embeddingOnlySearch, line 448) compares minScore against a 0..1 normalised cosine score, so switching a store to HYBRID silently turns non-empty results into no results.

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:565`** — contract
  `stmt.setDouble(4, minScore);`
  Returns an empty result list. request.minScore() is compared against the RRF score COALESCE(1.0/(60+v.rnk),0.0)+COALESCE(1.0/(60+k.rnk),0.0), whose maximum possible value is 2/(rrfK+1) = 0.0328, not against the 0..1 cosine similarity that embeddingOnlySearch produces and that minScore is defined against; every threshold above 0.0328 filters out all rows silently. The same rescaling makes the score field of every returned EmbeddingMatch ~0.03 instead of a 0..1 relevance, so callers that threshold or display scores from a VECTOR-mode store break when the mode is switched.

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

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — contract
  `private static volatile AgentsRegistry INSTANCE = discover();`
  discover() runs inside LazyHolder's static initializer, so the RuntimeException thrown at line 82 escapes as ExceptionInInitializerError and LazyHolder is left permanently erroneous. Every later AgentsRegistry.get() throws NoClassDefFoundError("Could not initialize class ...LazyHolder") instead of the documented RuntimeException, and refresh() cannot recover either — its own body touches LazyHolder and throws NoClassDefFoundError before reaching the re-assignment, so the documented re-discovery path is unusable for the rest of the JVM's life.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  allAgents() hands out the live HashMap field, contrary to the declared "@return an unmodifiable map" (line 24) and to EmptyAgentsRegistry, which returns Map.of(). The mutation succeeds and permanently alters the cached singleton: the following AgentsRegistry.get().getAgent("a") throws RuntimeException("No agent found with name: a") — or silently returns the substituted instance.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — contract
  `private static volatile AgentsRegistry INSTANCE = discover();`
  discover() runs inside LazyHolder's static initializer, so the RuntimeException thrown at line 82 surfaces as ExceptionInInitializerError, not the documented RuntimeException, and LazyHolder is permanently marked erroneous. Every later AgentsRegistry.get() AND AgentsRegistry.refresh() then throws NoClassDefFoundError (refresh() assigns to LazyHolder.INSTANCE, which touches the failed class), so the documented recovery path 'Call refresh() to force re-discovery' cannot run for the lifetime of the class loader.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  allAgents() is documented as returning 'an unmodifiable map' and the other implementation honours that with Map.of(), but the composite hands back the live private HashMap. The mutation succeeds and permanently alters the cached singleton: getAgent("x") afterwards returns the caller-injected agent, or every getAgent() throws 'No agent found' after a clear(). The mutation also bypasses the duplicate-name check the constructor exists to enforce.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  The call succeeds instead of throwing UnsupportedOperationException as the allAgents() javadoc ("an unmodifiable map") promises: the internal HashMap of the cached singleton registry is mutated, so every later getAgent() across the JVM sees the injected or removed entry, and the constructor's duplicate-name invariant is silently broken. EmptyAgentsRegistry returns Map.of(), so the two implementations of the same method disagree on mutability.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — contract
  `private static volatile AgentsRegistry INSTANCE = discover();`
  The throw happens during LazyHolder's static initializer, so the first AgentsRegistry.get() fails with ExceptionInInitializerError and the class is permanently marked erroneous. Every subsequent get() throws NoClassDefFoundError, and refresh() cannot recover because it also touches LazyHolder and throws NoClassDefFoundError before discover() is ever re-run — the javadoc's documented recovery path ("Call refresh() to force re-discovery") is unreachable for the whole life of the JVM.

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

5 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() with no Charset encodes with the platform default charset, so \u4f60\u597d is unmappable and becomes '?' bytes; the parser (which decodes as UTF-8) then produces a Document whose text reads "caf? ??" instead of "caf\u00e9 \u4f60\u597d". The same call on a UTF-8 JVM returns the correct text, so the loaded document content silently differs by host locale.

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — correctness
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))`
  String.getBytes() encodes with the platform default charset while the parser decodes the stream as UTF-8, so every non-ASCII character is turned into replacement characters or mojibake in the returned Document text; characters outside the default charset (CJK under windows-1252) are irrecoverably replaced by '?'. The single-argument load(url) path, which keeps the String, returns correct text for the same page, so the two overloads disagree on the same input.

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — contract
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset while every langchain4j DocumentParser (TextDocumentParser, ApacheTikaDocumentParser) decodes the stream as UTF-8, so multi-byte characters are re-decoded as mojibake, and characters unrepresentable in the default charset are irreversibly replaced by '?' before the parser ever sees them. The returned Document text differs from page.content(); the single-argument load(url) path, which never round-trips through bytes, keeps the same text intact.

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`** — correctness
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))`
  String.getBytes() encodes the page text with the platform default charset while the parser decodes the byte stream as UTF-8 (declared or assumed), so the parsed Document text contains mojibake or U+FFFD replacement characters instead of the original characters; unmappable characters are silently replaced with '?' before the parser ever sees them.

- **`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:43`** — stale-intent
  `String pageContent = pageContent(url);`
  load(String url) was rewritten: its body was extracted into a new public method pageContent(String url), which also adds a new info log ("Navigating to URL: {}") and rewords the debug log from "Waiting webpage fully loaded" to "Web page fully loaded". The returned Document is equivalent, but the method and the class's public API surface did change, and the intent's "Changes Made" list does not mention the new public pageContent method.

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
  The thrown RuntimeException's message is the literal string "Failed to load document from GitHub: {}" - the SLF4J placeholder is passed to the RuntimeException(String, Throwable) constructor, which does no formatting, so the top line of the stack trace and any getMessage() call show "{}" instead of the failure detail.

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`** — contract
  `throw new RuntimeException("Failed to load document from GitHub: {}", ioException);`
  RuntimeException(String, Throwable) does no SLF4J-style substitution, so the thrown exception's message is the literal text "Failed to load document from GitHub: {}" with no file URL; the caller sees an unformatted placeholder instead of the content identifier the message promises.

- **`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`** — contract
  `throw new RuntimeException("Failed to load document from GitHub: {}", ioException);`
  RuntimeException(String, Throwable) performs no SLF4J-style substitution, so the propagated exception message is the literal text "Failed to load document from GitHub: {}" with no URL or file identity; the caller sees a message that names no document.

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

6 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset, so the parser decodes mismatched bytes: "café" comes back as "cafÃ©" (or with U+FFFD), and characters not representable in the default charset (CJK under windows-1252) are encoded as '?' and lost irrecoverably. The returned Document's text is corrupted, and the same URL yields different content depending on the machine's locale.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:55`** — correctness
  `pageContent = webDriver.getPageSource();`
  The assignment succeeds inside the try, so the NullPointerException is raised at line 59 by pageContent.getBytes(), outside the catch block. It escapes as a bare NPE with no message instead of the RuntimeException("Failed to load document", e) every other failure in load() produces, so callers catching that contract see an unwrapped NPE.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — correctness
  `Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));`
  String.getBytes() encodes with the platform default charset while the parser decodes as UTF-8, so the returned Document's text contains mojibake or U+FFFD replacement characters instead of the page's characters; the same URL yields different document text depending on the machine's locale.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:55`** — boundary
  `pageContent = webDriver.getPageSource();`
  pageContent is null and line 59 dereferences it outside the try block, so a raw NullPointerException escapes load() instead of the wrapped RuntimeException("Failed to load document", e) every other failure path produces.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`** — contract
  `documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))`
  String.getBytes() encodes with the platform default charset while DocumentParser implementations (e.g. TextDocumentParser) decode the stream as UTF-8, so the returned Document text contains mojibake or U+FFFD replacement characters instead of the page's characters; the same page yields different Document text on different hosts.

- **`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:53`** — unimplemented
  `return ((JavascriptExecutor) requireNonNull(wd)).executeScript("return document.readyState").equals("complete");`
  The only wait condition is document.readyState == "complete", which is satisfied as soon as the initial document and its subresources have loaded. Content injected afterwards by asynchronous JavaScript (XHR/fetch-driven or SPA rendering) is not awaited, so getPageSource() can return a page missing exactly the dynamically loaded elements the intent says are captured.

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

10 finding(s) survived refutation:

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:91`** — correctness
  `private static final Pattern SANITIZE_PATTERN_START = Pattern.compile("^(\\s|`)*(?i:python)?\\s*");`
  sanitizeInput strips the leading "python" because (?i:python)? is optional and unanchored to any delimiter, so the code sent to the interpreter becomes "ic = 5" / "_path = '/tmp'" — a different program that either fails to parse or silently binds the wrong name.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`** — correctness
  `Object result = response.get("result");`
  getNestedMapProperty returns null, executeCode returns that null unchecked, and use() throws NullPointerException on response.get("result") — outside executeCode's try, so it escapes uncaught to the caller instead of the "Failed to execute code." RuntimeException.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:429`** — correctness
  `byte[] fileBytes = response.body().getBytes(StandardCharsets.UTF_8);`
  The body has already been decoded to a String; every byte sequence that is not valid UTF-8 became U+FFFD, and re-encoding with getBytes(UTF_8) emits 0xEF 0xBF 0xBD. The returned Base64 therefore decodes to corrupted content that does not match the remote file.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:433`** — correctness
  `if (e.getMessage().contains("404")) {`
  e.getMessage() is null and the catch block itself throws NullPointerException, discarding the original failure: the caller sees an NPE from line 433 instead of the intended "File not found" return or the "Failed to download file" RuntimeException carrying the cause.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:387`** — boundary
  `Map<String, Object> fileMetadataMap = valueList.get(0);`
  valueList.get(0) throws IndexOutOfBoundsException on the empty array (and convertValue returns null, so a missing "value" key throws NullPointerException). The exception is caught at line 390 and rethrown as RuntimeException("Failed to upload file: Index 0 out of bounds for length 0 ..."), reporting an index error instead of the actual server response.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`** — correctness
  `Object result = response.get("result");`
  getNestedMapProperty returns null at line 314, executeCode returns null, and use() dereferences it at line 213, throwing NullPointerException out of the @Tool method instead of the wrapped "Failed to execute code." error the rest of the method produces.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`** — contract
  `Object result = response.get("result");`
  getNestedMapProperty returns null at line 519, executeCode returns that null, and use()/execute() dereference it at line 213 with a raw NullPointerException instead of the wrapped "Failed to execute code." error the surrounding code returns for every other failure.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:429`** — correctness
  `byte[] fileBytes = response.body().getBytes(StandardCharsets.UTF_8);`
  The body was already decoded to a String; every byte sequence that is not valid UTF-8 has become U+FFFD, and re-encoding produces EF BF BD. The Base64 string returned to the caller decodes to a corrupted file that no longer matches the remote one, silently and with no error.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:272`** — correctness
  `input = SANITIZE_PATTERN_START.matcher(input).replaceAll("");`
  SANITIZE_PATTERN_START is `^(\s|`)*(?i:python)?\s*` with no word boundary after the optional keyword, so the leading "python" is stripped and `_version = 3` is what gets sent to the session. Different code than the caller asked for is executed, and the failure surfaces as an unrelated Python error.

- **`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:424`** — contract
  `if (response.statusCode() == 404) {`
  langchainHttpClient.execute returns a SuccessfulHttpResponse only for 2xx and throws for anything else, so statusCode() never holds 404 and this branch is unreachable dead code. The same is true of the `else` at line 315 in executeCode. The 404 case is instead handled only by the string test `e.getMessage().contains("404")` at line 433, which depends on the message text of whatever exception the pluggable HTTP client happens to throw.

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

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — contract
  `if (!result.getPagemap().isEmpty()) {`
  toWebSearchOrganicResults -> toResultMetadataMap dereferences the null map and throws NullPointerException, so search() aborts and returns nothing even though the guard added at line 189 established that items are present. Reachable on the same path the new method walks.

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — boundary
  `if (!result.getPagemap().isEmpty()) {`
  toResultMetadataMap dereferences null at line 171 and throws NullPointerException, which propagates out of the new toWebSearchOrganicResults stream (line 190-197) and out of search(), so the entire search call fails even though every other result item mapped fine.

- **`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`** — contract
  `if (!result.getPagemap().isEmpty()) {`
  `toWebSearchOrganicResults` maps that result and throws NullPointerException at the `.isEmpty()` call, so the whole `search(...)` call fails instead of returning the other results.

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

7 finding(s) survived refutation:

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  Only the ASCII space is treated as a separator, so lastIndexOf(' ') lands on the space before "proceed" and lastWord becomes "PROCEED
YES" instead of "YES"; the interior newline survives trim(), the comparison with "YES" fails and hasConverged returns false although both positions end in the same verdict — the debate loop keeps running past a real consensus.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — contract
  `String text = p.toString().trim();`
  p.toString() throws NullPointerException and hasConverged aborts instead of returning a boolean, whereas the sibling unanimous() tolerates the same input via Objects.equals.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  Only the literal ' ' character is treated as a word separator, so for the first position lastIndexOf(' ') finds the space inside "ship it." and lastWord becomes "IT.\nAGREE" (whitespace embedded, so not a last word at all), while the second yields "AGREE". The strings differ and hasConverged returns false, reporting no convergence for two positions that both end in AGREE. Symmetrically, two positions ending in different verdicts can compare equal when the trailing newline-joined tails happen to match, returning true.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — contract
  `String text = p.toString().trim();`
  p.toString() throws NullPointerException, propagating out of hasConverged and aborting the debate loop instead of returning a boolean. The sibling strategy unanimous() tolerates the same input (Objects.equals is null-safe), so the two implementations of the same interface behave incomparably on it.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:9`** — contract
  `boolean hasConverged(Collection<Object> positions);`
  Does not compile: Java generics are invariant, so `List<String>` is not a `Collection<Object>`. Every caller must copy its positions into a `new ArrayList<Object>(...)` first; `Collection<?>` would accept them directly.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`** — correctness
  `String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();`
  `lastIndexOf(' ')` only searches for a space, so `lastWord` becomes the whole remainder after the last space — "LOWER.\nYES" vs "BETTER.\nYES" — which compare unequal, so `hasConverged` returns false even though both positions end with the same verdict, and the debate never terminates on convergence.

- **`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`** — contract
  `String text = p.toString().trim();`
  Throws NullPointerException on `p.toString()`, whereas the sibling strategy `unanimous()` handles the same input without throwing because it compares with `Objects.equals`; the two implementations of the same interface disagree on whether null elements are permitted.

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

6 finding(s) survived refutation:

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`** — correctness
  `if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {`
  On update 1 the guard is false (artifacts are non-empty), so `messageResponse.complete("Paris is the")` runs. CompletableFuture.complete is idempotent, so updates 2 and 3 are discarded, and `messageResponse.get()` at line 164 returns the truncated first chunk. invokeAgent returns "Paris is the" as the agent's answer.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:187`** — contract
  `|| state == TaskState.TASK_STATE_FAILED`
  isTerminalState returns true, the early return at line 178-180 is skipped, and line 181 calls `messageResponse.complete("")`. `messageResponse.get()` returns the empty string instead of throwing, so the failure is swallowed: `serviceOutputParser.parseText(returnType, "")` runs on it and invokeAgent hands the caller an empty successful result for a task the server reported as failed/canceled/rejected.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`** — resource
  `if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {`
  completeFromTask returns without ever completing messageResponse, and no other code path completes it, so messageResponse.get() at line 164 blocks the calling thread forever. Before the change a TaskEvent always completed the future (with the joined artifact text, or an empty string), so this input returned instead of hanging.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`** — boundary
  `messageResponse.complete(extractTextFromParts(
                task.artifacts().stream().flatMap(a -> a.parts().stream()).toList()));`
  isTerminalState is true, so the early return is skipped and messageResponse is completed normally with the empty string. invokeAgent then returns serviceOutputParser.parseText(returnType, "") - the caller sees a successful empty answer instead of an error, and for a non-String returnType the empty text is fed to the output parser.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`** — contract
  `messageResponse.complete(extractTextFromParts(
                task.artifacts().stream().flatMap(a -> a.parts().stream()).toList()));`
  isTerminalState() returns true for those three states, so the guard on line 178 does not return and the future is completed *successfully* with the empty string. invokeAgent() then returns serviceOutputParser.parseText(returnType, "") instead of propagating an error: a remote task that failed, was cancelled or was rejected is reported to the caller as a successful invocation with an empty answer.

- **`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:71`** — undocumented
  `.withTransport(JSONRPCTransport.class, new JSONRPCTransportConfigBuilder())`
  Beyond renaming the SDK packages, the client is now built without any ClientConfig, dropping the explicit setStreaming(false) that previously forced non-streaming request/response. The agent call now runs over a streaming exchange, which is why the event handling had to gain a terminal-state guard and the error handler had to start swallowing post-completion SSE errors. The intent describes only a version bump and does not mention this runtime behaviour change.

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

2 finding(s) survived refutation:

- **`langchain4j/src/main/java/dev/langchain4j/store/embedding/inmemory/InMemoryEmbeddingStore.java:101`** — contract
  `entries.removeIf(entry -> entry.id.equals(id));`
  Silently returns having removed nothing instead of rejecting the argument: entry.id is non-null (Entry's constructor calls ensureNotBlank), so entry.id.equals(null) is false for every entry and the predicate never matches. Code holding an EmbeddingStore reference and relying on the id validation the interface's default remove(String) performs before delegating gets no IllegalArgumentException here, so a bad id read from config or user input is swallowed and the caller believes the deletion succeeded.

- **`langchain4j/src/main/java/dev/langchain4j/store/embedding/inmemory/InMemoryEmbeddingStore.java:118`** — contradicts
  `} else if (entry.embedded == null) {`
  The described strategy has two outcomes per entry: TextSegment proceeds, anything else raises UnsupportedOperationException. The code adds a third, unstated outcome: an entry whose embedded is null is silently kept (returns false) instead of raising. Entries added via add(String, Embedding) or addAll(List<Embedding>) always have a null embedded, so removeAll(Filter) quietly leaves them in the store on a store the intent says would throw.

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
