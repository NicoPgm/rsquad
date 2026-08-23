# Porting to another stack

The core knows no language. Everything a stack changes fits into seven questions, one abstract
class, `gate/adapters/base.py`.

> **One adapter has ever been executed: Python with pytest.** The per-stack catalogue at the
> bottom of this document is **hypotheses**, written from how those ecosystems resolve code, not
> from runs. Treat every row as a place to look, never as an answer. The Python answers were
> found by running the gate and watching it be wrong — three times, each time while looking
> green.

## Before the seven questions: the one rule

**Every defect in the original gate implementation was found by execution. None by review.** That
is not a remark about code quality; it is the shape of the problem. A gate that is wrong reports
success. It does not crash, it does not warn, and reading it will not tell you — a wrong
question 4 makes every test "valid" and the run looks like a clean bill of health.

So the porting procedure is not "implement seven methods". It is:

1. Implement the seven methods, however crudely.
2. **Replay against real history** — `rsquad gate --replay 20` — and read the *examined* count
   before the verdict.
3. Hand-verify three commits: one that modified a test, one that added a test file, one that
   touched nothing.
4. Only then trust a number.

Step 3 is where the port is actually validated. Everything before it is typing.

## The seven questions

### 1. Which files in the diff are tests?

Cheap, and the only one that is nearly always obvious. Python answers `path.endswith(".py")`,
because `watched_paths` already restricted the diff to `tests/`.

**Where it goes wrong:** stacks that colocate tests with sources (`src/foo.ts`,
`src/foo.test.ts`) cannot lean on a directory, so the filename predicate carries the whole
decision. Get it too wide and non-test files enter the gate; too narrow and it goes silent.

### 2. Which test functions are new or modified?

By comparing **function bodies across revisions**, never file-level granularity.

File-level is not merely coarse, it is fatal. On a touched file every pre-existing test gets
examined and reported suspect — because it passes on the base, which is its job. Measured on a
real commit: **35 false positives against 6 genuine findings.**

Python parses with `ast` and compares source text rather than an AST dump, deliberately: a
loosened `@pytest.mark.parametrize` case changes the test without changing its body.

**Where it goes wrong:**

- **The test name may not be an identifier.** In Jest, Vitest, RSpec and Mocha a test is a
  function call with a string literal — `test('handles empty input', () => {...})`. There is no
  declaration to parse and the name that reaches the JUnit report is that string, possibly after
  the runner concatenates enclosing `describe` blocks. Both the extraction and the later name
  match have to agree on the same rendering, or every exemption and every filter silently misses.
- **A regex will get you started and then lie.** Nested closures, template literals and
  `describe` nesting are exactly where it breaks, and it breaks by matching too little — silence,
  not noise.

### 3. How do we run that subset so it emits JUnit XML?

JUnit XML is the portable seam. pytest, Jest, Vitest, Surefire, gotestsum and .NET all emit it,
and it distinguishes `<failure>` (an assertion) from `<error>` (a crash during collection or
setup).

The command has one hard requirement: **it must not abort the whole run on a collection error.**
On the base, a brand-new test file is *always* uncollectable — it imports symbols that do not
exist yet. Python needs `--continue-on-collection-errors` for this; without it pytest runs
nothing and reports only the error, so the gate falls silent at precisely the moment it would
earn its keep.

Find your stack's equivalent before anything else. If there is none, question 5 below becomes
much larger.

### 4. How do we guarantee the code under test is the base's?

**This is the trap, and it is different in every ecosystem.**

Python: the package is installed editable and points at the main checkout's `src/`, so without
`PYTHONPATH` set to the worktree, pytest imports the **new** code and the gate validates
everything. Measured: 22 tests green while running against the code from after.

The failure mode is always the same and always silent. You do not get an error; you get a gate
that says everything is fine.

**How to know you got it right, mechanically:** take a commit that fixes a bug, replay the gate,
and confirm the new test is reported *valid* — i.e. it failed on the base. If a bug-fix commit's
test does not fail on the base, question 4 is wrong. This check costs one command and is the only
one that actually proves the isolation.

### 5. Which base failures mean "the symbol does not exist yet"?

The seam is not quite where it looks. A symbol that does not exist yet lands on either side of
`<failure>`/`<error>` depending on how the test names it:

