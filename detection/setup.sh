#!/usr/bin/env bash
# JetPack 7.2 / aarch64 / Python 3.12. Downloads/checks only; no inference.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -m)" != aarch64 ]]; then
  echo "Run this setup on the Jetson, not the Mac." >&2
  exit 1
fi
uv_bin="${UV_BIN:-$HOME/.local/bin/uv}"
export YOLO_CONFIG_DIR="$PWD/artifacts/ultralytics-config"
export YOLO_AUTOINSTALL=false
mkdir -p artifacts "$YOLO_CONFIG_DIR"
if [[ ! -x .venv-detect/bin/python ]]; then
  "$uv_bin" venv --python /usr/bin/python3 .venv-detect
fi
"$uv_bin" pip install --python .venv-detect/bin/python -r detection/requirements-gpu.txt
"$uv_bin" pip install --python .venv-detect/bin/python -r detection/requirements.txt
.venv-detect/bin/python detection/prepare.py
.venv-detect/bin/python detection/run.py --check | tee artifacts/detector-preflight.txt
"$uv_bin" pip freeze --python .venv-detect/bin/python > artifacts/detector-installed.txt
