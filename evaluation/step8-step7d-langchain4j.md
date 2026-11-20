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

4 finding(s) survived refutation:

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:115`** — correctness
  `return format("metadata/attributes/any(k: k/key eq '%s' and " + format + ")", key, value);`
  The generated filter is metadata/attributes/any(k: k/key eq 'author' and k/value eq 'O'Brien'), which is malformed OData, so Azure AI Search rejects the request. A value such as x' or k/value ne 'y can also rewrite the filter expression (filter injection).

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:115`** — correctness
  `return format("metadata/attributes/any(k: k/key eq '%s' and " + format + ")", key, value);`
  The value is interpolated unescaped into a single-quoted OData literal, producing k/value eq 'O'Brien'. Azure AI Search rejects the filter with a syntax error, and a crafted value can alter the filter logic.

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:72`** — correctness
  `if (filter instanceof IsIn) return "search.in(k/value, ('%s'))";`
  Values are joined with ", " into one quoted string, and search.in splits it on spaces and commas by default. The filter becomes the terms New, York and Paris, so "New York" never matches as a unit. It can also match documents whose value is just "New" or "York".

- **`langchain4j-azure-ai-search/src/main/java/dev/langchain4j/rag/content/retriever/azure/search/DefaultAzureAiSearchFilterMapper.java:115`** — correctness
  `return format("metadata/attributes/any(k: k/key eq '%s' and " + format + ")", key, value);`
  The key and value are interpolated into single-quoted OData literals without doubling the quote (' -> ''). The generated filter is malformed, e.g. k/value eq 'O'Brien', so Azure AI Search rejects the query. A crafted value such as x' or k/key ne 'y can also change the filter's meaning.

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

5 finding(s) survived refutation:

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:311`** — correctness
  `textAnswer = cBlock.text();`
  The assignment replaces textAnswer on each TEXT block, so only the last block is kept. Earlier text is silently dropped from the returned AiMessage.

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:345`** — correctness
  `throw new IllegalArgumentException("Unknown stop reason: " + stopReason);`
  finishReasonFrom throws IllegalArgumentException instead of returning a FinishReason such as CONTENT_FILTER. The whole chat call fails even though the service replied successfully.

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:311`** — correctness
  `textAnswer = cBlock.text();`
  The loop assigns instead of appending, so every TEXT block except the last is dropped. The returned AiMessage contains only the final block's text and the earlier text is lost silently.

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:345`** — contract
  `throw new IllegalArgumentException("Unknown stop reason: " + stopReason);`
  finishReasonFrom throws IllegalArgumentException after the API call has already succeeded and been billed, so the caller loses the response instead of getting a FinishReason such as CONTENT_FILTER or OTHER

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:311`** — correctness
  `textAnswer = cBlock.text();`
  Each TEXT block overwrites the previous one instead of being appended, so only the last text block reaches the AiMessage and the earlier text is silently dropped

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

