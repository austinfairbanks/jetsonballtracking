#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
# The first-stage tmux job was already running when the source video arrived.
# Wait for that job to finish; video.py requires completed final/test reports.
while tmux has-session -t '=volleyball-cv' 2>/dev/null; do
  sleep 30
done
training/.venv/bin/python -u training/video.py "$HOME/downloads/IMG_9217.MOV"
training/.venv/bin/python training/summarize.py
