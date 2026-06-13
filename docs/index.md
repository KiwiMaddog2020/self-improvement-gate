---
title: "The gate that edits a gate is rejected by the gate it edits"
date: 2026-06-12
---

# The gate that edits a gate is rejected by the gate it edits

<p class="dek">A safety contract for a self-improving agent loop: how to let a system propose changes to its own rules without letting it edit the rule that stops it, and why I have not turned the capability on.</p>

<p class="meta">Kevin Madson · June 2026 · 5 min read</p>

> **If someone forwarded this to you:** I build and operate agentic systems
> across multiple coding LLMs. One of them can mine its own operating history and
> propose changes to its own rules. This note is about the gate that decides
> whether any such change is allowed to land, and the reason that gate currently
> says no to everything.

<p class="contact-card">
<a href="https://github.com/KiwiMaddog2020/self-improvement-gate">github.com/KiwiMaddog2020/self-improvement-gate</a>
<span class="sep">·</span>
<a href="mailto:kevinmadson@protonmail.com">kevinmadson@protonmail.com</a> <!-- pragma: allowlist -->
</p>

---

## The danger is recursive

A system that can edit its own rules can, in principle, edit the rule that
constrains it. That is the whole problem in one sentence. If a loop is allowed to
propose changes to its own operating instructions, the failure you actually fear
is not a bad proposal. A bad proposal is easy: you reject it. The failure you
fear is a proposal that quietly rewrites the check that would have rejected it,
and then sails through the weakened check it just wrote.

So I built the check first, on its own, as a pure function with no power to do
anything except classify. It is about 250 lines of standard-library Python, and
it decides one thing: may this proposed change be promoted? It never writes. It
reads a proposal's diff, its evidence ledger, the rater's identity, the scores,
and returns a verdict. The interesting part is what it refuses, and the order in
which it refuses.

## Self-protection, evaluated against the trusted base

The verdict that matters most is this one:

```python
if not _gate_untouched(facts.get("changed_paths"), facts.get("gate_globs")):
    return {"verdict": "blocked_gate_edit", "reason": "gate_file_touched", "stage": "learn"}
```

If the proposed diff touches any file on the gate's own protected list, the
proposal is blocked, full stop. The subtlety is in where `gate_globs` comes from:
the protected list is read from the **trusted base revision**, never from the
candidate's own, possibly-rewritten copy. A proposal cannot shorten the list of
things it is forbidden to touch, because the list it is checked against is not
the one it ships. The gate that edits a gate is rejected by the gate it edits.

And this check runs before the proposal is ever scored. A fully approved, fully
aged, cross-model-clean promotion is still blocked the instant it touches the
cage. The test that pins this says it plainly:

```python
def test_gate_edit_is_checked_before_anything_can_pass():
    assert g.evaluate(**_facts(changed_paths=["protocol_gate.py"]))["verdict"] == "blocked_gate_edit"
```

## Four stages, and no single one can wave a promotion through

Self-protection is one of five invariants. The first is that the gate is
un-collapsible. A promotion has to clear four sequential stages, and each reads a
separate fact, so satisfying one can never substitute for another:

```python
def evaluate(**facts):
    if not bool(facts.get("measured")):          # MEASURE: was it actually measured?
        return reject("measurement_missing")
    if not _fg_passed(ledger, organ):            # PROVE: a human signed off on this organ
        return reject("fg_approval_missing")
    if not _hold_passed(ledger, organ, now_ts):  # HOLD: enough evidence, aged long enough
        return hold("hold_evidence_insufficient")
    if not _gate_untouched(changed_paths, globs): # LEARN: does it touch the cage?
        return blocked("gate_file_touched")
    ...
```

MEASURE asks whether the thing was measured at all. PROVE asks whether a human
signed a one-time approval for this class of change. HOLD asks whether the
supporting evidence has both aged past a minimum window and cleared a minimum
sample count, not one or the other. Only then does the LEARN stage check the
cage and the rater. You cannot buy a missing measurement with a strong score, or
a missing human sign-off with a long hold. Each gate is a different lock.

## You cannot vouch for your own independence

The fourth invariant is that the rating has to come from a different model family
than the one that produced the change, and crucially, the families are supplied
by the harness, never read from the proposal itself. A proposal cannot assert
that it was independently reviewed; independence is a fact about who ran what,
established outside the proposal's reach. Same-family ratings fail. Unknown or
blank provenance fails closed, not open.

The fifth invariant is two bars with no soft middle. A high-stakes change escalates
to a human regardless of score; everything else is auto-eligible only inside a
narrow band, and a score that is out of range, infinite, or not a number never
auto-promotes. The verdict at its very best is `promote_eligible`: a branch and a
proposal, never a write. A separate applier is the only thing that can write, and
that brings me to the honest part.

## The door is closed, on purpose

Here is what I will not dress up. This gate is the brake, and I built and proved
the brake before building the engine. The engine is not on.

Two concrete things keep it off. First, the PROVE stage requires a human-signed
approval for a class of change, and that ledger is empty: nothing has earned one,
so the gate returns `fg_approval_missing` on essentially everything it sees
today. Second, the impure applier that would act on a `promote_eligible` verdict
currently reads its trust facts from the environment rather than from verified
artifacts, which means it is not itself trustworthy enough to act unattended. So
the whole layer runs in proposal-only mode: it can mine its history, draft a
change, and open it for review, but a human runs the apply step by hand, every
time.

That is the opposite of a limitation I am hiding. It is the design. The part that
classifies is pure, total, and tested; the part that acts is held back precisely
because it is not yet as trustworthy as the part that classifies. A self-improving
loop earns the right to act on itself one verified piece at a time, and the gate
is the piece I trust first because it is the piece that can be proven in
isolation.

## What is in the repo

The [repository](https://github.com/KiwiMaddog2020/self-improvement-gate) is the
pure gate and the test oracle that defines it: eight tests, no I/O, that pin all
five invariants and run in a hundredth of a second.

```bash
python3 -m pytest tests -q   # 8 passed
```

The oracle is written first and is the real specification; the gate exists to
satisfy it. The impure half, the miner that reads the system's history and the
applier that would act on a verdict, stays private, because it touches a running
system's internal state and because, as above, it has not earned the right to act
on its own. What is public is the part worth trusting: a small, total function
that knows it must never be the thing that decides it is allowed to change
itself.

---

<p class="byline"><em>I build agentic systems across multiple coding LLMs. More of my research notes are <a href="/">here</a>.</em></p>
