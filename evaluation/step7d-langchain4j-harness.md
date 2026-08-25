# Evaluation replay

**18 scorable case(s) of 19 in the set.**

This report does not contain a detection rate and cannot: the verdict line under
each case is a human judgement. Fill them in, then read the fractions below with
their denominators visible — never as a percentage. On a handful of cases a 25 %
rate and a 75 % one are the same measurement.

## `langchain4j-4a36c67`

fix: Escape single quotes in Azure AI Search

| | |
|---|---|
| introduced in | `abc957a80` |
| file | `langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java` |
| detectable from diff | weak |

9 finding(s) survived refutation:

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:115`** — correctness
  `return format("metadata/attributes/any(k: k/key eq '%s' and " + format + ")", key, value);`
  The quote is interpolated raw, producing metadata/attributes/any(k: k/key eq 'author' and k/value eq 'O'Brien'), which is not a valid OData literal (a quote must be doubled). Azure AI Search rejects the request with HTTP 400 InvalidRequestParameter instead of returning results. A value such as "x' or k/key eq 'secret" likewise closes the literal and injects extra filter clauses.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:111`** — correctness
  `return comparisonValues.stream().map(Object::toString).sorted().collect(Collectors.joining(", "));`
  The values are flattened into one string literal, yielding search.in(k/value, ('New York, Paris')). search.in splits that literal on its default delimiters (space and comma), so the predicate becomes the set {New, York, Paris}: a document with city="New York" is not matched, while documents with city="New" or city="York" are matched. The filter silently returns the wrong document set.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:68`** — correctness
  `if (filter instanceof IsGreaterThan) return "k/value gt '%s'";`
  The number is emitted as a quoted literal, giving k/value gt '9'. Against the string-typed k/value field the comparison is lexicographic, so '10' gt '9' is false and the year=10 document is dropped from the results; if k/value is instead a numeric field, Edm.Int32 gt Edm.String is a type error and Azure returns HTTP 400. The same quoting is applied by IsGreaterThanOrEqualTo, IsLessThan and IsLessThanOrEqualTo on lines 69-71.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:111`** — correctness
  `return comparisonValues.stream().map(Object::toString).sorted().collect(Collectors.joining(", "));`
  All values are joined into one quoted OData literal, producing search.in(k/value, ('New York, Paris')). search.in with no explicit delimiter argument splits on space and comma, so the list becomes "New", "York", "Paris": a document with value "New York" is not matched, while documents with value "New" or "York" are wrongly matched.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:115`** — correctness
  `return format("metadata/attributes/any(k: k/key eq '%s' and " + format + ")", key, value);`
  The quote is interpolated raw and terminates the OData string literal: the emitted filter is metadata/attributes/any(k: k/key eq 'author' and k/value eq 'O'Brien'), which Azure AI Search rejects with an HTTP 400 invalid-expression error instead of returning the matching documents.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:68`** — correctness
  `if (filter instanceof IsGreaterThan) return "k/value gt '%s'";`
  The numeric comparison value is emitted inside single quotes, so the ordering comparison is done on strings: '1000' gt '999' is false lexicographically, and the document with year 1000 is excluded from the results.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:115`** — contract
  `return format("metadata/attributes/any(k: k/key eq '%s' and " + format + ")", key, value);`
  Produces metadata/attributes/any(k: k/key eq 'author' and k/value eq 'O'Brien'), which is not valid OData: the literal is terminated early. Azure AI Search rejects the request with HTTP 400 (invalid filter expression) instead of returning results. The OData grammar requires an embedded quote to be doubled ('') and nothing here escapes it.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:111`** — correctness
  `return comparisonValues.stream().map(Object::toString).sorted().collect(Collectors.joining(", "));`
  The values are joined into one quoted string and emitted as search.in(k/value, ('Ada Lovelace, John Smith')). With search.in's default delimiter set (comma and space) that string is split into the four tokens Ada, Lovelace, John, Smith, so documents whose value is exactly "John Smith" are not matched while documents whose value is "John" or "Smith" are. The filter silently returns the wrong document set rather than failing.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:68`** — correctness
  `if (filter instanceof IsGreaterThan) return "k/value gt '%s'";`
  comparisonValue().toString() is wrapped in single quotes, so the emitted OData is k/value gt '9' - a string literal. Against the string-typed k/value field of the default index that is a lexicographic comparison, and '10' gt '9' is false, so the document with 10 is excluded from the result set with no error reported. (If k/value were instead numerically typed, the quoted literal is a type mismatch and Azure returns HTTP 400.) Either way the numeric ordering the caller asked for is not what is evaluated.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-229309d`

Fix Bedrock stop-reason mapping for AWS-adde

| | |
|---|---|
| introduced in | `13d276992` |
| file | `langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java` |
| detectable from diff | weak |

4 finding(s) survived refutation:

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:345`** — boundary
  `throw new IllegalArgumentException("Unknown stop reason: " + stopReason);`
  finishReasonFrom falls through all three if-blocks and throws IllegalArgumentException("Unknown stop reason: guardrail_intervened"), so a successful HTTP 200 Converse response is turned into an exception and the answer text already parsed by aiMessageFrom is discarded, instead of mapping to FinishReason.CONTENT_FILTER / OTHER.

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:345`** — boundary
  `throw new IllegalArgumentException("Unknown stop reason: " + stopReason);`
  finishReasonFrom throws IllegalArgumentException("Unknown stop reason: guardrail_intervened") while converting an otherwise successful HTTP 200 response, so the whole chat call fails with an unrelated exception instead of returning a ChatResponse (langchain4j's FinishReason.CONTENT_FILTER is never produced).

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:311`** — correctness
  `textAnswer = cBlock.text();`
  Each TEXT block assigns over the previous one instead of appending, so the returned AiMessage carries only the last text block; all earlier text is silently dropped from the response (with exactly one TEXT block the behaviour is correct, which hides the bug).

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:345`** — contract
  `throw new IllegalArgumentException("Unknown stop reason: " + stopReason);`
  finishReasonFrom throws IllegalArgumentException, so a well-formed HTTP 200 Converse response (guardrail intervention or filtered content) is turned into a client-side exception and the model output already received is discarded instead of being returned with a FinishReason such as CONTENT_FILTER.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-e1dc391`

