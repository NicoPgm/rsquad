# Young repositories: the screening that unblocks the measurement

**Date:** 2026-08-23
**Produced by:** `evaluation/step7_origin.py`, with the path check corrected — see below.

`evaluation/step7-pool.md` ends by saying a younger repository is no longer an improvement to
consider but the precondition, because all three obstacles follow from the repositories being
old. This is that screening, on five Java projects whose history begins in 2021 or later.

## Result

| repo | first commit | qualifying | **usable** | mass-import | renamed-since | no history |
|---|---|---:|---:|---:|---:|---:|
| **langchain4j** | 2023-06 | 155 | **31** | 93 | 3 | 27 |
| **spring-ai** | 2023-07 | 39 | **12** | 21 | 2 | 4 |
| hertzbeat | 2021-11 | 28 | 3 | 10 | 7 | 8 |
| Stirling-PDF | 2023-01 | 18 | 3 | 12 | 1 | 2 |
| pkl | 2016-01 | **0** | 0 | — | — | — |

pkl qualifies nothing: 875 commits, and its history was imported from an internal repository in
2016, so it is not the young project its GitHub creation date suggests.

## The dates, which are the whole point

| When the buggy line was first written | langchain4j | spring-ai | old repos, for comparison |
|---|---:|---:|---:|
| **after the May 2026 cutoff** | **5** | **3** | 1 |
| 2025 – 2026-05 | 13 | 6 | 9 |
| 2021 – 2024 | 13 | 3 | 11 |
| before 2021 | **0** | **0** | 21 |

**Nothing before 2021, in either.** No repackaging-era paths, no twenty-year rename chains, and
the memorisation control that mature libraries cannot supply: 8 cases whose defect was written
after the model's knowledge cutoff, against 1 in the entire old pool.

Together the two give **43 usable cases** — the size that buys ±15 points — with both age strata
populated **inside each repository**, which is what the old pool could not do: there, "recent"
was 80 % jackson, so an age contrast would have been a repository contrast.

## The path check, corrected

The old pool tried to *reconstruct* each file's historical path by walking rename records. It got
some right and some wrong, twice. This asks instead:

```
git cat-file -e <origin>:<today's path>
```

If today's path does not resolve at the origin commit, the case is **dropped, not guessed**
(`renamed-since`). Exact, conservative, no heuristic — and it turns a silent "0 lines changed",
which reads as *nothing to review*, into an explicit rejection. `empty-diff` catches the rest.

Seven of hertzbeat's 28 fall out this way, against three of langchain4j's 155: the younger the
project, the less its paths have moved, which is the same fact as everything else on this page.

## One tunable, named before it is touched

