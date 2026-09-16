#!/usr/bin/env bash
# Source from a launcher after changing to the repository root.
if [[ -f ops/.local/jetson.env ]]; then
  source ops/.local/jetson.env
fi
: "${JETSON_SSH_TARGET:=jetson}"
printf -v jetson_remote_dir '%q' "${JETSON_REMOTE_DIR:-code/jetsonballtracking}"
