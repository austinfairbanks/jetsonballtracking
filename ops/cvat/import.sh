#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
for attempt in {1..60}; do
    if curl --fail --silent http://127.0.0.1:8082/api/server/about >/dev/null; then
        docker compose -f ops/cvat/compose.yaml exec -T server python manage.py shell < ops/cvat/bootstrap.py
        exit 0
    fi
    sleep 5
done
echo 'CVAT API did not become ready within five minutes' >&2
exit 1
