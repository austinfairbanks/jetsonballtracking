"""Read-only end-to-end smoke test; writes previews locally, never CVAT labels.

Run: uv run --no-project --python 3.12 --with pillow ops/cvat/test_sam2.py
"""
import hashlib
import http.cookiejar
import io
import json
from config import cvat_base_url
from pathlib import Path
import time
import urllib.request

from PIL import Image

ROOT = Path(__file__).resolve().parent
BASE = cvat_base_url()
cookies = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))


def request(path, payload=None):
    headers = {"Origin": BASE, "Referer": BASE + "/", "Content-Type": "application/json"}
    for cookie in cookies:
        if cookie.name == "csrftoken":
            headers["X-CSRFToken"] = cookie.value
    req = urllib.request.Request(BASE + path, headers=headers,
        data=json.dumps(payload).encode() if payload is not None else None)
    with opener.open(req, timeout=120) as response:
        return response.read()


request("/api/auth/login", json.loads((ROOT / ".local/login.json").read_text()))
before = request("/api/jobs/1/annotations")
models = json.loads(request("/api/lambda/functions"))
assert any(m["id"] == "volleyball-sam2" for m in models), models
assert not any(m["id"] == "volleyball-mobilesam" for m in models), models
print("SAM 2.1 Large listed by CVAT", flush=True)

samples = [
    (0, (62, 1510), (20, 1475, 104, 1553), "shade_grass"),
    (199, (320, 747), (301, 728, 338, 766), "small_roof"),
    (399, (589, 619), (558, 589, 620, 649), "sky"),
    (643, (99, 1561), (70, 1524, 124, 1601), "occluded"),
]
out = ROOT / ".local/sam2-tests"
out.mkdir(parents=True, exist_ok=True)
summary = []
for frame, center, box, name in samples:
    source = Image.open(io.BytesIO(request(f"/api/tasks/1/data?type=frame&number={frame}&quality=original"))).convert("RGB")
    for prompt in (["point", "box", "roi"] if frame in (0, 199) else ["point", "box"]):
        payload = {"task": 1, "job": 1, "frame": frame, "pos_points": [center], "neg_points": [], "obj_bbox": []}
        if prompt == "box":
            payload["obj_bbox"] = [list(box[:2]), list(box[2:])]
        if prompt == "roi":
            payload["roi"] = [max(0, box[0] - 70), max(0, box[1] - 70), min(source.width, box[2] + 70), min(source.height, box[3] + 70)]
        started = time.monotonic()
        result = json.loads(request("/api/lambda/functions/volleyball-sam2", payload))
        elapsed = time.monotonic() - started
        assert result["shapes"], (frame, prompt, result)
        canvas = source.copy()
        mask_bounds = []
        for shape in result["shapes"]:
            assert shape["type"] == "mask"
            *runs, x0, y0, x1, y1 = shape["points"]
            width, height = x1 - x0 + 1, y1 - y0 + 1
            assert sum(runs) == width * height
            assert 0 <= x0 <= x1 < source.width and 0 <= y0 <= y1 < source.height
            values = bytearray()
            for i, count in enumerate(runs):
                values.extend(bytes([255 if i % 2 else 0]) * count)
            mask = Image.frombytes("L", (width, height), bytes(values))
            green = Image.new("RGB", (width, height), (0, 255, 0))
            overlay = Image.blend(source.crop((x0, y0, x1 + 1, y1 + 1)), green, 0.4)
            canvas.paste(overlay, (x0, y0), mask)
            mask_bounds.append([x0, y0, x1, y1])
        crop = (max(0, box[0] - 50), max(0, box[1] - 50), min(source.width, box[2] + 50), min(source.height, box[3] + 50))
        preview = canvas.crop(crop).resize((600, 600))
        preview.save(out / f"{name}-{prompt}.png")
        row = {"frame": frame, "case": name, "prompt": prompt, "seconds": round(elapsed, 3), "mask_bounds": mask_bounds}
        summary.append(row)
        print(json.dumps(row), flush=True)
after = request("/api/jobs/1/annotations")
unchanged = hashlib.sha256(before).digest() == hashlib.sha256(after).digest()
print("Annotations unchanged during test:", unchanged, flush=True)
assert unchanged, "Annotations changed during read-only test; inspect concurrent edits"
(out / "results.json").write_text(json.dumps({"samples": summary, "annotations_unchanged": unchanged}, indent=2))
