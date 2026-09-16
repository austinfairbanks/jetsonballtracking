"""Single-model adapter for CVAT's Nuclio discovery/invocation HTTP protocol.

Authenticated macOS loopback worker; the private Compose bridge supplies image bytes.
Returns mask drafts, never writes CVAT annotations. CVAT converts masks to polygons.
"""

import base64
import hashlib
import io
import json
import logging
import hmac
import os
from pathlib import Path
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import cv2
import numpy as np
import torch
from PIL import Image
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

FUNCTION_ID = "volleyball-sam2"
DEVICE = "mps"
TOKEN = Path(os.environ["SAM2_TOKEN_FILE"]).read_text().strip()
if len(TOKEN) < 32:
    raise RuntimeError("A private service token is required")
METADATA = {
    "metadata": {
        "name": FUNCTION_ID,
        "annotations": {
            "name": "SAM 2.1 Large — volleyball helper",
            "type": "interactor",
            "version": "2",
            "spec": "[]",
            "min_pos_points": "1",
            "min_neg_points": "0",
            "startswith_box_optional": True,
            "help_message": "Enable Convert masks to polygons. Click inside the ball; add negative clicks outside. For tiny balls, use a tight box or ROI. Review before accepting.",
        },
    },
    "spec": {"description": "Meta SAM 2.1 Hiera Large on Apple GPU, click/box-prompted polygon drafts. Review each mask."},
    "status": {"state": "ready", "httpPort": 8070},
}


class Segmenter:
    def __init__(self):
        torch.set_num_threads(2)
        if not torch.backends.mps.is_available():
            raise RuntimeError("Apple GPU unavailable; run natively on macOS outside the sandbox")
        model = build_sam2(
            "configs/sam2.1/sam2.1_hiera_l.yaml",
            os.environ["SAM2_CHECKPOINT"], device=DEVICE,
        )
        self.predictor = SAM2ImagePredictor(model)
        self.image_key = None

    @torch.inference_mode()
    def predict(self, data):
        positive = np.asarray(data.get("pos_points", []), dtype=np.float32).reshape(-1, 2)
        negative = np.asarray(data.get("neg_points", []), dtype=np.float32).reshape(-1, 2)
        box = data.get("obj_bbox")
        box = np.asarray(box, dtype=np.float32).reshape(4) if box else None
        if box is not None and (not np.isfinite(box).all() or box[2] <= box[0] or box[3] <= box[1]):
            raise ValueError("Invalid bounding box")
        if not len(positive) and box is None:
            raise ValueError("Click inside the ball or supply a bounding box")
        if any(not np.isfinite(a).all() for a in (positive, negative)):
            raise ValueError("Non-finite prompt coordinates")
        raw = base64.b64decode(data["image"], validate=True)
        image_key = hashlib.sha256(raw).digest()
        if image_key != self.image_key:
            with Image.open(io.BytesIO(raw)) as source:
                image = np.array(source.convert("RGB"))
            self.predictor.set_image(image)
            self.image_key = image_key
        points = np.concatenate((positive, negative))
        labels = np.array([1] * len(positive) + [0] * len(negative))
        masks, scores, _ = self.predictor.predict(
            point_coords=points if len(points) else None,
            point_labels=labels if len(points) else None,
            box=box,
            multimask_output=box is None,
        )
        mask = masks[int(np.argmax(scores))].astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return {"shapes": []}
        # Single-object interaction: prefer the component containing a positive click.
        containing = [c for c in contours if any(
            cv2.pointPolygonTest(c, (float(p[0]), float(p[1])), False) >= 0
            for p in positive
        )]
        contour = max(containing or contours, key=cv2.contourArea)
        component = np.zeros_like(mask)
        cv2.drawContours(component, [contour], -1, 1, cv2.FILLED)
        mask &= component
        ys, xs = np.nonzero(mask)
        if len(xs) < 3:
            return {"shapes": []}
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
        flat = mask[y0:y1 + 1, x0:x1 + 1].ravel()
        boundaries = np.r_[0, np.flatnonzero(flat[1:] != flat[:-1]) + 1, len(flat)]
        runs = np.diff(boundaries).tolist()
        if flat[0]:
            runs.insert(0, 0)
        return {"shapes": [{"type": "mask", "points": runs + [x0, y0, x1, y1], "attributes": []}]}


class Handler(BaseHTTPRequestHandler):
    def authorized(self):
        if hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + TOKEN):
            return True
        self.reply(401, {"error": "Unauthorized"})
        return False

    def reply(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.authorized():
            return
        if self.path == "/health":
            self.reply(200, {"status": "ready", "model": FUNCTION_ID, "device": DEVICE,
                             "gpu_allocated_bytes": torch.mps.current_allocated_memory()})
        elif self.path == "/api/functions":
            self.reply(200, {FUNCTION_ID: METADATA})
        elif self.path == f"/api/functions/{FUNCTION_ID}":
            self.reply(200, METADATA)
        else:
            self.reply(404, {"error": "Not found"})

    def do_POST(self):
        if not self.authorized():
            return
        if self.path != "/api/function_invocations" or self.headers.get("x-nuclio-function-name") != FUNCTION_ID:
            self.reply(404, {"error": "Unknown function"})
            return
        length = int(self.headers.get("Content-Length", 0))
        if not 0 < length <= 32 * 1024 * 1024:
            self.reply(413, {"error": "Invalid payload size"})
            return
        started = time.monotonic()
        try:
            result = self.server.segmenter.predict(json.loads(self.rfile.read(length)))
        except (ValueError, KeyError, OSError) as error:
            self.reply(400, {"error": str(error)})
            return
        except Exception:
            logging.exception("Inference failed")
            self.reply(500, {"error": "Inference failed; inspect service logs"})
            return
        logging.info("Inference %.3fs, %d mask(s)", time.monotonic() - started, len(result["shapes"]))
        self.reply(200, result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = HTTPServer(("127.0.0.1", 8071), Handler)
    server.segmenter = Segmenter()
    logging.info("SAM 2.1 Large ready on Apple GPU, authenticated loopback port 8071")
    server.serve_forever()
