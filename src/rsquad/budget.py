"""Token accounting. What a review actually cost, never what it should have cost.

The source project learned this twice, expensively: a cost constant that was invented rather
than measured ran 2.3x low, and one derived from a bench that did not generalise ran 59 % low.
Both are in `evaluation/defects.yaml`. So nothing here estimates — it reports what the API
billed, and the only number this module will print is one that came back in a response.
"""

from __future__ import annotations

from dataclasses import dataclass

#: USD per million tokens, (input, output). First-party API rates.
TARIFFS = {
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}

#: Multipliers on the input rate.
CACHE_READ = 0.1
CACHE_WRITE = 1.25


@dataclass
class Spend:
    input_usd: float = 0.0
    output_usd: float = 0.0
    cache_write_usd: float = 0.0
    cache_read_usd: float = 0.0

    @property
    def total(self) -> float:
        return self.input_usd + self.output_usd + self.cache_write_usd + self.cache_read_usd


def cost(model: str, usage) -> Spend:
    """What one response cost. Unknown model -> zero, loudly absent rather than guessed."""
    rates = TARIFFS.get(model)
    if rates is None:
        return Spend()
    per_in, per_out = (r / 1_000_000 for r in rates)
    return Spend(
        input_usd=usage.input_tokens * per_in,
        output_usd=usage.output_tokens * per_out,
        cache_write_usd=usage.cache_creation_input_tokens * per_in * CACHE_WRITE,
        cache_read_usd=usage.cache_read_input_tokens * per_in * CACHE_READ,
    )


def total(model: str, usages) -> Spend:
    spend = Spend()
    for usage in usages:
        one = cost(model, usage)
        spend = Spend(spend.input_usd + one.input_usd, spend.output_usd + one.output_usd,
                      spend.cache_write_usd + one.cache_write_usd,
                      spend.cache_read_usd + one.cache_read_usd)
    return spend


def cache_verdict(usages) -> str:
    """Whether the cached prefix is actually being reused.

    Zero reads across several calls that share a prefix means a silent invalidator — the usual
    culprits being a timestamp in the system text, an unsorted dict, or a breakpoint placed
    after something variable. Worth surfacing: the failure is invisible except in the bill.
    """
    reads = sum(u.cache_read_input_tokens for u in usages)
    writes = sum(u.cache_creation_input_tokens for u in usages)
    if not writes and not reads:
        return "cache never engaged - prefix below the model's minimum, or absent"
    if not reads:
        return "cache written but never read - a silent invalidator is at work"
    return "cache read %d tokens against %d written" % (reads, writes)
