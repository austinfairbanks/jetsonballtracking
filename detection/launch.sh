#!/usr/bin/env bash
# Run on the Mac. The SSH tunnel remains in the foreground until Ctrl-C.
set -euo pipefail
cd "$(dirname "$0")/.."
source ops/jetson-config.sh
arguments=""
if (( $# > 0 )); then
  printf -v arguments '%q ' "$@"
fi
ssh -o BatchMode=yes -o ConnectTimeout=10 "$JETSON_SSH_TARGET" \
  "cd -- $jetson_remote_dir && bash detection/start.sh $arguments"
if [[ "${1:-}" == --check ]]; then
  exit 0
fi
echo "Open http://127.0.0.1:8765 in your browser. Keep this terminal open."
exec ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 \
  -L 127.0.0.1:8765:127.0.0.1:8765 "$JETSON_SSH_TARGET"
