# Evaluation replay

**1 scorable case(s) of 3 in the set.**

This report does not contain a detection rate and cannot: the verdict line under
each case is a human judgement. Fill them in, then read the fractions below with
their denominators visible — never as a percentage. On a handful of cases a 25 %
rate and a 75 % one are the same measurement.

## `spring-ai-61c076a`

Improve logs in StructuredOutputValidationAd

| | |
|---|---|
| introduced in | `323c590cd` |
| file | `spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java` |
| detectable from diff | yes |

6 finding(s) survived refutation:

- **`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:151`** — correctness
  `if (chatClientResponse.chatResponse() == null || !chatClientResponse.chatResponse().hasToolCalls()) {`
  On attempt 2 the whole validation block is skipped, so isValidationSuccess keeps the stale value false from attempt 1. The while condition on line 179 is therefore true and the loop overwrites chatClientResponse with a further model call: the tool-call response is discarded and never returned to the caller, the requested tool is never executed, and an extra billed model call is made. If the counter runs out on such an iteration the advisor returns a response it never validated while its state says validation failed.

- **`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:198`** — correctness
  `logger.debug("Validating JSON output against schema. Attempts left: " + this.maxRepeatAttempts);`
  Every one of the four log lines reads "Attempts left: 3"; the field is the immutable configured maximum, not the remaining count (repeatCounter is not in scope here), so the log reports 3 attempts left on the final attempt where none remain.

- **`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:151`** — correctness
  `if (chatClientResponse.chatResponse() == null || !chatClientResponse.chatResponse().hasToolCalls()) {`
  The whole if-block is skipped, so isValidationSuccess keeps the value left by the previous iteration. It stays false, the do/while keeps re-issuing the model call until repeatCounter exceeds maxRepeatAttempts (burning the remaining paid attempts on responses it never inspects), and adviseCall then returns the last tool-call ChatClientResponse as the final result even though its content was never validated against this.jsonSchema.

- **`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:151`** — correctness
  `if (chatClientResponse.chatResponse() == null || !chatClientResponse.chatResponse().hasToolCalls()) {`
  The if-block is skipped, so isValidationSuccess keeps the stale false from the previous iteration: the loop keeps calling the model even though the current response was never validated, and if the final iteration also carries tool calls the advisor returns that never-validated response as the result. Symmetrically, a first response with tool calls leaves isValidationSuccess at its initial true and the advisor returns it without ever validating anything.

- **`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:103`** — contract
  `var jsonMapper = new JacksonMcpJsonMapper(JsonParser.getObjectMapper());`
  The objectMapper argument is silently ignored when parsing the generated schema text into this.jsonSchema — the global JsonParser.getObjectMapper() is used instead — so the caller-supplied mapper only affects the validator, not schema parsing, contrary to the builder's documented 'ObjectMapper to be used for JSON processing'.

- **`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:103`** — unimplemented
  `var jsonMapper = new JacksonMcpJsonMapper(JsonParser.getObjectMapper());`
  The caller-supplied ObjectMapper is only passed to the DefaultJsonSchemaValidator; the schema text itself is deserialized with a JacksonMcpJsonMapper built on the global JsonParser.getObjectMapper(), so a custom ObjectMapper is ignored for that part of the JSON processing.

**Detected?** `yes` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## Excluded from scoring, and why

| case | reason |
|---|---|
| `spring-ai-a3e0b1e` | not findable from the diff (no) |
| `spring-ai-5a53710` | not findable from the diff (no) |

## To total it

- **detected / 1 scorable** — the headline, as a fraction.
- **findings that were not the known defect** — not errors (a genuine second bug
  is not a false positive), but the number that bounds a reader's cost, and the
  one that decides whether anyone keeps using this.

Nothing here measures a false-positive rate: every case is a diff known to
contain a defect. That needs the opposite corpus — clean commits — and it is
arguably the more useful of the two.

---

Harness transport, 1 case(s), 0 finding(s) refused by the guards. **No dollar cost**: the tokens are the harness's. That is the point of running the scaling measurement here.
