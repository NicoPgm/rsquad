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

8 finding(s) survived refutation:

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`** — correctness
  `TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);`
  `params` is built once, eagerly, and holds a single `MultipartField<InputStream>` wrapping one `new ByteArrayInputStream(audioBytes)` (line 178). The `Flux.create` lambda re-runs on every subscription and re-sends the same, already-drained stream, so the second and every later request uploads a 0-byte file: the API rejects it or returns a transcription of nothing. `call()` is one-shot so it is unaffected; a Flux is not.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:156`** — resource
  `.createStreaming(params)
			.subscribe(sink::next)`
  The `AsyncStreamResponse` returned by `createStreaming` is never retained and never closed, and no `sink.onCancel`/`sink.onDispose` hook is registered. On cancellation the SDK subscription keeps consuming the whole HTTP response body while every `sink::next` is silently dropped; the connection and its buffers are held until the server finishes the transcription instead of being released at cancel time.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:226`** — correctness
  `if (event.isTranscriptTextSegment()) {
			return event.asTranscriptTextSegment().text();
		}
		return "";`
  The terminal event falls through to `return ""` and is still mapped at line 168-172 into an `AudioTranscriptionResponse` carrying an empty `AudioTranscription`. A consumer that reads the last element (`stream(prompt).blockLast().getResult().getOutput()`) gets "" instead of the full transcript, and any consumer sees a spurious empty emission at the end of every stream.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:154`** — resource
  `Flux<TranscriptionStreamEvent> chunks = Flux.create(sink -> this.openAiClientAsync.audio()
			.transcriptions()
			.createStreaming(params)
			.subscribe(sink::next)`
  The handle returned by createStreaming(...).subscribe(...) is never closed: nothing is registered on sink.onCancel()/sink.onDispose(), so the underlying HTTP streaming response and its connection stay open and keep receiving events until the server ends the response, one leaked stream per cancelled subscription.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`** — correctness
  `TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);`
  params is built once outside Flux.create, so every subscription reuses the same MultipartField whose value is a single ByteArrayInputStream (buildParams line 178). The first subscription drains it; the second sends a zero-byte file part, so the request is rejected or returns an empty transcription instead of re-uploading the audio.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`** — contract
  `TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);
		if (logger.isTraceEnabled()) {
			logger.trace("OpenAiAudioTranscriptionModel stream with model: " + mergedOptions.getModel());`
  params is built once, outside the Flux.create lambda, and buildParams wraps the audio in a single ByteArrayInputStream via MultipartField.value(new ByteArrayInputStream(audioBytes)). The lambda runs per subscribe, so the second request re-sends params whose stream was already drained by the first request: the multipart file part is sent with zero bytes, and the retry or second subscriber gets an API error or an empty transcription instead of the audio.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`** — resource
  `.createStreaming(params)
			.subscribe(sink::next)`
  The AsyncStreamResponse returned by createStreaming is never closed and no sink.onCancel/onDispose hook is registered, so cancelling the Flux leaves the underlying HTTP streaming response open until the server finishes, holding its connection and completion callback. Repeated cancelled streams accumulate open responses and exhaust the async client's connection pool.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:117`** — undocumented
  `OpenAiAudioTranscriptionOptions mergedOptions = OpenAiAudioTranscriptionOptions.builder()`
  Beyond adding streaming, the change rewrites option handling in the existing non-streaming call(): the previous code rejected a prompt whose options were not OpenAiAudioTranscriptionOptions by throwing IllegalArgumentException("Prompt options are not of type OpenAiAudioTranscriptionOptions: ..."). That guard is gone and the foreign options object is now passed to builder.merge() instead, so callers relying on the failure no longer get it.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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

