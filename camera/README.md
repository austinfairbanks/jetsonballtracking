# Jetson camera bring-up

Configure `jetson` as an alias in your own SSH config, then connect with
`ssh jetson` and work in `~/code/jetsonballtracking`. Both machines
must be on Tailscale. The implementation branch is `codex/jetson-camera-capture`.

The connected camera is a USB UVC **Global Shutter Camera**, USB ID `32e4:0234`.
Use `/dev/video0`, or its stable path:

```text
/dev/v4l/by-id/usb-Global_Shutter_Camera_Global_Shutter_Camera_01.00.00-video-index0
```

This script targets USB/V4L2 capture. CSI/Argus capture is a separate path; see
[NVIDIA's camera interface documentation](https://docs.nvidia.com/jetson/archives/r36.4/DeveloperGuide/SD/CameraDevelopment/CameraSoftwareDevelopmentSolution.html).

## Live browser viewer

Open the URL printed by `bash camera/view.sh status` from a device on your Tailscale
network. The viewer offers raw frames and pretrained bounding boxes. From the
Mac or Jetson repository, use:

```bash
bash camera/view.sh start
bash camera/view.sh status
bash camera/view.sh stop
bash camera/view.sh test --seconds 60
```

`start` stays running in tmux; `test` stops after five minutes by default.
Use `start --camera-only` for capture without a detector. Stop the viewer before
using the standalone recording script below because both access the same USB
camera. See [detection/README.md](../detection/README.md) for setup and outputs.

## Environment

Use the Jetson's existing OpenCV build through a project venv. This preserves
the installed V4L2/GStreamer support without installing replacement wheels or
changing system packages. Python 3.12 is already installed on this board.

```bash
cd ~/code/jetsonballtracking
~/.local/bin/uv venv --python /usr/bin/python3 --system-site-packages .venv
.venv/bin/python -c 'import cv2; print(cv2.__version__)'
mkdir -p artifacts
.venv/bin/python camera/inventory.py > artifacts/inventory.json
```

Create the venv once; reuse it on subsequent runs. Inventory reports missing
optional utilities such as `v4l2-ctl` without installing anything.

## Record over SSH

Remove the lens cap and point the camera at a lit scene. Include a stationary
ball, move it, then remove it to capture an empty scene. Run inside tmux so an
SSH disconnect does not stop recording:

```bash
cd ~/code/jetsonballtracking
tmux new -s ball-camera
timeout --signal=TERM --kill-after=10s 110s \
  .venv/bin/python -u camera/capture.py \
  --device /dev/video0 --width 1280 --height 720 --fps 30 \
  --seconds 65 --output artifacts/camera-run-01 \
  > artifacts/camera-run-01.log 2>&1
echo $?
```

Detach with Ctrl-B then D; reconnect with `tmux attach -t ball-camera`.
Choose a **new output directory** for every recording. The command rejects
existing directories to preserve prior evidence. The outer timeout bounds a
stalled camera driver; if it has to kill the process, the clip/report may be
incomplete and the run must not count as successful.

Each run saves:

- `capture.avi`: MJPEG clip, verified by decoding all frames after recording.
- `sample-*.jpg`: first frame and a sample approximately every ten seconds.
- `timestamps.csv`: frame index and monotonic timestamp immediately after read.
- `report.json`: requested/negotiated settings, actual image size, successful
  frame count, measured FPS, maximum frame gap, decoded clip count and status.

Observed FPS is `(frames - 1) / (last_read_time - first_read_time)` and includes
the work of decoding, saving the video, and sampling images. It is neither
sensor exposure rate nor capture-to-display latency; driver drops cannot be
counted from these host timestamps. Camera-reported FPS is recorded separately.
AVI playback uses the camera-reported FPS (or requested FPS if unavailable), so
playback can be faster than wall time if delivery is slower. Use the CSV/report
for timing, not clip duration.

Exit status zero means the requested recording completed and every saved frame
decoded. `one_minute_capture_pass` additionally requires at least 60 seconds
between the first and last successful reads. It does **not** validate scene
content: review the clip for the ball, motion and empty scene. A dark or covered
lens can still pass the capture-duration check.

Copy results to the Mac from its repository directory:

```bash
scp -r jetson:code/jetsonballtracking/artifacts/camera-run-01 artifacts/
```

## Deploy local edits

The first deployment used a scoped SSH copy into the existing Jetson clone;
no GitHub push or remote pull is required to test uncommitted code. Both clones
have the camera branch checked out. From the Mac repository directory:

```bash
scp camera/capture.py camera/inventory.py camera/README.md \
  jetson:code/jetsonballtracking/camera/
```

Results and virtual environments belong in ignored `artifacts/` and `.venv/`.
See [BRINGUP.md](BRINGUP.md) for measured results and outstanding checks.