fix: Read error response body as UTF-8 witho

| | |
|---|---|
| introduced in | `f368ec038` |
| file | `http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java` |
| detectable from diff | weak |

12 finding(s) survived refutation:

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:136`** — boundary
  `byte[] bodyBytes = apacheResponse.getBody().getBodyBytes();`
  getBody() is null and .getBodyBytes() throws NullPointerException while the try-with-resources resource at line 113 is being initialised; the NPE is caught at line 116, so the listener receives onOpen(response) followed by onError(NullPointerException) and never onClose, turning an empty-but-valid response into a spurious client-side failure.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:164`** — correctness
  `return "Cannot read error response body: " + e.getMessage();`
  execute(request) returns a SuccessfulHttpResponse with statusCode 200 and body equal to the literal string "Cannot read error response body: Premature end of chunk coded message"; the truncated payload is discarded and no exception is raised, so the caller parses the diagnostic text as if it were the server's answer instead of retrying a failed transfer.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:101`** — contract
  `asyncClient.execute(apacheRequest, new FutureCallback<>() {`
  listener.onOpen and every parsed event fire only after the server closes the stream ~30 s later, all at once, instead of incrementally; against an endpoint that keeps the connection open the listener receives nothing at all, and the full response is held in memory rather than consumed as it arrives.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:61`** — contract
  `requestConfigBuilder.setConnectionRequestTimeout(`
  The pool hands out a free slot immediately so the 2 s value never applies, and the TCP connect runs under the default 3-minute connect timeout: execute() blocks for about three minutes before failing instead of failing after 2 s. The configured connect timeout has no observable effect on either the sync or the async client.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:136`** — boundary
  `byte[] bodyBytes = apacheResponse.getBody().getBodyBytes();`
  getBody() is null and .getBodyBytes() throws NullPointerException. The throw happens in the resource initializer of the enclosing try-with-resources, so it is caught at line 116 and reported as listener.onError(NullPointerException) right after onOpen; the listener never receives onClose. The Objects.requireNonNullElseGet guard on the next line only covers null bytes, never the null body one level up, so the zero-body edge is unprotected.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:61`** — contract
  `requestConfigBuilder.setConnectionRequestTimeout(
                    Timeout.ofMilliseconds(builder.connectTimeout().toMillis()));`
  RequestConfig.setConnectionRequestTimeout bounds how long a connection is waited for from the pool, not how long the TCP handshake may take (that is ConnectionConfig.setConnectTimeout in HttpClient 5). Leasing a fresh connection from an idle pool returns immediately, so the configured 100 ms never applies to the handshake and execute() blocks for the ConnectionConfig default (3 minutes) instead of failing after 100 ms.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:160`** — correctness
  `BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))`
  InputStreamReader is constructed without a Charset, so it uses Charset.defaultCharset() and ignores the charset declared by the entity. The bytes are decoded with the wrong charset and SuccessfulHttpResponse.body (built at line 149 from this same method) contains U+FFFD replacement characters or mojibake instead of the transmitted text.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:101`** — contract
  `asyncClient.execute(apacheRequest, new FutureCallback<>() {`
  SimpleHttpRequest/SimpleHttpResponse are the fully-buffered message API (the whole body is accumulated in memory and completed() only fires once the response is finished), which line 136 then re-wraps in a ByteArrayInputStream. No event is delivered incrementally: listener.onOpen and every onEvent fire only after the server closes the stream, and a stream the server never closes never delivers anything while the entire body grows in heap.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:61`** — contract
  `requestConfigBuilder.setConnectionRequestTimeout(
                    Timeout.ofMilliseconds(builder.connectTimeout().toMillis()));`
  connectionRequestTimeout bounds leasing a connection from the pool, not TCP connect establishment (in HttpClient 5 connect timeout lives on ConnectionConfig, not RequestConfig). The call blocks on connect far past 1 s (Apache's default connect timeout, 3 minutes), while under pool contention an unrelated pool wait now aborts after 1 s with ConnectionRequestTimeoutException. The configured connectTimeout never bounds what it names.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:74`** — resource
  `this.asyncClient.start();`
  start() spawns the I/O reactor dispatch threads and both clients own connection pools, but the class exposes no close/shutdown and never calls asyncClient.close() or syncClient.close(). Every discarded instance leaves its reactor threads alive and its pooled sockets open; thread and file-descriptor counts grow monotonically for the life of the JVM, and garbage collection does not reclaim them.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:160`** — correctness
  `BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {`
  InputStreamReader is built with no Charset, so the bytes are decoded with the platform default instead of the charset declared by the response Content-Type; SuccessfulHttpResponse.body() (and the HttpException message on the error path) carries mojibake, and downstream JSON parsing of that body yields corrupted strings.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:136`** — contract
  `byte[] bodyBytes = apacheResponse.getBody().getBodyBytes();`
  SimpleHttpResponse.getBody() returns null when no body was set, so getBody() throws NullPointerException before requireNonNullElseGet can defend the bytes. The NPE is raised in the try-with-resources resource expression at line 113 and caught by the catch at line 116, so the listener receives onError(NullPointerException) instead of a clean onClose after onOpen.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-10cd693`

Fix Bedrock guardrail assessment handling fo

| | |
|---|---|
| introduced in | `9c4892323` |
| file | `langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java` |
| detectable from diff | weak |

3 finding(s) survived refutation:

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:530`** — correctness
  `if (trace.guardrail().hasInputAssessment()) {`
  The method guards only against trace == null, then immediately dereferences trace.guardrail(), so a NullPointerException is thrown at this line (and again at trace.guardrail().hasOutputAssessments() on line 621) instead of returning a summary, aborting response conversion for an otherwise successful Bedrock call.

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:530`** — correctness
  `if (trace.guardrail().hasInputAssessment()) {`
  guardrailAssessmentSummaryFrom passes the trace != null guard and immediately dereferences trace.guardrail(), throwing NullPointerException instead of returning a summary; the same unguarded dereference repeats at line 621 (trace.guardrail().hasOutputAssessments()).

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:530`** — contract
  `if (trace.guardrail().hasInputAssessment()) {`
  trace.guardrail() returns null and the chained call hasInputAssessment() throws NullPointerException, aborting response conversion for the whole request. The method guards the outer trace == null case but never the nested guardrail member, which the SDK models as an optional field (same unguarded dereference again at line 621 and inside the loop at line 533).

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-7ddb6ff`

fix: Return generated text when GPULlama3 ge

| | |
|---|---|
| introduced in | `245b18392` |
| file | `langchain4j-gpu-llama3/src/main/java/dev/langchain4j/model/gpullama3/GPULlama3BaseModel.java` |
| detectable from diff | yes |

3 finding(s) survived refutation:

- **`langchain4j-gpu-llama3/src/main/java/dev/langchain4j/model/gpullama3/GPULlama3BaseModel.java:152`** — correctness
  `if (stopToken == null) {
            return "Ran out of context length...\n Increase context length with by passing to llama-tornado --max-tokens XXX";`
  responseText, decoded at line 142 from the 64 generated tokens, is computed and then thrown away; the method returns the literal string "Ran out of context length...\n Increase context length with by passing to llama-tornado --max-tokens XXX" as the model's answer. The caller gets a hardcoded English sentence instead of the truncated completion, and in the streaming model the tokenConsumer has already emitted the real tokens, so the final returned text contradicts what was streamed.

- **`langchain4j-gpu-llama3/src/main/java/dev/langchain4j/model/gpullama3/GPULlama3BaseModel.java:197`** — boundary
  `chatFormat.encodeMessage(new ChatFormat.Message(ChatFormat.Role.ASSISTANT, aiMessage.text())));`
  null is passed as the content of ChatFormat.Message and reaches the tokenizer, which dereferences it: NullPointerException escapes modelResponse instead of the message being skipped or encoded as empty.

- **`langchain4j-gpu-llama3/src/main/java/dev/langchain4j/model/gpullama3/GPULlama3BaseModel.java:152`** — correctness
  `if (stopToken == null) {
            return "Ran out of context length...\n Increase context length with by passing to llama-tornado --max-tokens XXX";`
  responseText, which holds the tokens the model actually produced, is decoded on line 142 and then discarded; the method returns the hardcoded diagnostic string "Ran out of context length..." instead. The caller receives that sentence as the model's answer with no way to distinguish it from a genuine reply, and in the streaming case the consumer has already received the real tokens, so the final aggregated response contradicts the stream.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-b2923fe`

fix: Correct mislabeled safeSearch field in

| | |
|---|---|
| introduced in | `d28f5ab47` |
| file | `langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java` |
| detectable from diff | yes |

6 finding(s) survived refutation:

- **`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`** — correctness
  `", siteRestrict=" + safeSearch +`
  toString() returns "...startIndex=null, siteRestrict=true, additionalParams={}}" - the safeSearch value is printed under the label of a field named siteRestrict that does not exist on the class, and safeSearch appears nowhere in the output, so any log or assertion reading the string reports the wrong field

- **`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:51`** — contract
  `this.additionalParams = getOrDefault(builder.additionalParams, () -> new HashMap<>());`
  the builder's map is stored by reference (no defensive copy) and additionalParams() at line 123 hands the same reference back, so the caller's put mutates the constructed request; hashCode() at line 154 hashes the mutated map and s.contains(r) now returns false while r is still in the set, and two requests built from the same map can no longer be distinguished from ones built with different params

- **`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`** — correctness
  `", siteRestrict=" + safeSearch +`
  the rendered string is "...startIndex=null, siteRestrict=true, additionalParams={}}" - the safeSearch value is emitted under the label of a field that does not exist on this class, and no safeSearch key appears at all, so logs and assertions on toString report the wrong field name

- **`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:51`** — contract
  `this.additionalParams = getOrDefault(builder.additionalParams, () -> new HashMap<>());`
  the caller's map is stored by reference with no defensive copy, so the all-final "immutable" request mutates after construction: hashCode() (line 154 folds in additionalParams) changes while the object sits in the set, and s.contains(r) then returns false

- **`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`** — correctness
  `", siteRestrict=" + safeSearch +`
  Returns "WebSearchRequest{...startIndex=null, siteRestrict=true, additionalParams={}}": the safeSearch value is printed under the label siteRestrict, a field this class does not have, so safeSearch never appears by name in logs or assertion failure messages and a reader sees a non-existent field instead.

- **`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`** — correctness
  `", siteRestrict=" + safeSearch +`
  The rendered string contains "siteRestrict=true" although no siteRestrict field exists; the value of safeSearch is printed under a name that belongs to no property, so log output and any string-based comparison of toString() report the wrong field name.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-5252739`

fix: Default ElasticsearchContentRetriever m

| | |
|---|---|
| introduced in | `2c170dd43` |
| file | `langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java` |
| detectable from diff | weak |

6 finding(s) survived refutation:

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:123`** — boundary
  `private int maxResults;`
  The primitive field defaults to 0 (the builder gives it no default, unlike indexName and configuration), so line 87 calls .maxResults(0) on EmbeddingSearchRequest.builder(); the request rejects a non-positive maxResults and retrieve() throws IllegalArgumentException instead of returning results. Every retrieval on a builder-constructed retriever that omitted maxResults fails.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:75`** — correctness
  `return this.fullTextSearch(query.text()).stream()`
  The full-text branch returns before minScore, filter and maxResults are ever used: fullTextSearch(String) receives only the query text, the EmbeddingSearchRequest at lines 85-90 is never built, and mapResultsToContentList (the only place the minScore threshold at line 101 is applied) is never called. The caller gets documents that do not match the filter and whose score is below the configured minScore, with no error and no log to say the parameters were dropped.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:101`** — boundary
  `.filter(f -> f.score() > minScore)`
  The match is dropped from the returned list even though minScore is an inclusive threshold in EmbeddingSearchRequest (the store already returned it because score >= minScore). The retriever silently returns fewer results than requested, and at the default minScore = 0.0 any zero-scored match is discarded. The comparison must be >= to match the threshold semantics used one line above when building the request.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:123`** — boundary
  `private int maxResults;`
  retrieve() builds EmbeddingSearchRequest with maxResults = 0. Because the value is a boxed 0 rather than null, the request's own default (3) never applies and its greater-than-zero validation rejects it, so every retrieve() call fails with IllegalArgumentException instead of retrieving with a sane default. A primitive int field cannot express "not set", so the omitted-value case has no working default.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:123`** — contract
  `private int maxResults;`
  The primitive field defaults to 0, so line 87 calls EmbeddingSearchRequest.builder().maxResults(0); EmbeddingSearchRequest validates maxResults with ensureGreaterThanZero, so every retrieve() throws IllegalArgumentException instead of returning results. Because the field is a primitive int, the builder cannot pass null and cannot fall back to the request's own default of 3.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:75`** — contract
  `return this.fullTextSearch(query.text()).stream()`
  The full-text branch returns before the EmbeddingSearchRequest is built, so the constructor-supplied filter, maxResults and minScore are never applied on that path: segments belonging to other userIds are returned, the result list is not capped at 5, and low-scoring matches are not dropped. The three fields are silently dead for this configuration while their javadoc promises they govern retrieval.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-f00ea5f`

Fixes Ickle injection issue (#5856)

| | |
|---|---|
| introduced in | `1d81014af` |
| file | `langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java` |
| detectable from diff | weak |

10 finding(s) survived refutation:

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:137`** — correctness
  `+ inFilterQuery + " and " + m + "name!='" + filter.key() + "')"`
  The generated clause is `(m0.value NOT IN ('Munich') and m0.name='city') OR (m0.value IN ('Munich') and m0.name!='city') OR (i.metadata is null)`. The metadata entry region=Munich satisfies the second disjunct (value IN the list, name != 'city'), so the document is returned even though its `city` value is exactly the excluded one. Any document carrying an excluded value under a different key is a false positive of the NOT IN filter.

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:77`** — correctness
  `return computeFilter("!=", filter.comparisonValue()) + metadataKeyLast(filter.key()) + addMetadataNullCheck();`
  The clause is `m0.value != 'Munich' and m0.name='city' OR (i.metadata is null)`. Both disjuncts are false: the join alias m0 never binds an entry named 'city', and i.metadata is not null. The document is filtered out, while a document with no metadata at all is kept by the null check — so 'key absent' matches only when the whole metadata collection is null, and the two absence cases give opposite results. The same hole exists in mapNotIn (line 136).

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:143`** — correctness
  `String filterQuery = m + "value " + operator + " '" + value + "'";`
  Produces `m0.name='author' and m0.value = 'O'Brien'`, which is not a parseable Ickle string literal; the query fails at parse time instead of returning the matching documents. Nothing escapes or parameterises the interpolated value, so every filter over a value with an apostrophe is unusable (and the same interpolation lets caller-supplied text alter the query text).

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:77`** — boundary
  `return computeFilter("!=", filter.comparisonValue()) + metadataKeyLast(filter.key()) + addMetadataNullCheck();`
  The generated clause is `m0.value != 'x' and m0.name='k' OR (i.metadata is null)`. No joined row satisfies `m0.name='k'`, and `i.metadata is null` is false because the metadata collection is non-empty, so the document is filtered out even though the key it must differ from is absent. The `addMetadataNullCheck()` disjunct only rescues the exactly-zero-metadata case, and even that case is already eliminated earlier by the inner join `join i.metadata m0` emitted by FilterResult, so it can never be true either.

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:137`** — correctness
  `+ inFilterQuery + " and " + m + "name!='" + filter.key() + "')"`
  The second disjunct `m0.value IN ('a') and m0.name!='k'` is satisfied by the joined row for "other", so the document is returned even though its "k" value is in the excluded list. Any document that carries an excluded value under some other metadata key defeats the NOT IN filter.

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:143`** — correctness
  `String filterQuery = m + "value " + operator + " '" + value + "'";`
  The value is interpolated into the Ickle query without escaping, producing `m0.value = 'O'Brien'`, which fails to parse and throws at query execution; a crafted value can also close the literal and inject arbitrary query fragments.

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:173`** — correctness
  `return "(NOT (" + map(filter.expression()).query + "))";`
  The negation is applied to a per-join-row predicate, not to the document: the generated clause is (NOT (m1.name='k' and m1.value = 'v')). The join row m1 = (other, y) satisfies the negation, so the document is returned even though it matches the inner filter and must be excluded. Every Not over a document with at least one non-matching metadata entry returns that document.

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:137`** — correctness
  `+ inFilterQuery + " and " + m + "name!='" + filter.key() + "')"`
  The second disjunct is m0.value IN ('a') and m0.name!='k', which is true for the join row (other, a): the first document is returned although its "k" value is in the excluded list. The same disjunct requires the value to be IN the list, so the document that simply lacks key "k" matches neither disjunct and is dropped, although NOT IN should include it. Both directions of the NOT IN filter are wrong.

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:29`** — correctness
  `for (int j = 0; j <= i; j++) {
                sb.append(" join i.metadata m").append(j);`
  The index consumed by the composite node is never referenced by any generated predicate, yet the join clause is built for every j from 0 to i, emitting " join i.metadata m0 join i.metadata m1 join i.metadata m2" with m0 unconstrained. The query therefore carries an extra unrestricted inner join over the metadata collection, multiplying each matching document by its number of metadata entries and excluding documents with no metadata entry at all.

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:155`** — contract
  `return " OR (i.metadata is null) ";`
  FilterResult always emits at least " join i.metadata m0", an inner join, so a document whose metadata is null produces no row at all and never reaches the WHERE clause. The i.metadata is null disjunct can never be true for any candidate row: it is a silent no-op, and the metadata-less documents it was written to rescue are still excluded.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-1023c67`

fix: do not consume the response body on the

| | |
|---|---|
| introduced in | `423d2fc27` |
| file | `http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java` |
| detectable from diff | weak |

4 finding(s) survived refutation:

- **`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:80`** — correctness
  `SuccessfulHttpResponse successResponse = fromOkHttpResponse(response);`
  fromOkHttpResponse takes the else branch at line 120 and calls readBody -> response.body().string(), which blocks until the server closes the stream and consumes/closes the body. onOpen therefore fires only after the stream ends, and getInputStream(response) at line 83 then hands parser.parse an already-consumed body, so the listener receives zero events and only onClose (or an onError from reading a closed source). The streamed payload is silently dropped.

- **`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:80`** — contract
  `SuccessfulHttpResponse successResponse = fromOkHttpResponse(response);`
  fromOkHttpResponse takes the else branch at line 120 and calls readBody, i.e. response.body().string(), which consumes and closes the single-shot body. getInputStream(response) at line 83 then hands parser.parse an exhausted/closed stream, so no SSE event is ever delivered: the listener gets onOpen immediately followed by onClose with zero events (or onError with IllegalStateException "closed"), and the stream payload is silently lost.

- **`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:39`** — boundary
  `okBuilder.connectTimeout(builder.connectTimeout().toMillis(), TimeUnit.MILLISECONDS);`
  Duration.toMillis() truncates to 0, and OkHttp interprets a timeout of 0 as "no timeout", so the client waits forever instead of failing fast — the exact opposite of the requested bound. The behaviour flips at 1_000_000 ns: 999_999 ns yields an infinite timeout, 1_000_000 ns yields 1 ms.

- **`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:80`** — contract
  `SuccessfulHttpResponse successResponse = fromOkHttpResponse(response);`
  fromOkHttpResponse takes the else branch and calls readBody, i.e. response.body().string(), which fully consumes and closes the one-shot body. The following getInputStream(response) then returns response.body().byteStream() on an already-exhausted, closed source, so parser.parse reads nothing: the listener gets onOpen followed immediately by onClose with zero events (or onError "closed"), and every streamed event is silently lost.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-765b564`

fix: Paginate ListObjects in TencentCosDocum

| | |
|---|---|
| introduced in | `e43f86809` |
| file | `document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java` |
| detectable from diff | weak |

4 finding(s) survived refutation:

- **`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:76`** — boundary
  `ObjectListing objectListing = cosClient.listObjects(listObjectsRequest);`
  Only the first page is walked: objectListing.isTruncated()/getNextMarker() is never consulted and cosClient.listNextBatchOfObjects is never called, so the returned list holds documents for only the first 1000 objects and the remaining 500 are silently dropped with no error and no log line.

- **`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:76`** — boundary
  `ObjectListing objectListing = cosClient.listObjects(listObjectsRequest);`
  listObjects returns a single truncated page capped at max-keys (1000 by default); objectListing.isTruncated() is never checked and listNextBatchOfObjects/setMarker is never called, so the method returns only the first 1000 objects' documents and silently drops the remaining 500, while its javadoc states it loads all documents from the bucket.

- **`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:76`** — contract
  `ObjectListing objectListing = cosClient.listObjects(listObjectsRequest);`
  listObjects returns a single truncated page (max-keys defaults to 1000) and the returned ObjectListing's isTruncated/nextMarker are never read, so the loop iterates only the first page: the method silently returns ~1000 documents instead of 2500, with no error and no log line.

- **`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:148`** — contract
  `throw new IllegalArgumentException("Tencent credentials are required.");`
  build() throws IllegalArgumentException instead of falling back to a default credentials provider, so the documented no-credentials path is unusable.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-cfd90e5`

fix: Avoid StringIndexOutOfBoundsException w

| | |
|---|---|
| introduced in | `504aa173d` |
| file | `experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java` |
| detectable from diff | yes |

10 finding(s) survived refutation:

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:296`** — boundary
  `return sqlQuery.substring(sqlQuery.indexOf("```sql") + 6, sqlQuery.lastIndexOf("```"));`
  indexOf("```sql") is 0 so beginIndex is 6, while lastIndexOf("```") is also 0, so substring(6, 0) throws StringIndexOutOfBoundsException. clean() is called at line 249, outside the try block at line 255, so the exception is not caught by the retry loop and propagates out of retrieve() to the caller.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:333`** — correctness
  `String columnValue = resultSet.getObject(i).toString();`
  resultSet.getObject(i) returns null and .toString() throws NullPointerException. It is swallowed by catch (Exception e) at line 265; e.getMessage() is null, so the retry at line 279 drops the previous query/error context, the same NULL is hit again, and retrieve() returns emptyList() — no content for a query that actually returned rows, plus a wasted extra LLM call.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:147`** — resource
  `ResultSet columns = metaData.getColumns(null, null, tableName, null);`
  columns, pk, fks (line 149) and tableRemarks (line 218) are never closed; four cursors per table stay open on the single Connection until generateDDL returns, so on a driver with a cursor cap the metadata call fails (e.g. ORA-01000 maximum open cursors exceeded) and is rethrown as RuntimeException from the constructor.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:296`** — boundary
  `return sqlQuery.substring(sqlQuery.indexOf("```sql") + 6, sqlQuery.lastIndexOf("```"));`
  indexOf("```sql") is 0 so beginIndex is 6, while lastIndexOf("```") finds the same single occurrence and returns 0, giving substring(6, 0), which throws StringIndexOutOfBoundsException. clean() is called on line 249, outside the try block that starts on line 255, so the exception escapes retrieve() to the caller instead of the documented empty-list/retry behaviour.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:333`** — correctness
  `String columnValue = resultSet.getObject(i).toString();`
  resultSet.getObject(i) returns null and .toString() throws NullPointerException. It is swallowed by the catch (Exception e) on line 265, the NPE message is fed back to the LLM as if it were a SQL error, and after maxRetries the retriever returns an empty list, so a perfectly valid query yields no content.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:147`** — resource
  `ResultSet columns = metaData.getColumns(null, null, tableName, null);`
  Four ResultSets per table (columns, pk on 148, fks on 149, tableRemarks on 218) are opened and never closed; they are only released when the connection is closed at the end of generateDDL. On drivers with a per-connection cursor cap (e.g. Oracle open_cursors, default 300) a schema of roughly 75+ tables exhausts the limit and construction fails with a SQLException wrapped in RuntimeException on line 231.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:333`** — contract
  `String columnValue = resultSet.getObject(i).toString();`
  NullPointerException on .toString(); it is swallowed by the catch (Exception e) in retrieve(), so the whole retrieval silently returns emptyList() after burning the retries, and the caller sees no content and no error for a query that executed successfully.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:296`** — boundary
  `return sqlQuery.substring(sqlQuery.indexOf("```sql") + 6, sqlQuery.lastIndexOf("```"));`
  indexOf and lastIndexOf return the same index, so substring is called with begin > end and throws StringIndexOutOfBoundsException. clean() is invoked at line 249, outside the try block at line 255, so the exception propagates out of retrieve() unhandled instead of being retried or degraded to an empty list.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:147`** — resource
  `ResultSet columns = metaData.getColumns(null, null, tableName, null);`
  4 x (number of tables) cursors stay open on the single connection until generateDDL returns; on drivers with a per-session cursor cap (e.g. Oracle ORA-01000 max open cursors) DDL generation fails with a SQLException, rethrown as RuntimeException from the constructor.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:279`** — contract
  `if (previousSqlQuery != null && previousErrorMessage != null) {`
  The guard is false even though previousSqlQuery is non-null, so the retry sends exactly the same two messages as the first attempt: the failed SQL is never shown back to the model and the retry cannot correct anything, it just re-bills an identical LLM call before retrieve() returns emptyList().

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-c2aa578`

fix: Avoid StringIndexOutOfBoundsException w

| | |
|---|---|
| introduced in | `0b5e2c6b6` |
| file | `experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java` |
| detectable from diff | yes |

6 finding(s) survived refutation:

- **`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:170`** — boundary
  `return hqlQuery.substring(hqlQuery.indexOf("```hql") + 6, hqlQuery.lastIndexOf("```"));`
  indexOf("```hql") == 0 and lastIndexOf("```") == 0, so substring(6, 0) is called with begin > end and throws StringIndexOutOfBoundsException. clean() is invoked at line 127, outside the try/catch at lines 131-142, so the exception escapes retrieve() to the caller instead of being retried or returning emptyList().

- **`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:170`** — boundary
  `return hqlQuery.substring(hqlQuery.indexOf("```hql") + 6, hqlQuery.lastIndexOf("```"));`
  indexOf("```hql") is 0 so the start index is 6, while lastIndexOf("```") also returns 0 — substring(6, 0) throws StringIndexOutOfBoundsException. clean() is called at line 127, outside the try/catch at line 131, so the exception is not caught, no retry happens even when maxRetries > 0, and retrieve() aborts by propagating the exception to the caller instead of returning emptyList().

- **`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:121`** — boundary
  `int attemptsLeft = maxRetries + 1;`
  attemptsLeft is 0, the while loop at line 122 never executes, and retrieve() returns emptyList() at line 145 without ever calling the ChatModel or the database, and without logging anything — an empty retrieval indistinguishable from a query that legitimately matched nothing.

- **`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:170`** — boundary
  `return hqlQuery.substring(hqlQuery.indexOf("```hql") + 6, hqlQuery.lastIndexOf("```"));`
  indexOf("```hql")+6 == 6 while lastIndexOf("```") == 0, so substring(6, 0) throws StringIndexOutOfBoundsException. clean() is called at line 127, outside the try block at line 131, so the exception is never caught: it escapes retrieve() entirely, bypassing the retry loop, instead of the documented empty-list-on-failure behaviour.

- **`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:184`** — resource
  `var results = query.getResultList();`
  The whole result set is materialised into a List, then serialised into a single JSON String by ResultsJsonSerializerImpl and embedded in the Content at line 198, which is fed back to the model. Memory grows with the row count (OutOfMemoryError on large tables) and, when it does fit, the prompt/token cost is unbounded.

- **`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:136`** — contract
  `errorMessage = e.getMessage();`
  errorMessage stays null, so the guard at line 154 (previousHqlQuery != null && previousErrorMessage != null) is false and neither the previous HQL nor the error is appended. The retry re-sends the exact same prompt with no feedback, so it deterministically reproduces the same query and the same failure while still paying for the extra model call; line 138 also logs "HQL execution failed, retrying ... : null".

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-7fe3e3e`

fix: Parse Ollama timestamps with variable-l

| | |
|---|---|
| introduced in | `b818baa1e` |
| file | `langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java` |
| detectable from diff | weak |

6 finding(s) survived refutation:

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:26`** — boundary
  `String nanoseconds = parts[1].substring(0, parts[1].indexOf('Z'));`
  substring(0, -1) throws StringIndexOutOfBoundsException, so deserialize propagates it out of Jackson and every Ollama response is rejected for clients in a negative offset zone; only '+' offsets and 'Z' are handled.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:23`** — correctness
  `String nanoseconds = parts[1].substring(0, parts[1].indexOf('+'));
                date = date.replaceAll(nanoseconds, "");`
  replaceAll strips every occurrence of "4" in the whole string, not just the fractional digits, producing "202-08-0T00:5:5.+02:00"; OffsetDateTime.parse then throws DateTimeParseException instead of returning the date.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:26`** — boundary
  `String nanoseconds = parts[1].substring(0, parts[1].indexOf('Z'));`
  parts[1] contains neither '+' nor 'Z', so indexOf('Z') returns -1 and substring(0, -1) throws StringIndexOutOfBoundsException; deserialization of every Ollama response fails on such hosts instead of returning an OffsetDateTime.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:24`** — correctness
  `date = date.replaceAll(nanoseconds, "");`
  replaceAll strips every occurrence of "54", producing "2024-08-04T00::.+02:00", and OffsetDateTime.parse throws DateTimeParseException rather than yielding 00:54:54+02:00.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:26`** — contract
  `String nanoseconds = parts[1].substring(0, parts[1].indexOf('Z'));`
  substring(0, -1) throws StringIndexOutOfBoundsException instead of returning a value; the exception escapes deserialize(), so every Ollama response carrying such a date fails to deserialize.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:24`** — contract
  `date = date.replaceAll(nanoseconds, "");`
  replaceAll treats its argument as a regex and replaces every occurrence, not only the fraction: the date becomes "2024-8-T00:54:54.+02:00", and OffsetDateTime.parse then throws DateTimeParseException rather than returning the parsed date.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-f31fb34`

fix: skip recording token usage metric when

| | |
|---|---|
| introduced in | `898beedd4` |
| file | `langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java` |
| detectable from diff | weak |

3 finding(s) survived refutation:

- **`langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java:70`** — correctness
  `responseContext.chatResponse().tokenUsage().inputTokenCount());`
  The guard on line 65 only rejects a null TokenUsage, so execution reaches line 70; addTokenMetric declares int tokenCount, so the null Integer is auto-unboxed and onResponse throws NullPointerException. Neither the input nor the output token metric is recorded for that response - the OUTPUT call on line 74 is never reached - and the exception propagates out of the listener callback.

- **`langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java:70`** — contract
  `responseContext.chatResponse().tokenUsage().inputTokenCount());`
  The guard on line 65 only rejects a null TokenUsage, so the null Integer returned by inputTokenCount()/outputTokenCount() is auto-unboxed into the int parameter of addTokenMetric and throws NullPointerException inside onResponse; no token metric is recorded for that response at all - not even the non-null half - and the listener invocation fails.

- **`langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java:70`** — contract
  `responseContext.chatResponse().tokenUsage().inputTokenCount());`
  inputTokenCount() returns a null Integer that is auto-unboxed into the int parameter of addTokenMetric, throwing NullPointerException inside onResponse; the guard on line 65 only checks the TokenUsage object, not its nullable fields, so neither the input nor the output token metric is recorded for that response.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-787f95c`

fix: Preserve BigInteger values when convert

| | |
|---|---|
| introduced in | `e8bfc9b13` |
| file | `langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolExecutionHelper.java` |
| detectable from diff | yes |

3 finding(s) survived refutation:

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolExecutionHelper.java:69`** — correctness
  `case LONG, BIG_INTEGER -> content.asLong();`
  content.asLong() delegates to BigInteger.longValue(), which keeps only the low 64 bits: the map returned by toObject holds -5670419503621182411 instead of 123456789012345678901, and ToolExecutionResult.result() therefore carries a silently wrong number while resultText (built from content.toString()) still shows the correct one. No exception is raised, so nothing signals the loss.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolExecutionHelper.java:69`** — boundary
  `case LONG, BIG_INTEGER -> content.asLong();`
  asLong() on a BigIntegerNode delegates to BigInteger.longValue(), which keeps only the low-order 64 bits. The map returned by toObject holds 0 for 18446744073709551616, and can hold a value of the opposite sign for other out-of-range inputs. No exception is raised, so the caller receives a silently corrupted number in ToolExecutionResult.result() while resultText still shows the correct digits.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolExecutionHelper.java:69`** — correctness
  `case LONG, BIG_INTEGER -> content.asLong();`
  asLong() delegates to BigInteger.longValue(), which narrows by keeping only the low 64 bits and throws no error: the map returned by toObject carries id=0 instead of 18446744073709551616 (and 9223372036854775808 becomes -9223372036854775808). The wrong value is handed to the caller via ToolExecutionResult.result() with no exception and no signal, while resultText still shows the correct digits, so the object and the text disagree.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-45e3ab8`

fix: Omit blank/null Content-Type part heade

| | |
|---|---|
| introduced in | `f368ec038` |
| file | `http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java` |
| detectable from diff | weak |

7 finding(s) survived refutation:

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:19`** — correctness
  `private static final String BOUNDARY = "----LangChain4j";`
  The assembled body contains the delimiter inside a part body, so the receiving server ends that part early and parses the remaining file bytes as further part headers/parts: the uploaded file is silently truncated, or the request is rejected as malformed multipart. No error is raised on the client side.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:38`** — correctness
  `+ name + "\"; filename=\"" + file.fileName() + "\"" + CRLF + "Content-Type: "`
  The emitted header becomes Content-Disposition: form-data; name="audio"; filename="my"file.mp3" — the server reads the filename as "my" and drops the rest — or, with a CRLF in the name, the injected text is parsed as an additional part header, so the request carries headers the caller never set.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:38`** — contract
  `+ name + "\"; filename=\"" + file.fileName() + "\"" + CRLF + "Content-Type: "`
  The value is interpolated into the Content-Disposition header without quoting or escaping, so the emitted header is malformed: with an embedded quote the server's quoted-string parser terminates the filename early (server sees filename "my" and trailing garbage, or rejects the request with 400); with an embedded CRLF arbitrary extra headers or a forged part boundary are injected into the multipart body.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:19`** — correctness
  `private static final String BOUNDARY = "----LangChain4j";`
  The boundary is a fixed constant and is never checked against part content, so the server's multipart parser terminates the part at the embedded occurrence: the uploaded file is silently truncated and the remaining bytes are parsed as further parts or rejected as a malformed body.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:38`** — contract
  `+ name + "\"; filename=\"" + file.fileName() + "\"" + CRLF + "Content-Type: "`
  the value is interpolated into the quoted-string of Content-Disposition with no escaping (RFC 7578 requires quoting/percent-escaping), so the receiver parses the filename as "my" and treats the remainder as further header parameters; with a CRLF the caller can inject arbitrary extra part headers into the multipart body

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:71`** — contract
  `ContentType.MULTIPART_FORM_DATA.withParameters(new BasicNameValuePair("boundary", BOUNDARY));`
  ContentType.MULTIPART_FORM_DATA carries ISO-8859-1 and withParameters re-emits the inherited charset, so the header sent is "multipart/form-data; charset=ISO-8859-1; boundary=----LangChain4j" while every part was encoded with getBytes(UTF_8); a receiver that honours the declared charset decodes "résumé" as "rÃ©sumÃ©"

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:19`** — correctness
  `private static final String BOUNDARY = "----LangChain4j";`
  the delimiter is a compile-time constant that is never checked against the payload, so the receiver ends the part at that offset and the uploaded file is silently truncated (and the remainder parsed as bogus parts); because the boundary is fixed, the collision is deterministic and every retry reproduces it

**Detected?** `no` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-6020c8a`

fix: Decode Markdown as UTF-8 instead of the

| | |
|---|---|
| introduced in | `63f4e02c5` |
| file | `document-parsers/langchain4j-document-parser-markdown/src/main/java/dev/langchain4j/data/document/parser/markdown/MarkdownDocumentParser.java` |
| detectable from diff | weak |

3 finding(s) survived refutation:

- **`document-parsers/langchain4j-document-parser-markdown/src/main/java/dev/langchain4j/data/document/parser/markdown/MarkdownDocumentParser.java:25`** — correctness
  `final Node node = parser.parseReader(new InputStreamReader(inputStream));`
  The one-argument InputStreamReader decodes with the platform default charset, so 0xC3 0xA9 is decoded as two separate characters and the rendered text at line 29 becomes a mojibake string instead of "cafe"; Document.from(text) at line 35 stores the corrupted text, and every downstream consumer (splitting, embedding, retrieval) sees it. The same file parsed on a UTF-8-default JVM yields different text, so the parser is not deterministic across hosts.

- **`document-parsers/langchain4j-document-parser-markdown/src/main/java/dev/langchain4j/data/document/parser/markdown/MarkdownDocumentParser.java:25`** — correctness
  `final Node node = parser.parseReader(new InputStreamReader(inputStream));`
  The bytes are decoded with the wrong charset before CommonMark ever sees them, so the returned Document carries mojibake or U+FFFD replacement characters ("CafÃ© â€” rÃ©sumÃ©", or "Caf?" under ASCII) instead of the source text. No exception is raised and isNullOrBlank(text) still passes, so the corruption is written silently into the Document and into anything downstream that embeds or indexes it. The same file parsed on a UTF-8-default JVM yields different text, making the parser's output host-dependent.

- **`document-parsers/langchain4j-document-parser-markdown/src/main/java/dev/langchain4j/data/document/parser/markdown/MarkdownDocumentParser.java:25`** — correctness
  `final Node node = parser.parseReader(new InputStreamReader(inputStream));`
  InputStreamReader is constructed without a Charset, so it decodes with the platform default instead of UTF-8: the returned Document text contains mojibake ("CafÃ© â€” rÃ©sumÃ©") or U+FFFD replacement characters, and the corrupted text is what gets embedded and indexed. The same file parsed on two hosts yields two different Documents.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `langchain4j-ca3b112`

fix(elasticsearch): apply hybrid filters to

| | |
|---|---|
| introduced in | `2c170dd43` |
| file | `langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java` |
| detectable from diff | yes |

3 finding(s) survived refutation:

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:133`** — correctness
  `.minScore(embeddingSearchRequest.minScore())`
  The request sets min_score=0.5 on a search whose top-level scores are RRF fusion scores, not similarity scores. With the default rank_constant of 60, a document ranked first by both retrievers scores 1/(60+1) + 1/(60+1) = 0.0328, so every hit is below 0.5 and Elasticsearch returns zero hits. The store silently yields an empty result list for queries that have perfect matches; any minScore above roughly 0.033 produces the same empty result.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:133`** — correctness
  `.minScore(embeddingSearchRequest.minScore())`
  The search returns zero hits regardless of how well documents match. minScore is a normalized similarity in [0,1], but the request ranks with an rrf retriever, whose score is the sum of 1/(rank_constant + rank) over the two legs and therefore never exceeds 2/61 = 0.0328 with the default rank_constant of 60. Passing that similarity threshold straight to Elasticsearch's min_score filters out every document as soon as minScore exceeds 0.0328; only the default minScore of 0.0 behaves sanely.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:133`** — contract
  `.minScore(embeddingSearchRequest.minScore()),`
  Zero hits are returned even when both the kNN and the match retriever rank documents highly. EmbeddingSearchRequest.minScore is a relevance threshold on the 0..1 similarity scale, but here it is passed as the top-level min_score of a search whose scores come from the rrf retriever, which emits reciprocal-rank scores of 1/(rank_constant+rank) - about 0.0164 for the top document with the default rank_constant of 60. Every score is therefore below any threshold above ~0.016, so the filter silently discards the whole result set instead of trimming weak matches.

**Detected?** `no` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## Excluded from scoring, and why

| case | reason |
|---|---|
| `langchain4j-3699d82` | not findable from the diff (no) |

## To total it

- **detected / 18 scorable** — the headline, as a fraction.
- **findings that were not the known defect** — not errors (a genuine second bug
  is not a false positive), but the number that bounds a reader's cost, and the
  one that decides whether anyone keeps using this.

Nothing here measures a false-positive rate: every case is a diff known to
contain a defect. That needs the opposite corpus — clean commits — and it is
arguably the more useful of the two.

---

Harness transport, 18 case(s), 0 finding(s) refused by the guards. **No dollar cost**: the tokens are the harness's. That is the point of running the scaling measurement here.
