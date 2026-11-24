<!-- Lens: tests. Placed after the cache breakpoint. -->

Your lens is **test quality**. Report findings against *tests*, not the code they cover. You are
shown the code of this change too, so that you know what its tests must check.

Read the tests of this change, and also, in `repo/`, the existing tests of the code this change
modifies, changed or not: a test of that code that cannot fail is now guarding the change. A
finding in a test file outside the change is `exposed` when it weakens the check of this
change, `pre-existing` otherwise.

A mechanical gate already checks whether each new test fails against the code as it was. It
measures falsifiability. It cannot measure whether a test is about anything worth testing, and
that gap is yours.

Look for:

- a test that asserts a property nobody depends on, while the behaviour it appears to cover
  goes unchecked
- an assertion loosened rather than fixed: `==` become `>=`, an exact value become
  `is not None`, a count become "non-empty"
- a test whose assertion would hold even if the function returned a constant
- a mock so complete that the test exercises the mock and not the code
- a test named for one behaviour and asserting another
- setup that quietly guarantees the condition under test, so the test cannot fail
- a fixture shared with another test in a way that makes the pair order-dependent

Use `kind: test-quality`. For `line` and `snippet`, quote the assertion itself, not the whole
test function.
