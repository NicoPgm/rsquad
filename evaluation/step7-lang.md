# Evaluation replay

**3 scorable case(s) of 3 in the set.**

This report does not contain a detection rate and cannot: the verdict line under
each case is a human judgement. Fill them in, then read the fractions below with
their denominators visible — never as a percentage. On a handful of cases a 25 %
rate and a 75 % one are the same measurement.

## `lang-surrogate-false-match`

The high-surrogate guard in containsAny/containsNone/indexOfAny short-circuits on `!isHighSurrogate(ch)`, so a lone LOW surrogate matches the low half of a search pair.

| | |
|---|---|
| introduced in | `fed6260161083f3e4a95b58883087381ee653327` |
| file | `src/main/java/org/apache/commons/lang3/StringUtils.java` |
| detectable from diff | weak |

9 finding(s) survived refutation:

- **`src/main/java/org/apache/commons/lang3/StringUtils.java:1094`** — correctness
  `if (!Character.isHighSurrogate(ch) || j == searchLast || i < csLast && searchChars[j + 1] == cs.charAt(i + 1)) {`
  Returns true even though the text contains no U+20000 code point; the low surrogate is matched in isolation. The removed branch (`j == 0 || !isLowSurrogate(ch) || !isHighSurrogate(searchChars[j-1]) || ...`) suppressed exactly this, so the pair-matching done for high surrogates is now one-sided: a lone low surrogate reports a false positive.

- **`src/main/java/org/apache/commons/lang3/StringUtils.java:1264`** — correctness
  `if (!Character.isHighSurrogate(ch) || j == searchLast || i < csLast && searchChars[j + 1] == cs.charAt(i + 1)) {`
  Returns false ("contains an invalid char") although the text contains none of the searched code points; the second half of a searched surrogate pair now matches on its own, where the previous low-surrogate branch rejected it.

- **`src/main/java/org/apache/commons/lang3/StringUtils.java:2838`** — correctness
  `if (!Character.isHighSurrogate(ch) || j == searchLast || i < csLast && searchChars[j + 1] == cs.charAt(i + 1)) {`
  Returns 1 instead of -1: reports the index of an isolated low surrogate as a hit for a supplementary code point that is not present in the input.

- **`src/main/java/org/apache/commons/lang3/StringUtils.java:1094`** — correctness
  `if (!Character.isHighSurrogate(ch) || j == searchLast || i < csLast && searchChars[j + 1] == cs.charAt(i + 1)) {`
  returns true: at i=1 the lone low surrogate '\uDC00' equals searchChars[1] and, because ch is not a high surrogate, the first disjunct short-circuits to true. The removed branch previously required the preceding cs char to equal the paired high surrogate searchChars[j-1], so this returned false. Half of a surrogate pair now counts as a match for a supplementary search character.

- **`src/main/java/org/apache/commons/lang3/StringUtils.java:1264`** — correctness
  `if (!Character.isHighSurrogate(ch) || j == searchLast || i < csLast && searchChars[j + 1] == cs.charAt(i + 1)) {`
  returns false (reports the string as containing an invalid char) although U+20000 does not occur; the match is only on the shared low surrogate '\uDC00' at i=1, which the deleted low-surrogate guard used to reject. Callers using containsNone as a validity check reject valid input.

- **`src/main/java/org/apache/commons/lang3/StringUtils.java:2838`** — correctness
  `if (!Character.isHighSurrogate(ch) || j == searchLast || i < csLast && searchChars[j + 1] == cs.charAt(i + 1)) {`
  returns 1 instead of -1: the lone low surrogate matches searchChars[1] and the new first disjunct accepts it without checking that cs.charAt(i-1) equals the paired high surrogate searchChars[j-1]. The reported index also points into the middle of a code point that is not the searched-for character.

- **`src/main/java/org/apache/commons/lang3/StringUtils.java:1094`** — correctness
  `if (!Character.isHighSurrogate(ch) || j == searchLast || i < csLast && searchChars[j + 1] == cs.charAt(i + 1)) {`
  returns true; previously the removed low-surrogate branch required the preceding char of cs to match searchChars[j-1], so a lone low surrogate did not match a search pair and the method returned false. Half a surrogate pair is now reported as a match.

- **`src/main/java/org/apache/commons/lang3/StringUtils.java:1264`** — correctness
  `if (!Character.isHighSurrogate(ch) || j == searchLast || i < csLast && searchChars[j + 1] == cs.charAt(i + 1)) {`
  returns false (claims the invalid supplementary char is present) whereas before the change it returned true, because matching a bare low surrogate no longer requires the preceding high surrogate to match.

- **`src/main/java/org/apache/commons/lang3/StringUtils.java:2838`** — correctness
  `if (!Character.isHighSurrogate(ch) || j == searchLast || i < csLast && searchChars[j + 1] == cs.charAt(i + 1)) {`
  returns 1 instead of -1: the index of an unpaired low surrogate is reported as a match for the supplementary code point search sequence.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `lang-strbuilder-empty-search`

`lastIndexOf(String)` starts the search at `size - 1`, so an empty search string is never found at the end position where it belongs.

| | |
|---|---|
| introduced in | `1b1f8eba3c59f8ab702d1c28c08d255998d13c9a` |
| file | `src/main/java/org/apache/commons/lang3/text/StrBuilder.java` |
| detectable from diff | weak |

