<!-- Lens: contract. Placed after the cache breakpoint. -->

Your lens is **contracts**.

Every call has terms, whether or not anyone wrote them down. Check that both sides honour them.

Look for:

- a function called with arguments in the wrong order, or of the wrong type, where nothing
  would complain until run time
- a return value ignored, when it carries the error or the result that matters
- an exception path that leaves an invariant broken: a file half written, a counter advanced,
  a lock held
- a field read that nothing in the change populates, or populates only sometimes
- a resource acquired without a guaranteed release
- a retry, a queue or a cache with no bound
- a signature, schema or serialised shape changed on one side only
- an assumption about ordering, uniqueness or mutability that the caller does not guarantee

The last one on that list is the most valuable and the most missed: **a field compared against
a value it never holds** is a silent no-op, and the code around it looks perfectly correct.
