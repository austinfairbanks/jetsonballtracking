"""Export task 1 without changing labels; credentials stay in .local/login.json.

Run with a project Python environment in tmux. Creates a fresh timestamped
directory under dataset/exports and checks annotations were stable throughout.
"""

import hashlib
import json
from pathlib import Path
import shutil
import time
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[2]
BASE = "http://127.0.0.1:8082"


def main():
    out = ROOT / "dataset/exports" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True, exist_ok=False)
    print(f"Output: {out}", flush=True)
    login = (ROOT / "ops/cvat/.local/login.json").read_bytes()
    req = urllib.request.Request(BASE + "/api/auth/login", data=login,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        token = json.load(response)["key"]

    def request(path, method="GET"):
        req = urllib.request.Request(BASE + path, method=method,
                                     headers={"Authorization": "Token " + token})
        return urllib.request.urlopen(req, timeout=120)

    def get(path):
        with request(path) as response:
            return json.load(response)

    def save_json(name, value):
        (out / name).write_text(json.dumps(value, indent=2) + "\n")

    before = get("/api/tasks/1/annotations")
    save_json("annotations.json", before)
    for name, path in [("task.json", "/api/tasks/1"),
                       ("data_meta.json", "/api/tasks/1/data/meta"),
                       ("labels.json", "/api/labels?task_id=1"),
                       ("server_about.json", "/api/server/about")]:
        save_json(name, get(path))
    archives = {}
    jobs = [("cvat-task-1-backup.zip", "/api/tasks/1/backup/export?location=local"),
            ("volleyball-segmentation.zip", "/api/tasks/1/dataset/export?" +
             urllib.parse.urlencode({"format": "Ultralytics YOLO Segmentation 1.0",
                                     "save_images": "true", "location": "local"}))]
    for filename, endpoint in jobs:
        try:
            with request(endpoint, "POST") as response:
                job = json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 409:
                raise
            job = json.load(error)
        rid = job["rq_id"]
        print(f"Queued {filename}: {rid}", flush=True)
        deadline = time.monotonic() + 3600
        last = None
        while time.monotonic() < deadline:
            state = get("/api/requests/" + urllib.parse.quote(rid, safe=""))
            if state["status"] != last:
                print(f"{filename}: {state['status']}", flush=True)
                last = state["status"]
            if state["status"] == "finished":
                break
            if state["status"] in {"failed", "canceled"}:
                raise RuntimeError(state.get("message", "Export failed"))
            time.sleep(5)
        else:
            raise TimeoutError("Export exceeded one hour")
        save_json(filename + ".request.json", state)
        url = urllib.parse.urlsplit(state["result_url"])
        if not url.path.startswith("/api/tasks/1/"):
            raise ValueError("Unexpected export download path")
        destination = out / filename
        partial = destination.with_suffix(".zip.part")
        with request(url.path + ("?" + url.query if url.query else "")) as response:
            with partial.open("wb") as target:
                shutil.copyfileobj(response, target, length=1024 * 1024)
        partial.rename(destination)
        with destination.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        with zipfile.ZipFile(destination) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"Corrupt ZIP entry: {bad}")
            members = archive.namelist()
        archives[filename] = {"sha256": digest, "bytes": destination.stat().st_size,
                              "entries": len(members)}
        print(f"Verified {filename}: {destination.stat().st_size} bytes, {len(members)} entries", flush=True)
    after = get("/api/tasks/1/annotations")
    save_json("annotations_after.json", after)
    if before != after:
        raise RuntimeError("Annotations changed during export; do not freeze this snapshot")
    save_json("export_report.json", {"task_id": 1, "annotations_unchanged": True,
                                   "archives": archives})
    print("SUCCESS: both archives verified; annotations unchanged.", flush=True)


if __name__ == "__main__":
    main()
