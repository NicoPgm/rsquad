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

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:73`** — correctness
  `} else {
            this.indexName = getOrDefault(indexName, DEFAULT_INDEX_NAME);`
  The name carried by the supplied `index` is ignored: this.indexName becomes "vectorsearch", so the SearchClient built at lines 85-89/98-102 targets index "vectorsearch" instead of "my-existing-index". Subsequent add/findRelevant calls read and write the wrong index (or fail with a 404 from Azure if "vectorsearch" does not exist), and deleteIndex() at line 207 would target "vectorsearch" as well.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:71`** — correctness
  `if (createOrUpdateIndex && index != null) {
            this.indexName = index.getName();
        } else {`
  the branch is skipped and this.indexName becomes DEFAULT_INDEX_NAME ("vectorsearch"), so searchClient is built against "vectorsearch" instead of "my-index"; all subsequent add/findRelevant calls read and write the wrong (or nonexistent) index while the supplied index object is silently ignored

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:71`** — contract
  `if (createOrUpdateIndex && index != null) {
            this.indexName = index.getName();
        } else {
            this.indexName = getOrDefault(indexName, DEFAULT_INDEX_NAME);`
  the branch falls through to getOrDefault(null, DEFAULT_INDEX_NAME), so this.indexName becomes "vectorsearch" and the SearchClient built at lines 85/98 is bound to the default index instead of the caller-supplied index; all subsequent add/findRelevant calls read and write the wrong Azure index (or fail because "vectorsearch" does not exist), and index.getName() is silently discarded

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
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
  The loop never skips metadataTextKey, so the returned map is {"text"="hello world", "author"="bob"} — the segment text is injected as a metadata entry instead of only "author". The pre-sized HashMap<>(size-1) shows only size-1 entries were intended, and the early-return guard on line 21 handles that case only when the map has exactly one field.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — correctness
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  putFields overwrites the field written on line 43, so the produced Struct contains text="some-metadata-value" and the segment's actual text "hello world" is silently dropped; retrieval later returns the metadata value as the segment text.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — correctness
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  the loop never skips metadataTextKey, so the returned metadata map contains {"text": "hello", "author": "bob"} — the segment text is leaked into the metadata as an extra entry. The special-case guard on line 21 only removes it when it is the only field, so any document with >=1 real metadata field round-trips with a spurious "text" metadata entry.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — correctness
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  putFields overwrites the field written on line 43, so the struct stored in Pinecone holds "other" instead of the segment text; the segment's text is silently lost and retrieval returns the metadata value as the document text.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — correctness
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  the loop never skips metadataTextKey, so the returned metadata map contains {"text": "hello world", "author": "bob"} — the segment's text is injected as a metadata field, contradicting the size==1 short-circuit at line 21 and the size()-1 capacity hint at line 25, and round-tripping a stored segment yields extra metadata that was never set by the caller.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`** — contract
  `metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());`
  putFields overwrites the field previously set at line 43, so the Struct sent to Pinecone contains "text" -> "some other value" and the segment's actual text "hello" is silently lost; reads of that vector return the wrong text.

- **`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`** — correctness
  `for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {`
  the loop never skips metadataTextKey, so the returned metadata map contains {"text":"hello","author":"bob"} — the segment text is leaked into the metadata, contradicting the single-entry branch on line 21 which strips it (and making the map sized filedsMap.size()-1 undersized)

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
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
  readStateBlocking returns null (and removes the key via writeState), and ConcurrentHashMap.replaceAll explicitly rejects a null result, so rootCallEnded throws NullPointerException before eviction/flush ever happens — the scope is never evicted or persisted.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — boundary
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null, and ConcurrentHashMap.replaceAll throws NullPointerException on the null replacement value; the exception propagates out of rootCallEnded, so registry.evict(memoryId) / flush(registry) never run and the scope is neither evicted nor persisted.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — contract
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null; ConcurrentHashMap.replaceAll explicitly throws NullPointerException on a null replacement value, so rootCallEnded aborts with an NPE. The map has already been mutated by the nested writeState(key, null) (which removed the key), so the scope is left partially resolved and neither evict nor flush runs.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:147`** — resource
  `registry.evict(memoryId);`
  The exception propagates out of state.replaceAll(...) at the top of rootCallEnded, so registry.evict(memoryId) (ephemeral) and flush(registry) (persistent) are never reached: the scope stays in the registry forever and persistent state is never written, whereas before the change the same failure only surfaced at the later readState call and eviction/flush still ran.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`** — correctness
  `state.replaceAll(this::readStateBlocking);`
  readStateBlocking returns null (and writeState has already removed the key), so ConcurrentHashMap.replaceAll throws NullPointerException out of rootCallEnded, aborting eviction/persistence of the scope.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
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
  the OrtSession created on line 28 is never closed before the constructor rethrows as RuntimeException, leaking the native session (and its loaded model memory) for the lifetime of the JVM

- **`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:28`** — resource
  `this.session = this.environment.createSession(modelPath, options);`
  the already-created OrtSession (and its native ONNX Runtime model memory) is never closed: the catch block on line 37 rethrows a RuntimeException and the class exposes no close()/AutoCloseable path, so the native session handle leaks for the lifetime of the JVM on every failed construction

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
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

**The replay did not run: expected str, bytes or os.PathLike object, not int**

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
  The score fed into this predicate is an RRF score whose maximum possible value is `1.0/(rrfK+1) + 1.0/(rrfK+1)` = 2/61 ≈ 0.0328 (a document ranked #1 in both CTEs). Therefore `score >= 0.7` is false for every row and `hybridSearch` always returns an empty `EmbeddingSearchResult`, silently, even when many documents match both the vector and keyword searches. The same `minScore` value against the same data returns matches in VECTOR mode.

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`** — correctness
  `WHERE ranked.score >= ?`
  The parameter bound at index 4 is the caller's minScore, but ranked.score is a Reciprocal Rank Fusion sum whose maximum possible value is 1.0/(rrfK+1) + 1.0/(rrfK+1) = 0.0328 for rrfK=60 (best rank is 1 in both CTEs). Every row is filtered out, so hybridSearch returns an empty EmbeddingSearchResult for any minScore >= 0.033, while the identical request in VECTOR mode (where score is a cosine similarity in [0,1]) returns matches.

- **`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`** — contract
  `WHERE ranked.score >= ?`
  The value bound to this parameter is the request's minScore, but the `score` column here is a Reciprocal Rank Fusion sum whose maximum possible value is 1.0/(rrfK+1) + 1.0/(rrfK+1) = 0.0328 for rrfK=60, not a cosine similarity in [0,1] as in embeddingOnlySearch. Every row is filtered out and hybridSearch returns an empty EmbeddingSearchResult, even for exact matches, so the same request that returns hits in VECTOR mode silently returns nothing in HYBRID mode.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
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
  The first call to AgentsRegistry.get() triggers LazyHolder's static initializer, which propagates the RuntimeException from the CompositeAgentsRegistry constructor wrapped as ExceptionInInitializerError instead of the documented RuntimeException. Every later call to get() throws NoClassDefFoundError because LazyHolder is permanently in erroneous state, and refresh() cannot recover since it also touches LazyHolder.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  The mutation succeeds instead of throwing UnsupportedOperationException as the allAgents() javadoc ("an unmodifiable map") promises, and permanently alters the shared registry state seen by all subsequent getAgent(...) calls.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — contract
  `private static volatile AgentsRegistry INSTANCE = discover();`
  CompositeAgentsRegistry's constructor throws RuntimeException inside the static initializer of LazyHolder, so the first get() fails with ExceptionInInitializerError and every subsequent call to get() or refresh() fails with NoClassDefFoundError; the documented recovery path refresh() can never re-run discover() because the holder class is permanently in the erroneous state.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  The mutation succeeds and permanently alters the shared singleton registry, contrary to the interface contract that allAgents() returns an unmodifiable map (EmptyAgentsRegistry returns Map.of(), which throws UnsupportedOperationException for the same call), so behaviour differs by provider count and registry state can be corrupted.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`** — contract
  `return mergedAgents;`
  The documented contract of allAgents() ("an unmodifiable map") is broken: the internal HashMap is handed out directly, so the mutation succeeds and permanently corrupts the shared registry state for all subsequent getAgent()/allAgents() calls, instead of raising UnsupportedOperationException as the EmptyAgentsRegistry (Map.of()) path does.

- **`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`** — contract
  `private static volatile AgentsRegistry INSTANCE = discover();`
  The RuntimeException thrown at line 82 escapes the LazyHolder static initializer, so get() fails with ExceptionInInitializerError and every later call — including refresh(), which also touches LazyHolder.INSTANCE — fails with NoClassDefFoundError. The documented recovery path ("Call refresh() to force re-discovery") can never succeed for the rest of the JVM's life.

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

**The replay did not run: not started — 5.0950 USD spent, and one more case could cross the --max-usd 8.00 cap**

## `langchain4j-0626661`

fix: Include failing file URL in GitHubDocumentLoader load-failure exception message (#5684)

| | |
|---|---|
| introduced in | `aaddb9226` |
| file | `document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java` |
| detectable from diff | yes |

**The replay did not run: not started — 5.0950 USD spent, and one more case could cross the --max-usd 8.00 cap**

## `langchain4j-f274731`

fix: Encode page content as UTF-8 in SeleniumDocumentLoader (#5671)

| | |
|---|---|
| introduced in | `36c175190` |
| file | `document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java` |
| detectable from diff | weak |

**The replay did not run: not started — 5.0950 USD spent, and one more case could cross the --max-usd 8.00 cap**

## `langchain4j-23098bd`

fix: Preserve binary bytes in Azure dynamic sessions file download (#5652)

| | |
|---|---|
| introduced in | `1fab3b7e4` |
| file | `code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java` |
| detectable from diff | yes |

**The replay did not run: not started — 5.0950 USD spent, and one more case could cross the --max-usd 8.00 cap**

## `langchain4j-575eb46`

fix: Skip search results with unresolvable URIs in GoogleCustomWebSearchEngine (#5628)

| | |
|---|---|
| introduced in | `b246cfde7` |
| file | `web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java` |
| detectable from diff | weak |

**The replay did not run: not started — 5.0950 USD spent, and one more case could cross the --max-usd 8.00 cap**

## `langchain4j-0d16d28`

fix: unanimousLastWord convergence to normalize verdict token (#5479)

| | |
|---|---|
| introduced in | `8b6aeead7` |
| file | `langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java` |
| detectable from diff | weak |

**The replay did not run: not started — 5.0950 USD spent, and one more case could cross the --max-usd 8.00 cap**

## `langchain4j-34b8d34`

fix: Surface failed A2A tasks as exceptions instead of empty results (#5471)

| | |
|---|---|
| introduced in | `a24e4f9d3` |
| file | `langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java` |
| detectable from diff | weak |

**The replay did not run: not started — 5.0950 USD spent, and one more case could cross the --max-usd 8.00 cap**

## `langchain4j-95a3aff`

Fix filtering for non-TextSegment entries in InMemoryEmbeddingStore (#5405)

| | |
|---|---|
| introduced in | `2b2c09f05` |
| file | `langchain4j/src/main/java/dev/langchain4j/store/embedding/inmemory/InMemoryEmbeddingStore.java` |
| detectable from diff | weak |

**The replay did not run: not started — 5.0950 USD spent, and one more case could cross the --max-usd 8.00 cap**

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

Model `claude-opus-5`, 59 call(s) across 15 case(s), 5.0950 USD billed. 0 finding(s) refused by the guards. cache read 97062 tokens against 7583 written
