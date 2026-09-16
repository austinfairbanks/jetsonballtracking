# First YOLO11n-seg results

Three-fold cross-validation kept source recordings intact. All 519 development
images were used for the final refit; the 123 group-8 images were excluded
from training and selection. These are results from the collected backyard
recordings, not evidence of performance in arbitrary environments.

| Fold | Best epoch | Validation mask mAP50 | Validation mask mAP50–95 |
| --- | ---: | ---: | ---: |
| fold1 | 36 | 0.7708 | 0.2668 |
| fold2 | 8 | 0.4001 | 0.1126 |
| fold3 | 3 | 0.5507 | 0.2255 |

Mean selected validation mask mAP50–95: **0.2016**
(population SD across three folds: 0.0652). These validation
scores were used for epoch selection and are not an independent final test.

Final refit: **8 epochs**, fresh pretrained initialization,
fixed duration selected from the median best fold epoch. No refit validation
or test-based checkpoint selection. Final epoch EMA weights were evaluated.

## Held-out test

| Metric | Value |
| --- | ---: |
| precision(B) | 0.9722 |
| recall(B) | 0.8758 |
| mAP50(B) | 0.9530 |
| mAP50-95(B) | 0.6672 |
| precision(M) | 0.9330 |
| recall(M) | 0.8000 |
| mAP50(M) | 0.8614 |
| mAP50-95(M) | 0.3370 |

At confidence 0.25, using box IoU ≥0.5 for a match:

- Precision: 88.000%; recall: 91.667%.
- TP / FP / FN: 110 / 15 / 10.
- Negative frames with false positives: 0 / 3.

The three negative test frames provide very limited evidence about false alarms.
Ultralytics summary precision/recall above use its curve-selected operating point;
the separately calculated counts use the fixed demo threshold.

[Final checkpoint](artifacts/training/yolo11n-seg-cv-v1/runs/final/weights/last.pt) ·
[Test metrics](artifacts/training/yolo11n-seg-cv-v1/test-result.json) ·
[All test predictions](artifacts/training/yolo11n-seg-cv-v1/test_predictions/predictions.json)

Test prediction contact sheets:

- [Sheet 1](artifacts/training/yolo11n-seg-cv-v1/test_predictions/contact-sheet-1.jpg)
- [Sheet 2](artifacts/training/yolo11n-seg-cv-v1/test_predictions/contact-sheet-2.jpg)
- [Sheet 3](artifacts/training/yolo11n-seg-cv-v1/test_predictions/contact-sheet-3.jpg)
- [Sheet 4](artifacts/training/yolo11n-seg-cv-v1/test_predictions/contact-sheet-4.jpg)
- [Sheet 5](artifacts/training/yolo11n-seg-cv-v1/test_predictions/contact-sheet-5.jpg)
- [Sheet 6](artifacts/training/yolo11n-seg-cv-v1/test_predictions/contact-sheet-6.jpg)

## Video

Processed and verified **5,528 / 5,528 frames**
from IMG_9217.MOV. Every frame was inferred independently using the exact tested
checkpoint and confidence 0.25. No tracking or skipped frames.

[Annotated MP4](artifacts/training/yolo11n-seg-cv-v1/video/IMG_9217/annotated.mp4) ·
[Frame predictions](artifacts/training/yolo11n-seg-cv-v1/video/IMG_9217/predictions.jsonl) ·
[Video verification report](artifacts/training/yolo11n-seg-cv-v1/video/IMG_9217/report.json)

The MP4 is silent and uses the source average frame rate. JSONL retains source
timestamps. Intervening frames have no ground truth, so the video is qualitative
evidence. Runtime measurements here are on Mac MPS, not Jetson.

## Reproduction

See [TRAINING_PLAN.md](TRAINING_PLAN.md) for settings, split, environment and runtime fixes.
The final checkpoint SHA256 is:

`3582ce6abfe97d76149c8b88338043ca8f1dd3c3fa19966c9998a473d3d3d3cf`
