# Local connection settings

Public source files contain no machine-specific addresses. Configure your own
SSH alias named `jetson`, or set `JETSON_SSH_TARGET` to your SSH destination.

For persistent launcher settings, copy `ops/jetson.env.example` to
`ops/.local/jetson.env` and edit it locally. That directory is ignored by Git.
`JETSON_REMOTE_DIR` is relative to the remote home directory unless absolute.
The default is `code/jetsonballtracking`. Environment overrides are supported:

```bash
JETSON_SSH_TARGET=jetson bash deployment/live.sh status
```

The launchers read this configuration on the Mac. On the Jetson, the viewer
gets its bind address from `tailscale ip -4`. `status` prints the private viewer
URL at runtime; do not paste that output into public documentation.

## CVAT

Copy `ops/cvat/.env.example` to `ops/cvat/.env` and set `CVAT_BASE_URL` to your
local or private HTTPS endpoint. Docker Compose uses it for the server's base
URL. For the Python API checks, export `CVAT_BASE_URL`, or save the URL alone in
`ops/cvat/.local/base-url`. Both local files are ignored.

The generated login and SAM token stay in `ops/cvat/.local/`; container keys
remain in the Docker data volumes. Keep those files, volume backups and raw
run artifacts out of commits. Use `git check-ignore <path>` to check exclusions.