`MAX_FILES_IN_ORIGIN = 10` rejects 93 of langchain4j's 155 — more than half. That bound exists to
exclude wholesale imports (jackson's 293-file first check-in), but in a young, fast-moving project
a twelve-file commit is an ordinary feature, and the review unit is **one file** regardless of how
many the commit touched.

Raising it would raise the yield. **Deciding that after seeing which cases it admits would be the
post-hoc adjustment this whole exercise exists to avoid**, so it stays at 10 unless it is changed
for a stated reason, before any labelling, and recorded here.

## Raw

```
========================================================================================================
pkl: 0 qualifying fix(es) -> {}
========================================================================================================
langchain4j: 155 qualifying fix(es) -> {'mass-import': 93, 'usable': 31, 'renamed-since': 3, 'no-history': 27, 'moved': 1}
  d5b13be1e fix: Use the name of the provided Azure AI S  <- b099922a1 (2024-06-13) AzureAiSearchEmbeddingStore with i 3 file(s)
  7e622bfdf Fix Pinecone segment text being overwritten   <- e848e6a88 (2024-07-23) [Feature] Pinecone: support storin 10 file(s)
  a4e0d84a5 fix: only serialize responseLogprobs and ena  <- aa0e48816 (2024-10-31) Adding GoogleAiGeminiStreamingChat 10 file(s)
  efcbc2b24 fix: Accept any memoryId type in CassandraCh  <- a41f522bd (2025-09-24) Follow-up to #3685: migrate nullab 3 file(s)
  277c80e30 fix: Handle nested Not in ChromaMetadataFilt  <- 73592ce72 (2024-08-22) 1505-feature-chroma-support-metada 1 file(s)
  7073d5af6 fix: Include cache token fields in Anthropic  <- 767b5b336 (2025-03-03) update AnthropicTokenUsage.toStrin 1 file(s)
  6d1af7497 fix: Use configured similarity metric in Cas  <- a41f522bd (2025-09-24) Follow-up to #3685: migrate nullab 3 file(s)
  840330c24 Avoid NullPointerException when an async age  <- fcf18fda1 (2026-05-28) Filter away non serializable state 5 file(s)
  771b0d265 fix: support 3D logit output in OnnxScoringB  <- 1c0671617 (2024-09-20) add scoring onnx (#1769)           8 file(s)
  4ffca6387 fix: avoid NoSuchElementException in dynamic  <- 1e0f13d36 (2026-06-23) Allow a tool to declare its compen 8 file(s)
  145ff4526 fix: treat an MCP $ref outside $defs as a pl  <- 632836213 (2026-03-31) Add $ref and $defs support to MCP  2 file(s)
  33b54373d Decode gzip/deflate responses in Utils.readB  <- 260e3b140 (2026-06-02) Allow @Tool methods to also be inh 7 file(s)
  e59754e99 fix: pass builder skipCreateVectorExtension   <- 313452c49 (2026-02-03) feat: PgVectorEmbeddingStore suppo 7 file(s)
  196bc5dc1 Follow up on AgentsRegistry implementation (  <- ff9dfc1c7 (2026-07-06) Introduce AgentsRegistry for integ 6 file(s)
  7fe5d6876 fix: avoid IllegalArgumentException in Retry  <- 57eb9be75 (2024-01-15) Flesh out RetryUtils with a policy 2 file(s)
  96a3af9ee fix: Use UTF-8 when encoding Playwright page  <- 0e7374d64 (2025-07-25) Add support for loading documents  2 file(s)
  0626661ba fix: Include failing file URL in GitHubDocum  <- aaddb9226 (2024-01-08) Add a GitHub document loader (#415 7 file(s)
  f274731d8 fix: Encode page content as UTF-8 in Seleniu  <- 36c175190 (2024-05-27) Draft: Add Selenium document loade 5 file(s)
  23098bd55 fix: Preserve binary bytes in Azure dynamic   <- 1fab3b7e4 (2025-09-26) New PR for ACA Dynamic Sessions -  5 file(s)
  d15ede8ad fix: honor root metadata mode in Weaviate re  <- b2094b421 (2024-06-13) [FEATURE] Implement embedding remo 2 file(s)
  575eb46fa fix: Skip search results with unresolvable U  <- b246cfde7 (2024-08-07) [Bugfix 1458] Allowing web search  5 file(s)
  cc37ab335 fix: support Float and Double values in Qdra  <- 2a5189a78 (2024-09-12) feat: Metadata filtering Qdrant (# 8 file(s)
  33be3339a fix: throw on unsupported Azure OpenAI servi  <- 18c8397b2 (2026-06-03) Remove default fallback to Netty w 4 file(s)
  cc074e617 fix: Add dockerTlsVerify builder method and   <- 24f71d16d (2025-09-30) Docker MCP transport (#3513)       7 file(s)
  0d16d2884 fix: unanimousLastWord convergence to normal  <- 8b6aeead7 (2026-06-12) Introduce new Debate agentic patte 8 file(s)
  4aff9c9af fix: swapped account and container names in   <- ab5e89255 (2024-01-09) Add Azure Blob Storage document lo 7 file(s)
  de7753020 fix: infinite loop in OnnxBertBiEncoder.part  <- 1a3ec9200 (2026-01-16) DX: added clarifying error message 1 file(s)
  b337eb8af Allow to declaratively create an agentic sys  <- 23d9b3801 (2025-09-24) Add declarative HumanInTheLoop (#3 6 file(s)
  95a3affdd Fix filtering for non-TextSegment entries in  <- 2b2c09f05 (2024-06-13) Implement remove methods for InMem 4 file(s)
  90d5ffbc1 fix: Improve schema generation of polymorphi  <- c648906e0 (2026-04-30) AI Services: support polymorphic r 10 file(s)
  61e4d391a fix(mcp-docker): apply SSLConfig to ApacheDo  <- 24f71d16d (2025-09-30) Docker MCP transport (#3513)       7 file(s)
========================================================================================================
spring-ai: 39 qualifying fix(es) -> {'mass-import': 21, 'usable': 12, 'renamed-since': 2, 'no-history': 4}
  b1384c846 Fix `OpenAiAudioTranscriptionModel` leaking   <- fc9286cb3 (2026-06-25) Add streaming support for OpenAI a 7 file(s)
  9ec7cfa3f Fix genai thinking level validation (#6339)   <- b1535b909 (2026-02-01) Update to Google GenAI SDK 1.37.0  5 file(s)
  698bde0d0 Merge streaming tool call deltas by index     <- d72057c82 (2026-06-04) Streamline OpenAiChatModel impleme 2 file(s)
  7bd3e1fb7 Fix OpenSearchVectorStore document deseriali  <- 197c51770 (2026-01-15) Add JSpecify annotations to OpenSe 4 file(s)
  4fbb484bb Fix Milvus metadata integer values returned   <- 0065949d5 (2025-02-24) Upgrade Milvus java sdk to 2.5.4   7 file(s)
  c256cfabf Fix null parent for tool call observations i  <- 1dde55d1e (2026-06-03) fix: bring parent span into Thread 6 file(s)
  12f5cbe61 Fix OpenAiChatModel.stream() to only buffer   <- 37cf20dfe (2024-11-28) Fix OpenAI ChatResponse usage calc 4 file(s)
  51e88e94a Fix integration tests after options changes   <- eba2cecca (2025-09-17) Add Ollama embedding hardware, mem 2 file(s)
  ec1e05282 Fix Redis vector store filter delete to pagi  <- bca65de6a (2025-01-28) Add filter-based deletion to Redis 2 file(s)
  9e56ef778 Fix OpenAiChatOptions.AbstractBuilder#combin  <- 13c39f107 (2025-08-20) Add mutual exclusivity validation  3 file(s)
  5f5721dae fix: Preserve ChatResponseMetadata during Op  <- 37cf20dfe (2024-11-28) Fix OpenAI ChatResponse usage calc 4 file(s)
  145b250f4 GH-5922: Preserve OpenAI response metadata    <- 6363352b8 (2024-07-25) Improve Anthropic function calling 8 file(s)
========================================================================================================
hertzbeat: 28 qualifying fix(es) -> {'mass-import': 10, 'no-history': 8, 'renamed-since': 7, 'usable': 3}
  2cea39891 fix(ai): create conversation when conversati  <- aac5bafe4 (2025-12-16) [bugfix]: AI conversation message  2 file(s)
  1b7f7f973 [fix] fixed the issue of plugin upload failu  <- 10b283522 (2025-05-20) [improve] add path validation for  1 file(s)
  3496ebf49 [fix] fixed the JMX service URL validation i  <- 62cf3d1b2 (2025-05-18) [improve] improve jndi validation  1 file(s)
========================================================================================================
Stirling-PDF: 18 qualifying fix(es) -> {'usable': 3, 'mass-import': 12, 'renamed-since': 1, 'no-history': 2}
  63ff3afb4 fix: restrict share link route tokens to UUI  <- e2ea720fc (2026-07-21) refactor(api): replace regex liter 8 file(s)
  e4c9b0410 build(deps): bump org.verapdf:validation-mod  <- 69b035c6e (2025-12-23) [V2] feat(security): add PDF stand 7 file(s)
  c80a5db5f folder and file fixes (#6461)                 <- 07b7c991f (2026-04-15) desktop mobile QR fixes (#6069)    2 file(s)
```
