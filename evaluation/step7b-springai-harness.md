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
  params is built once at assembly time and holds a single ByteArrayInputStream created in buildParams (line 178). Flux.create's lambda runs per subscription, so the second subscription calls createStreaming(params) with the same, already fully consumed stream: the multipart file part is uploaded as 0 bytes. The retry that was meant to recover from a transient failure instead sends an empty audio file and yields an API error or an empty transcription, so a retried stream() silently produces no text where call() (which rebuilds params per invocation) would succeed.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`** — resource
  `.subscribe(sink::next)`
  The sink registers no onCancel/onDispose handler, so the AsyncStreamResponse returned by createStreaming is never closed on cancellation. Subsequent sink::next calls are discarded while the underlying HTTP response body keeps being consumed to completion; the connection and its buffers stay held for the whole remaining server-side transcription instead of being released at cancel time.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`** — resource
  `.subscribe(sink::next)`
  The streaming subscription returned by `createStreaming(params).subscribe(...)` is never closed: the sink registers no `onCancel`/`onDispose` handler, so on cancellation the underlying HTTP/SSE response stays open and keeps receiving events into a terminated sink until the server ends the stream, holding the connection for the full duration of the transcription.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`** — correctness
  `TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);`
  `params` is built once at assembly time and holds a single `new ByteArrayInputStream(audioBytes)` (buildParams, line 178). The first subscription drains that stream; every later subscription re-sends the same exhausted stream, so the multipart file part is zero bytes and the request fails or returns an empty transcription instead of re-uploading the audio.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`** — resource
  `.subscribe(sink::next)`
  The AsyncStreamResponse returned by createStreaming is never closed: no sink.onCancel/onDispose hook calls close(), so the underlying HTTP response and its connection stay open until the server finishes sending the whole transcription. Repeated cancelled streams exhaust the connection pool. Events pushed by the SDK after cancellation also keep arriving into a dead sink.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`** — contract
  `TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);`
  params is built once outside Flux.create and holds a single ByteArrayInputStream (buildParams line 178). Flux.create runs its lambda per subscription, so the second HTTP request re-sends the same already-exhausted stream: the multipart file part is uploaded with zero bytes, and the API rejects the request or returns a transcription of nothing instead of the audio. A Flux is expected to be re-subscribable; this one silently is not.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:117`** — undocumented
  `OpenAiAudioTranscriptionOptions mergedOptions = OpenAiAudioTranscriptionOptions.builder()`
  Beyond adding streaming, the change rewrites the existing non-streaming call() path: the explicit instanceof check that rejected foreign prompt options with `IllegalArgumentException("Prompt options are not of type OpenAiAudioTranscriptionOptions: ...")` is removed and replaced by an unconditional builder merge. Callers relying on that documented failure mode for a wrong options type now get whatever merge() does instead, and the intent mentions no change to call().

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

3 finding(s) survived refutation:

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — correctness
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson deserializes every JSON number to Double when the target element type is Object, so the returned Document metadata holds Double 1.0 for "page" and a Double for "distance", instead of the Integer and Float that metadata.getInnerMap() produced before the change. Caller code that reads the value as its original type — (Integer) doc.getMetadata().get("page") or (Float) doc.getMetadata().get(DocumentMetadata.DISTANCE.value()) — throws ClassCastException, and equality checks against the originally added metadata (1 vs 1.0) now fail.

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — correctness
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson deserializing into TypeToken<Map<String, Object>> maps every JSON number to Double, so getMetadata().get("year") returns 2024.0 (Double) where the previous JSONObject.getInnerMap() returned Integer 2024; a caller doing (Integer) doc.getMetadata().get("year") now throws ClassCastException, and String.valueOf(...) renders "2024.0". The injected DocumentMetadata.DISTANCE value likewise changes from Float to Double, gaining float-to-double widening digits (e.g. 0.19999998807907104).

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — contract
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson's ObjectTypeAdapter deserializes every JSON number as Double when the target value type is Object, so the returned Document.getMetadata() holds Double 2024.0 and Double 3.0 instead of Integer 2024 and Long 3. The previous JSONObject.getInnerMap() preserved Integer/Long. Callers doing metadata.get("year").equals(2024) now get false, and a cast such as (Integer) metadata.get("year") throws ClassCastException. The same applies to the injected DocumentMetadata.DISTANCE value, which changes from Float to Double.

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
  searchResult.getDocuments() returns only the first 10 matches, so matchingIds holds 10 ids and only 10 keys are jsonDel'd. The remaining 15 matching documents stay in Redis while the method returns normally, with no exception and a debug line claiming "Deleted 10 documents matching filter expression" — the caller believes the filter delete removed everything it matched.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), ""));`
  String.replace() removes every occurrence, not just the leading one: "embedding:embedding:42" becomes "42", so the loop deletes key("42") = "embedding:42" — a different, unrelated document — while the intended key "embedding:embedding:42" survives. If no document exists under "embedding:42", jsonDel returns 0, RESPONSE_DEL_OK fails and the whole call throws IllegalStateException("Failed to delete documents by filter") after some other keys in the same pipeline were already deleted. toDocument() strips the prefix correctly with substring(this.prefix.length()); this path does not.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — boundary
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  The two-argument ftSearch sends FT.SEARCH with no LIMIT clause, so RediSearch applies its default LIMIT 0 10 and returns at most 10 documents. Only 10 keys are added to matchingIds and deleted; the 11th and every further match silently survive the delete, the method returns normally, and the leftovers still appear in later similarity searches. No paging loop over searchResult.getTotalResults() exists.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), ""));`
  String.replace strips every occurrence, not just the leading one, so docId becomes "a-b" instead of "a-embedding:b". pipeline.jsonDel(key("a-b")) targets the non-existent key "embedding:a-b", returns 0 instead of 1, so RESPONSE_DEL_OK fails, an IllegalStateException("Failed to delete documents by filter") is thrown, and the real document is never deleted. The rest of the file uses doc.getId().substring(this.prefix.length()) for the same conversion (line 372).

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — contract
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  ftSearch(index, queryString) uses RediSearch's default paging (LIMIT 0 10), so searchResult.getDocuments() carries at most 10 hits; only 10 of the 50 matching documents are deleted, the method logs 'Deleted 10 documents matching filter expression' and returns normally, leaving 40 matching documents in the store while the caller is told the delete succeeded.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), ""));`
  key("") is the bare prefix and String.replace strips every occurrence, not just the leading one: "docdoc-42" becomes "-42", so key(id) rebuilds "doc-42" and pipeline.jsonDel targets a key that does not exist. jsonDel returns 0L, RESPONSE_DEL_OK fails, and the method throws IllegalStateException("Failed to delete documents by filter") while the document is still present. toDocument() strips the same prefix correctly with substring(this.prefix.length()).

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

Harness transport, 4 case(s), 0 finding(s) refused by the guards. **No dollar cost**: the tokens are the harness's. That is the point of running the scaling measurement here.