3 finding(s) survived refutation:

- **`src/main/java/org/apache/commons/lang3/text/StrBuilder.java:2365`** — boundary
  `return lastIndexOf(str, size - 1);`
  The empty-string search now starts at size-1 instead of size, so "abc".lastIndexOf("") returns 2 instead of 3, and on an empty builder startIndex becomes -1 so it returns -1 instead of 0 — both differ from String.lastIndexOf semantics and from the pre-change result. For non-empty needles the result is unchanged, so the empty needle is the only reachable difference.

- **`src/main/java/org/apache/commons/lang3/text/StrBuilder.java:2365`** — boundary
  `return lastIndexOf(str, size - 1);`
  Returns size - 1 (4) instead of size (5) for the empty search string, and returns -1 instead of 0 on an empty builder, because the two-arg overload delegates to Strings.CS.lastIndexOf whose startIndex is the maximum match *start* position and which clamps an empty needle to min(startIndex, length) and rejects a negative startIndex. This diverges from String.lastIndexOf("") which yields length, and from the previous behaviour of this method.

- **`src/main/java/org/apache/commons/lang3/text/StrBuilder.java:2365`** — boundary
  `return lastIndexOf(str, size - 1);`
  Returns 2 instead of 3 for "abc" (String.lastIndexOf("") semantics return length), and returns -1 instead of 0 for the empty builder, because the delegate Strings.CS.lastIndexOf is called with startIndex = -1.

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `lang-bitfield-sign-extension`

`getValue` uses an arithmetic shift `>>` on a masked field, so a field including the top bit is sign-extended and comes back negative.

| | |
|---|---|
| introduced in | `4da246dbbd0c3e6a21011cf691d7d18c7e561b7c` |
| file | `src/main/java/org/apache/commons/lang3/BitField.java` |
| detectable from diff | yes |

8 finding(s) survived refutation:

- **`src/main/java/org/apache/commons/lang3/BitField.java:199`** — correctness
  `return getRawValue(holder) >> shiftCount;`
  the arithmetic shift sign-extends: 0xFF000000 >> 24 == -1, so getValue returns -1 instead of 255 (the previous >>> produced 255). Any mask whose highest set bit is bit 31 (e.g. 0x80000000 returns -1 instead of 1, 0xF0000000 returns -1 instead of 15) now yields a negative result, breaking the setValue/getValue round trip.

- **`src/main/java/org/apache/commons/lang3/BitField.java:215`** — correctness
  `return getRawValue(holder) >> shiftCount;`
  sign extension makes the result -1 instead of 255; likewise mask 0x8000000000000000L with holder Long.MIN_VALUE returns -1 instead of 1, so getValue no longer inverts setValue for any mask that includes bit 63.

- **`src/main/java/org/apache/commons/lang3/BitField.java:199`** — boundary
  `return getRawValue(holder) >> shiftCount;`
  getValue returns -1 instead of 255 (arithmetic shift sign-extends), so setValue/getValue no longer round-trip for any int mask that includes bit 31; previously >>> returned 255. Single-bit case new BitField(0x80000000).getValue(0x80000000) returns -1 instead of 1.

- **`src/main/java/org/apache/commons/lang3/BitField.java:215`** — boundary
  `return getRawValue(holder) >> shiftCount;`
  getValue returns -1 instead of 255, breaking the setValue(long,long)/getValue(long) round-trip for any long mask including bit 63; the single-bit mask 0x8000000000000000L with holder Long.MIN_VALUE now returns -1 instead of 1.

- **`src/main/java/org/apache/commons/lang3/BitField.java:199`** — correctness
  `return getRawValue(holder) >> shiftCount;`
  getRawValue returns the int 0xFF000000, which is negative, so the arithmetic shift sign-extends and the method returns -1 instead of 255 (previously, with >>>, it returned 255). Any mask including bit 31 now yields negative/garbage field values.

- **`src/main/java/org/apache/commons/lang3/BitField.java:215`** — correctness
  `return getRawValue(holder) >> shiftCount;`
  getRawValue returns a negative long, so the arithmetic shift sign-extends and the method returns -1 instead of 255; every long mask that covers bit 63 now reports negative field values.

- **`src/main/java/org/apache/commons/lang3/BitField.java:199`** — correctness
  `return getRawValue(holder) >> shiftCount;`
  arithmetic shift sign-extends: returns -1 instead of 255 (the previous >>> gave 255); every mask that includes bit 31 now yields negative/garbage field values

- **`src/main/java/org/apache/commons/lang3/BitField.java:215`** — correctness
  `return getRawValue(holder) >> shiftCount;`
  arithmetic shift sign-extends: returns -1 instead of 1; any long mask including bit 63 returns a negative value where the field value is expected

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## Excluded from scoring, and why

| case | reason |
|---|---|

## To total it

- **detected / 3 scorable** — the headline, as a fraction.
- **findings that were not the known defect** — not errors (a genuine second bug
  is not a false positive), but the number that bounds a reader's cost, and the
  one that decides whether anyone keeps using this.

Nothing here measures a false-positive rate: every case is a diff known to
contain a defect. That needs the opposite corpus — clean commits — and it is
arguably the more useful of the two.

---

Model `claude-opus-5`, 33 call(s) across 3 case(s), 2.6088 USD billed. cache read 50540 tokens against 5605 written
