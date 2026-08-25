# Acceptance worksheet — one word per finding

Below are claims a code reviewer made about specific lines of Java. Each one names a file and a
line, quotes the code, states the inputs that trigger the problem and the consequence that
follows.

## What to do

Read each block. Write one word after `**verdict:**`, replacing the `?`. Nothing else. Do not
edit any other part of the file.

| word | means |
|---|---|
| `act` | I would change this code, or file it. |
| `note` | True, and I would not act on it — too minor, out of scope, a known trade-off. |
| `wrong` | The claim is false, or the consequence does not follow from the inputs. |
| `unsure` | I cannot tell without more work than this finding deserves. |

**`unsure` is a real answer, not a skip.** A forced verdict is invented data.

You are not auditing correctness. The question is only: **was this worth reading?**

Judge each block on its own. Some claims resemble each other; that is expected, and each still
costs a reader a block to read.

Answer every block in order, and do not skip one because it is hard — a skipped block is the one
whose answer mattered.

---

### 001

`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:36`

```java
this.tokenizer = HuggingFaceTokenizer.newInstance(Paths.get(pathToTokenizer), tokenizerOptions);
```

**Given** a valid modelPath with a pathToTokenizer that does not exist or is unreadable, so HuggingFaceTokenizer.newInstance throws

**Then** the OrtSession created on line 28 has already loaded the model into native memory and is never closed: the exception is converted to RuntimeException, the partially built instance is discarded, and no reference to the session survives, so its native memory is leaked for the life of the process (and leaks again on every retried construction).

**verdict:** ?

---

### 002

`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:44`

```java
builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema")));
```

**Given** A ListToolsResult whose tool has inputSchema = {"$ref": "#/$defs/Input", "$defs": {"Input": {"type": "object"}}}

**Then** The new $ref branch at line 76 returns a JsonReferenceSchema, so the unchecked cast to JsonObjectSchema throws ClassCastException out of toolSpecificationListFromMcpResponse, aborting the whole tool list rather than one tool. Before this change the same input fell through to the typeNode == null branch and produced a JsonObjectSchema.

**verdict:** ?

---

### 003

`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:24`

```java
date = date.replaceAll(nanoseconds, "");
```

**Given** A timestamp whose fractional digits also occur earlier in the string — reachable because the fraction is emitted with trailing zeros stripped (the very 8-vs-9-digit variance the comment describes), e.g. "2024-08-04T00:54:54.54+02:00".

**Then** replaceAll strips every occurrence of "54", producing "2024-08-04T00::.+02:00", and OffsetDateTime.parse throws DateTimeParseException rather than yielding 00:54:54+02:00.

**verdict:** ?

---

### 004

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:61`

```java
requestConfigBuilder.setConnectionRequestTimeout(
```

**Given** Build the client with connectTimeout = Duration.ofSeconds(2) and send a request to an unroutable/blackholed host (e.g. https://10.255.255.1/v1/chat). connectTimeout is mapped to RequestConfig.setConnectionRequestTimeout, which bounds leasing a connection from the pool, not the TCP connect (that lives on ConnectionConfig.setConnectTimeout in HttpClient 5.x).

**Then** The pool hands out a free slot immediately so the 2 s value never applies, and the TCP connect runs under the default 3-minute connect timeout: execute() blocks for about three minutes before failing instead of failing after 2 s. The configured connect timeout has no observable effect on either the sync or the async client.

**verdict:** ?

---

### 005

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:272`

```java
input = SANITIZE_PATTERN_START.matcher(input).replaceAll("");
```

**Given** Default construction (sanitizeInput = true, set by the single-argument constructor) and code whose first token merely starts with the letters "python", e.g. `python_version = 3` or `PythonPath = "/mnt/data"`.

**Then** SANITIZE_PATTERN_START is `^(\s|`)*(?i:python)?\s*` with no word boundary after the optional keyword, so the leading "python" is stripped and `_version = 3` is what gets sent to the session. Different code than the caller asked for is executed, and the failure surfaces as an unrelated Python error.

**verdict:** ?

---

### 006

`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`

```java
String text = p.toString().trim();
```

**Given** unanimousLastWord() applied to a Collection<Object> that contains a null element, e.g. Arrays.asList("YES", null).

**Then** p.toString() throws NullPointerException and hasConverged aborts instead of returning a boolean, whereas the sibling unanimous() tolerates the same input via Objects.equals.

**verdict:** ?

---

### 007

`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:187`

```java
                || state == TaskState.TASK_STATE_FAILED
```

**Given** A TaskEvent (or TaskUpdateEvent) whose Task has `status().state() == TaskState.TASK_STATE_FAILED` (likewise `TASK_STATE_CANCELED` or `TASK_STATE_REJECTED`) and an empty `artifacts()` list — the normal shape of a remote agent that errored and produced no output.

**Then** isTerminalState returns true, the early return at line 178-180 is skipped, and line 181 calls `messageResponse.complete("")`. `messageResponse.get()` returns the empty string instead of throwing, so the failure is swallowed: `serviceOutputParser.parseText(returnType, "")` runs on it and invokeAgent hands the caller an empty successful result for a task the server reported as failed/canceled/rejected.

**verdict:** ?

---

### 008

`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`

```java
Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));
```

**Given** A page whose source contains any non-ASCII character (e.g. "café", "中文") loaded on a JVM whose default charset is not UTF-8 - the normal case for Java 17 on Windows (windows-1252) - and the usual TextDocumentParser, which decodes the stream as UTF-8.

**Then** String.getBytes() encodes with the platform default charset while the parser decodes as UTF-8, so the returned Document's text contains mojibake or U+FFFD replacement characters instead of the page's characters; the same URL yields different document text depending on the machine's locale.

**verdict:** ?

---

### 009

`auto-configurations/vector-stores/spring-ai-autoconfigure-vector-store-mongodb-atlas/src/main/java/org/springframework/ai/vectorstore/mongodb/autoconfigure/MongoDBAtlasVectorStoreAutoConfiguration.java:81`

```java
		return () -> mongoClientProvider.ifAvailable(mongoClient -> mongoClient
```

**Given** An application context containing exactly two (or more) MongoClient beans with none marked @Primary — e.g. a multi-cluster setup that defines its own MongoTemplate/MongoDatabaseFactory beans so Spring Boot's single-client auto-configuration backs off. Zero clients and exactly one client both behave fine; the behaviour changes at count >= 2.

**Then** ObjectProvider.ifAvailable delegates to getIfAvailable(), which for a non-collection type with multiple candidates and no primary calls resolveNotUnique and throws NoUniqueBeanDefinitionException. The exception is raised from the SmartInitializingSingleton callback during afterSingletonsInstantiated, so the whole application context fails to refresh and startup aborts — even though the metadata append is purely cosmetic. The sibling injection at line 93 avoids this by using getIfUnique.

**verdict:** ?

---

### 010

`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`

```java
documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))
```

**Given** A page whose source contains non-ASCII characters (e.g. "café", "日本語") loaded on a JVM whose default charset is not UTF-8 — Java 17 on a Windows locale defaults to windows-1252/cp1252.

**Then** String.getBytes() encodes with the platform default charset while DocumentParser implementations (e.g. TextDocumentParser) decode the stream as UTF-8, so the returned Document text contains mojibake or U+FFFD replacement characters instead of the page's characters; the same page yields different Document text on different hosts.

**verdict:** ?

---

### 011

`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:151`

```java
if (chatClientResponse.chatResponse() == null || !chatClientResponse.chatResponse().hasToolCalls()) {
```

**Given** maxRepeatAttempts = 3; the chain returns a response whose JSON fails schema validation on the first iteration, and on the second iteration returns a response with hasToolCalls() == true.

**Then** The if-block is skipped, so isValidationSuccess keeps the stale false from the previous iteration: the loop keeps calling the model even though the current response was never validated, and if the final iteration also carries tool calls the advisor returns that never-validated response as the result. Symmetrically, a first response with tool calls leaves isValidationSuccess at its initial true and the advisor returns it without ever validating anything.

**verdict:** ?

---

### 012

`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`

```java
SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);
```

**Given** A store holding 25 documents with metadata field country == "BG", then doDelete(new Filter.Expression(EQ, key("country"), value("BG"))). The two-argument ftSearch(String, String) builds a default redis.clients.jedis.search.Query, whose paging defaults to offset 0 / num 10 (FT.SEARCH default LIMIT 0 10).

**Then** searchResult.getDocuments() returns only the first 10 matches, so matchingIds holds 10 ids and only 10 keys are jsonDel'd. The remaining 15 matching documents stay in Redis while the method returns normally, with no exception and a debug line claiming "Deleted 10 documents matching filter expression" — the caller believes the filter delete removed everything it matched.

**verdict:** ?

---

### 013

`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:76`

```java
ObjectListing objectListing = cosClient.listObjects(listObjectsRequest);
```

**Given** loadDocuments("my-bucket", parser) on a bucket (or prefix) holding more than 1000 objects, e.g. 2500 keys.

**Then** listObjects returns a single truncated page (max-keys defaults to 1000) and the returned ObjectListing's isTruncated/nextMarker are never read, so the loop iterates only the first page: the method silently returns ~1000 documents instead of 2500, with no error and no log line.

**verdict:** ?

---

### 014

`document-parsers/langchain4j-document-parser-markdown/src/main/java/dev/langchain4j/data/document/parser/markdown/MarkdownDocumentParser.java:25`

```java
final Node node = parser.parseReader(new InputStreamReader(inputStream));
```

**Given** A UTF-8 encoded Markdown stream containing any non-ASCII byte sequence (e.g. the line "# Café — résumé", bytes C3 A9 / E2 80 94), parsed on a JVM whose Charset.defaultCharset() is not UTF-8 (the single-argument InputStreamReader constructor takes the platform default; on Java 17, which precedes JEP 400, that is windows-1252 on a Western Windows host and US-ASCII under LANG=C).

**Then** The bytes are decoded with the wrong charset before CommonMark ever sees them, so the returned Document carries mojibake or U+FFFD replacement characters ("CafÃ© â€” rÃ©sumÃ©", or "Caf?" under ASCII) instead of the source text. No exception is raised and isNullOrBlank(text) still passes, so the corruption is written silently into the Document and into anything downstream that embeds or indexes it. The same file parsed on a UTF-8-default JVM yields different text, making the parser's output host-dependent.

**verdict:** ?

---

### 015

`langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java:70`

```java
                responseContext.chatResponse().tokenUsage().inputTokenCount());
```

**Given** A chat response whose TokenUsage is non-null but carries a null count, e.g. TokenUsage built with only a total (new TokenUsage(null, null, 42)) or the no-arg TokenUsage() — providers that report aggregate usage only.

**Then** inputTokenCount() returns a null Integer that is auto-unboxed into the int parameter of addTokenMetric, throwing NullPointerException inside onResponse; the guard on line 65 only checks the TokenUsage object, not its nullable fields, so neither the input nor the output token metric is recorded for that response.

**verdict:** ?

---

### 016

`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`

```java
String text = p.toString().trim();
```

**Given** positions containing a null element, e.g. Arrays.asList("AGREE", null) — the parameter is a plain Collection<Object> with no null guard, and a null is what an agent that produced no output contributes.

**Then** p.toString() throws NullPointerException, propagating out of hasConverged and aborting the debate loop instead of returning a boolean. The sibling strategy unanimous() tolerates the same input (Objects.equals is null-safe), so the two implementations of the same interface behave incomparably on it.

**verdict:** ?

---

### 017

`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`

```java
throw new RuntimeException("Failed to load document from GitHub: {}", ioException);
```

**Given** Any GHContent whose read fails, e.g. loadDocument("owner", "repo", "main", "README.md", parser) where GitHubSource/DocumentLoader.load throws an IOException (network drop mid-download).

**Then** RuntimeException(String, Throwable) does no SLF4J-style substitution, so the thrown exception's message is the literal text "Failed to load document from GitHub: {}" with no file URL; the caller sees an unformatted placeholder instead of the content identifier the message promises.

**verdict:** ?

---

### 018

`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`

```java
        if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {
```

**Given** A server that answers sendMessage with a single TaskEvent (or a last TaskUpdateEvent) whose state is non-terminal - e.g. TASK_STATE_SUBMITTED or TASK_STATE_WORKING - and whose artifacts list is empty, and then emits no further event and closes the stream without error.

**Then** completeFromTask returns without ever completing messageResponse, and no other code path completes it, so messageResponse.get() at line 164 blocks the calling thread forever. Before the change a TaskEvent always completed the future (with the joined artifact text, or an empty string), so this input returned instead of hanging.

**verdict:** ?

---

### 019

`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:121`

```java
        int attemptsLeft = maxRetries + 1;
```

**Given** A retriever built with builder().maxRetries(-1) (or any value <= -1); maxRetries is never validated in the constructor at line 103 nor in the builder setter at line 284.

**Then** attemptsLeft is 0, the while loop at line 122 never executes, and retrieve() returns emptyList() at line 145 without ever calling the ChatModel or the database, and without logging anything — an empty retrieval indistinguishable from a query that legitimately matched nothing.

**verdict:** ?

---

### 020

`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:151`

```java
if (chatClientResponse.chatResponse() == null || !chatClientResponse.chatResponse().hasToolCalls()) {
```

**Given** maxRepeatAttempts = 3 (the builder default) and an iteration whose response has hasToolCalls() == true: e.g. call 1 returns text that fails schema validation (isValidationSuccess set to false), then call 2 (and the remaining calls) return a ChatResponse carrying tool calls.

**Then** The whole if-block is skipped, so isValidationSuccess keeps the value left by the previous iteration. It stays false, the do/while keeps re-issuing the model call until repeatCounter exceeds maxRepeatAttempts (burning the remaining paid attempts on responses it never inspects), and adviseCall then returns the last tool-call ChatClientResponse as the final result even though its content was never validated against this.jsonSchema.

**verdict:** ?

---

### 021

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:38`

```java
                + name + "\"; filename=\"" + file.fileName() + "\"" + CRLF + "Content-Type: "
```

**Given** a FormDataFile whose fileName() contains a double quote, e.g. "my\"file.txt", or a CRLF, e.g. "a.txt
X-Injected: 1"

**Then** the value is interpolated into the quoted-string of Content-Disposition with no escaping (RFC 7578 requires quoting/percent-escaping), so the receiver parses the filename as "my" and treats the remainder as further header parameters; with a CRLF the caller can inject arbitrary extra part headers into the multipart body

**verdict:** ?

---

### 022

`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:345`

```java
throw new IllegalArgumentException("Unknown stop reason: " + stopReason);
```

**Given** A successful ConverseResponse whose stopReason is any StopReason value other than END_TURN, STOP_SEQUENCE, MAX_TOKENS or TOOL_USE - e.g. CONTENT_FILTERED, GUARDRAIL_INTERVENED, or UNKNOWN_TO_SDK_VERSION when the service returns a stop reason newer than the bundled SDK enum.

**Then** finishReasonFrom throws IllegalArgumentException, so a well-formed HTTP 200 Converse response (guardrail intervention or filtered content) is turned into a client-side exception and the model output already received is discarded instead of being returned with a FinishReason such as CONTENT_FILTER.

**verdict:** ?

---

### 023

`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:39`

```java
okBuilder.connectTimeout(builder.connectTimeout().toMillis(), TimeUnit.MILLISECONDS);
```

**Given** A builder configured with a non-zero connect or read timeout shorter than one millisecond, e.g. Duration.ofNanos(500_000) or Duration.ofMicros(900).

**Then** Duration.toMillis() truncates to 0, and OkHttp interprets a timeout of 0 as "no timeout", so the client waits forever instead of failing fast — the exact opposite of the requested bound. The behaviour flips at 1_000_000 ns: 999_999 ns yields an infinite timeout, 1_000_000 ns yields 1 ms.

**verdict:** ?

---

### 024

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:160`

```java
BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))
```

**Given** A successful response whose body contains non-ASCII bytes and whose charset differs from the JVM default - e.g. Content-Type: text/plain; charset=ISO-8859-1 with byte 0xE9 (é) on a JVM defaulting to UTF-8, or a UTF-8 JSON body containing é on a Java 17 Windows JVM whose default charset is windows-1252.

**Then** InputStreamReader is constructed without a Charset, so it uses Charset.defaultCharset() and ignores the charset declared by the entity. The bytes are decoded with the wrong charset and SuccessfulHttpResponse.body (built at line 149 from this same method) contains U+FFFD replacement characters or mojibake instead of the transmitted text.

**verdict:** ?

---

### 025

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:38`

```java
                + name + "\"; filename=\"" + file.fileName() + "\"" + CRLF + "Content-Type: "
```

**Given** A FormDataFile whose fileName() contains a double quote or a CRLF, e.g. fileName() == "my\"file.wav" or "a.wav\r\nX-Injected: 1"; likewise a field/file name containing those characters.

**Then** The value is interpolated into the Content-Disposition header without quoting or escaping, so the emitted header is malformed: with an embedded quote the server's quoted-string parser terminates the filename early (server sees filename "my" and trailing garbage, or rejects the request with 400); with an embedded CRLF arbitrary extra headers or a forged part boundary are injected into the multipart body.

**verdict:** ?

---

