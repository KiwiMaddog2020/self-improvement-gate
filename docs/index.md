---
title: "The gate that edits a gate is rejected by the gate it edits"
date: 2026-06-12
---

# The gate that edits a gate is rejected by the gate it edits

<p class="dek">How to let an AI system propose changes to its own rules without letting it quietly edit the rule that stops it, and why I have not switched the dangerous half on.</p>

<p class="meta">Kevin Madson · June 2026 · 5 min read</p>

> **If someone forwarded this to you:** I build software with AI agents, programs
> that write and change code on their own. One of my systems can study its own past
> behavior and propose changes to its own rules. This note is about the safety check
> that decides whether any such change is allowed to take effect, and why that check
> currently says no to everything.

<p class="contact-card">
<a href="https://github.com/KiwiMaddog2020/self-improvement-gate">github.com/KiwiMaddog2020/self-improvement-gate</a>
<span class="sep">·</span>
<a href="mailto:kevinmadson@protonmail.com">kevinmadson@protonmail.com</a> <!-- pragma: allowlist -->
</p>

---

## The danger loops back on itself

A system that can change its own rules can, in principle, change the rule that
holds it back. That is the whole problem in one sentence. If a program is allowed
to propose edits to its own instructions, the failure you actually fear is not a
bad proposal. A bad proposal is easy: you reject it. The failure you fear is a
proposal that quietly rewrites the check that would have rejected it, and then
sails through the weakened check it just wrote. It is the same worry as someone
amending a constitution by smuggling the change past the very clause meant to
forbid it.

So I built the check first, on its own, as what programmers call a pure function:
a piece of code with no power to do anything except judge. It cannot write, delete,
or change a single thing. It is about 250 lines of plain Python, and it answers one
question: may this proposed change be allowed in? It reads what the change touches,
the evidence behind it, who reviewed it, and the scores, and returns a verdict.
The interesting part is what it refuses, and the order it refuses in.

## It protects itself, judged against the locked-down original

The verdict that matters most is this one (you can skip the code; the line below
says it in plain English):

```python
if not _gate_untouched(changed_paths, gate_globs):
    return {"verdict": "blocked_gate_edit", "reason": "gate_file_touched"}
```

If the proposed change touches any file on the gate's own protected list, it is
blocked, full stop. The subtlety is where that protected list comes from: it is read
from the locked-down original version of the system, never from the copy the change
itself is carrying. So a proposal cannot shorten the list of things it is forbidden
to touch, because the list it is checked against is not the one it brought along.
The gate that edits a gate is rejected by the gate it edits.

And this runs before the change is ever scored. Even a fully approved, fully aged,
independently reviewed change is blocked the instant it touches the safety machinery.
A test in the repo pins exactly that.

## Four locks in a row, and no one of them opens the door

Self-protection is one of five rules. The first is that the gate cannot be
shortcut. A change has to clear four checks in order, and each one reads a
completely separate fact, so passing one can never stand in for another:

```python
def evaluate(facts):
    if not measured:        return reject   # was it actually measured?
    if not human_approved:  return reject   # did a person sign off on this kind of change?
    if not enough_evidence: return hold      # enough track record, over enough time?
    if touches_the_gate:    return blocked   # does it touch the safety machinery?
    ...
```

Was it actually measured? Did a human sign off on this category of change? Has it
proven itself over enough cases and enough time? Only then does the last check ask
whether it touches the safety machinery and whether a genuinely independent
reviewer approved it. You cannot buy a missing measurement with a great score, or a
missing human sign-off with a long track record. Each lock opens on its own key.

## You cannot vouch for your own independence

The fourth rule is that the review has to come from a different AI than the one that
made the change, and the system decides who is who, never the change itself. A
proposal cannot simply claim it was independently reviewed; independence is a fact
about who actually ran what, settled outside the proposal's reach. A review from the
same AI fails. Unknown or unstated origin fails too, on the safe side, not the
permissive one.

The fifth rule is two clear bars with no soft middle. A high-stakes change always
goes to a human, no matter how good its score. Everything else can only auto-approve
inside a narrow band, and a score that is impossible, infinite, or simply missing
never auto-approves. The best verdict the gate can ever return is "eligible," which
means a proposed change on its own branch, never something already applied. A
separate program is the only thing allowed to actually apply a change, and that is
the honest part.

## The door is closed, on purpose

Here is what I will not dress up. This gate is the brake, and I built and proved the
brake before building the engine. The engine is not on.

Two concrete things keep it off. First, one of the four checks requires a human to
have signed off on a category of change, and that record is empty: nothing has
earned a sign-off, so the gate rejects essentially everything it sees today. Second,
the program that would actually apply an approved change currently decides who to
trust from loose settings rather than from verified records, which means it is not
yet trustworthy enough to act on its own. So the whole system runs in propose-only
mode: it can study its history, draft a change, and open it for review, but a human
runs the final apply step by hand, every time.

That is not a limitation I am hiding. It is the design. The part that judges is
small, complete, and tested; the part that acts is held back precisely because it is
not yet as trustworthy as the part that judges. A system earns the right to change
itself one proven piece at a time, and the gate is the piece I trust first, because
it is the piece that can be proven on its own.

## What is in the repo

The [repository](https://github.com/KiwiMaddog2020/self-improvement-gate) is the
pure gate and the set of tests that define what it must do: eight tests, no outside
dependencies, that pin all five rules and run in a hundredth of a second.

```bash
python3 -m pytest tests -q   # 8 passed
```

The tests are written first and are the real specification; the gate exists to
satisfy them. The other half, the part that studies the system's history and the
part that would apply an approved change, stays private, because it touches a live
system's internal state and, as above, has not earned the right to act on its own.
What is public is the part worth trusting: a small, complete piece of code that
knows it must never be the thing that decides it is allowed to change itself.

---

<p class="byline"><em>I build agentic systems across multiple coding LLMs. More of my research notes are <a href="/">here</a>.</em></p>
