#!/usr/bin/env bash
# Local check, replaces CI. Override the interpreter with PYTHON=/path/to/python.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
PYTHON="${PYTHON:-python3}"
"$PYTHON" -m pytest tests -q
