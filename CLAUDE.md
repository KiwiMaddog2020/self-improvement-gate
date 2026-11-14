# self-improvement-gate

## What this is

A safety contract for a self-improving agent loop, expressed as a pure, tested
promotion gate of about 250 lines of standard-library Python. It reads a
proposal and returns a verdict. It never writes.

## Build, test, run

- `bash bin/check.sh` runs the suite (set `PYTHON=/path/to/python` if needed).
- `python3 -m pytest tests -q` expects 8 passed.

## Layout

- protocol_gate.py: the gate.
- protocol_limits.py: limits and constants.
- tests/: the oracle, test_protocol_gate.py.
- docs/: GitHub Pages source for the write-up (the only published folder).
- bin/: local check script.

## House rules

- All work lands on the session branch, one commit per phase. No pull request unless asked. Never force-push or rewrite history.
- No GitHub Actions or other CI automation. Use the local check script.
- User-facing text has no em-dashes and keeps a PG-clean tone.
- Never skip or disable a test to get a pass.
- Published results, run data and pre-registrations are a research record and are never overwritten. New runs go in new folders.

## Invariants

- The gate is pure and never writes. No I/O, ever.
- The five invariants in the README (un-collapsible, self-protecting,
  cross-model fail-closed, two bars, proposal-only) are defined by the oracle in
  tests/test_protocol_gate.py.
- The gate-file registry is read from the trusted base revision, never from the
  candidate's own copy.
