<!-- The whole pull request, one section per file. Variable, after the cache breakpoint. -->

Files under review: {{FILES}}

You are shown every file of this change that your lens reads, so that a defect spanning
files is visible: a call whose meaning is defined in another file, an order of operations
split across two, a value produced here and consumed there. In each section, line numbers
are on the left, separated by a tab. Use them for `line`, and copy `snippet` from the text
to their right, without the number.

## The rest of the repository

The whole repository, as it stands after this change, is checked out in the `repo/`
directory of this job: the directory that holds `round-1/` and `schema/`. Investigate before
you answer: read and search it to see how the changed code is called, what it calls, what the
project declares (dependencies, configuration, its own written conventions), and how sibling
code does the same thing. Read what you need, not everything.

A defect that lives in a file outside the change is reported in that file, at the line where
it lives: its path as `file`, and `line` and `snippet` from that file as it stands in `repo/`.
The change did not touch that file, so such a defect is `exposed` or `pre-existing`, never
`introduced`.

{{SECTIONS}}

Each finding's `file` is one of these files or, for a defect outside the change, another
file of `repo/`; its `line` and `snippet` come from that file. Report a defect that spans
files at the line where it shows; if it shows in several files, report it once in each. If
there is nothing to report, return an empty list.