7 finding(s) survived refutation:

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:61`** — correctness
  `requestConfigBuilder.setConnectionRequestTimeout(`
  connectTimeout is applied as the connection-request (pool lease) timeout, not the TCP connect timeout, so the connect is not bounded by the configured 2s and falls back to the Apache default.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:136`** — boundary
  `byte[] bodyBytes = apacheResponse.getBody().getBodyBytes();`
  getBody() returns null and the call throws NullPointerException inside the try-with-resources header; it is caught and delivered as listener.onError(NPE) right after onOpen was already signalled, so the stream is reported as failed instead of closed. The Objects.requireNonNullElseGet guard on the next line is never reached.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:103`** — correctness
  `public void completed(SimpleHttpResponse apacheResponse) {`
  SimpleHttpResponse is only delivered once the whole body has been buffered, so onOpen and every parser event fire only after the server closes the stream; tokens are not delivered incrementally, and a long-lived stream never produces events and buffers unbounded in memory.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:136`** — boundary
  `byte[] bodyBytes = apacheResponse.getBody().getBodyBytes();`
  getBody() is null, so getBodyBytes() throws NullPointerException. The requireNonNullElseGet guard on the next line only covers bodyBytes, not getBody(). The exception is thrown while the try-with-resources opens the stream, so it is caught by catch (Exception) and listener.onError(NPE) fires after onOpen already fired, and the parser never runs and onClose is never called.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:61`** — contract
  `requestConfigBuilder.setConnectionRequestTimeout(
                    Timeout.ofMilliseconds(builder.connectTimeout().toMillis()));`
  The value is applied as the connection-request (pool lease) timeout, not the TCP connect timeout. The socket connect still uses Apache's default (about 3 minutes), so the configured 2s connect timeout is not enforced and the call hangs far past it.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:61`** — contract
  `requestConfigBuilder.setConnectionRequestTimeout(`
  setConnectionRequestTimeout bounds only the wait to lease a connection from the pool, not the TCP connect. The configured connect timeout is never applied to the connect phase, so the connect hangs for the default or OS timeout. Meanwhile an unrelated pool-lease limit is set instead.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/ApacheHttpClient.java:136`** — boundary
  `byte[] bodyBytes = apacheResponse.getBody().getBodyBytes();`
  NullPointerException at getBody().getBodyBytes(), because the null-guard covers only bodyBytes, not getBody(). The exception is caught by the surrounding catch (Exception), so listener.onError is called with an NPE after onOpen has already fired, and onClose is never called.

**Detected?** `no` — replace with `yes` or `no`. It counts as detected only if a
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
  trace.guardrail() returns null, so the call to hasInputAssessment() throws NullPointerException. The exception escapes guardrailAssessmentSummaryFrom and fails the whole chat call, even though the model response itself was valid.

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:530`** — boundary
  `if (trace.guardrail().hasInputAssessment()) {`
  trace.guardrail() returns null and hasInputAssessment() raises NullPointerException, failing the whole chat response instead of returning an empty summary

- **`langchain4j-bedrock/src/main/java/dev/langchain4j/model/bedrock/AbstractBedrockChatModel.java:530`** — contract
  `if (trace.guardrail().hasInputAssessment()) {`
  The method checks trace for null but then calls trace.guardrail() without a null check, so it throws NullPointerException on the dereference at lines 530 and 621. The whole chat response fails instead of returning a summary or null.

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

1 finding(s) survived refutation:

- **`langchain4j-gpu-llama3/src/main/java/dev/langchain4j/model/gpullama3/GPULlama3BaseModel.java:191`** — contract
  `new ChatFormat.Message(ChatFormat.Role.USER, userMessage.singleText())));`
  UserMessage.singleText() throws IllegalStateException when the message does not hold exactly one text content, so modelResponse fails for any multi-content user message instead of degrading or rejecting it clearly.

**Detected?** `no` — replace with `yes` or `no`. It counts as detected only if a
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

3 finding(s) survived refutation:

- **`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`** — correctness
  `", siteRestrict=" + safeSearch +`
  The output contains "siteRestrict=true": the safeSearch field is printed under the label siteRestrict, which is not a field of this class, so logs and debug output misname the field.

- **`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`** — correctness
  `", siteRestrict=" + safeSearch +`
  The string contains "siteRestrict=false" instead of "safeSearch=false", so logs and assertion messages name a field that does not exist on the class.

- **`langchain4j-core/src/main/java/dev/langchain4j/web/search/WebSearchRequest.java:167`** — correctness
  `", siteRestrict=" + safeSearch +`
  The output labels the safeSearch value as "siteRestrict=false". No such field exists, so logs and test failure messages misreport the field name.

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

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:87`** — boundary
  `.maxResults(maxResults)`
  Builder field maxResults defaults to 0 and is passed as an explicit value to EmbeddingSearchRequest.builder(); the request validates maxResults > 0, so retrieve throws IllegalArgumentException instead of using a default.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:101`** — boundary
  `.filter(f -> f.score() > minScore)`
  The request already passes minScore to the store, where the threshold is inclusive; this strict > re-filter drops matches exactly at the threshold, so they are silently missing from the result.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:123`** — boundary
  `private int maxResults;`
  retrieve passes maxResults(0) to EmbeddingSearchRequest.builder(), whose constructor requires maxResults greater than zero, so every retrieve call throws IllegalArgumentException instead of using a default

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:101`** — boundary
  `.filter(f -> f.score() > minScore)`
  the request was built with minScore as an inclusive threshold, but this strict > comparison drops the match at exactly minScore, so results at the threshold are silently lost

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:123`** — contract
  `private int maxResults;`
  maxResults defaults to primitive 0 and is passed to EmbeddingSearchRequest.builder().maxResults(0). The request enforces maxResults > 0, so the first retrieve() throws IllegalArgumentException instead of using a default. Full text mode ignores it, so the failure only shows up per configuration.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/rag/content/retriever/elasticsearch/ElasticsearchContentRetriever.java:101`** — boundary
  `.filter(f -> f.score() > minScore)`
  EmbeddingSearchRequest.minScore is inclusive (score >= minScore), but this post-filter uses strict >, so hits exactly at the threshold are silently dropped.

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

3 finding(s) survived refutation:

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:143`** — correctness
  `String filterQuery = m + "value " + operator + " '" + value + "'";`
  The generated Ickle query becomes m0.name='author' and m0.value = 'O'Brien', which fails to parse (query exception) for legitimate values, and a crafted value such as "x' OR m0.name!='" alters the filter logic (query injection).

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:185`** — correctness
  `return "m" + i + ".name='" + key + "' and ";`
  Keys and values are concatenated into the query string inside single quotes with no escaping (also lines 143, 181, 190, 137). The generated Ickle query is malformed and fails at query time. A crafted value can also change the query's meaning.

- **`langchain4j-infinispan/src/main/java/dev/langchain4j/store/embedding/infinispan/InfinispanMetadataFilterMapper.java:143`** — contract
  `String filterQuery = m + "value " + operator + " '" + value + "'";`
  The value is concatenated into the Ickle query inside single quotes with no escaping. The generated query is malformed (parse error at search time), and a crafted value such as "x' or m0.name!='" can change the filter logic.

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

3 finding(s) survived refutation:

- **`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:120`** — correctness
  `body = readBody(response);`
  fromOkHttpResponse, called from onResponse before parsing, reads the entire body with response.body().string(), which blocks until the stream ends and closes the source. getInputStream(response).byteStream() then reads a closed source and throws IllegalStateException, so listener.onError is called and no events are ever parsed. Even without the exception, the stream would be buffered rather than delivered incrementally.

- **`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:120`** — correctness
  `body = readBody(response);`
  fromOkHttpResponse consumes and closes the whole body via response.body().string() before the parser runs, so the stream is read to the end before onOpen fires, then getInputStream(response).byteStream() reads an already-consumed body, the parser gets no data or throws IllegalStateException, and listener.onError is called instead of streaming partial tokens

- **`http-clients/langchain4j-http-client-okhttp/src/main/java/dev/langchain4j/http/client/okhttp/OkHttpClient.java:134`** — contract
  `return "Cannot read error response body: " + e.getMessage();`
  readBody swallows the exception and fromOkHttpResponse returns a SuccessfulHttpResponse with status 200 and the body set to the text "Cannot read error response body: ...". The caller gets a successful response with a bogus body that fails JSON parsing later, instead of the TimeoutException or RuntimeException that execute's catch blocks are meant to raise.

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
  listObjects returns a single page of at most 1000 summaries and objectListing.isTruncated() is never checked, so listNextBatchOfObjects is never called. Only the first page is loaded, the remaining objects are silently omitted, and no warning is logged even though the method is documented as loading all documents.

- **`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:76`** — boundary
  `ObjectListing objectListing = cosClient.listObjects(listObjectsRequest);`
  Only the first page (up to 1000 keys) is read. objectListing.isTruncated() and getNextMarker() are never consulted and no further listObjects call is made, so the remaining objects are silently left out of the returned list with no warning, despite the Javadoc promising to load all documents.

- **`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:76`** — contract
  `ObjectListing objectListing = cosClient.listObjects(listObjectsRequest);`
  Only the first page of summaries is processed. isTruncated()/getNextMarker() are never consulted, no further listObjects call is made, and the remaining objects are silently omitted from the returned list, although the method is documented as loading all documents from the bucket.

- **`document-loaders/langchain4j-document-loader-tencent-cos/src/main/java/dev/langchain4j/data/document/loader/tencent/cos/TencentCosDocumentLoader.java:127`** — contract
  `Set the Tencent credentials. If not set, it will use the default credentials.`
  The Javadoc promises default credentials, but createCredentialsProvider() throws IllegalArgumentException("Tencent credentials are required."), so a caller following the documented contract gets an exception.

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

5 finding(s) survived refutation:

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:333`** — correctness
  `String columnValue = resultSet.getObject(i).toString();`
  NullPointerException is thrown inside execute(), caught by the generic catch (Exception) in retrieve(), and treated as an SQL error. The NPE text is sent back to the LLM as a 'database error', which cannot fix it. After the retries the method returns an empty list, so any query touching a nullable column with a NULL yields no content.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:333`** — boundary
  `String columnValue = resultSet.getObject(i).toString();`
  resultSet.getObject(i) returns null and .toString() throws NullPointerException. retrieve() catches it as a generic Exception, so the whole result is discarded. The retry sends the NPE message (possibly null, in which case no error feedback is added) back to the LLM, which cannot fix it. The caller gets an empty list for a valid query.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:296`** — boundary
  `return sqlQuery.substring(sqlQuery.indexOf("```sql") + 6, sqlQuery.lastIndexOf("```"));`
  lastIndexOf("```") equals the index of the opening fence, which is less than indexOf + 6. substring(begin, end) with begin > end throws StringIndexOutOfBoundsException. clean() is called outside the try/catch in retrieve(), so the exception escapes retrieve() and neither the retry nor the empty-list fallback runs.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:333`** — correctness
  `String columnValue = resultSet.getObject(i).toString();`
  getObject(i) returns null, so toString() throws NullPointerException. The generic catch in retrieve() swallows it and sets errorMessage to e.getMessage(), which is null for an NPE. The retry then sends no error feedback to the LLM because of the previousErrorMessage != null check, so the same query is regenerated and fails the same way. retrieve() returns an empty list although the query was valid.

- **`experimental/langchain4j-experimental-sql/src/main/java/dev/langchain4j/experimental/rag/content/retriever/sql/SqlDatabaseContentRetriever.java:296`** — boundary
  `return sqlQuery.substring(sqlQuery.indexOf("```sql") + 6, sqlQuery.lastIndexOf("```"));`
  lastIndexOf("```") equals the opening fence index, which is lower than indexOf + 6, so substring throws StringIndexOutOfBoundsException. clean() is called outside the try/catch in retrieve(), so the exception propagates to the caller instead of retrying or returning an empty list as the rest of the method does.

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

3 finding(s) survived refutation:

- **`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:170`** — boundary
  `return hqlQuery.substring(hqlQuery.indexOf("```hql") + 6, hqlQuery.lastIndexOf("```"));`
  substring(6, 0) throws StringIndexOutOfBoundsException. clean() is called at line 127, outside the try/catch, so the exception escapes retrieve() and the maxRetries loop never gets a chance to feed an error back to the LLM. The whole retrieval fails instead of retrying.

- **`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:170`** — boundary
  `return hqlQuery.substring(hqlQuery.indexOf("```hql") + 6, hqlQuery.lastIndexOf("```"));`
  substring(begin, end) with begin > end throws StringIndexOutOfBoundsException. clean() is called in retrieve() outside the try/catch, so the exception escapes retrieve() instead of being retried with the error fed back to the LLM, even when maxRetries > 0.

- **`experimental/langchain4j-experimental-hibernate/src/main/java/dev/langchain4j/rag/content/retriever/hibernate/HibernateContentRetriever.java:170`** — boundary
  `return hqlQuery.substring(hqlQuery.indexOf("```hql") + 6, hqlQuery.lastIndexOf("```"));`
  substring throws StringIndexOutOfBoundsException. clean() is called at line 127, outside the try/catch, so the exception escapes retrieve() and the maxRetries loop is bypassed. The caller gets an exception instead of a retry or an empty list.

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

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:26`** — correctness
  `String nanoseconds = parts[1].substring(0, parts[1].indexOf('Z'));`
  substring(0, -1) throws StringIndexOutOfBoundsException, a RuntimeException rather than an IOException. Deserialization fails for any Ollama server running west of UTC, even though the input is valid ISO-8601.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:24`** — correctness
  `date = date.replaceAll(nanoseconds, "");`
  The year or day is corrupted ("2024" becomes "24", giving "24-08-04T00:54:54.+02:00"). OffsetDateTime.parse then throws DateTimeParseException, or a wrong date results. This needs fractional digits that appear elsewhere in the timestamp, so it is rare with 8 or 9 digit nanosecond parts.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:26`** — boundary
  `String nanoseconds = parts[1].substring(0, parts[1].indexOf('Z'));`
  indexOf('Z') returns -1, so substring(0, -1) throws StringIndexOutOfBoundsException. Deserializing the response fails for every negative-offset time zone.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:24`** — correctness
  `date = date.replaceAll(nanoseconds, "");`
  replaceAll removes every occurrence of the digit string, not just the fraction. "00" is stripped from the hour and from the offset (+02:00 becomes +02:), and "10" from the hour. The result is a corrupted date or a DateTimeParseException.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:26`** — boundary
  `String nanoseconds = parts[1].substring(0, parts[1].indexOf('Z'));`
  indexOf('Z') returns -1, so substring(0, -1) throws StringIndexOutOfBoundsException. This is a RuntimeException, not an IOException, so Jackson deserialization of the Ollama response fails for any server running in a negative-offset timezone.

- **`langchain4j-ollama/src/main/java/dev/langchain4j/model/ollama/OllamaDateDeserializer.java:24`** — correctness
  `date = date.replaceAll(nanoseconds, "");`
  The date part '2024-08-04' is also stripped, giving '2024-08-T00:54:54.+02:00', and OffsetDateTime.parse throws DateTimeParseException. The call removes all occurrences of the digit string, not just the fractional part.

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

- **`langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java:70`** — boundary
  `responseContext.chatResponse().tokenUsage().inputTokenCount());`
  Auto-unboxing the null Integer into the int parameter throws NullPointerException in recordTokenUsageMetrics. If input is null, the OUTPUT metric on the following call is never recorded either. No token metrics are recorded for that response, and the exception escapes onResponse.

- **`langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java:74`** — boundary
  `responseContext.chatResponse().tokenUsage().outputTokenCount());`
  The null Integer is auto-unboxed into the primitive int parameter tokenCount of addTokenMetric and throws NullPointerException. If the input count is null, neither metric is recorded. If only the output count is null, the input metric is recorded and the output metric is silently lost. The exception escapes onResponse.

- **`langchain4j-micrometer-metrics/src/main/java/dev/langchain4j/micrometer/metrics/listeners/MicrometerMetricsChatModelListener.java:70`** — contract
  `responseContext.chatResponse().tokenUsage().inputTokenCount());`
  The Integer is auto-unboxed into the int parameter tokenCount of addTokenMetric and throws NullPointerException. The null check only covers tokenUsage(), not the individual counts. The exception escapes onResponse, and when it is the input count that is null the output-token metric is never recorded either.

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
  asLong() narrows the BigInteger to its low 64 bits without error, so toObject returns 0 for 2^64 (and a wrapped or negative value for other oversized integers). The structured result carries a silently wrong number, while resultText still holds the correct one.

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolExecutionHelper.java:69`** — boundary
  `case LONG, BIG_INTEGER -> content.asLong();`
  BigInteger values are narrowed with asLong(), silently wrapping or truncating to a wrong number in the result object, while resultText still carries the correct value, so the two representations disagree

