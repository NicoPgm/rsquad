<!-- One claim under test. Everything here varies, so it sits after the cache breakpoint. -->

## The claim

In `{{FILE}}`, at line {{LINE}}:

```
{{SNIPPET}}
```

- **Given these inputs** — {{INPUTS}}
- **the claim is that** — {{CONSEQUENCE}}

## What the change did to the file

```diff
{{DIFF}}
```

## The file as it now stands

Line numbers are on the left, separated by a tab. Use them for `evidence_line`, and copy
`evidence_snippet` from the text to their right — without the number.

```
{{NUMBERED}}
```

## The rest of the repository

The whole repository, as it stands after this change, is checked out in the `repo/` directory of this job: the directory that holds `round-1/` and `schema/`. You may read and search any file there to see how the code under review is called, what it calls, what the project declares (dependencies, configuration, its own written conventions), and what the changed code relies on. Read what you need, not everything. Use it to check the claim against the code it depends on; your evidence must still be quoted from the numbered file above.

{{CONTEXT}}{{ELISION}}Now try to kill the claim. If you cannot, say `stands` and quote what stopped you.
