"""Pure predicates for a self-improvement promotion gate.

When an agent loop is allowed to propose changes to its own operating rules,
this gate decides whether a proposed change may be promoted. It is intentionally
I/O-free: the CLI wrapper supplies git diffs, ledger entries, trusted-base policy
globs, harness-sourced family identities, timestamps, and scores. The gate only
classifies; it never writes.

The five invariants it enforces are documented in tests/test_protocol_gate.py,
which is the oracle that defines the cage.
"""

from __future__ import annotations

import fnmatch
import math
import os
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any

from protocol_limits import AUTO_SCORE_MAX, AUTO_SCORE_MIN

SECONDS_PER_WEEK = 7 * 24 * 60 * 60

_PRINCIPAL_ALIASES: dict[str, str] = {
    # GPT / Codex family
    "codex": "codex",
    "openaicodex": "codex",
    "codexcli": "codex",
    "codexreview": "codex",
    "gpt": "codex",
    "gpt5": "codex",
    "gpt55": "codex",
    "openai": "codex",
    # Claude family. Opus/Sonnet/Haiku are the same family for independence.
    "claude": "claude",
    "claudecode": "claude",
    "claudereview": "claude",
    "anthropic": "claude",
    "opus": "claude",
    "opusreview": "claude",
    "sonnet": "claude",
    "haiku": "claude",
    # Human signer/operator family. A named operator resolves to the family.
    "kevin": "human",
    "human": "human",
    "operator": "human",
    "user": "human",
}

INDEPENDENT_RATERS = frozenset({"claude", "codex", "human"})


def _canonical_principal(value: Any) -> str:
    """Return the closed-registry family for ``value``, or "" when unknown."""
    s = unicodedata.normalize("NFKC", str(value if value is not None else ""))
    key = re.sub(r"[^a-z0-9]+", "", s.lower())
    return _PRINCIPAL_ALIASES.get(key, "")


def _cross_model_ok(proposer_family: Any, rater_family: Any) -> bool:
    """True only for known, different model/operator families."""
    proposer = _canonical_principal(proposer_family)
    rater = _canonical_principal(rater_family)
    return bool(
        proposer
        and rater
        and proposer in INDEPENDENT_RATERS
        and rater in INDEPENDENT_RATERS
        and proposer != rater
    )


def _clean_policy_line(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s or s.startswith("#"):
        return ""
    if "\x00" in s:
        return None
    return s.replace("\\", "/")


def _normalize_path(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s or "\x00" in s:
        return None
    norm = os.path.normpath(s.replace("\\", "/")).replace("\\", "/")
    if norm == "." or norm.startswith("../") or norm == "..":
        return None
    if norm.startswith("./"):
        norm = norm[2:]
    return norm


def _iter_checked_strings(values: Any, *, policy: bool) -> list[str] | None:
    if isinstance(values, str) or values is None:
        return None
    try:
        iterator = iter(values)
    except TypeError:
        return None

    out: list[str] = []
    for value in iterator:
        item = _clean_policy_line(value) if policy else _normalize_path(value)
        if item is None:
            return None
        if item:
            out.append(item)
    return out


def _gate_untouched(changed_paths: Any, gate_globs: Any) -> bool:
    """False when any changed path matches any gate glob; fail closed on junk."""
    paths = _iter_checked_strings(changed_paths, policy=False)
    globs = _iter_checked_strings(gate_globs, policy=True)
    if paths is None or globs is None:
        return False

    for path in paths:
        for glob in globs:
            if fnmatch.fnmatchcase(path, glob):
                return False
    return True


def _fg_passed(ledger: Any, organ: Any) -> bool:
    """Return whether a human operator has signed an F->G approval for this organ."""
    if not isinstance(organ, str) or not organ.strip():
        return False
    if isinstance(ledger, dict) or ledger is None:
        return False
    try:
        entries = iter(ledger)
    except TypeError:
        return False

    for entry in entries:
        if not isinstance(entry, dict):
            return False
        if (
            entry.get("type") == "fg_approval"
            and entry.get("organ") == organ
            and _canonical_principal(entry.get("signed_by")) == "human"
        ):
            return True
    return False


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number


def _hold_passed(ledger: Any, organ: Any, now_ts: Any, *, min_weeks: Any, min_n: Any) -> bool:
    """Return whether the organ has enough held evidence for promotion."""
    if not isinstance(organ, str) or not organ.strip():
        return False
    now = _parse_ts(now_ts)
    weeks = _coerce_int(min_weeks)
    min_samples = _coerce_int(min_n)
    if now is None or weeks is None or min_samples is None or weeks < 0 or min_samples < 0:
        return False
    if isinstance(ledger, dict) or ledger is None:
        return False
    try:
        entries = iter(ledger)
    except TypeError:
        return False

    required_seconds = weeks * SECONDS_PER_WEEK
    for entry in entries:
        if not isinstance(entry, dict):
            return False
        if entry.get("type") != "hold_evidence" or entry.get("organ") != organ:
            continue
        hold_start = _parse_ts(entry.get("hold_start"))
        sample_n = _coerce_int(entry.get("sample_n"))
        if hold_start is None or sample_n is None:
            continue
        if (now - hold_start).total_seconds() >= required_seconds and sample_n >= min_samples:
            return True
    return False


def _classify_bar(*, tier3: Any, score: Any) -> str:
    """Classify the final score against the two promotion bars."""
    if bool(tier3):
        return "human"
    try:
        value = float(score)
    except (TypeError, ValueError):
        return "loop"
    if math.isfinite(value) and AUTO_SCORE_MIN <= value <= AUTO_SCORE_MAX:
        return "auto"
    return "loop"


def evaluate(**facts: Any) -> dict[str, str]:
    """Evaluate MEASURE -> PROVE -> HOLD -> LEARN as separate gate stages."""
    if not bool(facts.get("measured")):
        return {"verdict": "reject", "reason": "measurement_missing", "stage": "measure"}

    ledger = facts.get("ledger")
    organ = facts.get("organ")
    if not _fg_passed(ledger, organ):
        return {"verdict": "reject", "reason": "fg_approval_missing", "stage": "prove"}

    if not _hold_passed(
        ledger,
        organ,
        facts.get("now_ts"),
        min_weeks=facts.get("min_weeks"),
        min_n=facts.get("min_n"),
    ):
        return {"verdict": "hold", "reason": "hold_evidence_insufficient", "stage": "hold"}

    if not _gate_untouched(facts.get("changed_paths"), facts.get("gate_globs")):
        return {"verdict": "blocked_gate_edit", "reason": "gate_file_touched", "stage": "learn"}

    if not _cross_model_ok(facts.get("proposer_family"), facts.get("rater_family")):
        return {"verdict": "reject", "reason": "cross_model_independence_failed", "stage": "learn"}

    bar = _classify_bar(tier3=facts.get("tier3"), score=facts.get("score"))
    if bar == "human":
        return {"verdict": "needs_human", "reason": "tier3_requires_human", "stage": "learn"}
    if bar == "auto":
        if bool(facts.get("human_required") or facts.get("requires_human")):
            return {"verdict": "needs_human", "reason": "human_required", "stage": "learn"}
        return {"verdict": "promote_eligible", "reason": "auto_band_clear", "stage": "learn"}
    return {"verdict": "loop", "reason": "score_outside_auto_band", "stage": "learn"}