- **`langchain4j-mcp/src/main/java/dev/langchain4j/mcp/client/ToolExecutionHelper.java:69`** — correctness
  `case LONG, BIG_INTEGER -> content.asLong();`
  asLong() on a BigIntegerNode silently truncates to the low 64 bits, so the structured result object holds a wrong number (here 0) while resultText still holds the correct one; the two representations of the same result disagree with no error.

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

3 finding(s) survived refutation:

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:38`** — correctness
  `+ name + "\"; filename=\"" + file.fileName() + "\"" + CRLF + "Content-Type: "`
  The name and filename are concatenated into the Content-Disposition header with no escaping. A quote ends the filename early and yields a malformed header. CRLF in the filename injects extra part headers or splits the part. The server then parses the wrong filename or rejects the request.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:19`** — correctness
  `private static final String BOUNDARY = "----LangChain4j";`
  The fixed, non-random boundary appears inside a part body, so the server splits the part early and truncates or corrupts the uploaded file and parses the remainder as bogus parts.

- **`http-clients/langchain4j-http-client-apache/src/main/java/dev/langchain4j/http/client/apache/MultipartBodyPublisher.java:38`** — contract
  `+ "\"; filename=\"" + file.fileName() + "\"" + CRLF + "Content-Type: "`
  fileName, name and contentType are written raw into the Content-Disposition and Content-Type headers with no quoting or escaping. The quote ends the filename parameter early and a CRLF adds a header line or ends the part header block. The server then parses a corrupted or attacker-shaped multipart body.

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
  `parser.parseReader(new InputStreamReader(inputStream));`
  InputStreamReader is built without a charset, so bytes are decoded with the platform default; the document text contains mojibake (e.g. 'cafÃ©') or replacement characters, and the corrupted text is returned silently in Document.from(text).

