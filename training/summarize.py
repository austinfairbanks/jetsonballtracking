"""Create a reviewable results page from completed, measured stage reports."""

import json
from pathlib import Path

from pipeline import OUT, ROOT


def main():
    cv = json.loads((OUT / "cv_summary.json").read_text())
    final = json.loads((OUT / "final-result.json").read_text())
    test = json.loads((OUT / "test-result.json").read_text())
    video_path = OUT / "video/IMG_9217/report.json"
    video = json.loads(video_path.read_text()) if video_path.exists() else None
    prefix = str(OUT.relative_to(ROOT))
    rows = ["# First YOLO11n-seg results", "",
            "Three-fold cross-validation kept source recordings intact. All 519 development",
            "images were used for the final refit; the 123 group-8 images were excluded",
            "from training and selection. These are results from the collected backyard",
            "recordings, not evidence of performance in arbitrary environments.", "",
            "| Fold | Best epoch | Validation mask mAP50 | Validation mask mAP50–95 |",
            "| --- | ---: | ---: | ---: |"]
    for fold in cv["folds"]:
        metrics = fold["selected_metrics"]
        rows.append(f"| {fold['stage']} | {fold['selected_epoch']} | {metrics['metrics/mAP50(M)']:.4f} | {metrics['metrics/mAP50-95(M)']:.4f} |")
    rows.extend(["", f"Mean selected validation mask mAP50–95: **{cv['mean_mask_map50_95']:.4f}**",
                 f"(population SD across three folds: {cv['std_mask_map50_95']:.4f}). These validation",
                 "scores were used for epoch selection and are not an independent final test.", "",
                 f"Final refit: **{final['epochs_completed']} epochs**, fresh pretrained initialization,",
                 "fixed duration selected from the median best fold epoch. No refit validation",
                 "or test-based checkpoint selection. Final epoch EMA weights were evaluated.", "",
                 "## Held-out test", "", "| Metric | Value |", "| --- | ---: |"])
    for key, value in test["metrics"].items():
        if key.startswith("metrics/"):
            rows.append(f"| {key.removeprefix('metrics/')} | {value:.4f} |")
    point = test["operating_point"]
    rows.extend(["", "At confidence 0.25, using box IoU ≥0.5 for a match:", "",
                 f"- Precision: {point['precision']:.3%}; recall: {point['recall']:.3%}.",
                 f"- TP / FP / FN: {point['true_positives']} / {point['false_positives']} / {point['false_negatives']}.",
                 f"- Negative frames with false positives: {point['negative_frames_with_false_positive']} / 3.",
                 "", "The three negative test frames provide very limited evidence about false alarms.",
                 "Ultralytics summary precision/recall above use its curve-selected operating point;",
                 "the separately calculated counts use the fixed demo threshold.", "",
                 f"[Final checkpoint]({prefix}/runs/final/weights/last.pt) ·",
                 f"[Test metrics]({prefix}/test-result.json) ·",
                 f"[All test predictions]({prefix}/test_predictions/predictions.json)", "",
                 "Test prediction contact sheets:", ""])
    rows.extend(f"- [Sheet {i}]({prefix}/test_predictions/contact-sheet-{i}.jpg)" for i in range(1, 7))
    rows.extend(["", "## Video", ""])
    if video:
        rows.extend([f"Processed and verified **{video['frames_processed']:,} / {video['frames_decoded_from_output']:,} frames**",
                     "from IMG_9217.MOV. Every frame was inferred independently using the exact tested",
                     "checkpoint and confidence 0.25. No tracking or skipped frames.", "",
                     f"[Annotated MP4]({prefix}/video/IMG_9217/annotated.mp4) ·",
                     f"[Frame predictions]({prefix}/video/IMG_9217/predictions.jsonl) ·",
                     f"[Video verification report]({prefix}/video/IMG_9217/report.json)", "",
                     "The MP4 is silent and uses the source average frame rate. JSONL retains source",
                     "timestamps. Intervening frames have no ground truth, so the video is qualitative",
                     "evidence. Runtime measurements here are on Mac MPS, not Jetson."])
    else:
        rows.append("Video inference is pending; no completed video report exists yet.")
    rows.extend(["", "## Reproduction", "", "See [TRAINING_PLAN.md](TRAINING_PLAN.md) for settings, split, environment and runtime fixes.",
                 "The final checkpoint SHA256 is:", "", f"`{final['checkpoint_sha256']}`", ""])
    (ROOT / "TRAINING_RESULTS.md").write_text("\n".join(rows))


if __name__ == "__main__":
    main()
