"""Fetch the pinned official checkpoint; never load a model or open a camera."""

import hashlib
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "artifacts/models/yolo11n.pt"
URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt"
# SHA256 of the official release asset retrieved September 15, 2026.
SHA256 = "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"


def check_weights():
    if not WEIGHTS.is_file():
        raise RuntimeError("Model weights missing; run bash detection/setup.sh on the Jetson")
    if hashlib.sha256(WEIGHTS.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError(f"Checkpoint checksum mismatch: {WEIGHTS}")


def main():
    if WEIGHTS.exists():
        check_weights()
        print(f"Verified existing checkpoint: {WEIGHTS}")
        return
    WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL, timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError("Downloaded checkpoint failed SHA256 verification")
    temporary = WEIGHTS.with_suffix(".pt.part")
    temporary.write_bytes(data)
    temporary.replace(WEIGHTS)
    print(f"Downloaded and verified checkpoint: {WEIGHTS}")


if __name__ == "__main__":
    main()
