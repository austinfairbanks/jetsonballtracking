"""Three recording-grouped YOLO11n-seg fits, fixed-duration refit, then test.

Run through launch.sh in tmux. Child processes isolate GPU memory between fits.
Completed stages are checkpointed on disk; rerunning resumes unfinished work.
"""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/training/yolo11n-seg-cv-v1"
DATA = OUT / "data"
WEIGHTS = OUT / "pretrained/yolo11n-seg.pt"
SOURCE = ROOT / "dataset/volleyball-v1"
os.environ["YOLO_CONFIG_DIR"] = str(OUT / "ultralytics-config")
os.environ["YOLO_AUTOINSTALL"] = "false"
os.environ["MPLCONFIGDIR"] = str(OUT / "matplotlib-config")
os.environ["WANDB_MODE"] = "disabled"
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["OMP_NUM_THREADS"] = "4"

COMMON = dict(task="segment", imgsz=640, batch=8, device="mps", workers=0,
              epochs=100, patience=20, seed=42, deterministic=True,
              optimizer="AdamW", lr0=0.001, lrf=0.01, weight_decay=0.0005,
              warmup_epochs=3.0, cos_lr=True, amp=False, cache=False,
              mask_ratio=2, overlap_mask=True, mosaic=1.0, close_mosaic=10,
              mixup=0.0, copy_paste=0.0, degrees=0.0, fliplr=0.5, flipud=0.0,
              plots=True, save=True, save_period=-1, verbose=False)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def status(stage, **details):
    write_json(OUT / "status.json", {"stage": stage, "updated_at": datetime.now(timezone.utc).isoformat(), **details})


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(ROOT / "ops/dataset/verify.py"), str(SOURCE)], check=True)
    with (SOURCE / "split_manifest.csv").open() as stream:
        rows = [r for r in csv.DictReader(stream) if r["included"] == "True"]
    dev = [r for r in rows if int(r["recording_group"]) != 8]
    test = [r for r in rows if int(r["recording_group"]) == 8]
    assert len(dev) == 519 and len(test) == 123
    sizes = Counter(int(r["recording_group"]) for r in dev)
    buckets, counts = [[], [], []], [0, 0, 0]
    for group in sorted(sizes, key=lambda g: (-sizes[g], g)):
        target = min(range(3), key=lambda i: (counts[i], i))
        buckets[target].append(group)
        counts[target] += sizes[group]
    for kind in ("images", "labels"):
        (DATA / kind).mkdir(parents=True, exist_ok=True)
    for row in rows:
        original = SOURCE / "images" / row["split"] / row["image"]
        link = DATA / "images" / row["image"]
        if not link.exists():
            link.symlink_to(original)
        elif link.resolve() != original:
            raise RuntimeError("Unexpected training image mapping")
        src_label = SOURCE / "labels" / row["split"] / Path(row["image"]).with_suffix(".txt")
        shutil.copyfile(src_label, DATA / "labels" / src_label.name)

    def listing(name, selected):
        path = DATA / f"{name}.txt"
        path.write_text("".join(str(DATA / "images" / r["image"]) + "\n" for r in selected))
        return path

    def yaml(name, train, val, test_path=None):
        path = DATA / f"{name}.yaml"
        content = f"path: {DATA}\ntrain: {train}\nval: {val}\nnames:\n  0: volleyball\n"
        if test_path:
            content += f"test: {test_path}\n"
        path.write_text(content)
        return path

    folds, covered = [], []
    for i, groups in enumerate(buckets, 1):
        train = [r for r in dev if int(r["recording_group"]) not in groups]
        val = [r for r in dev if int(r["recording_group"]) in groups]
        assert not ({r["image"] for r in train} & {r["image"] for r in val})
        assert {int(r["recording_group"]) for r in train}.isdisjoint(groups)
        covered.extend(r["image"] for r in val)
        path = yaml(f"fold{i}", listing(f"fold{i}-train", train), listing(f"fold{i}-val", val))
        folds.append({"stage": f"fold{i}", "yaml": str(path), "train_images": len(train),
                      "val_images": len(val), "val_groups": sorted(groups),
                      "train_groups": sorted({int(r["recording_group"]) for r in train})})
    assert sorted(covered) == sorted(r["image"] for r in dev)
    dev_list, test_list = listing("development", dev), listing("test", test)
    # A val key is required by the framework. RefitTrainer disables all validation.
    yaml("final", dev_list, dev_list)
    yaml("evaluation", dev_list, dev_list, test_list)
    plan = {"model": "yolo11n-seg", "folds": folds, "common_settings": COMMON,
            "dataset_freeze_sha256": sha(SOURCE / "freeze.json"),
            "dataset_manifest_sha256": sha(SOURCE / "split_manifest.csv"),
            "selection": "highest validation mask mAP50-95 per fold; latest epoch on ties",
            "refit": "fresh pretrained initialization; median best fold epoch, rounded up; use final epoch EMA",
            "test_policy": "group 8 excluded from all training and CV selection",
            "prediction_confidence": 0.25, "prediction_nms_iou": 0.7,
            "development_images": len(dev), "test_images": len(test)}
    plan_path = OUT / "plan.json"
    if plan_path.exists() and json.loads(plan_path.read_text()) != plan:
        raise RuntimeError("Existing training plan differs; use a new experiment directory")
    write_json(plan_path, plan)
    if not WEIGHTS.exists():
        WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
        url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n-seg.pt"
        with urllib.request.urlopen(url, timeout=120) as response:
            payload = response.read()
        WEIGHTS.write_bytes(payload)
        write_json(OUT / "pretrained/source.json", {"url": url, "sha256": sha(WEIGHTS),
                   "verification": "SHA256 recorded from HTTPS download of official release; no independent upstream digest supplied"})
    if sha(WEIGHTS) != json.loads((OUT / "pretrained/source.json").read_text())["sha256"]:
        raise RuntimeError("Pretrained checkpoint changed")
    return plan


