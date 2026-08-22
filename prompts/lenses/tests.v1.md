<!-- Lens: tests. Placed after the cache breakpoint. -->

Your lens is **test quality**. Report findings against the *tests* in this change, not the code
they cover.

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