### 026

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:387`

```java
Map<String, Object> fileMetadataMap = valueList.get(0);
```

**Given** A 2xx upload response whose body is {"value": []} (empty array), or a body with no "value" key at all.

**Then** valueList.get(0) throws IndexOutOfBoundsException on the empty array (and convertValue returns null, so a missing "value" key throws NullPointerException). The exception is caught at line 390 and rethrown as RuntimeException("Failed to upload file: Index 0 out of bounds for length 0 ..."), reporting an index error instead of the actual server response.

**verdict:** ?

---

### 027

`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:55`

```java
pageContent = webDriver.getPageSource();
```

**Given** A WebDriver whose getPageSource() returns null - documented as nullable in the Selenium API and observed for non-HTML responses (e.g. a URL serving a PDF or an image) and for drivers on a blank/failed page.

**Then** The assignment succeeds inside the try, so the NullPointerException is raised at line 59 by pageContent.getBytes(), outside the catch block. It escapes as a bare NPE with no message instead of the RuntimeException("Failed to load document", e) every other failure in load() produces, so callers catching that contract see an unwrapped NPE.

**verdict:** ?

---

### 028

`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:123`

```java
private int maxResults;
```

**Given** A retriever built without calling maxResults(...), e.g. ElasticsearchContentRetriever.builder().restClient(client).embeddingModel(model).build(), then retrieve(Query.from("hello")) with the default knn configuration.

**Then** The primitive field defaults to 0, so line 87 calls EmbeddingSearchRequest.builder().maxResults(0); EmbeddingSearchRequest validates maxResults with ensureGreaterThanZero, so every retrieve() throws IllegalArgumentException instead of returning results. Because the field is a primitive int, the builder cannot pass null and cannot fall back to the request's own default of 3.

**verdict:** ?

---

### 029

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:155`

```java
        return " OR (i.metadata is null) ";
```

**Given** A document stored with no metadata, queried with new IsNotEqualTo("k", "v") (or IsNotIn), which produces the query fragment plus the join clause built by FilterResult.

**Then** FilterResult always emits at least " join i.metadata m0", an inner join, so a document whose metadata is null produces no row at all and never reaches the WHERE clause. The i.metadata is null disjunct can never be true for any candidate row: it is a silent no-op, and the metadata-less documents it was written to rescue are still excluded.

**verdict:** ?

---