def train(stage):
    import torch
    from ultralytics import settings
    from ultralytics.models.yolo.segment.train import SegmentationTrainer
    from ultralytics.utils.torch_utils import strip_optimizer

    settings.update({"sync": False, "wandb": False, "mlflow": False, "comet": False,
                     "clearml": False, "neptune": False, "tensorboard": False})
    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS unavailable; refusing accidental CPU training")
    torch.set_num_threads(4)
    a = torch.randn(32, 32, device="mps", requires_grad=True)
    a.square().mean().backward()
    torch.mps.synchronize()
    assert torch.isfinite(a.grad).all().item()
    del a

    class CVTrainer(SegmentationTrainer):
        def validate(self):
            metrics = self.validator(self)
            metrics.pop("fitness", None)
            fitness = float(metrics["metrics/mAP50-95(M)"])
            if self.best_fitness is None or fitness > self.best_fitness:
                self.best_fitness = fitness
            return metrics, fitness

    class RefitTrainer(CVTrainer):
        def validate(self):
            # No held-out labels or training-set metrics choose the final checkpoint.
            self.best_fitness = 0.0
            return {k: 0.0 for k in self.metrics}, 0.0

        def final_eval(self):
            strip_optimizer(self.last)

    options = dict(COMMON, model=str(WEIGHTS), data=str(DATA / f"{stage}.yaml"),
                   project=str(OUT / "runs"), name=stage, exist_ok=True)
    if stage == "final":
        selection = json.loads((OUT / "cv_summary.json").read_text())
        options.update(epochs=selection["final_epochs"], patience=0, val=False, plots=False)
    last = OUT / "runs" / stage / "weights/last.pt"
    if last.exists():
        # Resume only unstripped interrupted checkpoints, never restart a completed stage.
        ckpt = torch.load(last, map_location="cpu", weights_only=False)
        if ckpt.get("epoch", -1) >= 0:
            options["resume"] = str(last)
        else:
            raise RuntimeError(f"Completed checkpoint exists without stage report: {stage}")
    trainer = (RefitTrainer if stage == "final" else CVTrainer)(overrides=options)
    began = time.monotonic()

    def progress(current):
        losses = current.tloss.detach().cpu().tolist() if current.tloss is not None else []
        if not all(math.isfinite(x) for x in losses):
            raise RuntimeError("Non-finite training loss")
        metrics = {k: float(v) for k, v in current.metrics.items()}
        record = {"epoch": current.epoch + 1, "epochs_cap": current.epochs,
                  "losses": losses, "metrics": metrics,
                  "elapsed_seconds": round(time.monotonic() - began, 1),
                  "mps_allocated_bytes": torch.mps.current_allocated_memory()}
        status(stage, state="running", **record)
        with (OUT / f"{stage}-epochs.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")

    trainer.add_callback("on_fit_epoch_end", progress)
    status(stage, state="starting", settings=options)
    trainer.train()
    with trainer.csv.open() as stream:
        records = [{k.strip(): float(v) for k, v in row.items()} for row in csv.DictReader(stream)]
    if stage == "final":
        selected = records[-1]
        checkpoint = trainer.last
    else:
        selected = max(records, key=lambda r: (r["metrics/mAP50-95(M)"], r["epoch"]))
        checkpoint = trainer.best
    write_json(OUT / f"{stage}-result.json", {"stage": stage, "epochs_completed": len(records),
               "selected_epoch": int(selected["epoch"]), "selected_metrics": selected,
               "checkpoint": str(checkpoint), "checkpoint_sha256": sha(checkpoint),
               "seconds": round(time.monotonic() - began, 1),
               "validation_disabled": stage == "final"})


