#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source ops/jetson-config.sh
if [[ "$(uname -s)" != Linux ]]; then
  arguments=""
  if (( $# > 0 )); then printf -v arguments '%q ' "$@"; fi
  exec ssh "$JETSON_SSH_TARGET" "cd -- $jetson_remote_dir && bash deployment/live.sh $arguments"
fi
export DETECT_PYTHON="$PWD/.venv-deploy/bin/python"
export OMP_NUM_THREADS=4
action="${1:-start}"
if (( $# > 0 )); then shift; fi
case "$action" in
  start|test)
    bash camera/view.sh "$action" --weights "$PWD/artifacts/deployment/v1/model-fp16.engine" --task segment "$@"
    ;;
  stop|status) bash camera/view.sh "$action" ;;
  *) echo 'Usage: bash deployment/live.sh {start|test|stop|status} [--seconds 60]'; exit 2 ;;
esac
