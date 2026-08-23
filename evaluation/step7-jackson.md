# Evaluation replay

**3 scorable case(s) of 3 in the set.**

This report does not contain a detection rate and cannot: the verdict line under
each case is a human judgement. Fill them in, then read the fractions below with
their denominators visible — never as a percentage. On a handful of cases a 25 %
rate and a 75 % one are the same measurement.

## `jackson-stale-readonly-cache`

`addTypedSerializer` invalidates the read-only copy only when the key was absent (`put(...) == null`), so REPLACING a typed serializer leaves a stale copy in service.

| | |
|---|---|
| introduced in | `f319627edad9ab4993d165da0bb2a810764751bd` |
| file | `src/main/java/tools/jackson/databind/ser/SerializerCache.java` |
| detectable from diff | yes |

7 finding(s) survived refutation:

- **`src/main/java/tools/jackson/databind/ser/SerializerCache.java:246`** — correctness
  `if (_sharedMap.put(new TypeKey(type, true), ser) == null) {`
  _sharedMap.put returns serA (non-null), so _readOnlyMap is not cleared; getReadOnlyLookupMap() keeps handing out the snapshot containing serA, and serialization keeps using the replaced serializer instead of serB until some unrelated *new* key is cached (which may never happen after warmup). Before the change the snapshot was always invalidated and serB took effect.

- **`src/main/java/tools/jackson/databind/ser/SerializerCache.java:246`** — correctness
  `if (_sharedMap.put(new TypeKey(type, true), ser) == null) {`
  _readOnlyMap is not reset, so the cached ReadOnlyClassToSerializerMap keeps serving the superseded ser1 for that type while _sharedMap holds ser2; the two maps stay divergent until some unrelated first-time insertion or flush() happens to clear the snapshot.

- **`src/main/java/tools/jackson/databind/ser/SerializerCache.java:254`** — correctness
  `if (_sharedMap.put(new TypeKey(cls, true), ser) == null) {`
  The read-only snapshot is not invalidated, so lookups through getReadOnlyLookupMap() continue returning the replaced ser1 instead of ser2 indefinitely.

