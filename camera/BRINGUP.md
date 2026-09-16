# Camera bring-up — September 14, 2026

Code deployed over SSH to the Jetson checkout at `~/code/jetsonballtracking` on
`codex/jetson-camera-capture`, using an isolated uv environment that exposes
the existing Jetson OpenCV installation. No new system packages were installed.

## Installed stack (read from the board)

| Item | Value |
| --- | --- |
| Device-tree model | NVIDIA Jetson Orin Nano Engineering Reference Developer Kit Super |
| OS / architecture | Ubuntu 24.04.4 LTS / aarch64 |
| Kernel | 6.8.12-1021-tegra |
| JetPack package | 7.2.1-b49 |
| L4T | 39.2.1-20260806224157 |
| CUDA SDK / runtime | 13.2.2 / 13.2.86 |
| TensorRT library package | 10.16.2.10-1+cuda13.2 |
| Python / OpenCV | 3.12.3 / 4.8.0 |
| OpenCV capture support | V4L2, GStreamer 1.24.2, FFmpeg |
| Camera | USB Global Shutter Camera, ID 32e4:0234, `/dev/video0` |

Austin identified the camera as **SV-USBGS1200P01-UFV(2.8-12)**: the SVPRO
global-shutter USB camera with a 2.8–12 mm lens. The USB descriptors themselves
do not establish the exact sensor model.
Installed CUDA/TensorRT versions are inventory only; GPU inference has not been
tested. `v4l2-ctl` is not installed. A later `lsusb -v` read recorded the supported
modes in `artifacts/camera-usb-descriptor.txt` on the Mac: MJPEG advertises up
to 90 FPS at 1920×1200, 1080p and 720p. These rates have not been measured.
Raw inventory is saved in `artifacts/inventory.json` on both machines.

## Measured capture

Settings: 1280×720, USB V4L2, MJPG, requested/reported 30 FPS. Timing is measured
after host reads and includes recording overhead.

| Run | Capture time | Frames saved and decoded | Observed FPS | Largest frame gap |
| --- | ---: | ---: | ---: | ---: |
| `camera-smoke` | 5.019 s | 76 | 14.943 | 83.21 ms |
| `camera-minute-1` | 65.049 s | 977 | 15.004 | 70.08 ms |
| `camera-minute-2` | 65.047 s | 977 | 15.004 | 69.95 ms |

Both one-minute runs exited successfully and all 977 frames decoded in each,
verifying that capture can be closed and reopened for a repeat run. The camera
reports 30 FPS while observed recording throughput is approximately 15 FPS;
the reason has not been isolated. AVI playback uses the reported 30 FPS and is
therefore approximately twice real time in this run. Use `timestamps.csv` and
`report.json` for timing evidence.

An unavailable-device test correctly exited with status 1, zero frames, a
descriptive error, and `one_minute_capture_pass: false`.

## Outstanding scene check

The first and final sampled images from `camera-minute-1` are almost black.
Austin confirmed the lens cover was on; this is expected. Frame delivery and
recording work, but a useful scene has not been verified. Austin will remove
the cover for the next test. Record a ball, motion and an empty scene using
the command in [README.md](README.md).
Roadmap step 1 remains partially complete until that footage is reviewed.

Run artifacts are ignored by Git. Both one-minute clips, sample JPEGs,
timestamps and JSON reports were copied to the Mac under
`artifacts/camera-minute-1/` and `artifacts/camera-minute-2/` as well as retained
on the Jetson at the same repository-relative paths.
