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

{{CONTEXT}}{{ELISION}}Now try to kill the claim. If you cannot, say `stands` and quote what stopped you.
