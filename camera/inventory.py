"""Print read-only Jetson and camera inventory as JSON (standard library only)."""

import glob
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess


def run(*args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return {"returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc)}


def read(path):
    try:
        return Path(path).read_text().strip().strip("\x00")
    except OSError as exc:
        return str(exc)


def main():
    data = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "model": read("/proc/device-tree/model"),
        "os": read("/etc/os-release"),
        "l4t": read("/etc/nv_tegra_release"),
        "cuda": read("/usr/local/cuda/version.json"),
        "packages": run("dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${db:Status-Status}\n", "nvidia-jetpack", "nvidia-l4t-core", "cuda-cudart-*", "libnvinfer10"),
        "usb": run("lsusb"),
        "cameras": [{"device": "/dev/" + Path(path).parent.name, "name": read(path)} for path in sorted(glob.glob("/sys/class/video4linux/video*/name"))],
        "stable_camera_paths": glob.glob("/dev/v4l/by-id/*"),
        "v4l2": run("v4l2-ctl", "--list-devices"),
        "formats": run("v4l2-ctl", "--device=/dev/video0", "--list-formats-ext"),
    }
    try:
        import cv2
        data["opencv"] = {"version": cv2.__version__, "build": cv2.getBuildInformation()}
    except ImportError as exc:
        data["opencv"] = {"error": str(exc)}
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
