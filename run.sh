#!/bin/bash

if [[ -n "$VIRTUAL_ENV" ]]; then
  python "$0" "$@"
else
  if [[ -d "./.venv" ]]; then
    source "./.venv/bin/activate" && python "$0" "$@"
    deactivate
  else
    echo "Warning: No .venv found. Running with system Python." >&2
    python "$0" "$@"
  fi
fi