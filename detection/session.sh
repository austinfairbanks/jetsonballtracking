#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
run_dir="$1"
shift
export YOLO_CONFIG_DIR="$PWD/artifacts/ultralytics-config"
export YOLO_AUTOINSTALL=false
limit=360s
for (( i=1; i<=$#; i++ )); do
  if [[ "${!i}" == --seconds ]]; then
    next=$((i+1))
    if [[ "${!next:-}" == 0 ]]; then limit=0; fi
  fi
done
timeout --foreground --signal=TERM --kill-after=10s "$limit" \
  "${DETECT_PYTHON:-.venv-detect/bin/python}" -u detection/run.py --output "$run_dir" "$@" \
  > "$run_dir.log" 2>&1
result=$?
echo "$result" > "$run_dir.exit"
exit "$result"
