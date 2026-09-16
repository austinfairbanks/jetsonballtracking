# Public repository check

Checked September 15, 2026. No credential or private-endpoint exposure was
found in the cleaned files intended for GitHub or in the reachable Git history.

## Removed or excluded

Private Jetson addresses, the tailnet hostname and personal checkout paths were
removed from source files and documentation. Launchers now use ignored local
settings or environment variables. Existing connection settings were preserved
locally; [configuration instructions](ops/README.md) contain generic examples.
The deployment report generator was updated so it won't restore a private URL.

The generated CVAT password and SAM bearer token remain in ignored local files.
Ignore rules now also cover local connection files, `.env` files, private-key
and certificate files, extra virtual environments and logs. Datasets, raw
recordings, model artifacts and CVAT backups remain excluded. The selected
README demo assets are included deliberately.

## Checks performed

| Check | Result |
| --- | --- |
| `detect-secrets` 1.5.0, all candidate files and reachable history | No findings; network credential verification disabled. |
| Exact comparison against the locally saved CVAT password and SAM token | Neither value occurs in the candidate files or history. |
| Private endpoints and personal checkout paths | Removed from candidate files; retained only in ignored configuration. |
| GitHub branches/tags compared with local history | Remote `main` matches the single initial commit, which contains only the original README. No history rewrite needed. |
| Demo video | OCR completed on all 1,758 frames with no errors; no IP, MAC-address, private-endpoint or credential-pattern matches. |
| Media metadata | Inherited MP4 metadata removed without re-encoding. GIF metadata contains playback/palette settings. |
| Configuration changes | Three SSH launcher checks, shell syntax, Python parsing and CVAT Compose configuration passed. Six existing detection tests passed. |

Loopback addresses, generic connection examples and software version numbers
remain in the source. They do not identify the private machines.

This check covers the current repository files, reachable Git history and
included demo media. Automated scanning and OCR can miss secrets; this is not
an application penetration test or an audit of GitHub issues, releases or logs.
Keep local settings and raw artifacts excluded when committing future changes.
Repository visibility was not changed by this check.
