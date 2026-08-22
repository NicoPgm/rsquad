"""RSquad — a review squad built in a deliberate order.

    [0] MECHANICAL GATE   no agent. Tests, types, lint, and: does a new test fail
                          against the code as it was? A failure here stops everything;
                          nothing reaches the lenses.
    [1] CONFORMANCE LENS  one agent, WITH the spec. "Does the diff do what the spec says?"
    [2] BLIND LENSES      n agents, WITHOUT the spec. repro / bounds / contract / test quality.
    [3] REFUTATION        one agent per finding, separate context. Its job is to kill it.
                          Doubt means refuted.
    [4] RANKED QUEUE      for a human. Not a verdict.

The order carries the design. Only step [0] may block; opinions comment.
"""

__version__ = "0.1.0"
