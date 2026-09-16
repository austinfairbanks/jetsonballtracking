#!/usr/bin/env bash
# Run on the Jetson. No camera/model is started with --check.
set -euo pipefail
cd "$(dirname "$0")/.."
export YOLO_CONFIG_DIR="$PWD/artifacts/ultralytics-config"
export YOLO_AUTOINSTALL=false
mkdir -p "$YOLO_CONFIG_DIR"
python_bin="${DETECT_PYTHON:-.venv-detect/bin/python}"
if [[ "${1:-}" == --check ]]; then
  exec "$python_bin" detection/run.py --check
fi
"$python_bin" detection/run.py --check "$@"
if tmux has-session -t ball-detector 2>/dev/null; then
  echo "ball-detector is already running. Attach with: tmux attach -t ball-detector"
  exit 1
fi
mkdir -p artifacts
run_dir="$PWD/artifacts/detect-$(date +%Y%m%d-%H%M%S)"
printf -v command '%q ' env "DETECT_PYTHON=$python_bin" bash "$PWD/detection/session.sh" "$run_dir" "$@"
tmux new-session -d -s ball-detector "$command"
echo "Started camera session in tmux: ball-detector"
echo "Run directory: $run_dir"
echo "Log: $run_dir.log"
echo "Preview listens on port 8765 at the selected bind address."
