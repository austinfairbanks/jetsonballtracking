# Pretrained bounding-box test

A live camera viewer and pretrained bounding-box test are deployed to the Jetson.
Start and stop explicitly; no boot service or scheduler is installed.

September 15, 2026 live test: **1,058 frames in 71.44 seconds (14.81 processed
FPS)** at 1280×720, with actual CUDA YOLO11n inference. The inspected live image
showed a lit scene with person and cell-phone boxes. Both raw and annotated
MJPEG streams delivered consecutive valid JPEG frames to the Mac over Tailscale.
The run remains continuous; these are an interim measurement, not a final
benchmark. Evidence: Jetson `artifacts/detect-20260915-095028/`, with local
`artifacts/live-boxes.jpg` and `artifacts/live-raw.jpg` snapshots.

The model is pretrained **YOLO11n detection**, using the COCO classes. By default
it draws boxes, class names and confidence for common objects. `--ball-only`
restricts the result to the general `sports ball` class. This is not the custom
volleyball model and does not guarantee recognition of this ball.

## Live view from any Tailscale device

Run `bash camera/view.sh status` for the private URL while the viewer is running. The page has
**Bounding boxes** and **Raw camera** buttons. Access follows your tailnet's
access rules; the server binds only the Jetson's Tailscale IP. Tailscale encrypts
the connection between devices. No SSH tunnel is needed.

From the Mac repository or the Jetson repository:

```bash
bash camera/view.sh start                  # Continuous camera + YOLO boxes
bash camera/view.sh status
bash camera/view.sh stop
bash camera/view.sh test --seconds 60      # Timed camera + YOLO test
bash camera/view.sh start --camera-only    # Continuous feed without inference
```

Stop the existing session before starting another. `--ball-only --conf 0.20`
can be added to detector runs. Continuous viewing runs in the `ball-detector`
tmux session until stopped, the process fails, or the Jetson reboots. It keeps
only the first five minutes of historical samples and box logs to bound disk
use; current images and status continue updating. Both raw and annotated views
share one capture/inference loop, so raw viewing in detector mode has the same
processing cadence. Camera-only mode skips the model entirely.

Tailscale Serve was considered, but this Jetson requires a sudo password to
configure it. The direct Tailscale bind works without admin changes. No Funnel
or public exposure is configured. HTTPS Serve can be configured later by an
administrator, with the app bound to loopback and the proxy pointing to port
8765; the current viewer uses the direct Tailscale URL above.

The original SSH-tunnel launcher remains available for a five-minute test:

```bash
bash detection/launch.sh
```

Open http://127.0.0.1:8765 and keep that terminal open. Closing the tunnel does
not stop the remote test. This launcher uses loopback instead of the Tailscale
bind; stop any existing camera session before using it.

Setup-only check (no camera or model execution):

```bash
bash detection/launch.sh --check
```

## Outputs and timing

Each test gets a new `artifacts/detect-YYYYMMDD-HHMMSS/` directory in
`~/code/jetsonballtracking` on the Jetson:

- `latest.jpg` / `raw.jpg`: latest annotated/raw frames, atomically replaced.
- `sample-*.jpg`: annotated samples approximately every five seconds.
- `detections.jsonl`: image-space boxes, confidence, class, and host timestamps.
- `report.json`: settings, runtime environment, frame count and completion status.
- `status.json`: preview status, including an explicit no-detections state.

The adjacent `.log` and `.exit` files hold console output and exit status. Exit
zero means a completed test, not a claim of detection accuracy. A six-minute
outer watchdog bounds startup or driver stalls in timed mode (continuous mode has no deadline); a forced termination can leave
an incomplete report. The MJPEG browser stream is capped at 10 FPS per viewer; actual updates are
limited by the processing FPS shown in the image. Status refreshes at 2 Hz. Processing FPS includes
capture/inference/annotation overhead and initial model warmup. It is not a
formal latency or dropped-frame benchmark. This first detector saves images
and box logs, not an annotated video.

Model input is fixed to 640×640 via letterboxing, with an initial 1280×720 MJPG
camera request at 30 FPS. Earlier capture measured approximately 15 FPS with
the lens cover on. The detector explicitly selects GPU 0 and refuses CPU
fallback. Actual CUDA inference and a lit camera image were verified in the live test above;
volleyball accuracy has not been evaluated.

## Recreate the prepared environment on this Jetson

This setup targets the board's JetPack 7.2.1, Ubuntu 24.04 and Python 3.12.
Run long installations in tmux:

```bash
ssh jetson
cd ~/code/jetsonballtracking
tmux new -s detector-install
bash detection/setup.sh
```

The separate `.venv-detect` environment contains CUDA PyTorch 2.14.0+cu130,
torchvision 0.29.0+cu130, Ultralytics 8.3.203, NumPy 1.26.4 and OpenCV 4.11.0.
The CUDA package index and versions are pinned in `requirements-gpu.txt`.
The original camera `.venv` and system packages are unchanged. The pinned
OpenCV wheel supplies V4L2; this detector does not require GStreamer. Exact
installed packages are recorded in `artifacts/detector-installed.txt`.

Setup verifies imports, CUDA device visibility, V4L2 availability, and the
checkpoint checksum. It also executes tiny known-answer CUDA addition,
matrix multiplication, convolution and torchvision NMS checks. These passed
on this board on September 15, 2026. It does not construct the YOLO model, invoke a forward
pass, export an engine, or access the camera. A successful setup check is not
yet proof that inference works.

**Compatibility note:** PyTorch warns that this ARM64 build does not explicitly
support Orin `sm_87` (the listed kernels include `sm_80`). Despite that warning,
all four real GPU operator checks passed on this JetPack 7.2.1 board. The
warning remains visible and is recorded in the preflight report; the checks
fail on any CUDA error instead of assuming that device visibility proves
compatibility. Full YOLO11n CUDA inference also passed the live test above.
The warning remains relevant when changing versions or adding model operators.

Weights: `artifacts/models/yolo11n.pt`, from the official Ultralytics assets
release `v8.3.0`. SHA256:

```text
0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1
```

The source and checksum are pinned in `prepare.py`. The checkpoint is fetched
during setup so launch does not need a model download. Ultralytics
automatic dependency installation is disabled by the launch scripts.

References: [YOLO11](https://docs.ultralytics.com/models/yolo11),
[JetPack 7.2 native setup](https://docs.ultralytics.com/guides/nvidia-jetson),
[prediction API](https://docs.ultralytics.com/modes/predict).

## Development checks

`test_setup.py` uses mocks and temporary files; it never opens a camera or runs
inference. In a Python venv, run `python -m unittest discover -s detection -p
'test_*.py' -v`. Deploy changes with a scoped copy of `detection/` into the
existing Jetson clone, which is on `codex/jetson-camera-capture`.