### 030

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:429`

```java
byte[] fileBytes = response.body().getBytes(StandardCharsets.UTF_8);
```

**Given** DefaultFileDownloader.downloadFile called for a non-UTF-8 file stored in the session, e.g. a PNG produced by matplotlib or an .xlsx written by the executed code.

**Then** The body was already decoded to a String; every byte sequence that is not valid UTF-8 has become U+FFFD, and re-encoding produces EF BF BD. The Base64 string returned to the caller decodes to a corrupted file that no longer matches the remote one, silently and with no error.

**verdict:** ?

---

### 031

`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:59`

```java
Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));
```

**Given** load("http://host/page", parser) where the page source returned by getPageSource() contains non-ASCII text (e.g. "café" or "東京"), running on a JVM whose default charset is not UTF-8 (e.g. Java 17 on Windows, windows-1252) while the DocumentParser decodes the stream as UTF-8.

**Then** String.getBytes() encodes with the platform default charset, so the parser decodes mismatched bytes: "café" comes back as "cafÃ©" (or with U+FFFD), and characters not representable in the default charset (CJK under windows-1252) are encoded as '?' and lost irrecoverably. The returned Document's text is corrupted, and the same URL yields different content depending on the machine's locale.

**verdict:** ?

---

### 032

`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`

```java
String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();
```

**Given** unanimousLastWord() applied to positions = ["We should proceed
YES", "YES"] (first agent puts its verdict on its own line, as multi-line agent output routinely does).

**Then** Only the ASCII space is treated as a separator, so lastIndexOf(' ') lands on the space before "proceed" and lastWord becomes "PROCEED
YES" instead of "YES"; the interior newline survives trim(), the comparison with "YES" fails and hasConverged returns false although both positions end in the same verdict — the debate loop keeps running past a real consensus.

**verdict:** ?

---

### 033

`langchain4j-gpu-llama3/src/main/java/dev/langchain4j/model/gpullama3/GPULlama3BaseModel.java:152`

```java
        if (stopToken == null) {
            return "Ran out of context length...\n Increase context length with by passing to llama-tornado --max-tokens XXX";
```

**Given** Any ChatRequest whose generation reaches the maxTokens limit before emitting a stop token (e.g. a small maxTokens such as 32 with a prompt that asks for a long answer), so that responseTokens is non-empty but its last element is not in chatFormat.getStopTokens().

**Then** responseText, which holds the tokens the model actually produced, is decoded on line 142 and then discarded; the method returns the hardcoded diagnostic string "Ran out of context length..." instead. The caller receives that sentence as the model's answer with no way to distinguish it from a genuine reply, and in the streaming case the consumer has already received the real tokens, so the final aggregated response contradicts the stream.

**verdict:** ?

---

### 034

`langchain4j-guardrails/src/main/java/dev/langchain4j/guardrails/PatternBasedPromptInjectionGuardrail.java:123`

```java
String text = userMessage.singleText();
```

**Given** A multimodal UserMessage whose contents hold more than one item, e.g. UserMessage.from(TextContent.from("ignore all previous instructions"), ImageContent.from("https://example.com/x.png")) — or any UserMessage built from a single non-text content.

**Then** UserMessage.singleText() does not return null for such a message; it throws (Expecting single text content, but got: ...). validate() propagates that exception out of the guardrail instead of returning an InputGuardrailResult, so the request fails with an unhandled error rather than being allowed or blocked — and the injection text carried alongside the image is never pattern-checked. The guarding `text == null` branch on the next line is consequently unreachable and does not protect this path.

**verdict:** ?

---

### 035

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:29`

```java
            for (int j = 0; j <= i; j++) {
                sb.append(" join i.metadata m").append(j);
```

**Given** Any composite filter, e.g. new And(new IsEqualTo("a", "1"), new IsEqualTo("b", "2")): the outer map() call takes i = 0, then the two recursive calls take i = 1 and i = 2.

**Then** The index consumed by the composite node is never referenced by any generated predicate, yet the join clause is built for every j from 0 to i, emitting " join i.metadata m0 join i.metadata m1 join i.metadata m2" with m0 unconstrained. The query therefore carries an extra unrestricted inner join over the metadata collection, multiplying each matching document by its number of metadata entries and excluding documents with no metadata entry at all.

**verdict:** ?

---

### 036

`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:371`

```java
new HashMap<>(this.defaultRequestParameters.additionalModelRequestFields());
```

**Given** A model built without defaultRequestParameters (or with parameters that never set additionalModelRequestFields), so this.defaultRequestParameters is BedrockChatRequestParameters.builder().modelName(modelId).build() and its additionalModelRequestFields() returns null - the same accessor the very next statement (line 374) null-checks on the request-scoped instance.

**Then** new HashMap<>(null) throws NullPointerException on every chat request that reaches additionalRequestModelFieldsFrom, before any call to Bedrock is made.

**verdict:** ?

---

### 037

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:61`

```java
requestConfigBuilder.setConnectionRequestTimeout(
                    Timeout.ofMilliseconds(builder.connectTimeout().toMillis()));
```

**Given** ApacheHttpClient.builder().connectTimeout(Duration.ofMillis(100)) and a request to a host that silently drops SYN packets (unroutable IP / blackholed firewall).

**Then** RequestConfig.setConnectionRequestTimeout bounds how long a connection is waited for from the pool, not how long the TCP handshake may take (that is ConnectionConfig.setConnectTimeout in HttpClient 5). Leasing a fresh connection from an idle pool returns immediately, so the configured 100 ms never applies to the handshake and execute() blocks for the ConnectionConfig default (3 minutes) instead of failing after 100 ms.

**verdict:** ?

---

### 038

`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:133`

```java
.minScore(embeddingSearchRequest.minScore()),
```

**Given** Any EmbeddingSearchRequest built with a non-default minScore, e.g. EmbeddingSearchRequest.builder().queryEmbedding(e).maxResults(10).minScore(0.7).build(), issued against a store configured with ElasticsearchConfigurationHybrid.

**Then** Zero hits are returned even when both the kNN and the match retriever rank documents highly. EmbeddingSearchRequest.minScore is a relevance threshold on the 0..1 similarity scale, but here it is passed as the top-level min_score of a search whose scores come from the rrf retriever, which emits reciprocal-rank scores of 1/(rank_constant+rank) - about 0.0164 for the top document with the default rank_constant of 60. Every score is therefore below any threshold above ~0.016, so the filter silently discards the whole result set instead of trimming weak matches.

**verdict:** ?

---

### 039

`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`

```java
matchingIds.add(docId.replace(key(""), ""));
```

**Given** Default prefix "embedding:" and a document whose id itself contains the prefix string, e.g. Document id "embedding:42" (stored under Redis key "embedding:embedding:42"), matched by the filter expression.

**Then** String.replace() removes every occurrence, not just the leading one: "embedding:embedding:42" becomes "42", so the loop deletes key("42") = "embedding:42" — a different, unrelated document — while the intended key "embedding:embedding:42" survives. If no document exists under "embedding:42", jsonDel returns 0, RESPONSE_DEL_OK fails and the whole call throws IllegalStateException("Failed to delete documents by filter") after some other keys in the same pipeline were already deleted. toDocument() strips the prefix correctly with substring(this.prefix.length()); this path does not.

**verdict:** ?

---

### 040

`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolExecutionHelper.java:69`

```java
case LONG, BIG_INTEGER -> content.asLong();
```

**Given** A CallToolResult whose `structuredContent` holds an integer too large for a long, e.g. {"result":{"structuredContent":{"id":123456789012345678901}}}. Jackson parses 123456789012345678901 as a BigIntegerNode, so getNodeType() is NUMBER and numberType() is BIG_INTEGER, taking this arm.

**Then** content.asLong() delegates to BigInteger.longValue(), which keeps only the low 64 bits: the map returned by toObject holds -5670419503621182411 instead of 123456789012345678901, and ToolExecutionResult.result() therefore carries a silently wrong number while resultText (built from content.toString()) still shows the correct one. No exception is raised, so nothing signals the loss.

**verdict:** ?

---

### 041

`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:80`

```java
SuccessfulHttpResponse successResponse = fromOkHttpResponse(response);
```

**Given** A streaming call to execute(request, parser, listener) whose successful response carries no content-type header, or a content-type that does not contain the exact lowercase substring "text/event-stream" (e.g. "TEXT/EVENT-STREAM", or "application/x-ndjson").

**Then** fromOkHttpResponse takes the else branch at line 120 and calls readBody, i.e. response.body().string(), which consumes and closes the single-shot body. getInputStream(response) at line 83 then hands parser.parse an exhausted/closed stream, so no SSE event is ever delivered: the listener gets onOpen immediately followed by onClose with zero events (or onError with IllegalStateException "closed"), and the stream payload is silently lost.

**verdict:** ?

---

### 042

`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`

```java
matchingIds.add(docId.replace(key(""), ""));
```

**Given** Default prefix "embedding:" and a document whose id itself contains the prefix, e.g. Document id "a-embedding:b", stored under key "embedding:a-embedding:b", then deleted via a matching filter expression.

**Then** String.replace strips every occurrence, not just the leading one, so docId becomes "a-b" instead of "a-embedding:b". pipeline.jsonDel(key("a-b")) targets the non-existent key "embedding:a-b", returns 0 instead of 1, so RESPONSE_DEL_OK fails, an IllegalStateException("Failed to delete documents by filter") is thrown, and the real document is never deleted. The rest of the file uses doc.getId().substring(this.prefix.length()) for the same conversion (line 372).

**verdict:** ?

---

### 043

`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`

```java
if (!result.getPagemap().isEmpty()) {
```

**Given** A non-image search (searchTypeImage == false) whose Search contains at least one Result with no "pagemap" field in the JSON response, so Result.getPagemap() returns null. Google Custom Search omits pagemap for any page without structured data, so a single such hit in the result set is enough.

**Then** toResultMetadataMap dereferences null at line 171 and throws NullPointerException, which propagates out of the new toWebSearchOrganicResults stream (line 190-197) and out of search(), so the entire search call fails even though every other result item mapped fine.

**verdict:** ?

---

### 044

`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`

```java
.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())
```

**Given** A document added with a non-floating-point metadata value, e.g. new Document("c", Map.of("year", 2024)), then retrieved via similaritySearch.

**Then** Gson deserializing into TypeToken<Map<String, Object>> maps every JSON number to Double, so getMetadata().get("year") returns 2024.0 (Double) where the previous JSONObject.getInnerMap() returned Integer 2024; a caller doing (Integer) doc.getMetadata().get("year") now throws ClassCastException, and String.valueOf(...) renders "2024.0". The injected DocumentMetadata.DISTANCE value likewise changes from Float to Double, gaining float-to-double widening digits (e.g. 0.19999998807907104).

**verdict:** ?

---

### 045

`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`

```java
throw new RuntimeException("Failed to load document from GitHub: {}", ioException);
```

**Given** Any call reaching fromGitHub where reading the file content raises IOException, e.g. loadDocument("owner", "repo", "main", "README.md", parser) when the connection to the content URL drops mid-read.

**Then** The thrown RuntimeException's message is the literal string "Failed to load document from GitHub: {}" - the SLF4J placeholder is passed to the RuntimeException(String, Throwable) constructor, which does no formatting, so the top line of the stack trace and any getMessage() call show "{}" instead of the failure detail.

**verdict:** ?

---

### 046

`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`

```java
for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {
```

**Given** filedsMap = {"text_segment": stringValue("hello world"), "author": stringValue("bob")} with metadataTextKey = "text_segment" (i.e. any Pinecone match carrying at least one real metadata field besides the text field)

**Then** The loop never skips metadataTextKey, so the returned map is {"text_segment": "hello world", "author": "bob"} - the segment text is returned as a metadata entry. The early return at line 21 and the capacity hint `filedsMap.size() - 1` at line 25 both assume that key is excluded, so behaviour is inconsistent: with one field the text key is dropped, with two or more it is kept, and the text is duplicated into TextSegment metadata on every retrieval.

**verdict:** ?

---

### 047

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:333`

```java
                    String columnValue = resultSet.getObject(i).toString();
```

**Given** Any generated SELECT whose result set contains a SQL NULL cell, e.g. "SELECT name, email FROM customers" on a row where email IS NULL (or any LEFT JOIN with no match).

**Then** resultSet.getObject(i) returns null and .toString() throws NullPointerException. It is swallowed by catch (Exception e) at line 265; e.getMessage() is null, so the retry at line 279 drops the previous query/error context, the same NULL is hit again, and retrieve() returns emptyList() — no content for a query that actually returned rows, plus a wasted extra LLM call.

**verdict:** ?

---

### 048

`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:75`

```java
return this.fullTextSearch(query.text()).stream()
```

**Given** A retriever configured with ElasticsearchConfigurationFullText and built with maxResults(5), minScore(0.8) and a metadata filter, e.g. filter(metadataKey("userId").isEqualTo("42")), then retrieve(Query.from("hello")).

**Then** The full-text branch returns before the EmbeddingSearchRequest is built, so the constructor-supplied filter, maxResults and minScore are never applied on that path: segments belonging to other userIds are returned, the result list is not capped at 5, and low-scoring matches are not dropped. The three fields are silently dead for this configuration while their javadoc promises they govern retrieval.

**verdict:** ?

---

### 049

`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:565`

```java
stmt.setDouble(4, minScore);
```

**Given** A store built with searchMode(HYBRID) (default rrfK = 60) and any EmbeddingSearchRequest whose minScore is a normal relevance threshold, e.g. minScore(0.7) or even minScore(0.05), with a document that matches both the vector and the keyword query.

**Then** Returns an empty result list. request.minScore() is compared against the RRF score COALESCE(1.0/(60+v.rnk),0.0)+COALESCE(1.0/(60+k.rnk),0.0), whose maximum possible value is 2/(rrfK+1) = 0.0328, not against the 0..1 cosine similarity that embeddingOnlySearch produces and that minScore is defined against; every threshold above 0.0328 filters out all rows silently. The same rescaling makes the score field of every returned EmbeddingMatch ~0.03 instead of a 0..1 relevance, so callers that threshold or display scores from a VECTOR-mode store break when the mode is switched.

**verdict:** ?

---

### 050

`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolExecutionHelper.java:69`

```java
case LONG, BIG_INTEGER -> content.asLong();
```

**Given** A CallToolResult whose `structuredContent` holds an integer outside the signed 64-bit range, e.g. {"result":{"structuredContent":{"id":18446744073709551616}}}. Jackson parses that as a BigIntegerNode, so numberType() is BIG_INTEGER.

**Then** asLong() delegates to BigInteger.longValue(), which narrows by keeping only the low 64 bits and throws no error: the map returned by toObject carries id=0 instead of 18446744073709551616 (and 9223372036854775808 becomes -9223372036854775808). The wrong value is handed to the caller via ToolExecutionResult.result() with no exception and no signal, while resultText still shows the correct digits, so the object and the text disagree.

**verdict:** ?

---

### 051

`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:123`

```java
private int maxResults;
```

**Given** ElasticsearchContentRetriever.builder().restClient(client).embeddingModel(model).build() — i.e. a builder used without ever calling maxResults(), leaving the primitive int at 0.

**Then** retrieve() builds EmbeddingSearchRequest with maxResults = 0. Because the value is a boxed 0 rather than null, the request's own default (3) never applies and its greater-than-zero validation rejects it, so every retrieve() call fails with IllegalArgumentException instead of retrieving with a sane default. A primitive int field cannot express "not set", so the omitted-value case has no working default.

**verdict:** ?

---

### 052

`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:75`

```java
return this.fullTextSearch(query.text()).stream()
```

**Given** A retriever built with configuration = ElasticsearchConfigurationFullText, minScore = 0.8 and filter = metadataKey("type").isEqualTo("faq"), then retrieve(Query.from("hello")) over an index that also contains non-"faq" documents and low-scoring matches.

**Then** The full-text branch returns before minScore, filter and maxResults are ever used: fullTextSearch(String) receives only the query text, the EmbeddingSearchRequest at lines 85-90 is never built, and mapResultsToContentList (the only place the minScore threshold at line 101 is applied) is never called. The caller gets documents that do not match the filter and whose score is below the configured minScore, with no error and no log to say the parameters were dropped.

**verdict:** ?

---

### 053

`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`

```java
TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);
```

**Given** Subscribing more than once to the Flux returned by stream(), e.g. `model.stream(prompt).retry(1)` after a transient network error, `.repeat()`, or two subscribers on the same returned Flux.

**Then** params is built once outside Flux.create and holds a single ByteArrayInputStream (buildParams line 178). Flux.create runs its lambda per subscription, so the second HTTP request re-sends the same already-exhausted stream: the multipart file part is uploaded with zero bytes, and the API rejects the request or returns a transcription of nothing instead of the audio. A Flux is expected to be re-subscribable; this one silently is not.

**verdict:** ?

---

### 054

`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:133`

```java
.minScore(embeddingSearchRequest.minScore())
```

**Given** An EmbeddingSearchRequest built with a typical relevance threshold, e.g. EmbeddingSearchRequest.builder().queryEmbedding(e).maxResults(10).minScore(0.5).build(), with a textQuery that matches documents exactly.

**Then** The request sets min_score=0.5 on a search whose top-level scores are RRF fusion scores, not similarity scores. With the default rank_constant of 60, a document ranked first by both retrievers scores 1/(60+1) + 1/(60+1) = 0.0328, so every hit is below 0.5 and Elasticsearch returns zero hits. The store silently yields an empty result list for queries that have perfect matches; any minScore above roughly 0.033 produces the same empty result.

**verdict:** ?

---

### 055

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:68`

```java
if (filter instanceof IsGreaterThan) return "k/value gt '%s'";
```

**Given** map(new IsGreaterThan("year", 9)) against documents whose "year" attribute is 10.

**Then** The number is emitted as a quoted literal, giving k/value gt '9'. Against the string-typed k/value field the comparison is lexicographic, so '10' gt '9' is false and the year=10 document is dropped from the results; if k/value is instead a numeric field, Edm.Int32 gt Edm.String is a type error and Azure returns HTTP 400. The same quoting is applied by IsGreaterThanOrEqualTo, IsLessThan and IsLessThanOrEqualTo on lines 69-71.

**verdict:** ?

---

### 056

`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:151`

```java
if (chatClientResponse.chatResponse() == null || !chatClientResponse.chatResponse().hasToolCalls()) {
```

**Given** maxRepeatAttempts = 3 (the builder default); attempt 1 returns a non-tool-call response whose text fails schema validation, so isValidationSuccess becomes false and the prompt is augmented; attempt 2 returns a response with hasToolCalls() == true (internal tool execution disabled, so tool-call responses reach the advisor).

**Then** On attempt 2 the whole validation block is skipped, so isValidationSuccess keeps the stale value false from attempt 1. The while condition on line 179 is therefore true and the loop overwrites chatClientResponse with a further model call: the tool-call response is discarded and never returned to the caller, the requested tool is never executed, and an extra billed model call is made. If the counter runs out on such an iteration the advisor returns a response it never validated while its state says validation failed.

**verdict:** ?

---

### 057

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:147`

```java
            ResultSet columns = metaData.getColumns(null, null, tableName, null);
```

**Given** Constructing the retriever without databaseStructure so generateDDL runs, against a schema with many tables (e.g. 100 tables on Oracle with the default OPEN_CURSORS=300).

**Then** columns, pk, fks (line 149) and tableRemarks (line 218) are never closed; four cursors per table stay open on the single Connection until generateDDL returns, so on a driver with a cursor cap the metadata call fails (e.g. ORA-01000 maximum open cursors exceeded) and is rethrown as RuntimeException from the constructor.

**verdict:** ?

---

### 058

`spring-ai-model/src/main/java/org/springframework/ai/model/tool/DefaultToolCallingManager.java:243`

```java
.parentObservation(parent)
```

**Given** A blocking (non-reactive) tool call, where ToolCallReactiveContextHolder.getContext() is empty, so getOrDefault(ObservationThreadLocalAccessor.KEY, null) yields parent == null, while an enclosing chat-model observation is open in scope on the current thread (observationRegistry.getCurrentObservation() != null).

**Then** Observation.parentObservation(null) overwrites the parent that the observation's constructor already set from the registry's current observation, so the TOOL_CALL observation is emitted as a root span with no parent instead of a child of the enclosing chat-model observation, breaking the trace hierarchy on the imperative path that previously nested correctly.

**verdict:** ?

---

### 059

`document-loaders/langchain4j-document-loader-selenium/src/main/java/dev/langchain4j/data/document/loader/selenium/SeleniumDocumentLoader.java:55`

```java
pageContent = webDriver.getPageSource();
```

**Given** A WebDriver whose getPageSource() returns null - permitted by the WebDriver contract and returned by some drivers/contexts (e.g. after navigating to a non-HTML resource or a driver window with no document).

**Then** pageContent is null and line 59 dereferences it outside the try block, so a raw NullPointerException escapes load() instead of the wrapped RuntimeException("Failed to load document", e) every other failure path produces.

**verdict:** ?

---

### 060

`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`

```java
WHERE ranked.score >= ?
```

**Given** A store built with searchMode(HYBRID) and default rrfK (60), searched with an EmbeddingSearchRequest whose minScore is greater than 2.0/(rrfK+1) = 0.0328 - e.g. the very common minScore(0.5) or minScore(0.7).

**Then** Returns an empty result list for every query. The RRF score assembled two lines above is COALESCE(1.0/(60+v.rnk),0.0)+COALESCE(1.0/(60+k.rnk),0.0), whose maximum possible value is 1/61+1/61 = 0.0328 for a document ranked first in both CTEs, so the >= comparison against minScore filters out every row at any minScore above 0.0328. The same request against the VECTOR path (embeddingOnlySearch, line 448) compares minScore against a 0..1 normalised cosine score, so switching a store to HYBRID silently turns non-empty results into no results.

**verdict:** ?

---

### 061

`langchain4j/src/main/java/dev/langchain4j/store/embedding/inmemory/InMemoryEmbeddingStore.java:101`

```java
        entries.removeIf(entry -> entry.id.equals(id));
```

**Given** store.remove(null) or store.remove("") on an InMemoryEmbeddingStore, i.e. the same call that the two sibling overrides added in this change guard with ensureNotEmpty(ids, "ids") and ensureNotNull(filter, "filter")

**Then** Silently returns having removed nothing instead of rejecting the argument: entry.id is non-null (Entry's constructor calls ensureNotBlank), so entry.id.equals(null) is false for every entry and the predicate never matches. Code holding an EmbeddingStore reference and relying on the id validation the interface's default remove(String) performs before delegating gets no IllegalArgumentException here, so a bad id read from config or user input is swallowed and the caller believes the deletion succeeded.

**verdict:** ?

---

### 062

`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`

```java
.subscribe(sink::next)
```

**Given** A downstream cancellation of the returned Flux, e.g. model.stream(prompt).take(1).subscribe(...), or a subscriber that disposes after the first event, on a long audio file.

**Then** The sink registers no onCancel/onDispose handler, so the AsyncStreamResponse returned by createStreaming is never closed on cancellation. Subsequent sink::next calls are discarded while the underlying HTTP response body keeps being consumed to completion; the connection and its buffers stay held for the whole remaining server-side transcription instead of being released at cancel time.

**verdict:** ?

---

### 063

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:61`

```java
            requestConfigBuilder.setConnectionRequestTimeout(
                    Timeout.ofMilliseconds(builder.connectTimeout().toMillis()));
```

**Given** builder.connectTimeout(Duration.ofSeconds(1)) and a host that drops SYN packets (unroutable IP / dropped-packet firewall).

**Then** connectionRequestTimeout bounds leasing a connection from the pool, not TCP connect establishment (in HttpClient 5 connect timeout lives on ConnectionConfig, not RequestConfig). The call blocks on connect far past 1 s (Apache's default connect timeout, 3 minutes), while under pool contention an unrelated pool wait now aborts after 1 s with ConnectionRequestTimeoutException. The configured connectTimeout never bounds what it names.

**verdict:** ?

---

### 064

`langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java:70`

```java
                responseContext.chatResponse().tokenUsage().inputTokenCount());
```

**Given** A ChatModelResponseContext whose chatResponse().tokenUsage() is a non-null TokenUsage with a null inputTokenCount (or null outputTokenCount) - e.g. new TokenUsage(null, 120), which providers produce when the API reports only part of the usage block, or a streaming response that carries output tokens only.

**Then** The guard on line 65 only rejects a null TokenUsage, so execution reaches line 70; addTokenMetric declares int tokenCount, so the null Integer is auto-unboxed and onResponse throws NullPointerException. Neither the input nor the output token metric is recorded for that response - the OUTPUT call on line 74 is never reached - and the exception propagates out of the listener callback.

**verdict:** ?

---

### 065

`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`

```java
        messageResponse.complete(extractTextFromParts(
                task.artifacts().stream().flatMap(a -> a.parts().stream()).toList()));
```

**Given** A remote A2A agent that ends the task in a failure terminal state with no artifacts, i.e. a TaskEvent/TaskUpdateEvent whose task.status().state() is TASK_STATE_FAILED, TASK_STATE_CANCELED or TASK_STATE_REJECTED and whose task.artifacts() is empty.

**Then** isTerminalState() returns true for those three states, so the guard on line 178 does not return and the future is completed *successfully* with the empty string. invokeAgent() then returns serviceOutputParser.parseText(returnType, "") instead of propagating an error: a remote task that failed, was cancelled or was rejected is reported to the caller as a successful invocation with an empty answer.

**verdict:** ?

---

### 066

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`

```java
state.replaceAll(this::readStateBlocking);
```

**Given** A scope with a state entry holding an AsyncResponse for an async agent that failed (its blockingGet() rethrows the underlying failure), and whose value no downstream agent ever read, so the root call itself completed normally. Then rootCallEnded(registry) is called on an EPHEMERAL or PERSISTENT scope.

**Then** blockingGet() throws inside the replaceAll mapping function, so rootCallEnded exits at line 143 before the kind dispatch: an EPHEMERAL scope is never evicted from the AgenticScopeRegistry (it stays in the registry map for the process lifetime) and a PERSISTENT scope is never flushed, so its final state is never written. The exception also surfaces from a root call that previously succeeded.

**verdict:** ?

---

### 067

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:296`

```java
            return sqlQuery.substring(sqlQuery.indexOf("```sql") + 6, sqlQuery.lastIndexOf("```"));
```

**Given** The LLM returns an opening fence with no closing fence, e.g. the truncated output "```sql\nSELECT * FROM customers" (or, for the second branch at line 298, "SELECT 1 ```" with a single trailing fence).

**Then** indexOf("```sql") is 0 so beginIndex is 6, while lastIndexOf("```") is also 0, so substring(6, 0) throws StringIndexOutOfBoundsException. clean() is called at line 249, outside the try block at line 255, so the exception is not caught by the retry loop and propagates out of retrieve() to the caller.

**verdict:** ?

---

### 068

`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:51`

```java
        this.additionalParams = getOrDefault(builder.additionalParams, () -> new HashMap<>());
```

**Given** Map<String, Object> m = new HashMap<>(); WebSearchRequest r = WebSearchRequest.builder().searchTerms("cats").additionalParams(m).build(); Set<WebSearchRequest> s = new HashSet<>(); s.add(r); m.put("key", "value"); - equivalently r.additionalParams().put("key", "value"), since the getter at line 123 hands back the same instance

**Then** the caller's map is stored by reference with no defensive copy, so the all-final "immutable" request mutates after construction: hashCode() (line 154 folds in additionalParams) changes while the object sits in the set, and s.contains(r) then returns false

**verdict:** ?

---

### 069

`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`

```java
        if (node.has("$ref")) {
            return JsonReferenceSchema.builder()
```

**Given** A ListToolsResult containing one tool whose inputSchema is a root-level reference, e.g. {"$ref": "#/$defs/Node", "$defs": {"Node": {"type": "object", "properties": {"child": {"$ref": "#/$defs/Node"}}}}} - the shape pydantic v2 model_json_schema() emits for a self-referencing model.

**Then** The new $ref branch is tested before the type/no-type branch, so jsonNodeToJsonSchemaElement returns a JsonReferenceSchema for the root node, and line 44 `builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema")))` throws ClassCastException: JsonReferenceSchema cannot be cast to JsonObjectSchema. The exception escapes the loop, so toolSpecificationListFromMcpResponse yields no tools at all - every other tool of that server is lost too. Before this change the same schema fell into the typeNode == null branch and produced a (degraded but valid) JsonObjectSchema. The root $defs are also dropped, since the $ref return happens before the $defs collection at line 103.

**verdict:** ?

---

### 070

`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`

```java
TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);
```

**Given** Subscribing to the Flux returned by `stream(prompt)` more than once, e.g. `model.stream(prompt).retry(1)` after a transient network error, or two subscribers on the same Flux.

**Then** `params` is built once at assembly time and holds a single `new ByteArrayInputStream(audioBytes)` (buildParams, line 178). The first subscription drains that stream; every later subscription re-sends the same exhausted stream, so the multipart file part is zero bytes and the request fails or returns an empty transcription instead of re-uploading the audio.

**verdict:** ?

---

### 071

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:77`

```java
return computeFilter("!=", filter.comparisonValue()) + metadataKeyLast(filter.key()) + addMetadataNullCheck();
```

**Given** IsNotEqualTo("city", "Munich") against a document with non-empty metadata that does not contain the key at all, e.g. {country="France"}.

**Then** The clause is `m0.value != 'Munich' and m0.name='city' OR (i.metadata is null)`. Both disjuncts are false: the join alias m0 never binds an entry named 'city', and i.metadata is not null. The document is filtered out, while a document with no metadata at all is kept by the null check — so 'key absent' matches only when the whole metadata collection is null, and the two absence cases give opposite results. The same hole exists in mapNotIn (line 136).

**verdict:** ?

---

### 072

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`

```java
state.replaceAll(this::readStateBlocking);
```

**Given** A scope whose state map holds an AsyncResponse under some key (e.g. "result") whose blockingGet() resolves to null - an async agent that produced no output. Then rootCallEnded(registry) is called.

**Then** readStateBlocking returns null (it even calls writeState(key, null), which removes the entry), and ConcurrentHashMap.replaceAll throws NullPointerException on a null remapping result. rootCallEnded aborts at line 143, so registry.evict(memoryId) is never reached for EPHEMERAL scopes and flush(registry) is never reached for PERSISTENT ones, and the NPE propagates to the caller of the root agent invocation. Before this change the same value was reachable via readState(key), which returned null without throwing.

**verdict:** ?

---

### 073

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:77`

```java
return computeFilter("!=", filter.comparisonValue()) + metadataKeyLast(filter.key()) + addMetadataNullCheck();
```

**Given** A stored document whose metadata is non-empty but contains no entry named "k" (e.g. metadata {"other":"y"}), queried with IsNotEqualTo("k", "x").

**Then** The generated clause is `m0.value != 'x' and m0.name='k' OR (i.metadata is null)`. No joined row satisfies `m0.name='k'`, and `i.metadata is null` is false because the metadata collection is non-empty, so the document is filtered out even though the key it must differ from is absent. The `addMetadataNullCheck()` disjunct only rescues the exactly-zero-metadata case, and even that case is already eliminated earlier by the inner join `join i.metadata m0` emitted by FilterResult, so it can never be true either.

**verdict:** ?

---

### 074

`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:184`

```java
var results = query.getResultList();
```

**Given** Any LLM-generated HQL without a restriction over a large mapped entity, e.g. "from Order" against a table with millions of rows. Nothing in the class sets a max result count, and the default prompt at lines 61-66 does not ask for one.

**Then** The whole result set is materialised into a List, then serialised into a single JSON String by ResultsJsonSerializerImpl and embedded in the Content at line 198, which is fed back to the model. Memory grows with the row count (OutOfMemoryError on large tables) and, when it does fit, the prompt/token cost is unbounded.

**verdict:** ?

---

### 075

`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:530`

```java
if (trace.guardrail().hasInputAssessment()) {
```

**Given** A ConverseResponse whose trace is present but carries no guardrail member - e.g. a response routed through a Bedrock prompt router (ConverseTrace with promptRouter set and guardrail null), or any trace returned when no guardrail was attached to the request.

**Then** guardrailAssessmentSummaryFrom passes the trace != null guard and immediately dereferences trace.guardrail(), throwing NullPointerException instead of returning a summary; the same unguarded dereference repeats at line 621 (trace.guardrail().hasOutputAssessments()).

**verdict:** ?

---

### 076

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`

```java
Object result = response.get("result");
```

**Given** A 2xx response from code/execute whose JSON body has no "properties" key, or whose "properties" is not a JSON object (e.g. body `{}` or `{"properties":null}`).

**Then** getNestedMapProperty returns null at line 519, executeCode returns that null, and use()/execute() dereference it at line 213 with a raw NullPointerException instead of the wrapped "Failed to execute code." error the surrounding code returns for every other failure.

**verdict:** ?

---

### 077

`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:133`

```java
.minScore(embeddingSearchRequest.minScore())
```

**Given** Any EmbeddingSearchRequest built with minScore greater than about 0.033, e.g. EmbeddingSearchRequest.builder().queryEmbedding(e).maxResults(10).minScore(0.5).build() routed through hybridSearch.

**Then** The search returns zero hits regardless of how well documents match. minScore is a normalized similarity in [0,1], but the request ranks with an rrf retriever, whose score is the sum of 1/(rank_constant + rank) over the two legs and therefore never exceeds 2/61 = 0.0328 with the default rank_constant of 60. Passing that similarity threshold straight to Elasticsearch's min_score filters out every document as soon as minScore exceeds 0.0328; only the default minScore of 0.0 behaves sanely.

**verdict:** ?

---

### 078

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:71`

```java
                ContentType.MULTIPART_FORM_DATA.withParameters(new BasicNameValuePair("boundary", BOUNDARY));
```

**Given** any request built here where a field value or filename contains a non-ASCII character, e.g. formDataFields = {"name": "résumé"}

**Then** ContentType.MULTIPART_FORM_DATA carries ISO-8859-1 and withParameters re-emits the inherited charset, so the header sent is "multipart/form-data; charset=ISO-8859-1; boundary=----LangChain4j" while every part was encoded with getBytes(UTF_8); a receiver that honours the declared charset decodes "résumé" as "rÃ©sumÃ©"

**verdict:** ?

---

### 079

`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:103`

```java
var jsonMapper = new JacksonMcpJsonMapper(JsonParser.getObjectMapper());
```

**Given** StructuredOutputValidationAdvisor.builder().outputType(SomeType.class).objectMapper(customMapper).build(), where customMapper differs from JsonParser.getObjectMapper() (e.g. different deserialization features or a custom module).

**Then** The objectMapper argument is silently ignored when parsing the generated schema text into this.jsonSchema — the global JsonParser.getObjectMapper() is used instead — so the caller-supplied mapper only affects the validator, not schema parsing, contrary to the builder's documented 'ObjectMapper to be used for JSON processing'.

**verdict:** ?

---

### 080

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:147`

```java
            ResultSet columns = metaData.getColumns(null, null, tableName, null);
```

**Given** Constructing the retriever without a databaseStructure argument against a schema with many tables (generateDDL on line 129 iterates every TABLE and calls generateCreateTableStatement for each).

**Then** Four ResultSets per table (columns, pk on 148, fks on 149, tableRemarks on 218) are opened and never closed; they are only released when the connection is closed at the end of generateDDL. On drivers with a per-connection cursor cap (e.g. Oracle open_cursors, default 300) a schema of roughly 75+ tables exhausts the limit and construction fails with a SQLException wrapped in RuntimeException on line 231.

**verdict:** ?

---

### 081

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:91`

```java
    private static final Pattern SANITIZE_PATTERN_START = Pattern.compile("^(\\s|`)*(?i:python)?\\s*");
```

**Given** Default construction (sanitizeInput = true) and use("pythonic = 5") / execute("python_path = '/tmp'") — any code whose first token merely starts with the letters "python" rather than being a fenced-block language tag.

**Then** sanitizeInput strips the leading "python" because (?i:python)? is optional and unanchored to any delimiter, so the code sent to the interpreter becomes "ic = 5" / "_path = '/tmp'" — a different program that either fails to parse or silently binds the wrong name.

**verdict:** ?

---

### 082

`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`

```java
for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {
```

**Given** filedsMap = {"text": stringValue("hello world"), "index": numberValue(3)} with metadataTextKey = "text" (size >= 2 and containing the text key)

**Then** returns {"text": "hello world", "index": 3.0} — the segment text is copied into the returned metadata map, while the size == 1 case on line 21 returns {} for the very same key; the loop never skips metadataTextKey, so the text field leaks into the metadata of every retrieved segment that has at least one other field

**verdict:** ?

---

### 083

`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`

```java
documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))
```

**Given** load(url, documentParser) on a page whose HTML contains non-ASCII characters (e.g. a body containing "café" or CJK text) declaring <meta charset="utf-8">, running on a JVM whose default charset is not UTF-8 (Java 17 on Windows defaults to windows-1252).

**Then** String.getBytes() encodes the page text with the platform default charset while the parser decodes the byte stream as UTF-8 (declared or assumed), so the parsed Document text contains mojibake or U+FFFD replacement characters instead of the original characters; unmappable characters are silently replaced with '?' before the parser ever sees them.

**verdict:** ?

---

### 084

`document-loaders/langchain4j-document-loader-github/src/main/java/dev/langchain4j/data/document/loader/github/GitHubDocumentLoader.java:119`

```java
throw new RuntimeException("Failed to load document from GitHub: {}", ioException);
```

**Given** Any GHContent whose read fails, e.g. loadDocument("owner", "repo", "main", "README.md", parser) where the subsequent content fetch inside DocumentLoader.load throws an IOException.

**Then** RuntimeException(String, Throwable) performs no SLF4J-style substitution, so the propagated exception message is the literal text "Failed to load document from GitHub: {}" with no URL or file identity; the caller sees a message that names no document.

**verdict:** ?

---

### 085

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:173`

```java
        return "(NOT (" + map(filter.expression()).query + "))";
```

**Given** A document whose metadata has more than one entry, e.g. {"k": "v", "other": "y"}, queried with Not.not(new IsEqualTo("k", "v")).

**Then** The negation is applied to a per-join-row predicate, not to the document: the generated clause is (NOT (m1.name='k' and m1.value = 'v')). The join row m1 = (other, y) satisfies the negation, so the document is returned even though it matches the inner filter and must be excluded. Every Not over a document with at least one non-matching metadata entry returns that document.

**verdict:** ?

---

### 086

`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:123`

```java
private int maxResults;
```

**Given** ElasticsearchContentRetriever.builder().restClient(client).embeddingModel(model).build() — i.e. any caller who does not call maxResults(...) — then retrieve(Query.from("hello")) with the default knn configuration.

**Then** The primitive field defaults to 0 (the builder gives it no default, unlike indexName and configuration), so line 87 calls .maxResults(0) on EmbeddingSearchRequest.builder(); the request rejects a non-positive maxResults and retrieve() throws IllegalArgumentException instead of returning results. Every retrieval on a builder-constructed retriever that omitted maxResults fails.

**verdict:** ?

---

### 087

`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`

```java
        for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {
```

**Given** filedsMap containing two or more entries, one of which is the metadataTextKey entry, e.g. {"text": stringValue("hello world"), "author": stringValue("bob")} with metadataTextKey = "text"

**Then** The loop never skips metadataTextKey, so the returned map is {"text": "hello world", "author": "bob"} — the segment text is duplicated into the metadata as a field. The one-entry early return at line 21 and the capacity hint filedsMap.size() - 1 at line 25 show the text key is meant to be excluded, and it is excluded only when it is the sole field.

**verdict:** ?

---

### 088

`langchain4j-guardrails/src/main/java/dev/langchain4j/guardrails/PatternBasedPromptInjectionGuardrail.java:130`

```java
                LOGGER.warn("Prompt injection detected. pattern='{}' input='{}'", pattern.pattern(), text);
```

**Given** Any user message that matches a pattern, of arbitrary size - e.g. a multi-megabyte message containing the word "jailbreak", repeated on each request.

**Then** The full raw user text is written to the log at WARN with no length bound and no sanitisation, so an attacker controls log volume (megabytes per request) and, because the text is interpolated as-is, embedded newlines forge additional log lines. Rejected user content - which may include credentials or personal data pasted by the user - is persisted in the application log.

**verdict:** ?

---

### 089

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:143`

```java
String filterQuery = m + "value " + operator + " '" + value + "'";
```

**Given** IsEqualTo("author", "O'Brien") — any non-numeric comparison value (or metadata key, via metadataKey/metadataKeyLast) containing a single quote.

**Then** Produces `m0.name='author' and m0.value = 'O'Brien'`, which is not a parseable Ickle string literal; the query fails at parse time instead of returning the matching documents. Nothing escapes or parameterises the interpolated value, so every filter over a value with an apostrophe is unusable (and the same interpolation lets caller-supplied text alter the query text).

**verdict:** ?

---

### 090

`langchain4j-gpu-llama3/src/main/java/dev/langchain4j/model/gpullama3/GPULlama3BaseModel.java:152`

```java
        if (stopToken == null) {
            return "Ran out of context length...\n Increase context length with by passing to llama-tornado --max-tokens XXX";
```

**Given** Any request whose generation ends without emitting a stop token, e.g. init(..., maxTokens = 64, ...) followed by modelResponse(request asking for a long answer): generateTokens/generateTokensGPU returns 64 content tokens, none of which is in chatFormat.getStopTokens(), so stopToken stays null at line 136. The same path is taken when responseTokens comes back empty.

**Then** responseText, decoded at line 142 from the 64 generated tokens, is computed and then thrown away; the method returns the literal string "Ran out of context length...\n Increase context length with by passing to llama-tornado --max-tokens XXX" as the model's answer. The caller gets a hardcoded English sentence instead of the truncated completion, and in the streaming model the tokenConsumer has already emitted the real tokens, so the final returned text contradicts what was streamed.

**verdict:** ?

---

### 091

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:111`

```java
        return comparisonValues.stream().map(Object::toString).sorted().collect(Collectors.joining(", "));
```

**Given** An IsIn (or IsNotIn) whose comparison values contain a space or a comma, e.g. new IsIn("author", List.of("John Smith", "Ada Lovelace")).

**Then** The values are joined into one quoted string and emitted as search.in(k/value, ('Ada Lovelace, John Smith')). With search.in's default delimiter set (comma and space) that string is split into the four tokens Ada, Lovelace, John, Smith, so documents whose value is exactly "John Smith" are not matched while documents whose value is "John" or "Smith" are. The filter silently returns the wrong document set rather than failing.

**verdict:** ?

---

### 092

`auto-configurations/vector-stores/spring-ai-autoconfigure-vector-store-mongodb-atlas/src/main/java/org/springframework/ai/vectorstore/mongodb/autoconfigure/MongoDBAtlasVectorStoreAutoConfiguration.java:81`

```java
mongoClientProvider.ifAvailable(mongoClient -> mongoClient
```

**Given** An application context that has this auto-configuration active (MongoDBAtlasVectorStore, EmbeddingModel and MongoTemplate on the classpath, spring.ai.vectorstore.type unset or mongodb-atlas) and defines two or more com.mongodb.client.MongoClient beans with none marked @Primary — e.g. a multi-database or multi-tenant setup with `mongoClientA` and `mongoClientB`.

**Then** ObjectProvider.ifAvailable delegates to getIfAvailable(), which throws NoUniqueBeanDefinitionException when several candidates match and none is primary (only getIfUnique() returns null in that case). The exception is raised from the SmartInitializingSingleton callback during afterSingletonsInstantiated, so refresh fails and the whole application fails to start — a failure that did not exist before this bean was added, and one caused by an optional metadata-tagging concern.

**verdict:** ?

---

### 093

`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:37`

```java
        } catch (Exception e) {
            throw new RuntimeException(e);
```

**Given** A valid modelPath (so line 28 succeeds and the ONNX model is loaded into a native OrtSession) together with a pathToTokenizer that does not exist or holds an unreadable tokenizer.json, so HuggingFaceTokenizer.newInstance on line 36 throws.

**Then** The catch on line 37 rethrows as RuntimeException without calling session.close(); the partially built object is discarded, so the native OrtSession and the model weights it loaded (typically hundreds of MB off-heap) stay allocated until JVM exit. Repeating the failing construction, e.g. in a retry or per-request factory, grows native memory each time since OrtSession is only released by an explicit close().

**verdict:** ?

---

### 094

`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:311`

```java
textAnswer = cBlock.text();
```

**Given** A ConverseResponse whose output().message().content() holds two or more blocks of type TEXT, e.g. [TEXT("Let me check that."), TOOL_USE(...), TEXT(" Done.")] or [TEXT(part1), TEXT(part2)].

**Then** Each TEXT block assigns over the previous one instead of appending, so the returned AiMessage carries only the last text block; all earlier text is silently dropped from the response (with exactly one TEXT block the behaviour is correct, which hides the bug).

**verdict:** ?

---

### 095

`models/spring-ai-transformers/src/main/java/org/springframework/ai/transformers/TransformersEmbeddingModel.java:271`

```java
this.session.close();
```

**Given** close() invoked twice on the same fully initialized instance - e.g. the Javadoc advertises both try-with-resources and Spring's inferred destroy method, so an application that closes the model explicitly and then lets the ApplicationContext shut down calls it a second time.

**Then** The null guards only cover the never-initialized case; the fields are still non-null after the first close, so the second call re-enters OrtSession.close() on an already-closed session, which throws IllegalStateException("Trying to close an already closed OrtSession") - surfacing as a bean destruction failure during context shutdown. AutoCloseable's contract asks close() to be idempotent.

**verdict:** ?

---

### 096

`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:9`

```java
boolean hasConverged(Collection<Object> positions);
```

**Given** A caller holding the positions of a debate in a typed collection, e.g. `List<String> positions = List.of("YES", "YES"); strategy.hasConverged(positions);`

**Then** Does not compile: Java generics are invariant, so `List<String>` is not a `Collection<Object>`. Every caller must copy its positions into a `new ArrayList<Object>(...)` first; `Collection<?>` would accept them directly.

**verdict:** ?

---

### 097

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:68`

```java
if (filter instanceof IsGreaterThan) return "k/value gt '%s'";
```

**Given** new IsGreaterThan("year", 999) against a document whose metadata value is 1000 (same for IsGreaterThanOrEqualTo, IsLessThan, IsLessThanOrEqualTo with any numeric comparison value).

**Then** The numeric comparison value is emitted inside single quotes, so the ordering comparison is done on strings: '1000' gt '999' is false lexicographically, and the document with year 1000 is excluded from the results.

**verdict:** ?

---

### 098

`document-parsers/langchain4j-document-parser-markdown/src/main/java/dev/langchain4j/data/document/parser/markdown/MarkdownDocumentParser.java:25`

```java
final Node node = parser.parseReader(new InputStreamReader(inputStream));
```

**Given** An InputStream over a UTF-8 encoded Markdown file containing any non-ASCII byte, e.g. the two bytes 0xC3 0xA9 that encode e-acute in the word "cafe", parsed on a JVM whose Charset.defaultCharset() is not UTF-8 (Java 17 on a Windows western locale resolves to windows-1252; on Java 18+ the same happens with -Dfile.encoding=COMPAT).

**Then** The one-argument InputStreamReader decodes with the platform default charset, so 0xC3 0xA9 is decoded as two separate characters and the rendered text at line 29 becomes a mojibake string instead of "cafe"; Document.from(text) at line 35 stores the corrupted text, and every downstream consumer (splitting, embedding, retrieval) sees it. The same file parsed on a UTF-8-default JVM yields different text, so the parser is not deterministic across hosts.

**verdict:** ?

---

### 099

`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:80`

```java
SuccessfulHttpResponse successResponse = fromOkHttpResponse(response);
```

**Given** A streaming call via execute(request, parser, listener) where the server answers 200 with a Content-Type that does not contain "text/event-stream" (e.g. "application/json", "application/x-ndjson", or no Content-Type header at all) and then sends the event body in chunks.

**Then** fromOkHttpResponse takes the else branch at line 120 and calls readBody -> response.body().string(), which blocks until the server closes the stream and consumes/closes the body. onOpen therefore fires only after the stream ends, and getInputStream(response) at line 83 then hands parser.parse an already-consumed body, so the listener receives zero events and only onClose (or an onError from reading a closed source). The streamed payload is silently dropped.

**verdict:** ?

---

### 100

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:74`

```java
this.indexName = getOrDefault(indexName, DEFAULT_INDEX_NAME);
```

**Given** initialize(endpoint, keyCredential, null, false, 1536, new SearchIndex("products"), null) - i.e. a caller supplies a ready-made SearchIndex but leaves createOrUpdateIndex false (indexName must be null/blank here, otherwise line 69 throws).

**Then** The `createOrUpdateIndex && index != null` guard on line 71 is false, so this.indexName becomes "vectorsearch" instead of index.getName() = "products". The SearchClient built at line 88/101 is bound to "vectorsearch", so every subsequent add/addAll/findRelevant reads and writes the wrong index - and if "vectorsearch" does not exist, Azure returns an index-not-found error even though the caller named an existing index.

**verdict:** ?

---

### 101

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:101`

```java
asyncClient.execute(apacheRequest, new FutureCallback<>() {
```

**Given** Any Server-Sent Events request, e.g. a chat endpoint with Accept: text/event-stream that emits one event per second for 30 seconds. This overload of CloseableHttpAsyncClient.execute uses SimpleRequestProducer/SimpleResponseConsumer, which buffer the whole message and fire completed() only at end of message; getInputStream() then wraps the already complete byte[] in a ByteArrayInputStream.

**Then** listener.onOpen and every parsed event fire only after the server closes the stream ~30 s later, all at once, instead of incrementally; against an endpoint that keeps the connection open the listener receives nothing at all, and the full response is held in memory rather than consumed as it arrives.

**verdict:** ?

---

### 102

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:136`

```java
byte[] bodyBytes = apacheResponse.getBody().getBodyBytes();
```

**Given** A streaming call (execute(request, parser, listener)) whose server answers with a successful response carrying no entity at all - e.g. 204 No Content, or a 200 to which the async consumer passes a null entity. SimpleResponseConsumer only calls setBody when the decoded entity is non-null, so SimpleHttpResponse.getBody() returns null.

**Then** getBody() is null and .getBodyBytes() throws NullPointerException. The throw happens in the resource initializer of the enclosing try-with-resources, so it is caught at line 116 and reported as listener.onError(NullPointerException) right after onOpen; the listener never receives onClose. The Objects.requireNonNullElseGet guard on the next line only covers null bytes, never the null body one level up, so the zero-body edge is unprotected.

**verdict:** ?

---

### 103

`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`

```java
String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();
```

**Given** Two positions whose verdict sits on its own line, e.g. "Costs are lower.\nYES" and "Latency is better.\nYES" (agent output where the final verdict follows a newline rather than a space).

**Then** `lastIndexOf(' ')` only searches for a space, so `lastWord` becomes the whole remainder after the last space — "LOWER.\nYES" vs "BETTER.\nYES" — which compare unequal, so `hasConverged` returns false even though both positions end with the same verdict, and the debate never terminates on convergence.

**verdict:** ?

---

### 104

`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`

```java
Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));
```

**Given** Any page whose HTML contains non-ASCII text (e.g. a page containing "café" or CJK characters) loaded on a JVM whose default charset is not UTF-8 — the JDK 17 default on Windows (windows-1252) or on a POSIX box with LANG=C (US-ASCII).

**Then** String.getBytes() encodes with the platform default charset while every langchain4j DocumentParser (TextDocumentParser, ApacheTikaDocumentParser) decodes the stream as UTF-8, so multi-byte characters are re-decoded as mojibake, and characters unrepresentable in the default charset are irreversibly replaced by '?' before the parser ever sees them. The returned Document text differs from page.content(); the single-argument load(url) path, which never round-trips through bytes, keeps the same text intact.

**verdict:** ?

---

### 105

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:38`

```java
+ name + "\"; filename=\"" + file.fileName() + "\"" + CRLF + "Content-Type: "
```

**Given** addFile called with a FormDataFile whose fileName() contains a double quote or a CRLF, e.g. fileName = "my\"file.mp3" or fileName = "a.mp3\r\nX-Injected: 1". Same for a field/file map key containing those characters at line 29/37. Nothing escapes or validates the interpolated values.

**Then** The emitted header becomes Content-Disposition: form-data; name="audio"; filename="my"file.mp3" — the server reads the filename as "my" and drops the rest — or, with a CRLF in the name, the injected text is parsed as an additional part header, so the request carries headers the caller never set.

**verdict:** ?

---

### 106

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:164`

```java
return "Cannot read error response body: " + e.getMessage();
```

**Given** A 2xx response whose body read fails part-way: a chunked response truncated by the peer (MalformedChunkCodingException / "Premature end of chunk coded message") or a connection reset during the body read. readBody() is on the success path too (line 149), and BufferedReader.lines() rethrows the IOException as UncheckedIOException, which this catch(Exception) swallows.

**Then** execute(request) returns a SuccessfulHttpResponse with statusCode 200 and body equal to the literal string "Cannot read error response body: Premature end of chunk coded message"; the truncated payload is discarded and no exception is raised, so the caller parses the diagnostic text as if it were the server's answer instead of retrying a failed transfer.

**verdict:** ?

---

### 107

`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:136`

```java
errorMessage = e.getMessage();
```

**Given** maxRetries >= 1 and a failure whose Throwable.getMessage() returns null, e.g. a NullPointerException raised inside ResultsJsonSerializerImpl.toString or any exception constructed with the no-arg constructor.

**Then** errorMessage stays null, so the guard at line 154 (previousHqlQuery != null && previousErrorMessage != null) is false and neither the previous HQL nor the error is appended. The retry re-sends the exact same prompt with no feedback, so it deterministically reproduces the same query and the same failure while still paying for the extra model call; line 138 also logs "HQL execution failed, retrying ... : null".

**verdict:** ?

---

### 108

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:74`

```java
        this.asyncClient.start();
```

**Given** Constructing ApacheHttpClient more than once and discarding the instances, e.g. building a new model/client per request or per test method.

**Then** start() spawns the I/O reactor dispatch threads and both clients own connection pools, but the class exposes no close/shutdown and never calls asyncClient.close() or syncClient.close(). Every discarded instance leaves its reactor threads alive and its pooled sockets open; thread and file-descriptor counts grow monotonically for the life of the JVM, and garbage collection does not reclaim them.

**verdict:** ?

---

### 109

`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`

```java
metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());
```

**Given** metadataToStruct(TextSegment.from("hello world", Metadata.from("text_segment", "bob")), "text_segment")

**Then** The loop calls putFields with the same key that line 43 used for the text, so the struct field "text_segment" ends up holding "bob" and the segment text "hello world" is silently lost before the vector is stored; a later read back returns the metadata value as the segment text.

**verdict:** ?

---

### 110

`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:312`

```java
matchingIds.add(docId.replace(key(""), ""));
```

**Given** A store built with .prefix("doc") holding a document whose id is "doc-42" (stored under Redis key "docdoc-42"), then a doDelete(filterExpression) whose filter matches it.

**Then** key("") is the bare prefix and String.replace strips every occurrence, not just the leading one: "docdoc-42" becomes "-42", so key(id) rebuilds "doc-42" and pipeline.jsonDel targets a key that does not exist. jsonDel returns 0L, RESPONSE_DEL_OK fails, and the method throws IllegalStateException("Failed to delete documents by filter") while the document is still present. toDocument() strips the same prefix correctly with substring(this.prefix.length()).

**verdict:** ?

---

### 111

`document-parsers/langchain4j-document-parser-markdown/src/main/java/dev/langchain4j/data/document/parser/markdown/MarkdownDocumentParser.java:25`

```java
final Node node = parser.parseReader(new InputStreamReader(inputStream));
```

**Given** A UTF-8 encoded Markdown stream containing any non-ASCII byte sequence (e.g. "# Café — résumé" or CJK text) parsed on a JVM whose default charset is not UTF-8 (Java 17 on a Windows host defaults to windows-1252; any JVM started with -Dfile.encoding=ISO-8859-1 behaves the same).

**Then** InputStreamReader is constructed without a Charset, so it decodes with the platform default instead of UTF-8: the returned Document text contains mojibake ("CafÃ© â€” rÃ©sumÃ©") or U+FFFD replacement characters, and the corrupted text is what gets embedded and indexed. The same file parsed on two hosts yields two different Documents.

**verdict:** ?

---

### 112

`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:83`

```java
OnnxTensor inputIdsTensor = createTensor(environment, inputIds);
```

**Given** scoreAll(query, documents) called with an empty documents list (documents.size() == 0)

**Then** pairs is empty, so batchEncode returns a zero-length Encoding[] and inputIds is `new long[0][]`; createTensor cannot derive the second dimension of a zero-length 2D array and throws (IllegalArgumentException / OrtException) instead of the method returning an empty score list. The throw is not an OrtException in the IllegalArgumentException case, so it escapes the catch on line 64 unwrapped.

**verdict:** ?

---

### 113

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:19`

```java
    private static final String BOUNDARY = "----LangChain4j";
```

**Given** A file whose content() bytes contain the sequence "\r\n------LangChain4j" (the delimiter is "--" + BOUNDARY), for example uploading a previously captured multipart body produced by this same class, or any user-supplied file crafted to contain that string.

**Then** The boundary is a fixed constant and is never checked against part content, so the server's multipart parser terminates the part at the embedded occurrence: the uploaded file is silently truncated and the remaining bytes are parsed as further parts or rejected as a malformed body.

**verdict:** ?

---

### 114

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:115`

```java
return format("metadata/attributes/any(k: k/key eq '%s' and " + format + ")", key, value);
```

**Given** new IsEqualTo("author", "O'Brien") — any key or comparison value containing a single quote.

**Then** The quote is interpolated raw and terminates the OData string literal: the emitted filter is metadata/attributes/any(k: k/key eq 'author' and k/value eq 'O'Brien'), which Azure AI Search rejects with an HTTP 400 invalid-expression error instead of returning the matching documents.

**verdict:** ?

---

### 115

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:101`

```java
        asyncClient.execute(apacheRequest, new FutureCallback<>() {
```

**Given** Any call to execute(request, parser, listener) against an SSE endpoint, e.g. a chat completion with stream=true.

**Then** SimpleHttpRequest/SimpleHttpResponse are the fully-buffered message API (the whole body is accumulated in memory and completed() only fires once the response is finished), which line 136 then re-wraps in a ByteArrayInputStream. No event is delivered incrementally: listener.onOpen and every onEvent fire only after the server closes the stream, and a stream the server never closes never delivers anything while the entire body grows in heap.

**verdict:** ?

---

### 116

`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolExecutionHelper.java:69`

```java
case LONG, BIG_INTEGER -> content.asLong();
```

**Given** A tool response whose structuredContent holds an integer outside long range, e.g. {"structuredContent": {"id": 18446744073709551616}}. Jackson parses any integer literal above Long.MAX_VALUE (9223372036854775807) or below Long.MIN_VALUE into a BigIntegerNode, whose numberType() is BIG_INTEGER.

**Then** asLong() on a BigIntegerNode delegates to BigInteger.longValue(), which keeps only the low-order 64 bits. The map returned by toObject holds 0 for 18446744073709551616, and can hold a value of the opposite sign for other out-of-range inputs. No exception is raised, so the caller receives a silently corrupted number in ToolExecutionResult.result() while resultText still shows the correct digits.

**verdict:** ?

---

### 117

`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`

```java
.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())
```

**Given** Add a document with integral metadata, e.g. Document with metadata Map.of("page", 1), then run any similaritySearch that returns it. The stored JSON is {"page":1}, and line 369 additionally injects "distance" as a float via addProperty.

**Then** Gson deserializes every JSON number to Double when the target element type is Object, so the returned Document metadata holds Double 1.0 for "page" and a Double for "distance", instead of the Integer and Float that metadata.getInnerMap() produced before the change. Caller code that reads the value as its original type — (Integer) doc.getMetadata().get("page") or (Float) doc.getMetadata().get(DocumentMetadata.DISTANCE.value()) — throws ClassCastException, and equality checks against the originally added metadata (1 vs 1.0) now fail.

**verdict:** ?

---

### 118

`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:345`

```java
throw new IllegalArgumentException("Unknown stop reason: " + stopReason);
```

**Given** A ConverseResponse whose stopReason is any StopReason value outside {END_TURN, STOP_SEQUENCE, MAX_TOKENS, TOOL_USE} - notably GUARDRAIL_INTERVENED (Bedrock guardrail blocks the request/response) or CONTENT_FILTERED, and also the SDK's UNKNOWN_TO_SDK_VERSION when a newer service enum value arrives.

**Then** finishReasonFrom throws IllegalArgumentException("Unknown stop reason: guardrail_intervened") while converting an otherwise successful HTTP 200 response, so the whole chat call fails with an unrelated exception instead of returning a ChatResponse (langchain4j's FinishReason.CONTENT_FILTER is never produced).

**verdict:** ?

---

### 119

`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:198`

```java
logger.debug("Validating JSON output against schema. Attempts left: " + this.maxRepeatAttempts);
```

**Given** maxRepeatAttempts = 3 and a response that fails validation four times, with DEBUG logging enabled.

**Then** Every one of the four log lines reads "Attempts left: 3"; the field is the immutable configured maximum, not the remaining count (repeatCounter is not in scope here), so the log reports 3 attempts left on the final attempt where none remain.

**verdict:** ?

---

### 120

`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`

```java
SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);
```

**Given** A store holding 11 or more documents matching the filter expression, e.g. 11 documents with metadata country == 'BG', then doDelete(Filter.Expression for country == 'BG').

**Then** The two-argument ftSearch sends FT.SEARCH with no LIMIT clause, so RediSearch applies its default LIMIT 0 10 and returns at most 10 documents. Only 10 keys are added to matchingIds and deleted; the 11th and every further match silently survive the delete, the method returns normally, and the leftovers still appear in later similarity searches. No paging loop over searchResult.getTotalResults() exists.

**verdict:** ?

---

### 121

`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:26`

```java
String lastWord = text.substring(text.lastIndexOf(' ') + 1).trim().toUpperCase();
```

**Given** positions = ["I think we should ship it.\nAGREE", "AGREE"] — i.e. any position whose final verdict is separated from the preceding text by a newline or tab rather than a space (a very common LLM output shape: reasoning, newline, verdict on its own line).

**Then** Only the literal ' ' character is treated as a word separator, so for the first position lastIndexOf(' ') finds the space inside "ship it." and lastWord becomes "IT.\nAGREE" (whitespace embedded, so not a last word at all), while the second yields "AGREE". The strings differ and hasConverged returns false, reporting no convergence for two positions that both end in AGREE. Symmetrically, two positions ending in different verdicts can compare equal when the trailing newline-joined tails happen to match, returning true.

**verdict:** ?

---

### 122

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`

```java
state.replaceAll(this::readStateBlocking);
```

**Given** A scope whose state holds an AsyncResponse under some key (e.g. "result") whose blockingGet() resolves to null - an async agent that produced no output - and then rootCallEnded is called.

**Then** readStateBlocking returns null for that key, and Map.replaceAll forbids a null remapping result: ConcurrentHashMap.replaceAll throws NullPointerException out of rootCallEnded. The key has already been removed from state by the nested writeState(key, null), later entries are never resolved, and the EPHEMERAL eviction / PERSISTENT flush below never runs, so the scope stays in the registry and is never persisted while the exception propagates to the workflow caller.

**verdict:** ?

---

### 123

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:147`

```java
ResultSet columns = metaData.getColumns(null, null, tableName, null);
```

**Given** Constructing the retriever without an explicit databaseStructure against a schema with many tables: generateDDL holds one Connection open and calls generateCreateTableStatement per table, which opens four metadata ResultSets (columns, pk, fks, tableRemarks) and closes none.

**Then** 4 x (number of tables) cursors stay open on the single connection until generateDDL returns; on drivers with a per-session cursor cap (e.g. Oracle ORA-01000 max open cursors) DDL generation fails with a SQLException, rethrown as RuntimeException from the constructor.

**verdict:** ?

---

### 124

`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:170`

```java
return hqlQuery.substring(hqlQuery.indexOf("```hql") + 6, hqlQuery.lastIndexOf("```"));
```

**Given** A model reply that opens a fence but never closes it, e.g. text() returning "```hql\nselect e from Entity e" (truncated output, or a stop sequence cutting the closing fence). Same for the "```sql" branch at line 172 and the bare "```" branch at line 174.

**Then** indexOf("```hql")+6 == 6 while lastIndexOf("```") == 0, so substring(6, 0) throws StringIndexOutOfBoundsException. clean() is called at line 127, outside the try block at line 131, so the exception is never caught: it escapes retrieve() entirely, bypassing the retry loop, instead of the documented empty-list-on-failure behaviour.

**verdict:** ?

---

### 125

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`

```java
return mergedAgents;
```

**Given** Two or more AgentsRegistry providers on the classpath, so discover() returns a CompositeAgentsRegistry; a caller then does AgentsRegistry.get().allAgents().put("x", someAgent) or .clear()

**Then** The call succeeds instead of throwing UnsupportedOperationException as the allAgents() javadoc ("an unmodifiable map") promises: the internal HashMap of the cached singleton registry is mutated, so every later getAgent() across the JVM sees the injected or removed entry, and the constructor's duplicate-name invariant is silently broken. EmptyAgentsRegistry returns Map.of(), so the two implementations of the same method disagree on mutability.

**verdict:** ?

---

### 126

`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:26`

```java
for (Map.Entry<String, Value> entry : filedsMap.entrySet()) {
```

**Given** structToMetadata(filedsMap, "text_segment") with filedsMap = {"text_segment" -> Value(string "hello world"), "author" -> Value(string "bob")}

**Then** The loop never skips metadataTextKey, so the returned map is {"text_segment"="hello world", "author"="bob"} instead of {"author"="bob"}: the segment text is re-injected as a metadata entry. The code contradicts itself — the guard on line 21 and the capacity filedsMap.size() - 1 on line 25 both assume the text key is excluded, and it is excluded only when it is the sole field.

**verdict:** ?

---

### 127

`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:345`

```java
throw new IllegalArgumentException("Unknown stop reason: " + stopReason);
```

**Given** A ConverseResponse whose stopReason is StopReason.GUARDRAIL_INTERVENED or StopReason.CONTENT_FILTERED (returned by Bedrock when a guardrail or content filter cuts the generation short), or StopReason.UNKNOWN_TO_SDK_VERSION when the service adds a value the bundled SDK does not know.

**Then** finishReasonFrom falls through all three if-blocks and throws IllegalArgumentException("Unknown stop reason: guardrail_intervened"), so a successful HTTP 200 Converse response is turned into an exception and the answer text already parsed by aiMessageFrom is discarded, instead of mapping to FinishReason.CONTENT_FILTER / OTHER.

**verdict:** ?

---

### 128

`langchain4j-onnx-scoring/src/main/java/dev/langchain4j/model/scoring/onnx/OnnxScoringBertCrossEncoder.java:36`

```java
            this.tokenizer = HuggingFaceTokenizer.newInstance(Paths.get(pathToTokenizer), tokenizerOptions);
        } catch (Exception e) {
            throw new RuntimeException(e);
```

**Given** A valid modelPath together with a pathToTokenizer that does not exist or holds an unreadable tokenizer.json (same for any OrtException thrown by session.getInputNames() on line 29): the OrtSession is created on line 28, then line 29 or 36 throws.

**Then** The catch rethrows as RuntimeException while the already-created OrtSession is never closed; the constructed object is discarded, so nothing can ever call session.close() and the native model memory stays allocated for the JVM lifetime (OrtSession releases native memory only via close(), it has no finalizer). Repeated construction attempts, e.g. a retry loop around model loading, accumulate one leaked model per attempt.

**verdict:** ?

---

### 129

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:136`

```java
byte[] bodyBytes = apacheResponse.getBody().getBodyBytes();
```

**Given** A streaming call execute(request, parser, listener) against an endpoint that answers with a successful but entity-less response, e.g. HTTP 204 No Content, or 200 with Content-Length: 0. SimpleResponseConsumer only calls setBody(...) when an entity was received, so SimpleHttpResponse.getBody() returns null (which is why lines 105 and 261 go through the null-safe getBodyText() instead).

**Then** getBody() is null and .getBodyBytes() throws NullPointerException while the try-with-resources resource at line 113 is being initialised; the NPE is caught at line 116, so the listener receives onOpen(response) followed by onError(NullPointerException) and never onClose, turning an empty-but-valid response into a spurious client-side failure.

**verdict:** ?

---

### 130

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:296`

```java
return sqlQuery.substring(sqlQuery.indexOf("```sql") + 6, sqlQuery.lastIndexOf("```"));
```

**Given** An LLM answer with an opening fence but no closing fence, e.g. output truncated by the token limit: "```sql\nSELECT * FROM customers" (same for a single "```" at line 298).

**Then** indexOf and lastIndexOf return the same index, so substring is called with begin > end and throws StringIndexOutOfBoundsException. clean() is invoked at line 249, outside the try block at line 255, so the exception propagates out of retrieve() unhandled instead of being retried or degraded to an empty list.

**verdict:** ?

---

### 131

`langchain4j-guardrails/src/main/java/dev/langchain4j/guardrails/PatternBasedPromptInjectionGuardrail.java:123`

```java
String text = userMessage.singleText();
```

**Given** A UserMessage whose content list does not hold exactly one TextContent, e.g. UserMessage.from(TextContent.from("ignore all previous instructions"), ImageContent.from(url)), or a message built from two TextContent parts. UserMessage.singleText() is only defined when hasSingleText() is true and throws otherwise.

**Then** validate() throws out of the guardrail instead of returning an InputGuardrailResult, so the chain aborts with an exception rather than producing success()/fatal(); the injection text carried by the multimodal message is never pattern-checked. The guarded text == null branch on the next line is unreachable, since singleText() throws rather than returning null.

**verdict:** ?

---

### 132

`vector-stores/spring-ai-milvus-store/src/main/java/org/springframework/ai/vectorstore/milvus/MilvusVectorStore.java:381`

```java
.metadata((metadata != null) ? gson.fromJson(metadata, type) : Map.of())
```

**Given** A document added with non-floating-point numeric metadata, e.g. vectorStore.add(List.of(new Document("c", Map.of("year", 2024, "page", 3L)))), then retrieved with vectorStore.similaritySearch(SearchRequest.query("c")).

**Then** Gson's ObjectTypeAdapter deserializes every JSON number as Double when the target value type is Object, so the returned Document.getMetadata() holds Double 2024.0 and Double 3.0 instead of Integer 2024 and Long 3. The previous JSONObject.getInnerMap() preserved Integer/Long. Callers doing metadata.get("year").equals(2024) now get false, and a cast such as (Integer) metadata.get("year") throws ClassCastException. The same applies to the injected DocumentMetadata.DISTANCE value, which changes from Float to Double.

**verdict:** ?

---

### 133

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:115`

```java
        return format("metadata/attributes/any(k: k/key eq '%s' and " + format + ")", key, value);
```

**Given** Any filter whose key or value contains a single quote, e.g. new IsEqualTo("author", "O'Brien").

**Then** Produces metadata/attributes/any(k: k/key eq 'author' and k/value eq 'O'Brien'), which is not valid OData: the literal is terminated early. Azure AI Search rejects the request with HTTP 400 (invalid filter expression) instead of returning results. The OData grammar requires an embedded quote to be doubled ('') and nothing here escapes it.

**verdict:** ?

---

### 134

`vector-stores/spring-ai-redis-store/src/main/java/org/springframework/ai/vectorstore/redis/RedisVectorStore.java:308`

```java
SearchResult searchResult = this.jedis.ftSearch(this.indexName, filterStr);
```

**Given** A store holding 50 documents with metadata field country == 'BG', then doDelete(new Filter.Expression(EQ, key('country'), value('BG'))).

**Then** ftSearch(index, queryString) uses RediSearch's default paging (LIMIT 0 10), so searchResult.getDocuments() carries at most 10 hits; only 10 of the 50 matching documents are deleted, the method logs 'Deleted 10 documents matching filter expression' and returns normally, leaving 40 matching documents in the store while the caller is told the delete succeeded.

**verdict:** ?

---

### 135

`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:76`

```java
        ObjectListing objectListing = cosClient.listObjects(listObjectsRequest);
```

**Given** A bucket containing 1500 non-empty objects (no prefix), i.e. loadDocuments("my-bucket", parser) where the listing exceeds the COS page size of 1000 keys.

**Then** Only the first page is walked: objectListing.isTruncated()/getNextMarker() is never consulted and cosClient.listNextBatchOfObjects is never called, so the returned list holds documents for only the first 1000 objects and the remaining 500 are silently dropped with no error and no log line.

**verdict:** ?

---

### 136

`langchain4j-gpu-llama3/src/main/java/dev/langchain4j/model/gpullama3/GPULlama3BaseModel.java:197`

```java
chatFormat.encodeMessage(new ChatFormat.Message(ChatFormat.Role.ASSISTANT, aiMessage.text())));
```

**Given** A ChatRequest whose message history contains an AiMessage with no text, e.g. AiMessage.from(List<ToolExecutionRequest>), where text() is null (UserMessage and SystemMessage are validated non-blank, AiMessage is not).

**Then** null is passed as the content of ChatFormat.Message and reaches the tokenizer, which dereferences it: NullPointerException escapes modelResponse instead of the message being skipped or encoded as empty.

**verdict:** ?

---

### 137

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:137`

```java
                + inFilterQuery + " and " + m + "name!='" + filter.key() + "')"
```

**Given** A document with metadata {"k": "a", "other": "a"} queried with new IsNotIn("k", List.of("a")); and a document with metadata {"other": "y"} (key "k" absent) queried with the same filter.

**Then** The second disjunct is m0.value IN ('a') and m0.name!='k', which is true for the join row (other, a): the first document is returned although its "k" value is in the excluded list. The same disjunct requires the value to be IN the list, so the document that simply lacks key "k" matches neither disjunct and is dropped, although NOT IN should include it. Both directions of the NOT IN filter are wrong.

**verdict:** ?

---

### 138

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`

```java
private static volatile AgentsRegistry INSTANCE = discover();
```

**Given** A META-INF/services/dev.langchain4j.agentic.planner.AgentsRegistry entry naming a class that is missing, not instantiable, or whose no-arg constructor throws — ServiceLoader.Provider::get then raises ServiceConfigurationError inside discover(); alternatively two providers declaring the same agent name, which makes the CompositeAgentsRegistry constructor throw

**Then** The throw happens during LazyHolder's static initializer, so the first AgentsRegistry.get() fails with ExceptionInInitializerError and the class is permanently marked erroneous. Every subsequent get() throws NoClassDefFoundError, and refresh() cannot recover because it also touches LazyHolder and throws NoClassDefFoundError before discover() is ever re-run — the javadoc's documented recovery path ("Call refresh() to force re-discovery") is unreachable for the whole life of the JVM.

**verdict:** ?

---

### 139

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:71`

```java
        if (createOrUpdateIndex && index != null) {
            this.indexName = index.getName();
```

**Given** initialize(endpoint, keyCredential, null, false /* createOrUpdateIndex */, dimensions, new SearchIndex("my-custom-index"), null /* indexName */) — a caller-supplied SearchIndex together with createOrUpdateIndex = false, which the argument validation at lines 66-70 explicitly permits (it only rejects index together with a non-blank indexName).

**Then** The `index` argument is silently discarded: the else branch sets this.indexName to DEFAULT_INDEX_NAME ("vectorsearch") because indexName is null, so searchClient at lines 85-89 / 98-102 is bound to "vectorsearch" instead of "my-custom-index", and lines 105-111 never use `index` either. Subsequent addAll/findRelevant calls read and write the wrong Azure index (findRelevant returns an empty list, or results from an unrelated index) with no error or log line.

**verdict:** ?

---

### 140

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:137`

```java
+ inFilterQuery + " and " + m + "name!='" + filter.key() + "')"
```

**Given** IsNotIn("city", List.of("Munich")) against a document whose metadata is {city="Munich", region="Munich"}.

**Then** The generated clause is `(m0.value NOT IN ('Munich') and m0.name='city') OR (m0.value IN ('Munich') and m0.name!='city') OR (i.metadata is null)`. The metadata entry region=Munich satisfies the second disjunct (value IN the list, name != 'city'), so the document is returned even though its `city` value is exactly the excluded one. Any document carrying an excluded value under a different key is a false positive of the NOT IN filter.

**verdict:** ?

---

### 141

`langchain4j-pgvector/src/main/java/dev/langchain4j/store/embedding/pgvector/PgVectorEmbeddingStore.java:546`

```java
WHERE ranked.score >= ?
```

**Given** A store built with searchMode(HYBRID) and default rrfK, searched with EmbeddingSearchRequest.minScore(0.7) (or any value above ~0.033) and a query string that matches a stored segment exactly, e.g. query "pgvector hybrid" against a row whose text is "pgvector hybrid".

**Then** Returns an empty EmbeddingSearchResult. minScore is a cosine-similarity threshold in [0,1] (embeddingOnlySearch compares it against (2 - distance)/2), but here it is compared against the RRF score built at line 542, whose maximum is 1.0/(rrfK+1) + 1.0/(rrfK+1) = 2/61 = 0.0328 with the default rrfK=60. Every row is filtered out, so the best-matching document is silently dropped instead of returned.

**verdict:** ?

---

### 142

`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`

```java
.subscribe(sink::next)
```

**Given** Any downstream that cancels the returned Flux before the server finishes, e.g. `model.stream(prompt).take(1).subscribe()` or `.timeout(Duration.ofSeconds(1))`.

**Then** The streaming subscription returned by `createStreaming(params).subscribe(...)` is never closed: the sink registers no `onCancel`/`onDispose` handler, so on cancellation the underlying HTTP/SSE response stays open and keeps receiving events into a terminated sink until the server ends the stream, holding the connection for the full duration of the transcription.

**verdict:** ?

---

### 143

`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:80`

```java
SuccessfulHttpResponse successResponse = fromOkHttpResponse(response);
```

**Given** A streaming call (the SSE overload) whose successful response carries a Content-Type that does not contain "text/event-stream" - e.g. "application/json", "application/x-ndjson", or no Content-Type header at all.

**Then** fromOkHttpResponse takes the else branch and calls readBody, i.e. response.body().string(), which fully consumes and closes the one-shot body. The following getInputStream(response) then returns response.body().byteStream() on an already-exhausted, closed source, so parser.parse reads nothing: the listener gets onOpen followed immediately by onClose with zero events (or onError "closed"), and every streamed event is silently lost.

**verdict:** ?

---

### 144

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:68`

```java
        if (filter instanceof IsGreaterThan) return "k/value gt '%s'";
```

**Given** An ordering comparison over a numeric metadata value, e.g. new IsGreaterThan("views", 9) against a document whose metadata value is 10 (same for IsGreaterThanOrEqualTo, IsLessThan, IsLessThanOrEqualTo on lines 69-71).

**Then** comparisonValue().toString() is wrapped in single quotes, so the emitted OData is k/value gt '9' - a string literal. Against the string-typed k/value field of the default index that is a lexicographic comparison, and '10' gt '9' is false, so the document with 10 is excluded from the result set with no error reported. (If k/value were instead numerically typed, the quoted literal is a type mismatch and Azure returns HTTP 400.) Either way the numeric ordering the caller asked for is not what is evaluated.

**verdict:** ?

---

### 145

`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:101`

```java
.filter(f -> f.score() > minScore)
```

**Given** A retriever built with minScore = 0.8 (or the builder default 0.0) where the store returns a match whose score is exactly 0.8 (respectively exactly 0.0).

**Then** The match is dropped from the returned list even though minScore is an inclusive threshold in EmbeddingSearchRequest (the store already returned it because score >= minScore). The retriever silently returns fewer results than requested, and at the default minScore = 0.0 any zero-scored match is discarded. The comparison must be >= to match the threshold semantics used one line above when building the request.

**verdict:** ?

---

### 146

`spring-ai-model/src/main/java/org/springframework/ai/model/tool/DefaultToolCallingManager.java:243`

```java
.parentObservation(parent)
```

**Given** A non-reactive (imperative) tool call: ChatClient.call() on a plain thread with a real ObservationRegistry, an enclosing observation already active on that thread (the ChatClient/HTTP server observation), and no reactor context in play — so ToolCallReactiveContextHolder.getContext() is the empty context and line 229-230 yields parent == null.

**Then** parentObservation(null) is applied unconditionally, overwriting the parent Micrometer already derived from registry.getCurrentObservation() when the observation was created. The tool-call observation is started with a null parent, so its span is emitted as a new trace root instead of a child of the enclosing chat observation, breaking the trace hierarchy on the imperative path that previously nested correctly.

**verdict:** ?

---

### 147

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:111`

```java
return comparisonValues.stream().map(Object::toString).sorted().collect(Collectors.joining(", "));
```

**Given** map(new IsIn("city", asList("New York", "Paris"))) — an IsIn/IsNotIn whose values contain a space or a comma.

**Then** The values are flattened into one string literal, yielding search.in(k/value, ('New York, Paris')). search.in splits that literal on its default delimiters (space and comma), so the predicate becomes the set {New, York, Paris}: a document with city="New York" is not matched, while documents with city="New" or city="York" are matched. The filter silently returns the wrong document set.

**verdict:** ?

---

### 148

`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:26`

```java
                String nanoseconds = parts[1].substring(0, parts[1].indexOf('Z'));
```

**Given** A timestamp with a fractional second and a negative UTC offset, e.g. p.getText() returns "2024-08-04T00:54:54.764563036-05:00" (an Ollama server running anywhere west of UTC). date.contains(".") is true, parts[1] is "764563036-05:00", parts[1].contains("+") is false, so the else branch runs and parts[1].indexOf('Z') is -1.

**Then** substring(0, -1) throws StringIndexOutOfBoundsException, so deserialize propagates it out of Jackson and every Ollama response is rejected for clients in a negative offset zone; only '+' offsets and 'Z' are handled.

**verdict:** ?

---

### 149

`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:76`

```java
        ObjectListing objectListing = cosClient.listObjects(listObjectsRequest);
```

**Given** A bucket (or prefix) containing more than 1000 matching objects, e.g. 1500 files, loaded via loadDocuments(bucket, parser) or loadDocuments(bucket, prefix, parser).

**Then** listObjects returns a single truncated page capped at max-keys (1000 by default); objectListing.isTruncated() is never checked and listNextBatchOfObjects/setMarker is never called, so the method returns only the first 1000 objects' documents and silently drops the remaining 500, while its javadoc states it loads all documents from the bucket.

**verdict:** ?

---

### 150

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`

```java
        state.replaceAll(this::readStateBlocking);
```

**Given** A scope whose `state` map holds an `AsyncResponse` entry whose `blockingGet()` resolves to `null` (an async agent that completed with no output). `readStateBlocking` then calls `writeState(key, null)`, which removes the entry, and returns `null` as the new value.

**Then** `ConcurrentHashMap.replaceAll` rejects a null remapping result (`if (newValue == null) throw new NullPointerException();`), so `rootCallEnded` throws NPE before reaching the `kind` dispatch below: an EPHEMERAL scope is never `registry.evict(memoryId)`-ed (it stays in the registry) and a PERSISTENT scope is never `flush`-ed (the final state is never persisted), and the NPE propagates to the caller that ended the root call.

**verdict:** ?

---

### 151

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:160`

```java
                    BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
```

**Given** A JVM whose default charset is not UTF-8 (Java 17 on a Windows locale defaults to windows-1252) receiving a UTF-8 response body containing non-ASCII characters, e.g. a model reply with accented text or an emoji.

**Then** InputStreamReader is built with no Charset, so the bytes are decoded with the platform default instead of the charset declared by the response Content-Type; SuccessfulHttpResponse.body() (and the HttpException message on the error path) carries mojibake, and downstream JSON parsing of that body yields corrupted strings.

**verdict:** ?

---

### 152

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:137`

```java
+ inFilterQuery + " and " + m + "name!='" + filter.key() + "')"
```

**Given** A stored document with metadata {"k":"a", "other":"a"} queried with IsNotIn("k", ["a"]).

**Then** The second disjunct `m0.value IN ('a') and m0.name!='k'` is satisfied by the joined row for "other", so the document is returned even though its "k" value is in the excluded list. Any document that carries an excluded value under some other metadata key defeats the NOT IN filter.

**verdict:** ?

---

### 153

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`

```java
return mergedAgents;
```

**Given** Two providers registering agents "a" and "b", so discover() returns a CompositeAgentsRegistry; caller does AgentsRegistry.get().allAgents().clear() (or .put("a", other)).

**Then** allAgents() hands out the live HashMap field, contrary to the declared "@return an unmodifiable map" (line 24) and to EmptyAgentsRegistry, which returns Map.of(). The mutation succeeds and permanently alters the cached singleton: the following AgentsRegistry.get().getAgent("a") throws RuntimeException("No agent found with name: a") — or silently returns the substituted instance.

**verdict:** ?

---

### 154

`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:26`

```java
String nanoseconds = parts[1].substring(0, parts[1].indexOf('Z'));
```

**Given** Any Ollama timestamp with a fractional part and a negative UTC offset, e.g. "2024-08-04T00:54:54.764563036-05:00" (an Ollama host in any Americas timezone). parts[1] is "764563036-05:00": it contains no '+', so the else branch runs, and it contains no 'Z' either, so indexOf('Z') returns the not-found sentinel -1.

**Then** substring(0, -1) throws StringIndexOutOfBoundsException instead of returning a value; the exception escapes deserialize(), so every Ollama response carrying such a date fails to deserialize.

**verdict:** ?

---

### 155

`models/spring-ai-transformers/src/main/java/org/springframework/ai/transformers/TransformersEmbeddingModel.java:271`

```java
this.session.close();
```

**Given** A TransformersEmbeddingModel that has completed afterPropertiesSet() and is closed twice - the exact combination the new Javadoc advertises: the instance is a Spring bean (Spring infers close() as the destroy method for an AutoCloseable bean) and user code also closes it, e.g. via try-with-resources or an explicit close() before context shutdown.

**Then** The second call re-enters close() with this.session non-null and already closed; OrtSession.close() rejects a repeat close (it guards on its internal closed flag and throws IllegalStateException, "Trying to close an already closed OrtSession.") instead of being a no-op. close() keeps no closed flag and never nulls the fields, so the exception escapes to the caller - or is swallowed as a destroy-method warning at context shutdown - even though AutoCloseable implementations are expected to tolerate repeated close().

**verdict:** ?

---

### 156

`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:530`

```java
if (trace.guardrail().hasInputAssessment()) {
```

**Given** A ConverseResponse carrying a non-null ConverseTrace whose guardrail member is null - e.g. a response from an intelligent prompt router, where ConverseTrace populates promptRouter only, or any trace returned while no guardrail was applied to the call.

**Then** trace.guardrail() returns null and the chained call hasInputAssessment() throws NullPointerException, aborting response conversion for the whole request. The method guards the outer trace == null case but never the nested guardrail member, which the SDK models as an optional field (same unguarded dereference again at line 621 and inside the loop at line 533).

**verdict:** ?

---

### 157

`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`

```java
metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());
```

**Given** textSegment with text "hello world" and metadata containing the entry "text_segment" -> "anything", called with metadataTextKey = "text_segment"

**Then** putFields overwrites the field written at line 43, so the Struct stored in Pinecone carries "anything" as the text field instead of "hello world"; the segment text is silently lost and retrieval returns the metadata value as the segment content. Nothing in the method rejects or renames a metadata key that collides with metadataTextKey.

**verdict:** ?

---

### 158

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:333`

```java
String columnValue = resultSet.getObject(i).toString();
```

**Given** Any generated SELECT whose result set contains a SQL NULL in any cell, e.g. SELECT id, email FROM customers where one row has email IS NULL. ResultSet.getObject returns Java null for a SQL NULL.

**Then** NullPointerException on .toString(); it is swallowed by the catch (Exception e) in retrieve(), so the whole retrieval silently returns emptyList() after burning the retries, and the caller sees no content and no error for a query that executed successfully.

**verdict:** ?

---

### 159

`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:170`

```java
            return hqlQuery.substring(hqlQuery.indexOf("```hql") + 6, hqlQuery.lastIndexOf("```"));
```

**Given** The LLM returns an opening code fence with no closing fence, e.g. aiMessage().text() == "```hql\nSELECT e FROM Entity e" (or the same with "```sql", or a bare "```" prefix, which hit lines 172 and 174 identically).

**Then** indexOf("```hql") == 0 and lastIndexOf("```") == 0, so substring(6, 0) is called with begin > end and throws StringIndexOutOfBoundsException. clean() is invoked at line 127, outside the try/catch at lines 131-142, so the exception escapes retrieve() to the caller instead of being retried or returning emptyList().

**verdict:** ?

---

### 160

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`

```java
Object result = response.get("result");
```

**Given** A 2xx code-execution response whose JSON body has no "properties" key, or where "properties" is null / not a JSON object (e.g. body "{}").

**Then** getNestedMapProperty returns null at line 314, executeCode returns null, and use() dereferences it at line 213, throwing NullPointerException out of the @Tool method instead of the wrapped "Failed to execute code." error the rest of the method produces.

**verdict:** ?

---

### 161

`langchain4j-pinecone/src/main/java/dev/langchain4j/store/embedding/pinecone/PineconeHelper.java:50`

```java
metadataBuilder.putFields(key, Value.newBuilder().setStringValue(value.toString()).build());
```

**Given** textSegment with text "the real content" and metadata containing an entry whose key equals metadataTextKey (e.g. metadata {"text": "foo"} with the default metadataTextKey "text")

**Then** putFields overwrites the field written on line 43, so the Struct stored in Pinecone carries "foo" as the text field instead of "the real content"; the segment text is silently lost and reads back wrong

**verdict:** ?

---

### 162

`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:51`

```java
this.additionalParams = getOrDefault(builder.additionalParams, () -> new HashMap<>());
```

**Given** Map<String, Object> m = new HashMap<>(); WebSearchRequest r = WebSearchRequest.builder().searchTerms("cats").additionalParams(m).build(); Set<WebSearchRequest> s = new HashSet<>(); s.add(r); m.put("key", "value");

**Then** the builder's map is stored by reference (no defensive copy) and additionalParams() at line 123 hands the same reference back, so the caller's put mutates the constructed request; hashCode() at line 154 hashes the mutated map and s.contains(r) now returns false while r is still in the set, and two requests built from the same map can no longer be distinguished from ones built with different params

**verdict:** ?

---

### 163

`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:157`

```java
.subscribe(sink::next)
```

**Given** Any caller that cancels the returned Flux before the transcription finishes, e.g. `model.stream(prompt).take(1).subscribe(...)`, `.timeout(Duration.ofSeconds(2))`, or simply disposing the subscription.

**Then** The AsyncStreamResponse returned by createStreaming is never closed: no sink.onCancel/onDispose hook calls close(), so the underlying HTTP response and its connection stay open until the server finishes sending the whole transcription. Repeated cancelled streams exhaust the connection pool. Events pushed by the SDK after cancellation also keep arriving into a dead sink.

**verdict:** ?

---

### 164

`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`

```java
", siteRestrict=" + safeSearch +
```

**Given** Any built request, e.g. WebSearchRequest.from("hello"), then calling toString().

**Then** Returns "WebSearchRequest{...startIndex=null, siteRestrict=true, additionalParams={}}": the safeSearch value is printed under the label siteRestrict, a field this class does not have, so safeSearch never appears by name in logs or assertion failure messages and a reader sees a non-existent field instead.

**verdict:** ?

---

### 165

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:424`

```java
if (response.statusCode() == 404) {
```

**Given** DefaultFileDownloader.downloadFile for a path that does not exist in the session, so the service answers 404.

**Then** langchainHttpClient.execute returns a SuccessfulHttpResponse only for 2xx and throws for anything else, so statusCode() never holds 404 and this branch is unreachable dead code. The same is true of the `else` at line 315 in executeCode. The 404 case is instead handled only by the string test `e.getMessage().contains("404")` at line 433, which depends on the message text of whatever exception the pluggable HTTP client happens to throw.

**verdict:** ?

---

### 166

`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:26`

```java
String nanoseconds = parts[1].substring(0, parts[1].indexOf('Z'));
```

**Given** Any timestamp with a fractional part and a negative UTC offset, e.g. "2024-08-04T00:54:54.764563036-05:00" (what Ollama emits on any host west of UTC), or a fractional timestamp with no offset at all, e.g. "2024-08-04T00:54:54.764563036".

**Then** parts[1] contains neither '+' nor 'Z', so indexOf('Z') returns -1 and substring(0, -1) throws StringIndexOutOfBoundsException; deserialization of every Ollama response fails on such hosts instead of returning an OffsetDateTime.

**verdict:** ?

---

### 167

`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`

```java
if (!result.getPagemap().isEmpty()) {
```

**Given** A non-image web search (searchTypeImage == false) whose response contains at least one Result with no "pagemap" field, e.g. search.getItems() = [Result{title="T", link="https://x/", snippet="s", pagemap=null}]. The google-api-client model leaves absent JSON fields null, and Google Custom Search routinely omits pagemap.

**Then** toWebSearchOrganicResults -> toResultMetadataMap dereferences the null map and throws NullPointerException, so search() aborts and returns nothing even though the guard added at line 189 established that items are present. Reachable on the same path the new method walks.

**verdict:** ?

---

### 168

`langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java:70`

```java
responseContext.chatResponse().tokenUsage().inputTokenCount());
```

**Given** A chat response whose TokenUsage object is non-null but carries a null count field, e.g. TokenUsage(null, 12, 12) or the very common streaming/partial case TokenUsage with inputTokenCount set and outputTokenCount null.

**Then** The guard on line 65 only rejects a null TokenUsage, so the null Integer returned by inputTokenCount()/outputTokenCount() is auto-unboxed into the int parameter of addTokenMetric and throws NullPointerException inside onResponse; no token metric is recorded for that response at all - not even the non-null half - and the listener invocation fails.

**verdict:** ?

---

### 169

`models/spring-ai-openai/src/main/java/org/springframework/ai/openai/OpenAiAudioTranscriptionModel.java:149`

```java
TranscriptionCreateParams params = buildParams(mergedOptions, audioBytes, filename);
```

**Given** Any prompt, e.g. new AudioTranscriptionPrompt(new ClassPathResource("speech.mp3")), where the returned Flux is subscribed more than once: model.stream(prompt).retry(1).subscribe(...), or a second subscribe on the same Flux, or any operator that resubscribes (retryWhen, repeat, two subscribers on a cold Flux).

**Then** params is built once at assembly time and holds a single ByteArrayInputStream created in buildParams (line 178). Flux.create's lambda runs per subscription, so the second subscription calls createStreaming(params) with the same, already fully consumed stream: the multipart file part is uploaded as 0 bytes. The retry that was meant to recover from a transient failure instead sends an empty audio file and yields an API error or an empty transcription, so a retried stream() silently produces no text where call() (which rebuilds params per invocation) would succeed.

**verdict:** ?

---

### 170

`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:181`

```java
        messageResponse.complete(extractTextFromParts(
                task.artifacts().stream().flatMap(a -> a.parts().stream()).toList()));
```

**Given** A task whose state is TASK_STATE_FAILED, TASK_STATE_CANCELED or TASK_STATE_REJECTED and whose artifacts list is empty (the normal shape of a failed task: it carries a status message, not artifacts).

**Then** isTerminalState is true, so the early return is skipped and messageResponse is completed normally with the empty string. invokeAgent then returns serviceOutputParser.parseText(returnType, "") - the caller sees a successful empty answer instead of an error, and for a non-String returnType the empty text is fed to the output parser.

**verdict:** ?

---

### 171

`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`

```java
", siteRestrict=" + safeSearch +
```

**Given** WebSearchRequest.from("cats") then calling toString() (safeSearch defaults to true at line 50)

**Then** toString() returns "...startIndex=null, siteRestrict=true, additionalParams={}}" - the safeSearch value is printed under the label of a field named siteRestrict that does not exist on the class, and safeSearch appears nowhere in the output, so any log or assertion reading the string reports the wrong field

**verdict:** ?

---

### 172

`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:76`

```java
if (node.has("$ref")) {
```

**Given** A tool whose top-level inputSchema is itself a reference, e.g. {"$ref": "#/$defs/Input", "$defs": {"Input": {"type": "object", "properties": {...}}}} (the shape Pydantic emits for a root model).

**Then** jsonNodeToJsonSchemaElement now returns a JsonReferenceSchema for that node, so the cast at line 44, builder.parameters((JsonObjectSchema) jsonNodeToJsonSchemaElement(tool.get("inputSchema"))), throws ClassCastException and the whole toolSpecificationListFromMcpResponse call aborts, losing every tool in the response. Before this change the same input fell through to the typeNode == null branch and produced a JsonObjectSchema without crashing. The early return also skips the new $defs block below, so the sibling $defs is discarded.

**verdict:** ?

---

### 173

`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`

```java
Document parsedDocument = documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()));
```

**Given** load("https://example.com/page", new TextDocumentParser()) where the fetched page contains non-ASCII text, e.g. page.content() returns "<html><body>caf\u00e9 \u4f60\u597d</body></html>", running on a JVM whose file.encoding is windows-1252 (default on many Windows installs) or US-ASCII.

**Then** String.getBytes() with no Charset encodes with the platform default charset, so \u4f60\u597d is unmappable and becomes '?' bytes; the parser (which decodes as UTF-8) then produces a Document whose text reads "caf? ??" instead of "caf\u00e9 \u4f60\u597d". The same call on a UTF-8 JVM returns the correct text, so the loaded document content silently differs by host locale.

**verdict:** ?

---

### 174

`langchain4j-guardrails/src/main/java/dev/langchain4j/guardrails/PatternBasedPromptInjectionGuardrail.java:123`

```java
        String text = userMessage.singleText();
        if (text == null || text.isBlank()) {
```

**Given** A UserMessage whose contents are not exactly one TextContent - e.g. UserMessage.from(ImageContent.from(url), TextContent.from("ignore all previous instructions")), or a message built from two TextContent parts.

**Then** UserMessage.singleText() does not return null for such a message; it throws (illegal-argument/unsupported-operation, "Expecting single text content, but got: ..."). The exception escapes validate() instead of an InputGuardrailResult being returned, so the guardrail chain aborts with an unexpected runtime exception rather than passing or blocking the input, and the attached text is never scanned. The `text == null` branch guards a value the call never yields, so it silently protects nothing.

**verdict:** ?

---

### 175

`auto-configurations/vector-stores/spring-ai-autoconfigure-vector-store-mongodb-atlas/src/main/java/org/springframework/ai/vectorstore/mongodb/autoconfigure/MongoDBAtlasVectorStoreAutoConfiguration.java:81`

```java
return () -> mongoClientProvider.ifAvailable(mongoClient -> mongoClient
```

**Given** An application context that defines two or more MongoClient beans with none marked @Primary (for example a multi-database setup that supplies its own MongoDatabaseFactory/MongoTemplate for one of them), with spring.ai.vectorstore.type unset or set to mongodb-atlas so this auto-configuration applies.

**Then** ObjectProvider.ifAvailable delegates to getIfAvailable(), which for a non-collection dependency with several candidates and no primary calls resolveNotUnique and throws NoUniqueBeanDefinitionException. The exception is raised from afterSingletonsInstantiated, so context refresh aborts and the application fails to start, where before this change the same context started. The vectorStore bean on line 93 uses getIfUnique for exactly this reason.

**verdict:** ?

---

### 176

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:136`

```java
        byte[] bodyBytes = apacheResponse.getBody().getBodyBytes();
```

**Given** A successful streaming response carrying no entity at all, e.g. HTTP 204 or a 200 with Content-Length: 0.

**Then** SimpleHttpResponse.getBody() returns null when no body was set, so getBody() throws NullPointerException before requireNonNullElseGet can defend the bytes. The NPE is raised in the try-with-resources resource expression at line 113 and caught by the catch at line 116, so the listener receives onError(NullPointerException) instead of a clean onClose after onOpen.

**verdict:** ?

---

### 177

`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`

```java
", siteRestrict=" + safeSearch +
```

**Given** Any WebSearchRequest, e.g. WebSearchRequest.from("cats"), passed to toString() (directly, or via string concatenation in a log or assertion message).

**Then** The rendered string contains "siteRestrict=true" although no siteRestrict field exists; the value of safeSearch is printed under a name that belongs to no property, so log output and any string-based comparison of toString() report the wrong field name.

**verdict:** ?

---

### 178

`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:143`

```java
String filterQuery = m + "value " + operator + " '" + value + "'";
```

**Given** IsEqualTo("author", "O'Brien") — any String comparison value (or metadata key, via metadataKey/metadataKeyLast) containing a single quote.

**Then** The value is interpolated into the Ickle query without escaping, producing `m0.value = 'O'Brien'`, which fails to parse and throws at query execution; a crafted value can also close the literal and inject arbitrary query fragments.

**verdict:** ?

---

### 179

`models/spring-ai-transformers/src/main/java/org/springframework/ai/transformers/TransformersEmbeddingModel.java:271`

```java
this.session.close();
```

**Given** A fully initialised TransformersEmbeddingModel (afterPropertiesSet() has run, so this.session is non-null) whose close() is invoked twice — precisely the combination the new Javadoc invites: a Spring-managed bean, for which Spring infers close() as the destroy method and calls it at context shutdown, that user code also wrapped in try-with-resources (or any code that simply calls close() a second time).

**Then** The null guard only protects against a never-initialised session, not an already-closed one. ai.onnxruntime.OrtSession.close() sets an internal `closed` flag and throws IllegalStateException("Trying to close an already closed OrtSession.") when called again, so the second close() propagates that exception out of the try-with-resources block (or is logged as a destroy-method failure during context shutdown). The tokenizer half is idempotent (DJL NativeResource clears its handle), so only the session leg fails, and it fails after the try/finally has already run — no resource is leaked, but the caller observes an unexpected unchecked exception at teardown.

**verdict:** ?

---

### 180

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:296`

```java
            return sqlQuery.substring(sqlQuery.indexOf("```sql") + 6, sqlQuery.lastIndexOf("```"));
```

**Given** An LLM response with an opening fence but no closing fence, e.g. sqlQuery = "```sql\nSELECT * FROM customers" (truncated output, or a model that omits the trailing fence). Same for the else-branch on line 298 with "```SELECT * FROM customers".

**Then** indexOf("```sql") is 0 so beginIndex is 6, while lastIndexOf("```") finds the same single occurrence and returns 0, giving substring(6, 0), which throws StringIndexOutOfBoundsException. clean() is called on line 249, outside the try block that starts on line 255, so the exception escapes retrieve() to the caller instead of the documented empty-list/retry behaviour.

**verdict:** ?

---

### 181

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:333`

```java
                    String columnValue = resultSet.getObject(i).toString();
```

**Given** Any generated SELECT whose result set contains a SQL NULL in any cell, e.g. "SELECT id, email FROM customers" where one row has email IS NULL.

**Then** resultSet.getObject(i) returns null and .toString() throws NullPointerException. It is swallowed by the catch (Exception e) on line 265, the NPE message is fed back to the LLM as if it were a SQL error, and after maxRetries the retriever returns an empty list, so a perfectly valid query yields no content.

**verdict:** ?

---

### 182

`document-loaders/langchain4j-document-loader-playwright/src/main/java/dev/langchain4j/data/document/loader/playwright/PlaywrightDocumentLoader.java:66`

```java
documentParser.parse(new ByteArrayInputStream(pageContent.getBytes()))
```

**Given** load(url, documentParser) on a page whose HTML contains non-ASCII characters (e.g. "café", "中文"), running on a JVM whose default charset is not UTF-8 (Java 17 on Windows, where file.encoding defaults to windows-1252, or any JVM started with -Dfile.encoding=ISO-8859-1).

**Then** String.getBytes() encodes with the platform default charset while the parser decodes the stream as UTF-8, so every non-ASCII character is turned into replacement characters or mojibake in the returned Document text; characters outside the default charset (CJK under windows-1252) are irrecoverably replaced by '?'. The single-argument load(url) path, which keeps the String, returns correct text for the same page, so the two overloads disagree on the same input.

**verdict:** ?

---

### 183

`langchain4j-agentic-a2a/src/main/java/dev/langchain4j/agentic/a2a/DefaultA2AClientBuilder.java:178`

```java
        if (!isTerminalState(task.status().state()) && task.artifacts().isEmpty()) {
```

**Given** The builder no longer disables streaming (the `setStreaming(false)` ClientConfig was removed at line 70-72), so a server that streams a task emits TaskUpdateEvents while the task is still non-terminal. Walk with: update 1 = state `TASK_STATE_WORKING` with one artifact part "Paris is the", update 2 = same state with the artifact continued "Paris is the capital of France", update 3 = `TASK_STATE_COMPLETED` with the full artifact.

**Then** On update 1 the guard is false (artifacts are non-empty), so `messageResponse.complete("Paris is the")` runs. CompletableFuture.complete is idempotent, so updates 2 and 3 are discarded, and `messageResponse.get()` at line 164 returns the truncated first chunk. invokeAgent returns "Paris is the" as the agent's answer.

**verdict:** ?

---

### 184

`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`

```java
                ", siteRestrict=" + safeSearch +
```

**Given** any instance, e.g. WebSearchRequest.from("cats").toString()

**Then** the rendered string is "...startIndex=null, siteRestrict=true, additionalParams={}}" - the safeSearch value is emitted under the label of a field that does not exist on this class, and no safeSearch key appears at all, so logs and assertions on toString report the wrong field name

**verdict:** ?

---

### 185

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`

```java
private static volatile AgentsRegistry INSTANCE = discover();
```

**Given** Two AgentsRegistry providers on the classpath that both expose an agent named "researcher" (or any provider whose get() throws). First call: AgentsRegistry.get().

**Then** discover() runs inside LazyHolder's static initializer, so the RuntimeException thrown at line 82 escapes as ExceptionInInitializerError and LazyHolder is left permanently erroneous. Every later AgentsRegistry.get() throws NoClassDefFoundError("Could not initialize class ...LazyHolder") instead of the documented RuntimeException, and refresh() cannot recover either — its own body touches LazyHolder and throws NoClassDefFoundError before reaching the re-assignment, so the documented re-discovery path is unusable for the rest of the JVM's life.

**verdict:** ?

---

### 186

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:115`

```java
return format("metadata/attributes/any(k: k/key eq '%s' and " + format + ")", key, value);
```

**Given** map(new IsEqualTo("author", "O'Brien")) — any key or comparison value whose text contains a single quote.

**Then** The quote is interpolated raw, producing metadata/attributes/any(k: k/key eq 'author' and k/value eq 'O'Brien'), which is not a valid OData literal (a quote must be doubled). Azure AI Search rejects the request with HTTP 400 InvalidRequestParameter instead of returning results. A value such as "x' or k/key eq 'secret" likewise closes the literal and injects extra filter clauses.

**verdict:** ?

---

### 187

`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:24`

```java
date = date.replaceAll(nanoseconds, "");
```

**Given** A timestamp whose fractional digits also occur earlier in the string. Ollama formats with Go's RFC3339Nano, which strips trailing zeros, so short fractions are reachable: "2024-08-04T00:54:54.04+02:00" yields nanoseconds = "04".

**Then** replaceAll treats its argument as a regex and replaces every occurrence, not only the fraction: the date becomes "2024-8-T00:54:54.+02:00", and OffsetDateTime.parse then throws DateTimeParseException rather than returning the parsed date.

**verdict:** ?

---

### 188

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:429`

```java
                byte[] fileBytes = response.body().getBytes(StandardCharsets.UTF_8);
```

**Given** downloadFile("plot.png") or any non-UTF-8 file (image, zip, pickle) present in the session.

**Then** The body has already been decoded to a String; every byte sequence that is not valid UTF-8 became U+FFFD, and re-encoding with getBytes(UTF_8) emits 0xEF 0xBF 0xBD. The returned Base64 therefore decodes to corrupted content that does not match the remote file.

**verdict:** ?

---

### 189

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/store/embedding/azure/search/AbstractAzureAiSearchEmbeddingStore.java:71`

```java
        if (createOrUpdateIndex && index != null) {
```

**Given** initialize(endpoint, cred, null, false, dimensions, index, null) where index is a SearchIndex named "my-index" and createOrUpdateIndex is false (the one combination of the two guarded values that falls to the else branch with a non-null index)

**Then** The condition is false, so this.indexName becomes getOrDefault(null, DEFAULT_INDEX_NAME) = "vectorsearch" and the SearchClient built at line 88/101 is bound to "vectorsearch" instead of "my-index"; every add and findRelevant then reads and writes the wrong index (or fails against a nonexistent one), while the caller-supplied index name is silently discarded — line 66 forbids passing indexName alongside index, so there is no way to reach the intended name on this path.

**verdict:** ?

---

### 190

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:57`

```java
private static volatile AgentsRegistry INSTANCE = discover();
```

**Given** Two ServiceLoader providers of AgentsRegistry on the classpath that both expose the same agent name (or any provider whose allAgents() throws), then a first call to AgentsRegistry.get() followed by AgentsRegistry.refresh().

**Then** discover() runs inside LazyHolder's static initializer, so the RuntimeException thrown at line 82 surfaces as ExceptionInInitializerError, not the documented RuntimeException, and LazyHolder is permanently marked erroneous. Every later AgentsRegistry.get() AND AgentsRegistry.refresh() then throws NoClassDefFoundError (refresh() assigns to LazyHolder.INSTANCE, which touches the failed class), so the documented recovery path 'Call refresh() to force re-discovery' cannot run for the lifetime of the class loader.

**verdict:** ?

---

### 191

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:19`

```java
    private static final String BOUNDARY = "----LangChain4j";
```

**Given** a FormDataFile whose content() contains the byte sequence CRLF + "------LangChain4j" (for example a log or source file that quotes this class's own boundary)

**Then** the delimiter is a compile-time constant that is never checked against the payload, so the receiver ends the part at that offset and the uploaded file is silently truncated (and the remainder parsed as bogus parts); because the boundary is fixed, the collision is deterministic and every retry reproduces it

**verdict:** ?

---

### 192

`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:111`

```java
return comparisonValues.stream().map(Object::toString).sorted().collect(Collectors.joining(", "));
```

**Given** new IsIn("city", asList("New York", "Paris")) — any IsIn/IsNotIn whose comparison value contains a space or a comma.

**Then** All values are joined into one quoted OData literal, producing search.in(k/value, ('New York, Paris')). search.in with no explicit delimiter argument splits on space and comma, so the list becomes "New", "York", "Paris": a document with value "New York" is not matched, while documents with value "New" or "York" are wrongly matched.

**verdict:** ?

---

### 193

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:213`

```java
        Object result = response.get("result");
```

**Given** A 2xx response from code/execute whose JSON body has no top-level "properties" key (or has it as a non-object), e.g. body "{}" or an envelope like {"id":"...","status":"Succeeded"}.

**Then** getNestedMapProperty returns null, executeCode returns that null unchecked, and use() throws NullPointerException on response.get("result") — outside executeCode's try, so it escapes uncaught to the caller instead of the "Failed to execute code." RuntimeException.

**verdict:** ?

---

### 194

`langchain4j-agentic-patterns/src/main/java/dev/langchain4j/agentic/patterns/debate/ConvergenceStrategy.java:25`

```java
String text = p.toString().trim();
```

**Given** A positions collection containing a null element, e.g. `Arrays.asList("YES", null)`.

**Then** Throws NullPointerException on `p.toString()`, whereas the sibling strategy `unanimous()` handles the same input without throwing because it compares with `Objects.equals`; the two implementations of the same interface disagree on whether null elements are permitted.

**verdict:** ?

---

### 195

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/scope/DefaultAgenticScope.java:143`

```java
state.replaceAll(this::readStateBlocking);
```

**Given** a scope whose state map holds an AsyncResponse under some key whose blockingGet() resolves to null (an async agent that produced no output), then rootCallEnded is called

**Then** readStateBlocking returns null, and ConcurrentHashMap.replaceAll rejects a null remapping value, so rootCallEnded throws NullPointerException before eviction/flush ever runs — the ephemeral scope is never evicted and the persistent scope is never flushed

**verdict:** ?

---

### 196

`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:148`

```java
throw new IllegalArgumentException("Tencent credentials are required.");
```

**Given** TencentCosDocumentLoader.builder().region("ap-guangzhou").build() — no tencentCredentials(...) call, which the javadoc on tencentCredentials states is allowed ("If not set, it will use the default credentials.").

**Then** build() throws IllegalArgumentException instead of falling back to a default credentials provider, so the documented no-credentials path is unusable.

**verdict:** ?

---

### 197

`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:237`

```java
        return ref;
```

**Given** A tool inputSchema such as {"type":"object","properties":{"a":{"$ref":"#/components/schemas/Foo"}},"$defs":{"Foo":{"type":"string"}}} — any $ref pointer not starting with "#/$defs/" or "#/definitions/".

**Then** extractReferenceKey returns the whole pointer "#/components/schemas/Foo" as the reference name, while the definitions map built at line 107 is keyed by bare names ("Foo"), so the produced JsonReferenceSchema points at a definition key that does not exist and the argument schema handed to the model contains an unresolvable reference.

**verdict:** ?

---

### 198

`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:170`

```java
            return hqlQuery.substring(hqlQuery.indexOf("```hql") + 6, hqlQuery.lastIndexOf("```"));
```

**Given** The LLM returns a reply containing exactly one fence marker, e.g. the text "```hql select p from Person p" (opening fence never closed, or truncated by max output tokens). Same for the two sibling branches: "```sql select 1" at line 172 and "select 1 ```" at line 174.

**Then** indexOf("```hql") is 0 so the start index is 6, while lastIndexOf("```") also returns 0 — substring(6, 0) throws StringIndexOutOfBoundsException. clean() is called at line 127, outside the try/catch at line 131, so the exception is not caught, no retry happens even when maxRetries > 0, and retrieve() aborts by propagating the exception to the caller instead of returning emptyList().

**verdict:** ?

---

### 199

`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:530`

```java
if (trace.guardrail().hasInputAssessment()) {
```

**Given** A ConverseResponse whose trace() is non-null but whose guardrail() member is null — e.g. a response carrying only a prompt-router trace, or a trace returned with no guardrail assessment section (no guardrail applied to that call). guardrailAssessmentSummaryFrom is then called with that non-null trace.

**Then** The method guards only against trace == null, then immediately dereferences trace.guardrail(), so a NullPointerException is thrown at this line (and again at trace.guardrail().hasOutputAssessments() on line 621) instead of returning a summary, aborting response conversion for an otherwise successful Bedrock call.

**verdict:** ?

---

### 200

`code-execution-engines/langchain4j-code-execution-engine-azure-acads/src/main/java/dev/langchain4j/code/azure/acads/SessionsREPLTool.java:433`

```java
                if (e.getMessage().contains("404")) {
```

**Given** langchainHttpClient.execute(request) throws an exception with a null detail message (e.g. an IOException/RuntimeException constructed with no message, or a wrapping exception whose cause carries the text).

**Then** e.getMessage() is null and the catch block itself throws NullPointerException, discarding the original failure: the caller sees an NPE from line 433 instead of the intended "File not found" return or the "Failed to download file" RuntimeException carrying the cause.

**verdict:** ?

---

### 201

`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:23`

```java
                String nanoseconds = parts[1].substring(0, parts[1].indexOf('+'));
                date = date.replaceAll(nanoseconds, "");
```

**Given** A timestamp whose fractional part is short enough to also occur elsewhere in the string — Go's RFC3339Nano marshalling, which Ollama uses, strips trailing zeros, so nanos = 400000000 yields "2024-08-04T00:54:54.4+02:00". nanoseconds is then "4".

**Then** replaceAll strips every occurrence of "4" in the whole string, not just the fractional digits, producing "202-08-0T00:5:5.+02:00"; OffsetDateTime.parse then throws DateTimeParseException instead of returning the date.

**verdict:** ?

---

### 202

`langchain4j-agentic/src/main/java/dev/langchain4j/agentic/planner/AgentsRegistry.java:90`

```java
return mergedAgents;
```

**Given** Two or more providers on the classpath (so discover() returns a CompositeAgentsRegistry), then a caller doing AgentsRegistry.get().allAgents().clear() or .put("x", someAgent).

**Then** allAgents() is documented as returning 'an unmodifiable map' and the other implementation honours that with Map.of(), but the composite hands back the live private HashMap. The mutation succeeds and permanently alters the cached singleton: getAgent("x") afterwards returns the caller-injected agent, or every getAgent() throws 'No agent found' after a clear(). The mutation also bypasses the duplicate-name check the constructor exists to enforce.

**verdict:** ?

---

### 203

`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolSpecificationHelper.java:106`

```java
for (Map.Entry<String, JsonNode> entry : ((ObjectNode) defsNode).properties()) {
```

**Given** An inputSchema whose "$defs" (or "definitions") field is present but JSON null, e.g. {"type": "object", "properties": {}, "definitions": null}, or present but not an object (an array).

**Then** node.has("$defs") is true for an explicitly-null field and node.get(...) returns a NullNode rather than Java null, so the guard defsNode != null passes and the cast to ObjectNode throws ClassCastException, aborting conversion of the entire tool list instead of skipping the empty definitions block.

**verdict:** ?

---

### 204

`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:279`

```java
if (previousSqlQuery != null && previousErrorMessage != null) {
```

**Given** A failure whose exception carries no message, e.g. the NullPointerException from line 333, or a driver SQLException constructed without a reason; line 266 then stores errorMessage = null.

**Then** The guard is false even though previousSqlQuery is non-null, so the retry sends exactly the same two messages as the first attempt: the failed SQL is never shown back to the model and the retry cannot correct anything, it just re-bills an identical LLM call before retrieve() returns emptyList().

**verdict:** ?

---

### 205

`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:19`

```java
private static final String BOUNDARY = "----LangChain4j";
```

**Given** buildMultipartEntity with formDataFiles containing one FormDataFile whose content() bytes include the sequence "\r\n------LangChain4j\r\n" (for example an audio or text file that happens to embed that literal, or any file supplied by a third party). The boundary is a compile-time constant, so it is never checked against, nor derived from, the payload.

**Then** The assembled body contains the delimiter inside a part body, so the receiving server ends that part early and parses the remaining file bytes as further part headers/parts: the uploaded file is silently truncated, or the request is rejected as malformed multipart. No error is raised on the client side.

**verdict:** ?

---

### 206

`web-search-engines/langchain4j-web-search-engine-google-custom/src/main/java/dev/langchain4j/web/search/google/customsearch/GoogleCustomWebSearchEngine.java:171`

```java
if (!result.getPagemap().isEmpty()) {
```

**Given** A non-image search whose response contains at least one Result with no `pagemap` field in the JSON (e.g. a PDF or plain-text hit); the generated Google client model returns null for absent @Key fields, so `result.getPagemap()` is null.

**Then** `toWebSearchOrganicResults` maps that result and throws NullPointerException at the `.isEmpty()` call, so the whole `search(...)` call fails instead of returning the other results.

**verdict:** ?

---

### 207

`spring-ai-model/src/main/java/org/springframework/ai/model/tool/DefaultToolCallingManager.java:243`

```java
.parentObservation(parent)
```

**Given** Any non-reactive (blocking) tool-execution path, e.g. ChatModel.call() invoked from a Spring MVC controller with a tracing-backed ObservationRegistry: ToolCallReactiveContextHolder.getContext() is empty, so line 229-230 yields parent == null, while a current observation (server/advisor span) is active on the thread.

**Then** Observation.parentObservation(null) unconditionally writes null into the observation context (Context.setParentObservation), overwriting the parent that Micrometer already captured from ObservationRegistry.getCurrentObservation() when the observation was created. The TOOL_CALL observation is emitted as a root span instead of a child of the enclosing span, so tool calls disappear from the request trace on the imperative path. The call should be made only when parent != null.

**verdict:** ?

---
