"""The meta-loop gate (the cage): the safety contract, test-first.

This oracle DEFINES the cage. `protocol_gate.py` (pure predicates, no I/O) must
satisfy every test here before any impure wrapper or any organ of the loop ships.

The five non-negotiable invariants:
1. UN-COLLAPSIBLE: a promotion passes only if MEASURE -> PROVE -> HOLD -> LEARN
   ALL hold; each reads a SEPARATE fact, so no single check can be satisfied to
   wave a promotion through.
2. SELF-PROTECTING: a diff touching any gate-file glob is BLOCKED_GATE_EDIT,
   evaluated against the gate registry from the TRUSTED BASE REF, never the
   candidate's own (possibly-rewritten) registry. The gate that edits a gate is
   rejected by the gate it edits.
3. CROSS-MODEL, FAIL-CLOSED: a same-family (or unknown-provenance) rating never
   satisfies the gate; families are harness-sourced, never proposal metadata.
4. TWO BARS: Tier-3 promotions require 9.5 + a human; everything else is
   auto-eligible only inside the auto band. Out-of-range/non-finite scores never
   auto-promote.
5. PROPOSAL-ONLY DEFAULT: the verdict is at most `promote_eligible` (branch +
   gate); it is NEVER a direct write. The applier is the sole writer.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # so protocol_gate can import protocol_limits
GATE = REPO / "protocol_gate.py"

_spec = importlib.util.spec_from_file_location("protocol_gate", GATE)
g = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(g)

NOW = "2026-06-01T00:00:00Z"
GATE_GLOBS = ["gate_files.txt", "protocol_gate.py", "memory/**", "tests/protocol_regression/**"]


# -- _cross_model_ok: harness-sourced, fail-closed, canonical-by-family -------

def test_cross_model_requires_a_different_independent_family():
    assert g._cross_model_ok("claude", "codex") is True
    assert g._cross_model_ok("codex", "claude") is True
    # same family (any spelling/alias) never passes
    assert g._cross_model_ok("claude", "claude") is False
    assert g._cross_model_ok("codex", "openai-codex") is False     # alias -> same family
    assert g._cross_model_ok("claude", "opus") is False             # opus is claude-family
    # unknown / blank provenance fails closed
    for bad in ("", "  ", None, "self", "rubber-stamp", "gpt-but-typoed-???"):
        assert g._cross_model_ok("claude", bad) is False, bad
        assert g._cross_model_ok(bad, "codex") is False, bad


# -- _gate_untouched: a diff touching the cage is blocked (base-ref globs) -----

def test_a_diff_touching_any_gate_file_is_not_untouched():
    assert g._gate_untouched(["memory/foo.md"], GATE_GLOBS) is False          # promotable but gate-listed too
    assert g._gate_untouched(["gate_files.txt"], GATE_GLOBS) is False          # editing the registry itself
    assert g._gate_untouched(["protocol_gate.py"], GATE_GLOBS) is False
    assert g._gate_untouched(["tests/protocol_regression/case_01.json"], GATE_GLOBS) is False
    # a change that is NOT under a gate glob is untouched
    assert g._gate_untouched(["docs/note.md"], GATE_GLOBS) is True
    assert g._gate_untouched([], GATE_GLOBS) is True
    # fail closed on a malformed change list
    assert g._gate_untouched(["gate_files.txt", "docs/ok.md"], GATE_GLOBS) is False


# -- _fg_passed: a committed F->G approval for THIS organ must exist -----------

def _fg(organ):
    return {"type": "fg_approval", "organ": organ, "signed_by": "kevin", "ts": "2026-05-01T00:00:00Z"}


def test_fg_requires_a_signed_approval_for_the_organ():
    ledger = [_fg("organ-a")]
    assert g._fg_passed(ledger, "organ-a") is True          # "kevin" resolves to the human family
    assert g._fg_passed(ledger, "organ-d") is False        # wrong organ
    assert g._fg_passed([], "organ-a") is False             # no approval at all
    # an approval not signed by a human is not an approval
    assert g._fg_passed([{"type": "fg_approval", "organ": "organ-a", "signed_by": "claude"}], "organ-a") is False


# -- _hold_passed: >= min_weeks AND >= min_n, from the HOLD evidence -----------

def _hold(organ, start, n):
    return {"type": "hold_evidence", "organ": organ, "hold_start": start, "sample_n": n}


def test_hold_requires_both_the_window_and_the_sample_floor():
    far = [_hold("organ-a", "2026-04-01T00:00:00Z", 50)]   # ~9 weeks before NOW, n=50
    assert g._hold_passed(far, "organ-a", NOW, min_weeks=4, min_n=20) is True
    # too recent (window not met)
    recent = [_hold("organ-a", "2026-05-28T00:00:00Z", 50)]
    assert g._hold_passed(recent, "organ-a", NOW, min_weeks=4, min_n=20) is False
    # window met but too few samples
    thin = [_hold("organ-a", "2026-04-01T00:00:00Z", 5)]
    assert g._hold_passed(thin, "organ-a", NOW, min_weeks=4, min_n=20) is False
    assert g._hold_passed([], "organ-a", NOW, min_weeks=4, min_n=20) is False
    # malformed timestamp fails closed
    assert g._hold_passed([_hold("organ-a", "whenever", 50)], "organ-a", NOW, min_weeks=4, min_n=20) is False


# -- _classify_bar: two bars; non-finite/out-of-range never auto-promotes ------

def test_tier3_needs_human_others_auto_only_in_band():
    assert g._classify_bar(tier3=True, score=9.9) == "human"     # tier3 always escalates
    assert g._classify_bar(tier3=False, score=0.92) == "auto"    # in the auto band
    assert g._classify_bar(tier3=False, score=0.50) == "loop"    # below the band -> keep iterating
    for bad in (float("nan"), float("inf"), -1.0, 2.0):
        assert g._classify_bar(tier3=False, score=bad) != "auto", bad   # never auto on a bad score


# -- the composite: the 4 stages are sequential + un-collapsible ---------------

def _facts(**over):
    base = {
        "measured": True,
        "ledger": [_fg("organ-a"), _hold("organ-a", "2026-04-01T00:00:00Z", 50)],
        "organ": "organ-a",
        "now_ts": NOW,
        "changed_paths": ["memory/pins/new.md"],
        "gate_globs": ["gate_files.txt", "protocol_gate.py", "tests/protocol_regression/**"],
        "proposer_family": "claude",
        "rater_family": "codex",
        "tier3": False,
        "score": 0.9,
        "min_weeks": 4,
        "min_n": 20,
    }
    base.update(over)
    return base


def test_clean_promotion_is_eligible_never_a_direct_write():
    v = g.evaluate(**_facts())
    assert v["verdict"] == "promote_eligible"   # NOT "promoted"/"applied" -- the applier writes
    assert v["verdict"] not in ("promoted", "applied", "written", "merged")


def test_every_single_stage_failing_blocks_the_promotion():
    # MEASURE
    assert g.evaluate(**_facts(measured=False))["verdict"] != "promote_eligible"
    # PROVE (no F->G)
    assert g.evaluate(**_facts(ledger=[_hold("organ-a", "2026-04-01T00:00:00Z", 50)]))["verdict"] != "promote_eligible"
    # HOLD (window not met)
    assert g.evaluate(**_facts(ledger=[_fg("organ-a"), _hold("organ-a", "2026-05-28T00:00:00Z", 50)]))["verdict"] != "promote_eligible"
    # LEARN: gate-edit
    bad = g.evaluate(**_facts(changed_paths=["gate_files.txt"]))
    assert bad["verdict"] == "blocked_gate_edit"
    # LEARN: same-family rating
    assert g.evaluate(**_facts(rater_family="claude"))["verdict"] != "promote_eligible"
    # LEARN: tier3 -> needs a human, not auto
    assert g.evaluate(**_facts(tier3=True, score=9.9))["verdict"] == "needs_human"


def test_gate_edit_is_checked_before_anything_can_pass():
    # even a fully-approved, held, cross-model-clean promotion is blocked if it
    # touches the cage -- self-protection is not bypassable by passing the others.
    assert g.evaluate(**_facts(changed_paths=["protocol_gate.py"]))["verdict"] == "blocked_gate_edit"
