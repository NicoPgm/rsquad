<!-- Lens: bounds. Placed after the cache breakpoint. -->

Your lens is **boundaries**.

Take every collection, range, index, slice, counter, timeout and limit the change touches, and
push each one to its edge.

Look for:

- empty, exactly one, and exactly the maximum
- an index or slice computed from a length, off by one
- a division or a percentage whose denominator can be zero
- a range whose end is exclusive where the code treats it as inclusive, or the reverse
- a window, page or batch whose last chunk is a different size
- a comparison that is `<` where it must be `<=`, at the one value where it matters
- a default that is only correct for the common case

Name the exact value at which the behaviour changes. "For a large list" is not a boundary;
"when `len(items) == 0`" is.