- **`src/main/java/tools/jackson/databind/ser/SerializerCache.java:246`** — correctness
  `if (_sharedMap.put(new TypeKey(type, true), ser) == null) {`
  LookupCache.put returns the previous value (serA), which is non-null, so _readOnlyMap is never set to null. The stale read-only snapshot keeps returning serA for that type to every consumer that obtains it (e.g. SerializationContext's known-serializers map) until some unrelated new key or flush() invalidates it; serB is only visible via the slow _sharedMap path.

- **`src/main/java/tools/jackson/databind/ser/SerializerCache.java:254`** — correctness
  `if (_sharedMap.put(new TypeKey(cls, true), ser) == null) {`
  put returns serA (non-null), so the read-only snapshot is not invalidated and continues to hand out serA for TypeKey(SomeClass, true) even though _sharedMap now holds serB, producing serialization with the superseded serializer until an unrelated insertion or flush() clears the snapshot.

- **`src/main/java/tools/jackson/databind/ser/SerializerCache.java:246`** — correctness
  `if (_sharedMap.put(new TypeKey(type, true), ser) == null) {`
  put() returns serA (non-null), so _readOnlyMap is not cleared and the stale snapshot keeps serving serA; subsequent lookups through the read-only map return the old serializer instead of serB indefinitely

- **`src/main/java/tools/jackson/databind/ser/SerializerCache.java:254`** — correctness
  `if (_sharedMap.put(new TypeKey(cls, true), ser) == null) {`
  the replacement is written to _sharedMap but the read-only snapshot is not invalidated, so readers continue to get serA from the cached ReadOnlyClassToSerializerMap

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `jackson-map-empty-wrong-variable`

Inside a loop over entries, the NON_EMPTY check compares the suppressible value against `value` instead of `elemValue` — the wrong variable, twice.

| | |
|---|---|
| introduced in | `9d4d101e472a90be4f268d4d34a20658ee84143c` |
| file | `src/main/java/com/fasterxml/jackson/databind/ser/std/MapSerializer.java` |
| detectable from diff | yes |

8 finding(s) survived refutation:

- **`src/main/java/com/fasterxml/jackson/databind/ser/std/MapSerializer.java:654`** — correctness
  `} else if ((supp == null) || !supp.equals(value)) {`
  `supp.equals(value)` compares the suppressable value "" against the whole Map object instead of the element "", so it is never equal; the method returns false instead of true, and the map is written out even though every entry holds the suppressed value.

- **`src/main/java/com/fasterxml/jackson/databind/ser/std/MapSerializer.java:678`** — correctness
  `} else if ((supp == null) || !supp.equals(value)) {`
  `supp.equals(value)` compares Integer 0 against the Map instance rather than the element 0, so the comparison always fails and isEmpty() returns false; the map is serialized instead of being suppressed.

- **`src/main/java/com/fasterxml/jackson/databind/ser/std/MapSerializer.java:654`** — correctness
  `} else if ((supp == null) || !supp.equals(value)) {`
  `supp.equals(value)` compares the suppressable value against the whole Map instance instead of the element, so it is never equal; the method returns false and `isEmpty()` reports the map as non-empty, so the property is serialized instead of being suppressed.

- **`src/main/java/com/fasterxml/jackson/databind/ser/std/MapSerializer.java:678`** — correctness
  `} else if ((supp == null) || !supp.equals(value)) {`
  `supp.equals(value)` tests equality against the Map object rather than the entry value, so the branch always returns false; `isEmpty()` returns false for a map whose every value equals the suppressable value, defeating content suppression.

- **`src/main/java/com/fasterxml/jackson/databind/ser/std/MapSerializer.java:654`** — correctness
  `} else if ((supp == null) || !supp.equals(value)) {`
  `supp.equals(value)` compares the suppressable element value against the whole `Map<?,?>` instance, which can never be equal, so the branch always returns `false`; `isEmpty` reports the map as non-empty and the property is written out instead of being suppressed.

- **`src/main/java/com/fasterxml/jackson/databind/ser/std/MapSerializer.java:678`** — correctness
  `} else if ((supp == null) || !supp.equals(value)) {`
  `supp.equals(value)` tests the suppressable value against the Map object rather than the element, is always false, so the method returns `false` and the map is never treated as empty even when every entry holds the suppressable value.

- **`src/main/java/com/fasterxml/jackson/databind/ser/std/MapSerializer.java:654`** — correctness
  `} else if ((supp == null) || !supp.equals(value)) {`
  supp.equals(value) compares the suppressable value against the whole Map instead of the element, so it is never equal and isEmpty() returns false; the map is serialized instead of being suppressed

- **`src/main/java/com/fasterxml/jackson/databind/ser/std/MapSerializer.java:678`** — correctness
  `} else if ((supp == null) || !supp.equals(value)) {`
  supp is compared to the Map rather than each element value, so the comparison always fails and isEmpty() returns false, causing the map to be emitted despite all values matching the suppression value

**Detected?** `?` — replace with `yes` or `no`. It counts as detected only if a
finding above anchors at the defect **and** its consequence describes the actual
failure. A finding that points at the right line for the wrong reason is a
coincidence, and counting it inflates every later number.

## `jackson-builder-cache-defaults`

Three Builder fields documented as "Maximum Size of the LookupCache instance" have no initialiser, so the builder defaults every cache size to 0.

| | |
|---|---|
| introduced in | `38fffc4cacbf3e57f93d7117187db1693a841c84` |
| file | `src/main/java/tools/jackson/databind/cfg/DefaultCacheProvider.java` |
| detectable from diff | weak |

4 finding(s) survived refutation:

- **`src/main/java/tools/jackson/databind/cfg/DefaultCacheProvider.java:135`** — contract
  `private int _maxDeserializerCacheSize;`
  Unset fields are now 0 instead of DeserializerCache.DEFAULT_MAX_CACHE_SIZE / SerializerCache.DEFAULT_MAX_CACHE_SIZE / TypeFactory.DEFAULT_MAX_CACHE_SIZE, so build() (documented as "using defaults where not specified") returns a provider whose _buildCache(0) creates SimpleLookupCache<>(0, 0): the deserializer/serializer/type caches retain nothing and every lookup re-constructs the value, silently disabling caching.

- **`src/main/java/tools/jackson/databind/cfg/DefaultCacheProvider.java:211`** — boundary
  `return new DefaultCacheProvider(_maxDeserializerCacheSize, _maxSerializerCacheSize, _maxTypeFactoryCacheSize);`
  The unset field is now 0 instead of the DEFAULT_MAX_CACHE_SIZE constant, so _buildCache(0) creates SimpleLookupCache(0, 0) and that cache retains nothing: every deserializer/serializer/type lookup is recomputed on each call. The javadoc on build() ("using defaults where not specified") no longer holds.

- **`src/main/java/tools/jackson/databind/cfg/DefaultCacheProvider.java:135`** — contract
  `private int _maxDeserializerCacheSize;`
  The unset builder fields are now Java-default 0 instead of DeserializerCache/SerializerCache/TypeFactory.DEFAULT_MAX_CACHE_SIZE, so build() passes 0 into the DefaultCacheProvider constructor and _buildCache(0) creates a SimpleLookupCache(0, 0): the corresponding cache retains nothing, contradicting build()'s documented "using defaults where not specified" and silently disabling deserializer/serializer/type-factory caching.

- **`src/main/java/tools/jackson/databind/cfg/DefaultCacheProvider.java:135`** — correctness
  `private int _maxDeserializerCacheSize;`
  the unset fields default to 0 instead of DeserializerCache.DEFAULT_MAX_CACHE_SIZE / SerializerCache.DEFAULT_MAX_CACHE_SIZE / TypeFactory.DEFAULT_MAX_CACHE_SIZE, so _buildCache(0) creates SimpleLookupCache(0, 0) and no serializers/deserializers/types are ever retained, destroying caching performance (and contradicting build()'s documented 'using defaults where not specified')

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

Model `claude-opus-5`, 31 call(s) across 3 case(s), 2.4492 USD billed. cache read 53143 tokens against 0 written
