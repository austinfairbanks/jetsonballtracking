# Volleyball CVAT

Private URL: configured locally with `CVAT_BASE_URL`; use your own tailnet hostname.

Local URL: http://127.0.0.1:8082

See [local configuration](../README.md) for the ignored endpoint settings.

Login: `volleyball`; generated password is in `.local/login.json` (git-ignored).

## Labeling task

- Task 1: Volleyball — all keyframes — polygon segmentation.
- All 644 PNGs from `dataset/keyframes`, sorted by filename, in one annotation job.
- One label: `volleyball`, polygon only, no attributes.
- Trace the visible ball boundary, excluding hands and background.
- Leave images with no visible ball empty; annotate every visible volleyball.
- Original filenames are retained. All supplied files use the `video1-` prefix;
  see [the image key](../../IMAGE_KEY.md) for Austin's scene/angle ranges and
  completed-labeling report. The overcast angle boundary is confirmed at
  521/522; confirm source-video identities before splitting training/test data.
- Imported originals are copied into CVAT's persistent data volume. Source
  images are mounted read-only. Cached annotation images use quality 100.

## Operations

Run from the repository root:

```bash
docker compose -f ops/cvat/compose.yaml up -d
docker compose -f ops/cvat/compose.yaml stop
docker compose -f ops/cvat/compose.yaml ps
docker compose -f ops/cvat/compose.yaml exec -T server python < ops/cvat/check.py
```

The Compose project `jetson-volleyball-cvat` has its own network and volumes.
It does not share task databases or annotation storage with the existing CVAT.
It reuses the locally installed server/UI images, pinned by image ID. Those
images are amd64 and run under the existing Docker VM's emulation on this Mac.
There is one server process and one worker servicing the background queues.
Analytics, Grafana, ClickHouse, and Vector are omitted. Import/export jobs run
mostly serially. SAM 2.1 Large supplies interactive masks using the Mac's GPU.

## SAM 2.1 Large labeling assistant

Save any unsaved work, refresh the job, then open **AI Tools → Interactors**.
Choose **SAM 2.1 Large — volleyball helper**, select `volleyball`, and turn on
**Convert masks to polygons**. Click **Interact** and left-click inside the ball.
Right-click unwanted background to exclude it. Review the boundary before
accepting and saving. Begin with a full-image center click and no ROI. Use
**Start with a bounding box** for ambiguous outlines. An optional **region of
interest (ROI)** preserves more detail but can select a ball panel instead of
the whole ball (observed on the shaded test frame); clear it if the result gets
worse. Set polygon simplification low for small balls. With default
shortcuts, press **N** to finish the outline, **F** for the next frame, and **N**
to reuse the selected interactor. Save regularly.

Empty images still get no annotation. SAM is prompted segmentation, not a
volleyball detector: clicking background can produce a background mask. Check
dark panels, hands, occlusion, motion blur, and grass carefully. This assists
dataset labeling; it does not replace the future live Jetson segmentation model.

The service uses the standard CVAT Nuclio discovery/invocation protocol through
a small custom adapter, **not** a Nuclio dashboard or a CVAT server patch.
Inference runs natively on macOS with PyTorch MPS (Apple GPU); it fails startup
if the GPU is unavailable rather than silently switching to CPU. A lightweight
ARM64 Docker bridge forwards CVAT requests to the native worker through
`host.lima.internal:8071`. The worker binds only to `127.0.0.1:8071` and requires
a generated bearer token, stored in git-ignored `.local/sam2-token` and mounted
read-only into the bridge as a Compose secret. The bridge has no published port
or annotation/data-volume access. Only the last image embedding is cached.
No annotations are saved automatically.

Model source is pinned to official SAM 2 commit
`2b90b9f5ceec907a1c18123530e92e794ad901a4`; the official SAM 2.1 Hiera Large
checkpoint is SHA256-verified by `sam2/setup.sh`. Python dependencies use the
isolated `.local/sam2-venv` environment managed with uv. The adapter returns
standard CVAT RLE masks for the existing mask-to-polygon UI conversion.

The native worker is a per-user macOS LaunchAgent named
`com.austinfairbanks.volleyball-sam2`, configured to start at login and restart
after failure. It runs independently of Docker. Setup requires native macOS GPU
access and permission to register the LaunchAgent; run it outside the sandbox.

```bash
bash ops/cvat/sam2/setup.sh
docker compose -f ops/cvat/compose.yaml up -d --build sam2
tail -30 ops/cvat/.local/sam2-gpu.log
docker compose -f ops/cvat/compose.yaml logs --tail=30 sam2
launchctl kickstart -k gui/$(id -u)/com.austinfairbanks.volleyball-sam2
uv run --no-project --python 3.12 --with pillow ops/cvat/test_sam2.py
```

The read-only smoke test exercises model discovery and click/box inference
through the private HTTPS CVAT API. It stores previews/results under
`ops/cvat/.local/sam2-tests/` and never writes annotation data. Browser UI
interaction must still be confirmed by the annotator.

The private Tailscale route was configured with:

```bash
tailscale serve --bg --https=8457 http://127.0.0.1:8082
```

Keep Docker/Colima and Tailscale running for remote access. Stop/start preserves
annotations. Do not remove this project's Docker volumes: they hold the labels,
database, and imported images. Export annotations or a task backup in CVAT before
any deliberate teardown of persistent storage.

## Disk capacity

CVAT blocks startup when Docker's filesystem exceeds 90% usage, even if macOS
still has free space. The shared Colima data disk was expanded from 100 to
120 GiB on September 13, 2026, alongside unused tool-image and build-cache cleanup.
Check it with `colima ssh -- df -h /mnt/lima-colima`; also check macOS free space
with `df -h /System/Volumes/Data`. Further growth requires a Colima restart and
temporarily interrupts every Docker service on this machine. Keep the 90% health
threshold enabled and preserve data/backup volumes during cleanup.
