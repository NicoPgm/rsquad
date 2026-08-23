# Evaluation replay

**4 scorable case(s) of 7 in the set.**

This report does not contain a detection rate and cannot: the verdict line under
each case is a human judgement. Fill them in, then read the fractions below with
their denominators visible — never as a percentage. On a handful of cases a 25 %
rate and a 75 % one are the same measurement.

## `spring-ai-b1384c8`

Fix `OpenAiAudioTranscriptionModel` leaking the stream on cancellation (#6759)

| | |
|---|---|
| introduced in | `fc9286cb3` |
| file | `models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java` |
| detectable from diff | weak |

7 finding(s) survived refutation:

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`** — correctness
  `TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);`
  `params` is built once at assembly time and holds a single `MultipartField<InputStream>` wrapping one `ByteArrayInputStream` (buildParams line 178). The first subscription drains that stream; the second subscription passes the same exhausted stream to `createStreaming`, so the request is sent with an empty/zero-byte audio part and the API rejects it or returns an empty transcription instead of repeating the first result.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:154`** — resource
  `Flux<TranscriptionStreamEvent> chunks = Flux.create(sink -> this.openAiClientAsync.audio()`
  The sink never registers an onCancel/onDispose handler, so the `AsyncStreamResponse` returned by `createStreaming(params)` is never closed. The underlying HTTP streaming connection and its buffered events stay alive until the server ends the response; repeated cancelled streams accumulate open connections.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`** — resource
  `.subscribe(sink::next)`
  Nothing is registered on the sink (no `sink.onCancel`/`sink.onDispose`), so the underlying `AsyncStreamResponse` returned by `createStreaming` is never closed: the HTTP connection stays open and events keep being pushed into `sink::next` (dropped) until the server finishes the stream. The connection/handle is leaked per cancelled call.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:169`** — correctness
  `String text = extractStreamEventText(event);`
  `extractStreamEventText` falls through to `return "";` and the Flux still emits an `AudioTranscriptionResponse` whose transcript text is the empty string, so a consumer using `.last()`/`.blockLast()` on the stream observes an empty transcription instead of transcribed text.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`** — resource
  `.subscribe(sink::next)`
  The `AsyncStreamResponse` returned by `createStreaming(...)` is never closed: no `sink.onCancel`/`onDispose` hook is registered, so the underlying HTTP response body and connection stay open until the server finishes streaming, leaking connections on every cancelled stream.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`** — contract
  `TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);`
  `params` is built once outside the `Flux.create` lambda and holds a single `ByteArrayInputStream` (created in `buildParams`) that is already at EOF after the first request; the second `createStreaming(params)` call uploads a zero-byte file, so the request fails or returns an empty transcription instead of re-sending the audio.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:117`** — undocumented
  `OpenAiAudioTranscriptionOptions mergedOptions = OpenAiAudioTranscriptionOptions.builder()`
  Beyond adding stream(), the existing call() path was rewritten: the previous explicit type check that threw IllegalArgumentException for prompt options that are not OpenAiAudioTranscriptionOptions was removed in favour of a builder merge, changing observable behaviour of call() for callers passing foreign option types. The intent does not mention altering call().

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `spring-ai-4fbb484`

Fix Milvus metadata integer values returned as Long instead of Double

| | |
|---|---|
| introduced in | `0065949d5` |
| file | `vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java` |
| detectable from diff | weak |

4 finding(s) survived refutation:

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — correctness
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson maps every JSON number to Double when the target value type is Object, so the returned Document metadata holds 2020.0 (Double) instead of Integer 2020, and 1.2345678901234568E18 instead of the exact long. Callers that cast, e.g. (Integer) doc.getMetadata().get("year"), now throw ClassCastException, and large integral values lose precision. The previous fastjson getInnerMap() preserved Integer/Long.

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — correctness
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson's default deserialization for the `Map<String, Object>` target type maps every JSON number to `Double`, so `metadata.get("page")` returns `1.0` (a Double) instead of the Integer that was stored, and the long `9007199254740993` comes back as `9.007199254740992E15`, silently losing precision. The distance entry, previously a `Float` (fastjson `getInnerMap()` preserved the inserted type), is now a `Double`, so any consumer doing `(Integer) meta.get("page")` or `(Float) meta.get("distance")` throws ClassCastException.

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — contract
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson's default adapter for `Object` deserialises every JSON number as `Double`, so `doc.getMetadata().get("page")` returns `1.0` (Double) instead of the `Integer` the fastjson `getInnerMap()` path returned; the injected `distance` value likewise changes from Float to Double. Callers doing `(Integer) metadata.get("page")` or `(Float) metadata.get("distance")` now throw ClassCastException.

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:165`** — undocumented
  `public static final String SIMILARITY_FIELD_NAME = "score";`
  Besides renaming the constant and its value, the change also promotes it from `private static final DISTANCE_FIELD_NAME` to a `public` constant, adding new public API surface that the intent does not mention.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `spring-ai-c256cfa`