3 finding(s) survived refutation:

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — correctness
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson's default adapter for the Object value type of Map<String, Object> deserializes every JSON number as Double, so metadata.get("year") returns Double 2024.0 instead of Integer 2024, and metadata.get("distance") returns a Double where the previous getInnerMap() path yielded Integer/Float; callers that cast the value (e.g. (Integer) or (Float)) get a ClassCastException, and equality checks against the originally stored value fail.

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — correctness
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson's default deserialization of Object-valued map entries turns every JSON number into a Double, so getMetadata().get("page") returns 42.0 (Double) instead of the Integer/Long that fastjson's getInnerMap() yielded, and getMetadata().get(DocumentMetadata.DISTANCE.value()) returns a Double where the previous metadata.put(...) of a float stored a Float. Caller code doing (Integer) doc.getMetadata().get("page") or (Float) doc.getMetadata().get("distance") now throws ClassCastException, and integer metadata renders as "42.0".

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — contract
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson deserialising into TypeToken<Map<String, Object>> binds every JSON number to Double, so doc.getMetadata().get("page") returns Double 1.0 instead of the Integer 1 that the previous JSONObject.getInnerMap() returned; callers doing (Integer) metadata.get("page") throw ClassCastException and rendered metadata reads "1.0". The same coercion applies to the injected DocumentMetadata.DISTANCE value, which changes from Float to Double.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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

**No finding survived.** Missed, and no judgement needed.

## `spring-ai-ec1e052`

Fix Redis vector store filter delete to paginate search results

| | |
|---|---|
| introduced in | `bca65de6a` |
| file | `vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java` |
| detectable from diff | weak |

6 finding(s) survived refutation:

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — correctness
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  FT.SEARCH applies its default LIMIT 0 10 because no Query with an explicit limit is passed, so searchResult.getDocuments() returns only 10 of the 25 matches; exactly 10 documents are deleted, the remaining 15 stay in Redis, and the method returns normally with no error, so the caller believes the filtered delete completed.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), ""));`
  String.replace removes every occurrence of the prefix, not just the leading one, yielding id "doc-1"; pipeline.jsonDel("embedding:doc-1") targets a non-existent key and returns 0, so the real document is never deleted and the non-1 response makes the method throw IllegalStateException("Failed to delete documents by filter") even though the other matched documents were removed.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — boundary
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  The two-argument ftSearch(index, query) sends FT.SEARCH with no LIMIT clause, so RediSearch applies its default LIMIT 0 10 and returns only the first 10 documents. matchingIds holds 10 ids, exactly 10 keys are jsonDel'd, and the method returns normally without error. The remaining 15 matching documents stay in Redis while the caller is told the delete succeeded. There is no paging loop and no check of searchResult.getTotalResults(), so the silent under-delete is unbounded in size.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), ""));`
  String.replace removes every occurrence, not just the leading prefix, so docId becomes "doc-1" instead of "doc-embedding:1". pipeline.jsonDel(key("doc-1")) targets the key "embedding:doc-1", which does not exist, so the reply is 0 rather than 1. RESPONSE_DEL_OK fails, an IllegalStateException("Failed to delete some documents") is thrown and rewrapped by the outer catch — while the document that actually matched the filter is still present, and any other ids batched in the same pipeline have already been deleted.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — contract
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  FT.SEARCH applies its server-side default LIMIT 0 10 when no Query with an explicit limit is passed, so getDocuments() yields at most 10 hits; searchResult.getTotalResults() is never read and no paging loop exists. Only 10 of the 50 documents are deleted and the method returns normally, so the caller sees a successful delete while 40 matching documents remain in the store and keep surfacing in similarity searches.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), ""));`
  String.replace strips every occurrence, not just the leading one, so the derived id is "a-1" and the pipeline issues JSON.DEL on "embedding:a-1", a key that does not exist. The real key survives while the response for the missing key is not 1L, so the errResponse check fires and the method throws IllegalStateException after having already deleted the other matched documents, leaving the delete half applied. (doSimilaritySearch strips the same prefix correctly via substring(this.prefix.length()).)

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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

Harness transport, 4 case(s), 0 finding(s) refused by the guards. **No dollar cost**: the tokens are the harness's. That is the point of running the scaling measurement here.
