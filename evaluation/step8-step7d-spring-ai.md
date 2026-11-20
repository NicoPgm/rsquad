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

3 finding(s) survived refutation:

- **`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:151`** — correctness
  `if (chatClientResponse.chatResponse() == null || !chatClientResponse.chatResponse().hasToolCalls()) {`
  The tool-call branch skips validation and never updates isValidationSuccess, which is still false from iteration 1. The do-while condition stays true and the model is called again, with the stale augmented prompt, until repeatCounter exceeds maxRepeatAttempts. This wastes calls. If the budget runs out, a tool-call response is returned as the final result.

- **`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:198`** — correctness
  `logger.debug("Validating JSON output against schema. Attempts left: " + this.maxRepeatAttempts);`
  The debug log prints 'Attempts left: 3' on every validation, because it logs the configured maximum and not the remaining count. On the final attempt it still reports 3 left, which misleads anyone diagnosing the retry boundary.

- **`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/StructuredOutputValidationAdvisor.java:179`** — correctness
  `while (!isValidationSuccess && repeatCounter <= this.maxRepeatAttempts);`
  The loop treats the unvalidated tool-call response as a failed validation and re-sends the same augmented request until maxRepeatAttempts is exhausted, wasting model calls, and may return a tool-call response to the caller.

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
