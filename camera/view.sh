#!/usr/bin/env bash
# Control the Jetson viewer from the Mac or from the Jetson itself.
set -euo pipefail
cd "$(dirname "$0")/.."
source ops/jetson-config.sh
if [[ "$(uname -s)" != Linux ]]; then
  arguments=""
  if (( $# > 0 )); then printf -v arguments '%q ' "$@"; fi
  exec ssh -o BatchMode=yes -o ConnectTimeout=10 "$JETSON_SSH_TARGET" \
    "cd -- $jetson_remote_dir && bash camera/view.sh $arguments"
fi
action="${1:-start}"
if (( $# > 0 )); then shift; fi
tailnet_ip="$(tailscale ip -4)"
case "$action" in
  start|test)
    # Bind only the Tailscale interface. This requires no sudo/Serve configuration.
    if [[ "$action" == start ]]; then
      bash detection/start.sh --host "$tailnet_ip" --seconds 0 "$@"
    else
      bash detection/start.sh --host "$tailnet_ip" "$@"
    fi
    echo "Live camera: http://$tailnet_ip:8765"
    ;;
  stop)
    if tmux has-session -t ball-detector 2>/dev/null; then
      tmux send-keys -t ball-detector C-c
      echo "Stop requested."
    else
      echo "Camera viewer is not running."
    fi
    ;;
  status)
    if tmux has-session -t ball-detector 2>/dev/null; then
      echo "Live camera: http://$tailnet_ip:8765"
      curl --fail --silent "http://$tailnet_ip:8765/status.json" || true
    else
      echo "Camera viewer is stopped."
    fi
    ;;
  *) echo "Usage: bash camera/view.sh {start|test|stop|status} [--camera-only] [--ball-only]" >&2; exit 2 ;;
esac
