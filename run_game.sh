#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "Starting AP Biology Evolution Game..."

if command -v uv >/dev/null 2>&1; then
  uv run python scripts/run_game.py
elif command -v python3 >/dev/null 2>&1; then
  python3 -m pip install -e .
  python3 scripts/run_game.py
elif command -v python >/dev/null 2>&1; then
  python -m pip install -e .
  python scripts/run_game.py
else
  echo "Python was not found. Install Python 3.11+ from https://www.python.org/downloads/ and run this again."
  exit 1
fi
