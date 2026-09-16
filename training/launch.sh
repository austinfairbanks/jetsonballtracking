#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export UV_CACHE_DIR=/tmp/volleyball-training-uv-cache
uv sync --project training --python 3.12
training/.venv/bin/python -u training/pipeline.py
