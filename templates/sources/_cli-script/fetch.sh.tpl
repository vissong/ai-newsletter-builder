#!/usr/bin/env bash
# {{name}} — CLI wrapper script
# Runs the CLI command and converts output to the standard JSON array.
# All diagnostics go to stderr; only the JSON array goes to stdout.
set -euo pipefail

# --- Configuration ---
COMMAND="{{command}}"
PARSER="{{parser}}"  # rsstail | jsonl | tencent-news-cli | raw

echo "Running: $COMMAND" >&2
RAW_OUTPUT=$($COMMAND 2>&1) || {
  echo "error: command failed" >&2
  exit 1
}

# --- Parse output to JSON ---
# TODO: implement parser logic based on $PARSER type
# For now, output an empty array as placeholder
echo "[]"
