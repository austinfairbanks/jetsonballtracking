"""YOLO detection or segmentation with an SSH-friendly browser preview."""

import argparse
from datetime import datetime, timezone
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import signal
import sys
import threading
import time
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "artifacts/models/yolo11n.pt"
PAGE = b"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jetson live camera</title>
<style>body{margin:24px;background:#101418;color:#eee;font:18px system-ui}
img{display:block;max-width:100%;max-height:80vh;margin:16px 0}
small{color:#b8c5ce}button{padding:10px;margin-right:10px;cursor:pointer}</style><h1>Jetson live camera</h1>
<button onclick="view('boxes')">Bounding boxes</button><button onclick="view('raw')">Raw camera</button>
<p id="status">Waiting for the first frame...</p><img id="frame" alt="Live camera feed" src="/stream.mjpg?view=boxes">
<small>Pretrained COCO model. Sports ball is a general class, not a custom volleyball model.</small>
<script>function view(mode){document.getElementById('frame').src='/stream.mjpg?view='+mode;}
async function refresh(){try{
const r=await fetch('/status.json',{cache:'no-store'});if(!r.ok)throw Error();
const s=await r.json();document.getElementById('status').textContent=
(s.frames && Date.now()/1000-s.updated_unix_seconds>5?'Stream stalled: ':'')+s.message;
}catch(e){document.getElementById('status').textContent='Preview disconnected or test ended. Check the run log.';}
setTimeout(refresh,500);}refresh();</script></html>"""


class Preview(BaseHTTPRequestHandler):
    def __init__(self, *args, output, **kwargs):
        self.output = output
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == "/stream.mjpg":
            filename = "raw.jpg" if parse_qs(parsed.query).get("view") == ["raw"] else "latest.jpg"
            self.stream(self.output / filename)
            return
        if path == "/":
            content, kind = PAGE, "text/html; charset=utf-8"
        elif path in {"/frame.jpg", "/status.json"}:
            try:
                content = (self.output / ("latest.jpg" if path == "/frame.jpg" else "status.json")).read_bytes()
            except FileNotFoundError:
                self.send_error(503, "Waiting for first frame")
                return
            kind = "image/jpeg" if path == "/frame.jpg" else "application/json"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass

    def stream(self, path):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.connection.settimeout(5)
        last = None
        try:
            while not self.server.stopped.is_set():
                try:
                    stamp = path.stat().st_mtime_ns
                    if stamp != last:
                        data = path.read_bytes()
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " +
                                         str(len(data)).encode() + b"\r\n\r\n" + data + b"\r\n")
                        self.wfile.flush()
                        last = stamp
                except FileNotFoundError:
                    pass
                self.server.stopped.wait(0.1)  # Preview capped at 10 FPS per viewer.
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass


def atomic_write(path, content):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(path)


def check_gpu_ops(torch, torchvision):
    """Tiny arithmetic checks, not model inference; fail on any CUDA error."""
    x = torch.tensor([[1., 2.], [3., 4.]], device="cuda")
    if (x + 1).cpu().tolist() != [[2., 3.], [4., 5.]]:
        raise RuntimeError("CUDA addition check failed")
    if (x @ x).cpu().tolist() != [[7., 10.], [15., 22.]]:
        raise RuntimeError("CUDA matrix multiplication check failed")
    y = torch.nn.functional.conv2d(torch.ones((1, 1, 3, 3), device="cuda"),
                                   torch.ones((1, 1, 2, 2), device="cuda"))
    if y.cpu().tolist() != [[[[4., 4.], [4., 4.]]]]:
        raise RuntimeError("CUDA convolution check failed")
    boxes = torch.tensor([[0., 0., 10., 10.], [1., 1., 9., 9.]], device="cuda")
    scores = torch.tensor([.9, .8], device="cuda")
    if torchvision.ops.nms(boxes, scores, .5).cpu().tolist() != [0]:
        raise RuntimeError("CUDA NMS check failed")


def preflight():
    """Imports and tiny GPU checks: no camera, model construction or inference."""
    import cv2
    import numpy
    import torch
    import torchvision
    import ultralytics
    from prepare import check_weights

    check_weights()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; this demo requires the Jetson GPU")
    if not torchvision.extension._has_ops():
        raise RuntimeError("Torchvision compiled operators are unavailable")
    if not torch._C._dispatch_has_kernel_for_dispatch_key("torchvision::nms", "CUDA"):
        raise RuntimeError("Torchvision has no CUDA non-maximum suppression operator")
    if not cv2.videoio_registry.hasBackend(cv2.CAP_V4L2):
        raise RuntimeError("OpenCV has no V4L2 camera backend")
    capability = torch.cuda.get_device_capability(0)
    arch = f"sm_{capability[0]}{capability[1]}"
    architectures = torch.cuda.get_arch_list()
    check_gpu_ops(torch, torchvision)
    return {"torch": torch.__version__, "torchvision": torchvision.__version__,
            "ultralytics": ultralytics.__version__, "opencv": cv2.__version__,
            "numpy": numpy.__version__, "cuda_runtime": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0), "gpu_arch": arch,
            "compiled_architectures": architectures, "weights": str(WEIGHTS),
            "architecture_warning": arch not in architectures,
            "gpu_operator_checks": "addition, matmul, convolution and NMS passed",
            "inference_tested": False}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check setup without opening camera or executing model")
    parser.add_argument("--device", default="/dev/video0")
    parser.add_argument("--host", default="127.0.0.1", help="Preview bind address; use the Jetson Tailscale IP for tailnet viewing")
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--weights", type=Path, default=WEIGHTS)
    parser.add_argument("--task", choices=["detect", "segment"], default="detect")
    parser.add_argument("--ball-only", action="store_true", help="Show only COCO sports ball boxes")
    parser.add_argument("--camera-only", action="store_true", help="Stream camera without loading a model")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or not 0 <= args.seconds <= 300:
        parser.error("--seconds must be 0 (continuous) or at most 300")
    if not math.isfinite(args.conf) or not 0 < args.conf <= 1:
        parser.error("--conf must be greater than 0 and at most 1")
    return args


def main():
    global PAGE
    args = parse_args()
    try:
        if args.camera_only:
            import cv2
            environment = {"opencv": cv2.__version__, "inference_tested": False, "mode": "camera-only"}
        else:
            environment = preflight()
            if args.weights != WEIGHTS and not args.weights.is_file():
                raise FileNotFoundError(args.weights)
            environment["weights"] = str(args.weights.resolve())
            environment["task"] = args.task
    except Exception as exc:
        print(f"Setup check failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(environment, indent=2), flush=True)
    if args.check:
        print("SETUP READY. Camera not opened; model not executed.")
        return 0

    import cv2
    if not args.camera_only:
        from ultralytics import YOLO
    if args.task == "segment":
        PAGE = PAGE.replace(b"Bounding boxes", b"Volleyball masks").replace(
            b"Pretrained COCO model. Sports ball is a general class, not a custom volleyball model.",
            b"Custom YOLO11n-seg volleyball model. Image-only predictions; no temporal tracking.")

    output = args.output or ROOT / "artifacts" / ("detect-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    output.mkdir(parents=True, exist_ok=False)
    report = {"started_utc": datetime.now(timezone.utc).isoformat(), "environment": environment,
              "settings": {"device": args.device, "seconds": args.seconds, "conf": args.conf,
                           "ball_only": args.ball_only, "camera_only": args.camera_only,
                           "weights": str(args.weights), "task": args.task,
                           "imgsz": 640, "gpu_device": None if args.camera_only else 0},
              "status": "failed", "frames": 0}
    capture = server = None
    frames = 0
    started = None
    next_sample = 0.0
    error = None

    def status(message):
        atomic_write(output / "status.json", json.dumps({"message": message, "frames": frames,
                     "updated_unix_seconds": time.time(), "camera_only": args.camera_only}).encode())

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    try:
        status("Starting camera..." if args.camera_only else "Loading model; first inference may take a moment...")
        server = ThreadingHTTPServer((args.host, 8765), partial(Preview, output=output))
        server.stopped = threading.Event()
        threading.Thread(target=server.serve_forever, daemon=True).start()
        model = None if args.camera_only else YOLO(str(args.weights), task=args.task)
        ball_ids = [i for i, name in model.names.items() if name == "sports ball"] if model else []
        if args.ball_only and not ball_ids:
            raise RuntimeError("Checkpoint has no sports ball class")
        capture = cv2.VideoCapture(args.device, cv2.CAP_V4L2)
        if not capture.isOpened():
            raise RuntimeError(f"Cannot open camera {args.device}")
        for prop, value in [(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG")),
                            (cv2.CAP_PROP_FRAME_WIDTH, 1280), (cv2.CAP_PROP_FRAME_HEIGHT, 720),
                            (cv2.CAP_PROP_FPS, 30), (cv2.CAP_PROP_BUFFERSIZE, 1)]:
            capture.set(prop, value)
        report["camera"] = {"width": capture.get(cv2.CAP_PROP_FRAME_WIDTH),
                            "height": capture.get(cv2.CAP_PROP_FRAME_HEIGHT),
                            "reported_fps": capture.get(cv2.CAP_PROP_FPS)}
        started = time.monotonic()
        with (output / "detections.jsonl").open("w") as log:
            while args.seconds == 0 or time.monotonic() - started < args.seconds:
                ok, frame = capture.read()
                read_time = time.monotonic()
                if not ok or frame is None:
                    raise RuntimeError("Camera read failed")
                ok, raw_jpeg = cv2.imencode(".jpg", frame)
                if not ok:
                    raise RuntimeError("Cannot encode camera frame")
                atomic_write(output / "raw.jpg", raw_jpeg.tobytes())
                boxes = []
                annotated = frame.copy()
                if model is not None:
                    result = model.predict(frame, device=0, imgsz=640, rect=False, conf=args.conf,
                                       iou=0.7, retina_masks=args.task == "segment", half=False,
                                       classes=ball_ids if args.ball_only else None,
                                       verbose=False, save=False)[0]
                    if model.predictor.device.type != "cuda":
                        raise RuntimeError("Predictor is not using CUDA")
                    # CPU conversion synchronizes completion before recording timing.
                    boxes = result.boxes.data.cpu().tolist()
                    annotated = result.plot()
                    if args.task == "segment":
                        for box in boxes:
                            center = (round((box[0]+box[2])/2), round((box[1]+box[3])/2))
                            cv2.circle(annotated, center, 4, (0, 255, 255), -1)
                predicted = time.monotonic()
                frames += 1
                elapsed = predicted - started
                message = f"{len(boxes)} detections | {frames / elapsed:.1f} processed FPS | {elapsed:.0f}s"
                if not boxes:
                    message = "No detections | " + message.split(" | ", 1)[1]
                if args.camera_only:
                    message = "Camera only | " + message.split(" | ", 1)[1]
                cv2.putText(annotated, message, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
                ok, jpeg = cv2.imencode(".jpg", annotated)
                if not ok:
                    raise RuntimeError("Cannot encode annotated frame")
                atomic_write(output / "latest.jpg", jpeg.tobytes())
                status(message)
                record = {"frame": frames, "read_monotonic_seconds": read_time,
                          "elapsed_seconds": elapsed, "predict_seconds": predicted - read_time,
                          "boxes": [{"xyxy": row[:4], "confidence": row[4],
                                     "class_id": int(row[5]), "label": result.names[int(row[5])]} for row in boxes]}
                # Continuous viewing keeps only five minutes of sample/box history.
                if elapsed <= 300:
                    log.write(json.dumps(record) + "\n")
                if elapsed >= next_sample:
                    if elapsed <= 300:
                        (output / f"sample-{frames:06d}.jpg").write_bytes(jpeg.tobytes())
                    log.flush()
                    if elapsed <= 300:
                        print(message, flush=True)
                    report.update(status="running", frames=frames, wall_seconds=elapsed,
                                  processed_fps=frames / elapsed, inference_tested=frames > 0 and model is not None)
                    atomic_write(output / "report.json", (json.dumps(report, indent=2) + "\n").encode())
                    next_sample = elapsed + 5
        report["status"] = "completed"
    except KeyboardInterrupt:
        report["status"] = "interrupted"
    except Exception as exc:
        error = str(exc)
        report["status"] = "failed"
        report["error"] = error
        print(f"Detection failed: {error}", file=sys.stderr, flush=True)
    finally:
        if capture is not None:
            capture.release()
        if server is not None:
            server.stopped.set()
            server.shutdown()
            server.server_close()
        elapsed = time.monotonic() - started if started is not None else 0
        report.update(frames=frames, wall_seconds=elapsed,
                      processed_fps=frames / elapsed if elapsed else 0,
                      inference_tested=frames > 0 and not args.camera_only)
        status(f"Test {report['status']}. {frames} frames processed.")
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 1 if error or report["status"] != "completed" else 0


if __name__ == "__main__":
    sys.exit(main())