```
from mod import thing          -> fails at collection  -> <error>   -> no signal
import mod ... mod.thing(...)  -> fails in the body    -> <failure> -> "valid"
```

Same missing symbol, opposite verdicts, decided by import style. Left alone, the gate
over-reports `valid`. Fixing this in the Python adapter moved the measured coverage from 43 % to
**21 %** — the published figure was more than double the truth (`gate-baseline.md`).

The default answers "no" — every failure discriminates — which is wrong in the safe direction: it
over-counts `valid` rather than discarding real findings.

**Override it narrowly.** The risk is the false negative. Python matches a small allowlist of
message shapes:

```
ModuleNotFoundError:        ImportError:
NameError: name 'x' is not defined
AttributeError: module 'x' has no attribute 'y'
```

That last row is why it is an allowlist and not "any `AttributeError`".
`AttributeError: 'NoneType' object has no attribute 'y'` is a test catching a real defect, and
discarding it would be worse than the problem being fixed.

### 6. Which definitions elsewhere does a change reference?

The context pack (ADR-0004): the definitions of first-party symbols the changed lines name,
resolved deterministically, so a lens can check how a change uses its neighbours without being
handed file-reading tools.

Two constraints bind any implementation:

- **Deterministic.** Same revision and same diff must give the same definitions in the same
  order. A pack that varies cannot be replayed, and a squad that cannot be replayed cannot be
  measured.
- **Symbol-driven, never directory-driven.** Follow what the change references. A resolver that
  walks the tree could reach a specification, and blindness would stop being a property of the
  mechanism.

The default resolves nothing, which is the honest behaviour for a stack nobody has taught it: a
smaller pack, never a wrong one.

Measured on Python, 34 changed files: **65 % resolve at least one definition, 3.2 on average.**
Leaf modules resolve nothing and need nothing; orchestration files resolve the most and need it
most.

### 7. What will the runner call the module a test lives in?

`tests/sub/test_beta.py` → `tests.sub.test_beta`, which is what pytest writes into the JUnit
`classname`. Verified against a real report rather than assumed: a method in a class gets the
class appended (`tests.test_alpha.TestGrouped`), so the core matches the module as a **dotted
prefix**, not by equality.

Without it a test name carries no file, and two files each holding a `test_roundtrip` are the
same test: touch one and the other is examined and reported suspect for passing on the base —
which is its job.

**The default returns the path unchanged**, which no dotted classname will ever match. The core
decides once per report whether the convention is recognised and, if not, falls back to matching
bare names — the behaviour that existed before files were tracked. A stack nobody has taught this
gets today's noise, never silence. That direction is not a detail: a gate that examines nothing
reports "0 suspect", which reads as a clean bill of health.

### And assume an eighth

Questions 5, 6 and 7 all arrived *after* the protocol was declared complete — one from a crash,
one from a conversation, one from the squad reviewing this gate's own ancestor. The protocol has
been "finished" three times.

## The catalogue — hypotheses, not answers

Read every cell as "look here first".

### JavaScript / TypeScript, Jest or Vitest

| | Hypothesis |
|---|---|
| 1 | `.test.*` / `.spec.*` / `__tests__/`; tests colocate with sources, so the filename carries everything |
| 2 | **Hardest of any stack listed.** Tests are calls with string names; needs a real parser, and the extracted name must match the runner's `describe > test` concatenation exactly |
| 3 | `jest --reporters=jest-junit`, `vitest --reporter=junit`. Both continue past a failed import by default — verify, do not assume |
| 4 | **Two traps, not one.** `node_modules` resolution and workspace symlinks reaching back to the main checkout; and any build step — if tests run against `dist/`, a stale `dist/` built from head is the editable-install failure wearing different clothes. Also `tsconfig` path aliases pointing at absolute locations |
| 5 | `Cannot find module`, `ReferenceError: x is not defined`. **Do not match `TypeError: x is not a function`** — that is also what a real defect looks like |
| 6 | Resolution must honour `tsconfig` paths and package `exports`; more configuration-driven than Python, so expect a lower resolve rate |
| 7 | Jest and Vitest write the file path, not a dotted module, into `classname` — so the prefix rule may not apply and the fallback may be all you get |

### Java, Maven / Surefire