- **`document-parsers/langchain4j-document-parser-markdown/src/main/java/dev/langchain4j/data/document/parser/markdown/MarkdownDocumentParser.java:25`** — correctness
  `parser.parseReader(new InputStreamReader(inputStream))`
  InputStreamReader without an explicit charset decodes with the platform default, so multi-byte characters are turned into mojibake or replacement characters in the resulting Document text, and output differs between machines

- **`document-parsers/langchain4j-document-parser-markdown/src/main/java/dev/langchain4j/data/document/parser/markdown/MarkdownDocumentParser.java:25`** — contract
  `parser.parseReader(new InputStreamReader(inputStream));`
  InputStreamReader without an explicit Charset decodes bytes with the platform default charset, so the text is silently mojibake'd (e.g. 'é' becomes 'Ã©') and the returned Document has corrupted content; the result varies by host environment

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

4 finding(s) survived refutation:

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:100`** — correctness
  `krb.filter(ElasticsearchMetadataFilterMapper.map(embeddingSearchRequest.filter()));`
  The filter is applied only to the KnnRetriever. The standard (match) retriever at line 130 has no filter, so the type "b" document still comes back through the text leg of the RRF fusion. The caller gets results that violate the requested metadata filter.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:129`** — boundary
  `.retriever(r -> r.rrf(rf -> rf.retrievers(List.of(`
  The rrf retriever's rank_window_size defaults to 10 and must be >= the request size. With maxResults > 10 Elasticsearch rejects the search with a validation error (or, on versions that do not validate, caps the result set at 10), so the hybrid search cannot return the requested number of results.

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:130`** — contract
  `Retriever.of(rt -> rt.standard(st -> st.query(matchQuery))),`
  The filter is applied only to the kNN retriever (krb.filter); the standard match retriever is unfiltered, so RRF fusion returns documents violating the requested filter, breaking the EmbeddingSearchRequest filter contract (and leaking documents the caller meant to exclude).

- **`langchain4j-elasticsearch/src/main/java/dev/langchain4j/store/embedding/elasticsearch/ElasticsearchConfigurationHybrid.java:129`** — boundary
  `.retriever(r -> r.rrf(rf -> rf.retrievers(List.of(`
  rankWindowSize is never set, so the rrf retriever uses its default of 10 while size is maxResults; Elasticsearch rejects the request (rank_window_size must be >= size) or at most returns 10 fused hits, so searches asking for more than 10 results fail or are truncated.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
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
