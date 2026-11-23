<!-- One file, checked against the stated intent. Everything here varies. -->

## The stated intent

Everything below is what this change said it would do. It is the **only** source you may quote a
requirement from.

{{INTENT}}

---

File under review: `{{FILE}}`

## What the change did to it

```diff
{{DIFF}}
```

## The file as it now stands

Line numbers are on the left, separated by a tab. Use them for `line`, and copy `snippet` from
the text to their right — without the number.

```
{{NUMBERED}}
```

## The rest of the repository

The whole repository, as it stands after this change, is checked out in the `repo/` directory of this job: the directory that holds `round-1/` and `schema/`. You may read and search any file there to see how the code under review is called, what it calls, what the project declares (dependencies, configuration, its own written conventions), and what the changed code relies on. Read what you need, not everything. A divergence may depend on another file, but it must still be reported at a line of `{{FILE}}`, with a snippet copied from the numbered file above.

{{CONTEXT}}{{ELISION}}Report divergences between the intent above and `{{FILE}}` only. If the change does what it said,
return an empty list — that is the usual answer.