Fix null parent for tool call observations in blocking mode

| | |
|---|---|
| introduced in | `1dde55d1e` |
| file | `spring-ai-model/src/main/java/org/springframework/ai/model/tool/DefaultToolCallingManager.java` |
| detectable from diff | weak |

1 finding(s) survived refutation:

- **`spring-ai-model/src/main/java/org/springframework/ai/model/tool/DefaultToolCallingManager.java:243`** — correctness
  `.parentObservation(parent)`
  parentObservation(null) overwrites the parent that Micrometer's SimpleObservation already resolved from ObservationRegistry.getCurrentObservation() at creation time, so the TOOL_CALL observation is emitted with no parent and the tool-call span becomes a detached root instead of a child of the chat-model span.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `spring-ai-ec1e052`

Fix Redis vector store filter delete to paginate search results

| | |
|---|---|
| introduced in | `bca65de6a` |
| file | `vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java` |
| detectable from diff | weak |

7 finding(s) survived refutation:

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — correctness
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  FT.SEARCH without an explicit LIMIT returns only the first 10 hits, so matchingIds holds 10 ids; only 10 of the 25 matching documents are deleted and the method returns normally (logging "Deleted 10 documents matching filter expression"), leaving 15 matching documents in the store while the caller believes the filtered delete succeeded.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), ""));`
  String.replace strips every occurrence, not just the leading prefix, producing id "x-1"; pipeline.jsonDel("embedding:x-1") targets a non-existent key, returns 0 which fails the RESPONSE_DEL_OK predicate, so an IllegalStateException("Failed to delete documents by filter") is thrown while the intended document is never deleted.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — boundary
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  Jedis' `ftSearch(String, String)` builds a Query with the default paging LIMIT 0 10, so `searchResult.getDocuments()` contains at most 10 entries. Only the first 10 matching documents are deleted; the remaining matches silently stay in the store while the method returns normally, so callers believe the filtered delete succeeded.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), ""));`
  `String.replace` strips every occurrence, not just the leading one, yielding id "x-1"; `pipeline.jsonDel(key("x-1"))` targets a non-existent key and returns 0 instead of 1, so the error check trips and the method throws IllegalStateException("Failed to delete documents by filter") while the real document remains stored. (Contrast `toDocument`, which correctly uses `substring(this.prefix.length())`.)

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — contract
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  FT.SEARCH applies its default result window of LIMIT 0 10 when no Query with an explicit limit is supplied, so searchResult.getDocuments() returns at most 10 documents. Only those 10 keys are passed to jsonDel; the remaining 40 matching documents stay in Redis while the call returns normally, so the caller sees a successful filter-delete that silently left data behind.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), "")); // Remove the key prefix to`
  String.replace removes every occurrence, not just the leading prefix, yielding id "a-1"; key(id) then targets "embedding:a-1", which does not exist. jsonDel returns 0 instead of 1, RESPONSE_DEL_OK fails, and the method throws IllegalStateException("Failed to delete documents by filter") while the actual document remains stored.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — boundary
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  ftSearch with only a query string uses RediSearch's default LIMIT 0 10, so only the first 10 matching document ids are collected and deleted; the remaining matching documents silently stay in the store while the method returns normally

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## Excluded from scoring, and why

| case | reason |
|---|---|
| `spring-ai-9ec7cfa` | not findable from the diff (no) |
| `spring-ai-698bde0` | not findable from the diff (no) |
| `spring-ai-7bd3e1f` | not findable from the diff (no) |

## To total it

- **detected / 4 scorable** — the headline, as a fraction.
- **findings that were not the known defect** — not errors (a genuine second bug
  is not a false positive), but the number that bounds a reader's cost, and the
  one that decides whether anyone keeps using this.

Nothing here measures a false-positive rate: every case is a diff known to
contain a defect. That needs the opposite corpus — clean commits — and it is
arguably the more useful of the two.

---

Model `claude-opus-5`, 40 call(s) across 4 case(s), 4.5263 USD billed. 0 finding(s) refused by the guards. cache read 67762 tokens against 0 written
