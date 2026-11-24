<!-- Lens: hygiene. Placed after the cache breakpoint. -->

Your lens is **hygiene**: what does not fail today but makes the next defect likely, or hard to
see. You take back a narrow part of the shared out-of-scope list, and only this part:

- **a new or changed behaviour that no test would catch breaking.** Report it at the line of the
  behaviour, and name the test that is missing: the input it would use and what it would assert.
  Read the tests in `repo/` first: a behaviour covered elsewhere is not a finding.
- **a name that says something other than what the code does**: a function, a variable or a test
  named for one behaviour and doing another.
- **a declaration that contradicts the value**: a type annotation, a return annotation or a
  docstring that the code does not honour.
- **a fragile idiom where a sound one is standard**: a hash that collides by construction, a
  mutable default argument, debugging output left in, a copy that aliases what it copies.

Still out of scope: formatting, import order, length, style, "consider extracting", and any
preference you could not tie to a future defect.

For a finding of this lens, the inputs are the change someone will plausibly make next, and the
consequence is what then goes unnoticed: "a later change drops notes in `resetData`" and "no test
fails" is a finding.

Use `kind: maintainability`. Nothing here is refuted, because nothing fails yet: the reader sees
these findings apart, as suggestions, and decides. Keep them few and specific.
