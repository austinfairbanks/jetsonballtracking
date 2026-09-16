"""Run the frozen, evaluated checkpoint on every decoded video frame."""

import argparse
import json
import math
from pathlib import Path
import time

from pipeline import OUT, sha, write_json


def main(source):
    import cv2
    import torch
    from ultralytics import YOLO

    source = source.expanduser().resolve()
    destination = OUT / "video" / source.stem
    destination.mkdir(parents=True, exist_ok=True)
    report_path = destination / "report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text())
        if report["source_sha256"] != sha(source):
            raise RuntimeError("Source changed since completed video inference")
        print(f"Completed video retained: {destination}", flush=True)
        return
    final = json.loads((OUT / "final-result.json").read_text())
    test = json.loads((OUT / "test-result.json").read_text())
    checkpoint = Path(final["checkpoint"])
    checkpoint_sha = sha(checkpoint)
    assert checkpoint_sha == final["checkpoint_sha256"] == test["checkpoint_sha256"]
    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS unavailable")
    torch.set_num_threads(4)
    source_sha = sha(source)
    source_stat = source.stat()
    model = YOLO(checkpoint)
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open {source}")
    capture.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
    expected_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(fps) or fps <= 0:
        raise RuntimeError("Invalid source frame rate")
    rotation = capture.get(cv2.CAP_PROP_ORIENTATION_META)
    video_path = destination / "annotated.mp4"
    writer = None
    frame_count = detected_frames = detection_count = 0
    began = time.monotonic()
    try:
        with (destination / "predictions.jsonl").open("w") as stream:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                timestamp_ms = capture.get(cv2.CAP_PROP_POS_MSEC)
                height, width = frame.shape[:2]
                if writer is None:
                    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
                    if not writer.isOpened():
                        raise RuntimeError("Video encoder failed to open")
                result = model.predict(frame, imgsz=640, conf=.25, iou=.7,
                                       device="mps", retina_masks=True, verbose=False)[0]
                boxes = result.boxes.xyxy.cpu().tolist()
                confidences = result.boxes.conf.cpu().tolist()
                polygons = result.masks.xy if result.masks is not None else []
                detections = [{"confidence": confidence, "box_xyxy": box,
                               "box_center_xy": [(box[0]+box[2])/2, (box[1]+box[3])/2],
                               "mask_polygon_xy": polygons[i].tolist() if len(polygons) > i else []}
                              for i, (box, confidence) in enumerate(zip(boxes, confidences))]
                annotated = result.plot()
                cv2.putText(annotated, f"YOLO11n-seg | frame {frame_count} | detections {len(boxes)}",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 255), 2)
                writer.write(annotated)
                stream.write(json.dumps({"frame_index": frame_count, "source_timestamp_ms": timestamp_ms,
                                         "detections": detections}, allow_nan=False) + "\n")
                if frame_count in (0, expected_frames // 4, expected_frames // 2, 3 * expected_frames // 4):
                    cv2.imwrite(str(destination / f"preview-{frame_count:06d}.jpg"), annotated)
                frame_count += 1
                detected_frames += bool(boxes)
                detection_count += len(boxes)
                if frame_count % 100 == 0:
                    elapsed = time.monotonic() - began
                    progress = {"state": "running", "frames": frame_count, "expected_frames": expected_frames,
                                "elapsed_seconds": elapsed, "pipeline_fps": frame_count / elapsed}
                    write_json(destination / "status.json", progress)
                    print(json.dumps(progress), flush=True)
    finally:
        capture.release()
        if writer is not None:
            writer.release()
    assert frame_count > 0 and frame_count == expected_frames, (frame_count, expected_frames)
    assert source.stat().st_size == source_stat.st_size and sha(source) == source_sha, "Source changed during inference"
    # Decode the complete output to verify that the encoder retained every frame.
    check = cv2.VideoCapture(str(video_path))
    verified_frames = 0
    while check.read()[0]:
        verified_frames += 1
    check.release()
    assert verified_frames == frame_count, (verified_frames, frame_count)
    elapsed = time.monotonic() - began
    report = {"source": str(source), "source_sha256": source_sha, "source_bytes": source_stat.st_size,
              "checkpoint": str(checkpoint), "checkpoint_sha256": checkpoint_sha,
              "frames_processed": frame_count, "frames_decoded_from_output": verified_frames,
              "frames_with_detections": detected_frames, "detections": detection_count,
              "output": str(video_path), "output_sha256": sha(video_path),
              "width": width, "height": height, "fps": fps, "source_rotation_metadata": rotation,
              "imgsz": 640, "confidence": .25, "nms_iou": .7, "device": "Mac MPS",
              "temporal_state": False, "frame_stride": 1, "elapsed_seconds_including_output_verification": elapsed,
              "notes": "Silent overlay video at source average FPS; original frame timestamps retained in JSONL. No labels for intervening frames, so detection counts are not accuracy metrics."}
    write_json(report_path, report)
    write_json(destination / "status.json", {"state": "complete", "frames": frame_count, "output": str(video_path)})
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    main(parser.parse_args().source)
