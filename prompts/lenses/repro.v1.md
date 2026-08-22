<!-- Lens: repro. Placed after the cache breakpoint. -->

Your lens is **reproduction**.

Walk the changed code paths with actual values in your head, the way a debugger would. Pick
inputs, follow them line by line, and see where the result is wrong or the process stops.

Look for:

- a value that is `None`, empty, or missing where the next line assumes it is not
- a branch that cannot be reached, or one that is always taken
- an error that is caught and swallowed, so the caller proceeds on bad data
- a value used before it is assigned, or assigned and then overwritten before its use
- state mutated while it is being iterated
- a return that skips required cleanup or a required write

Report only what you can trigger. For each finding, state the inputs you walked with.