| | Hypothesis |
|---|---|
| 1 | `src/test/java/**` |
| 2 | Methods annotated `@Test`; needs a Java parser. Names are identifiers, which makes this easier than JS |
| 3 | `mvn -Dtest=... test` writes `target/surefire-reports/*.xml` without asking |
| 4 | The base worktree must be **compiled**, so this is not a path variable but a build. And a locally installed artifact of the project in `~/.m2` can shadow the worktree |
| 5 | **This question may not exist in the same form.** A missing symbol is a *compilation* failure, so the base run produces no report at all rather than a classifiable failure. The core currently treats a missing report as `RunnerFailed` — correct for "the runner never started", wrong for "the base could not compile, which is exactly what a new test should do". **This is the deepest unknown in the catalogue** and probably needs a core change, not just an adapter |
| 6 | Imports are explicit and resolvable; likely the best resolve rate of any stack here |
| 7 | Surefire writes the fully-qualified class name, which is the closest of any stack here to what the core expects |

### Go

| | Hypothesis |
|---|---|
| 1 | `_test.go` |
| 2 | `func TestXxx(t *testing.T)` via `go/ast` — in the standard library, so the cheapest question 2 on this list |
| 3 | `gotestsum --junitfile` |
| 4 | **Possibly nearly free**: the toolchain builds from the module directory, so a worktree is naturally isolated. Watch `replace` directives pointing at absolute paths, a `vendor/` directory, and `GOFLAGS` |
| 5 | Same structural problem as Java — a missing symbol fails the package build, and `gotestsum` reports a build failure rather than a test failure |
| 6 | Explicit imports, package-level resolution; should resolve well |

### C# / .NET

| | Hypothesis |
|---|---|
| 1 | `*Tests.cs`, or by test project |
| 2 | `[Fact]` / `[Test]` attributes; needs Roslyn or an equivalent parser |
| 3 | `dotnet test` emits `.trx` natively; JUnit XML needs a logger package or a conversion step. **The one stack on this list where the portable seam is not free** |
| 4 | NuGet cache and `ProjectReference` versus `PackageReference`; a project referencing a published package of itself would shadow the worktree |
| 5 | Compilation again — see Java |
| 6 | Namespaces resolve statically; should be tractable |

### Ruby / RSpec

| | Hypothesis |
|---|---|
| 1 | `_spec.rb` |
| 2 | String-named blocks, same problem as JS: `describe`/`it` nesting decides the reported name |
| 3 | `rspec --format RspecJunitFormatter` |
| 4 | `$LOAD_PATH` and a `Gemfile` with a `path:` source pointing at the main checkout |
| 5 | `NameError: uninitialized constant`, `NoMethodError: undefined method`. The second is dangerous — it is also what a real defect produces |
| 6 | Dynamic loading; expect the **lowest** resolve rate here, and accept an empty pack rather than guessing |

## The pattern across the catalogue

Two things repeat, and they are the useful output of writing it down:

**Interpreted languages have a question 5; compiled ones have a question 4½.** Where a missing
symbol is a build error, the base run yields nothing to classify — the whole run fails. The gate's
current core reads that as "the runner never started" and reports `RunnerFailed`, which is the
right answer to a different question. A compiled-language port has to distinguish "the base did
not build because the test references code that does not exist yet" — the expected, informative
case — from "the base did not build because something is broken". **That distinction does not
exist in the core today.** It is the first thing a Java or Go port will hit.

**Where the test name is a string, question 2 dominates the port.** JS, Ruby and anything
xUnit-by-block make the name a runtime value assembled from nesting. Everything downstream —
exemption markers, the changed-function filter, the JUnit name match — depends on reproducing
that assembly exactly, and every mismatch fails silently toward "nothing examined".

## Acceptance criterion for a port

The extraction of this gate from its original project was accepted on a mechanical criterion, and
a port should be too. Pick 20 commits of real history and require:

1. The **examined** count is non-zero and hand-checkable on three commits.
2. A known bug-fix commit's new test is reported **valid** — proving question 4 isolates.
3. A commit adding a whole new test file is reported **no signal**, not valid — proving question 5
   is doing its job.
4. A commit touching no tests is reported as touching no tests, not as clean.

Anything less and the number you publish will be the one you have to retract. The 47 % figure in
the original project survived two weeks and three defects before becoming 21 %.
