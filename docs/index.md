---
title: "The gate that edits a gate is rejected by the gate it edits"
date: 2026-06-12
---

# The gate that edits a gate is rejected by the gate it edits

<p class="dek">How to let an AI system propose changes to its own rules without letting it quietly weaken the rule that stops it, and why I have left the dangerous half switched off.</p>

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

A system that can rewrite its own rules can rewrite the rule that holds it back. That is the whole problem in one sentence. Give a program the power to propose edits to its own instructions and the failure you fear is not a bad proposal. Bad proposals are trivial: you read them, you reject them, done. The one that should keep you up at night is the proposal that quietly loosens the check meant to catch it, then sails through the weakened check it just authored. Picture an amendment that repeals, in its own fine print, the clause that was supposed to forbid it.

So I wrote the check first, alone, as a pure function: code with no power except to judge. It cannot write, delete, deploy, or touch state. About 250 lines of plain Python, and it answers exactly one question. May this proposed change be admitted? It reads what the change touches, the evidence behind it, who reviewed it, and the scores it carries, and it returns a verdict. The interesting part is not that it says no. It is what it refuses, and the order it refuses in.

## It checks itself against the locked original, not the copy in hand

The verdict that matters most is this one. Skip the code if you like; the sentence under it carries the whole idea.

```python
if not _gate_untouched(changed_paths, gate_globs):
    return {"verdict": "blocked_gate_edit", "reason": "gate_file_touched"}
```

Touch any file on the gate's protected list and the change is blocked, full stop. The subtlety is provenance. That protected list is read from the locked-down original version of the system, never from the copy the change is carrying. A proposal therefore cannot shorten the list of things it is forbidden to touch, because the list it is measured against is not the one it brought to the table. The gate that edits a gate is rejected by the gate it edits.

This fires before any score is computed. A change can be fully aged, fully approved, blessed by an independent reviewer, and it still dies the instant it reaches into the safety machinery. A test in the repo pins precisely that case.

## Four locks in a row, each opened by its own key

Self-protection is one of five rules. The first: the gate cannot be short-circuited. A change clears four checks in sequence, and each reads a separate fact, so clearing one can never substitute for another.

```python
def evaluate(facts):
    if not measured:        return reject   # was it actually measured?
    if not human_approved:  return reject   # did a person sign off on this kind of change?
    if not enough_evidence: return hold      # enough track record, over enough time?
    if touches_the_gate:    return blocked   # does it touch the safety machinery?
    ...
```

Was it measured? Did a human sign off on this category of change? Has it earned its keep over enough cases and enough elapsed time? Only after all three does the last check ask whether the change reaches into the safety machinery, and whether a genuinely independent reviewer approved it. You cannot pay for a missing measurement with a dazzling score, or cover a missing human sign-off with a long track record. Different locks, different keys, no master.

## You cannot vouch for your own independence

The fourth rule: the review must come from a different AI than the one that produced the change, and the system, not the proposal, decides who is who. A change cannot assert its own clean bill of health. Independence is a fact about which model actually ran which step, established outside the proposal's reach. A review traced back to the authoring AI fails. So does an origin that is unknown or unstated. The default lands on the safe side, not the convenient one.

The fifth rule is two hard thresholds with nothing soft between them. A high-stakes change always routes to a human, however good its score. Everything else can auto-approve only inside a narrow band, and a score that is missing, infinite, or otherwise nonsensical never auto-approves at all. The best verdict the gate will ever hand back is "eligible": a candidate sitting on its own branch, not something already live. Applying a change is the job of a separate program, and only that program. That separation is the honest center of the whole thing.

## The door is shut, on purpose

Here is the part I will not dress up. This gate is the brake. I built and proved the brake before building the engine, and the engine is not running.

Two specific things keep it off. The human sign-off check reads from a record of approved change categories, and that record is empty. Nothing has earned a sign-off, so the gate rejects essentially everything it sees today. And the program that would apply an approved change still decides who to trust from loose configuration rather than verified records, which means it is not yet trustworthy enough to act unattended. So the system runs propose-only: it can study its history, draft a change, and open it for review, but a human runs the final apply step by hand, every single time.

I am not hiding that as a shortcoming. It is the design. The part that judges is small, finished, and tested. The part that acts is deliberately held back, because it is not yet as trustworthy as the part that judges. A system earns the right to change itself one proven piece at a time. The gate is the piece I trust first, because it is the one piece that can be proven in isolation.

## What is in the repo

The [repository](https://github.com/KiwiMaddog2020/self-improvement-gate) holds the pure gate and the tests that define what it must do: eight tests, zero outside dependencies, pinning all five rules and finishing in about a hundredth of a second.

```bash
python3 -m pytest tests -q   # 8 passed
```

The tests came first and are the real specification; the gate exists only to satisfy them. The other half stays private, the part that studies the live system's history and the part that would apply an approved change, because it reaches into a running system's internal state and, as above, has not earned the right to act on its own. What is public is the part worth trusting: a small, complete piece of code that knows it must never be the thing deciding it is allowed to change itself.

---

<p class="byline"><em>I build agentic systems across multiple coding LLMs. More of my research notes are <a href="/">here</a>.</em></p>
