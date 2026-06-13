"""Shared constants for the promotion gate.

The values here are deliberately plain module constants so the pure gate module
can be imported through ``importlib.util`` without dataclass/module-registration
edge cases.
"""

from __future__ import annotations

AUTO_SCORE_MIN = 0.85
AUTO_SCORE_MAX = 0.95
TIER3_HUMAN_SCORE_MIN = 9.5

DEFAULT_HOLD_MIN_WEEKS = 4
DEFAULT_HOLD_MIN_N = 20

LEDGER_MAX_AGE_DAYS = 180
HARNESS_FAMILY_TTL_SECONDS = 6 * 60 * 60
GATE_DECISION_TTL_SECONDS = 24 * 60 * 60
