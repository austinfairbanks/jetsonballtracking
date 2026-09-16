"""Headless USB/V4L2 camera recording with host-side timing evidence."""

import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import signal
import sys
import time


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/video0")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=float, default=30)
    parser.add_argument("--seconds", type=float, default=65)
    parser.add_argument("--fourcc", default="MJPG", help="Requested camera pixel format")
    parser.add_argument("--output", type=Path, required=True, help="New run directory")
    args = parser.parse_args()
    if (args.width <= 0 or args.height <= 0 or
            not math.isfinite(args.fps) or args.fps <= 0 or
            not math.isfinite(args.seconds) or args.seconds <= 0):
        parser.error("Dimensions, FPS and duration must be finite and positive")
    if len(args.fourcc) != 4:
        parser.error("--fourcc must contain exactly four characters")
    return args


def verify_clip(cv2, path):
    """Decode the saved clip, catching silent writer failures before reporting success."""
    reader = cv2.VideoCapture(str(path))
    frames = 0
    try:
        if not reader.isOpened():
            raise RuntimeError("Saved clip cannot be opened")
        while True:
            ok, frame = reader.read()
            if not ok:
                break
            if frame is None or frame.size == 0:
                raise RuntimeError("Saved clip contains an empty frame")
            frames += 1
    finally:
        reader.release()
    return frames


def main():
    args = parse_args()
    try:
        import cv2
    except ImportError:
        print("OpenCV is missing. Use the Jetson venv described in camera/README.md.", file=sys.stderr)
        return 1

    # Refuse to overwrite any previous evidence.
    args.output.mkdir(parents=True, exist_ok=False)
    report = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "requested": {**vars(args), "output": str(args.output)},
        "opencv_version": cv2.__version__,
        "timing": "Host monotonic timestamps immediately after read(); includes decode, writing and sampling overhead. Not sensor timestamps or capture latency.",
        "status": "failed",
    }
    capture = None
    writer = None
    count = 0
    first = last = None
    max_gap = 0.0
    next_sample = 0.0
    next_progress = 5.0
    error = None
    clip = args.output / "capture.avi"

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    try:
        capture = cv2.VideoCapture(args.device, cv2.CAP_V4L2)
        if not capture.isOpened():
            raise RuntimeError(f"Cannot open {args.device}; check connection, permissions and other camera processes")
        settings = [
            ("fourcc", cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*args.fourcc)),
            ("width", cv2.CAP_PROP_FRAME_WIDTH, args.width),
            ("height", cv2.CAP_PROP_FRAME_HEIGHT, args.height),
            ("fps", cv2.CAP_PROP_FPS, args.fps),
            ("buffer_size", cv2.CAP_PROP_BUFFERSIZE, 1),
        ]
        report["settings_accepted"] = {name: capture.set(prop, value) for name, prop, value in settings}
        reported_fps = capture.get(cv2.CAP_PROP_FPS)
        codec = int(capture.get(cv2.CAP_PROP_FOURCC))
        report["negotiated"] = {
            "width": capture.get(cv2.CAP_PROP_FRAME_WIDTH),
            "height": capture.get(cv2.CAP_PROP_FRAME_HEIGHT),
            "fps": reported_fps,
            "fourcc": "".join(chr((codec >> (8 * i)) & 255) for i in range(4)),
            "backend": capture.getBackendName(),
        }
        playback_fps = reported_fps if math.isfinite(reported_fps) and reported_fps > 0 else args.fps
        report["clip_playback_fps"] = playback_fps
        print(json.dumps(report["negotiated"]), flush=True)
        with (args.output / "timestamps.csv").open("w", newline="") as handle:
            timestamps = csv.writer(handle)
            timestamps.writerow(["frame", "monotonic_ns", "elapsed_seconds"])
            while True:
                ok, frame = capture.read()
                stamp = time.monotonic_ns()
                if not ok or frame is None or frame.size == 0:
                    raise RuntimeError(f"Camera read failed after {count} frames")
                if first is None:
                    first = stamp
                    height, width = frame.shape[:2]
                    report["actual_frame_size"] = {"width": width, "height": height}
                    writer = cv2.VideoWriter(str(clip), cv2.VideoWriter_fourcc(*"MJPG"), playback_fps, (width, height))
                    if not writer.isOpened():
                        raise RuntimeError("Cannot open MJPEG/AVI writer")
                if frame.shape[:2] != (height, width):
                    raise RuntimeError("Camera frame dimensions changed during recording")
                elapsed = (stamp - first) / 1e9
                if last is not None:
                    max_gap = max(max_gap, (stamp - last) / 1e9)
                last = stamp
                writer.write(frame)
                timestamps.writerow([count, stamp, f"{elapsed:.9f}"])
                count += 1
                if elapsed >= next_sample:
                    sample = args.output / f"sample-{count:06d}.jpg"
                    if not cv2.imwrite(str(sample), frame):
                        raise RuntimeError(f"Cannot save {sample}")
                    next_sample += 10
                if elapsed >= next_progress:
                    print(f"{elapsed:.1f}s | {count} frames | {(count - 1) / elapsed:.2f} FPS", flush=True)
                    handle.flush()
                    next_progress += 5
                if elapsed >= args.seconds:
                    break
    except KeyboardInterrupt:
        error = "Capture interrupted"
    except Exception as exc:
        error = str(exc)
    finally:
        if capture is not None:
            capture.release()
        if writer is not None:
            writer.release()

    elapsed = (last - first) / 1e9 if first is not None and last is not None else 0.0
    report.update(frames=count, capture_seconds=elapsed,
                  observed_fps=(count - 1) / elapsed if elapsed > 0 else 0.0,
                  max_frame_gap_seconds=max_gap)
    if writer is not None:
        try:
            decoded = verify_clip(cv2, clip)
            report["decoded_clip_frames"] = decoded
            if decoded != count:
                raise RuntimeError(f"Saved clip has {decoded} readable frames; expected {count}")
        except Exception as exc:
            error = f"{error}; {exc}" if error else str(exc)
    report["status"] = "failed" if error else "completed"
    report["one_minute_capture_pass"] = error is None and elapsed >= 60 and count > 1
    report["scene_content_verified"] = False  # Ball / motion / empty scene require review.
    if error:
        report["error"] = error
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