def evaluate():
    import numpy as np
    import torch
    from PIL import Image, ImageDraw
    from ultralytics import YOLO

    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS unavailable")
    final = json.loads((OUT / "final-result.json").read_text())
    checkpoint = Path(final["checkpoint"])
    assert sha(checkpoint) == final["checkpoint_sha256"]
    model = YOLO(checkpoint)
    status("test", state="evaluating", checkpoint_sha256=sha(checkpoint))
    metrics = model.val(data=str(DATA / "evaluation.yaml"), split="test", device="mps",
                        imgsz=640, batch=8, workers=0, plots=True, save_json=False,
                        project=str(OUT / "runs"), name="test", exist_ok=True,
                        conf=0.001, iou=0.7, half=False, verbose=False)
    report = {"checkpoint": str(checkpoint), "checkpoint_sha256": sha(checkpoint),
              "images": 123, "positive_images": 120, "negative_images": 3,
              "metrics": {k: float(v) for k, v in metrics.results_dict.items()},
              "timing_ms_per_image": {k: float(v) for k, v in metrics.speed.items()},
              "timing_scope": "Mac MPS validation, not Jetson or camera throughput",
              "prediction_confidence": 0.25, "prediction_nms_iou": 0.7}
    predictions = OUT / "test_predictions"
    predictions.mkdir(exist_ok=True)
    results = model.predict(source=str(DATA / "test.txt"), stream=True, device="mps",
                            imgsz=640, conf=0.25, iou=0.7, retina_masks=True,
                            save=False, verbose=False)
    with (SOURCE / "split_manifest.csv").open() as stream:
        reference = {r["image"]: r for r in csv.DictReader(stream) if r["split"] == "test"}
    rows, tiles = [], []
    tp = fp = fn = negatives_with_fp = 0
    center_errors = []
    for result in results:
        filename = Path(result.path).name
        ref = reference[filename]
        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        masks = result.masks.xy if result.masks is not None else []
        detections = [{"confidence": float(c), "box_xyxy": b.tolist(),
                       "box_center_xy": ((b[:2] + b[2:]) / 2).tolist(),
                       "mask_polygon_xy": np.asarray(masks[i]).tolist() if len(masks) > i else []}
                      for i, (b, c) in enumerate(zip(boxes, confidences))]
        label = DATA / "labels" / Path(filename).with_suffix(".txt")
        coordinates = label.read_text().split()
        matched = False
        if coordinates:
            points = np.array(list(map(float, coordinates[1:]))).reshape(-1, 2)
            height, width = result.orig_shape
            points *= (width, height)
            gt = np.r_[points.min(axis=0), points.max(axis=0)]
            if len(boxes):
                intersection = np.maximum(0, np.minimum(boxes[:, 2:], gt[2:]) - np.maximum(boxes[:, :2], gt[:2])).prod(axis=1)
                union = (boxes[:, 2:] - boxes[:, :2]).prod(axis=1) + np.prod(gt[2:] - gt[:2]) - intersection
                ious = intersection / np.maximum(union, 1e-9)
                index = int(ious.argmax())
                matched = bool(ious[index] >= .5)
                if matched:
                    center_errors.append(float(np.linalg.norm((boxes[index, :2] + boxes[index, 2:] - gt[:2] - gt[2:]) / 2)))
            tp += int(matched)
            fn += int(not matched)
            fp += len(boxes) - int(matched)
        else:
            fp += len(boxes)
            negatives_with_fp += int(len(boxes) > 0)
        canvas = Image.fromarray(result.plot()[:, :, ::-1])
        ImageDraw.Draw(canvas).text((12, 12), f"image {ref['image_number']} | YOLO11n-seg | {len(boxes)} predictions", fill="yellow")
        canvas.save(predictions / Path(filename).with_suffix(".jpg"), quality=92)
        thumb = canvas.copy()
        thumb.thumbnail((180, 320))
        tile = Image.new("RGB", (200, 350), "#181818")
        tile.paste(thumb, ((200 - thumb.width) // 2, 25))
        ImageDraw.Draw(tile).text((5, 5), f"{ref['image_number']} detections={len(boxes)}", fill="white")
        tiles.append(tile)
        rows.append({"image": filename, "ground_truth_objects": int(ref["objects"]),
                     "matched_at_box_iou_0_5": matched, "detections": detections})
    assert len(rows) == 123 and {r["image"] for r in rows} == set(reference)
    for offset in range(0, len(tiles), 24):
        subset = tiles[offset:offset + 24]
        sheet = Image.new("RGB", (1200, 350 * math.ceil(len(subset) / 6)), "#101010")
        for i, tile in enumerate(subset):
            sheet.paste(tile, ((i % 6) * 200, (i // 6) * 350))
        sheet.save(predictions / f"contact-sheet-{offset // 24 + 1}.jpg", quality=90)
    write_json(predictions / "predictions.json", rows)
    report["operating_point"] = {"confidence": .25, "matching_box_iou": .5,
          "true_positives": tp, "false_positives": fp, "false_negatives": fn,
          "precision": tp / (tp + fp) if tp + fp else 0,
          "recall": tp / (tp + fn) if tp + fn else 0,
          "negative_frames_with_false_positive": negatives_with_fp,
          "median_matched_box_center_error_original_pixels": statistics.median(center_errors) if center_errors else None}
    write_json(OUT / "test-result.json", report)
    status("complete", state="complete", test_metrics=report["metrics"], predictions=str(predictions))


def orchestrate():
    plan = prepare()
    versions = {p: importlib.metadata.version(p) for p in ("torch", "torchvision", "ultralytics", "numpy", "pillow", "opencv-python")}
    write_json(OUT / "environment.json", {"python": sys.version, "packages": versions,
               "uv_lock_sha256": sha(ROOT / "training/uv.lock"), "pipeline_sha256": sha(__file__)})

    def run(stage):
        result = OUT / f"{stage}-result.json"
        if result.exists():
            print(f"Completed stage retained: {stage}", flush=True)
            return
        log = OUT / f"{stage}.log"
        print(f"Starting {stage}; log {log}", flush=True)
        with log.open("a") as stream:
            subprocess.run([sys.executable, __file__, "--stage", stage], stdout=stream,
                           stderr=subprocess.STDOUT, check=True)

    for fold in plan["folds"]:
        run(fold["stage"])
    folds = [json.loads((OUT / f"fold{i}-result.json").read_text()) for i in (1, 2, 3)]
    scores = [f["selected_metrics"]["metrics/mAP50-95(M)"] for f in folds]
    summary = {"folds": folds, "mean_mask_map50_95": statistics.mean(scores),
               "std_mask_map50_95": statistics.pstdev(scores),
               "final_epochs": math.ceil(statistics.median(f["selected_epoch"] for f in folds)),
               "selection_used_test": False, "prediction_confidence": .25}
    write_json(OUT / "cv_summary.json", summary)
    run("final")
    run("test")
    print("COMPLETE: CV, final refit, test evaluation, and 123 frame predictions.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["fold1", "fold2", "fold3", "final", "test"])
    args = parser.parse_args()
    try:
        if args.stage == "test":
            evaluate()
        elif args.stage:
            train(args.stage)
        else:
            orchestrate()
    except Exception as error:
        status(args.stage or "orchestration", state="failed", error=f"{type(error).__name__}: {error}")
        raise
