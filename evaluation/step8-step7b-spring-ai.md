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

3 finding(s) survived refutation:

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`** — resource
  `.subscribe(sink::next)`
  The sink registers no onDispose or onCancel callback and the handle returned by subscribe(...) is discarded. Cancelling the Flux therefore never closes the underlying async HTTP stream. The request keeps running to completion, holding the connection and consuming the remaining events, and sink.next just drops them.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`** — resource
  `.subscribe(sink::next)`
  The Flux.create sink has no onDispose or onCancel hook, so the AsyncStreamResponse returned by subscribe() is never closed. The HTTP stream stays open until the server finishes, and every remaining event is still pushed into the cancelled sink. Flux.create also buffers without bound by default, so a slow consumer makes the buffer grow.

- **`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`** — resource
  `.subscribe(sink::next)`
  The AsyncStreamResponse returned by subscribe() is discarded, and no sink.onDispose or onCancel hook closes it. Cancelling the Flux does not stop the underlying streaming request, so the connection stays open and keeps reading until the server finishes. Events are still pushed to a cancelled sink and silently dropped.

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
  gson.fromJson into Map<String,Object> turns every JSON number into Double, so the returned metadata has year=2020.0 instead of the Integer 2020 that was stored (the previous fastjson getInnerMap kept integers). Callers comparing or casting metadata values to Integer/Long get a ClassCastException or a failed equality.

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — correctness
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Gson deserializes into Map<String,Object> and turns every JSON number into Double. The integer 2020 comes back as 2020.0, and the long 9007199254740993 loses precision. Metadata read back no longer equals what was stored, and the previous getInnerMap() path preserved Integer and Long.

- **`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`** — correctness
  `.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())`
  Every JSON number comes back as java.lang.Double (2020.0), not Integer or Long. Callers that cast or compare metadata values with equals() against the original types get ClassCastException or false. Large longs also lose precision. The previous fastjson getInnerMap() preserved integer types.

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

5 finding(s) survived refutation:

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — boundary
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  ftSearch(String, String) builds a Query with no explicit limit, so RediSearch returns its default page of 10 results. Only 10 documents are collected and deleted, and the method returns normally. The other 15 matching documents silently remain in the store.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), ""));`
  String.replace removes every occurrence of the prefix, not only the leading one, so the id becomes 'a-b'. key('a-b') points at a key that does not exist, jsonDel returns 0, and the method throws IllegalStateException('Failed to delete some documents'). The matching document is not deleted.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — boundary
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  Only the first 10 matching documents are returned, so only those 10 are deleted. The method returns normally with no error while the other 15 matching documents remain in the store.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`** — contract
  `SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);`
  RediSearch returns only its default page of 10 results. Only those 10 documents are deleted, the call reports success, and the other 15 matching documents remain in the store. A single delete(filter) does not delete everything that matches.

- **`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`** — correctness
  `matchingIds.add(docId.replace(key(""), "")); // Remove the key prefix to`
  String.replace removes every occurrence of the prefix, not only the leading one. The recovered ID is "foo", so jsonDel(key("foo")) targets a key that does not exist. It returns 0, RESPONSE_DEL_OK fails, and the method throws IllegalStateException while the document stays in the store.

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
