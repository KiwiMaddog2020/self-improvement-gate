# self-improvement-gate

A safety contract for a self-improving agent loop, expressed as a pure,
fully-tested promotion gate.

When a loop is allowed to mine its own operating history and propose changes to
its own rules, something has to decide whether a proposed change may be promoted.
This is that decider. It is about 250 lines of standard-library Python with no
I/O: it reads a proposal's diff, evidence ledger, rater identity, and scores, and
returns a verdict. It never writes.

The write-up lives at
**https://kiwimaddog2020.github.io/self-improvement-gate/**.

## The five invariants

The oracle in [`tests/test_protocol_gate.py`](tests/test_protocol_gate.py)
defines the cage, and the gate exists to satisfy it:

1. **Un-collapsible.** A promotion clears MEASURE then PROVE then HOLD then LEARN,
   in order, and each reads a separate fact. No single check can be satisfied to
   wave a promotion through.
2. **Self-protecting.** A diff touching any gate-file glob is `blocked_gate_edit`,
   evaluated against the gate registry from the *trusted base revision*, never the
   candidate's own copy. The gate that edits a gate is rejected by the gate it
   edits, and this is checked before anything can pass.
3. **Cross-model, fail-closed.** A same-family or unknown-provenance rating never
   satisfies the gate; the families are supplied by the harness, never read from
   the proposal.
4. **Two bars.** High-stakes changes escalate to a human; everything else is
   auto-eligible only inside a narrow score band, and out-of-range or non-finite
   scores never auto-promote.
5. **Proposal-only.** The best possible verdict is `promote_eligible`, a branch
   and a proposal. The gate is never a write; a separate applier is the sole
   writer.

## Run it

```bash
python3 -m pytest tests -q   # 8 passed, no I/O, ~0.02s
```

## What is here, and what is not

This is the pure gate plus its oracle, extracted from a larger private
orchestration loop. The impure half, the miner that reads the running system's
history and the applier that would act on a `promote_eligible` verdict, stays
private. It is also, deliberately, not cleared to act on its own yet: the
human-approval ledger is empty (so the gate rejects essentially everything today)
and the applier still reads its trust facts from the environment rather than from
verified artifacts. The whole layer runs proposal-only, with a human running the
apply step by hand. The note explains why that is the design rather than a
limitation.

## License

MIT (see LICENSE).
