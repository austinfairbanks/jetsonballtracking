# YOLO11n-seg: three-fold recording-grouped cross-validation

Completed September 15, 2026 on the Mac mini's M2 Pro GPU: three folds, an
8-epoch refit, 123-image test evaluation and all 5,528 video-frame predictions.
See [TRAINING_RESULTS.md](TRAINING_RESULTS.md) and the subsequent
[Jetson deployment results](DEPLOYMENT_RESULTS.md).

The frozen dataset remains unchanged. Pool its original train/validation sets
into 519 development images; keep group 8's 123 test images excluded from all
training and model selection. Each group is a separate source recording.

| Fold | Validation recording groups | Train images | Validation images |
| --- | --- | ---: | ---: |
| 1 | 7 | 330 | 189 |
| 2 | 1, 6 | 360 | 159 |
| 3 | 2, 3, 4, 5 | 348 | 171 |

Groups are allocated greedily by image count, with deterministic group-ID
tie breaking. Every development image appears in validation exactly once.
This tests transfer between recordings in the collected environments; it does
not establish performance on arbitrary environments or every possible image.

1. Initialize each fold independently from the same official `yolo11n-seg.pt`.
   Train one class (`volleyball`) at input size 640, batch 8, AdamW learning
   rate 0.001, seed 42, mask ratio 2, maximum 100 epochs, patience 20. Disable
   mixed precision on MPS. Exact settings and hashes are saved in `plan.json`.
2. Choose each fold checkpoint using validation mask mAP50–95. Use the median
   best epoch (rounded up) as the final training duration. CV scores describe
   validation used for selection; the separate test set is the final estimate.
3. Reinitialize from pretrained weights and train on all 519 development images
   for that fixed duration. Disable validation and checkpoint selection during
   refit; use the final epoch's EMA weights. Test labels never choose epochs,
   confidence thresholds, or checkpoints.
4. Evaluate that checkpoint on all 123 test images. Save box/mask metrics,
   precision/recall at confidence 0.25 and box IoU 0.5, negative-frame false
   positives, per-image predictions, overlays, and six contact sheets.
5. Run the same frozen model on every frame of `~/downloads/IMG_9217.MOV`.
   The transferred file initially probed as 5,528 frames at approximately
   30 FPS, 1080×1920 after automatic rotation. Save a silent annotated MP4 and
   frame-indexed JSONL with source timestamps, confidence, box center, and mask
   polygons. Each image is processed independently; there is no tracking,
   frame skipping, or prior-frame state. Verify every output frame decodes.
6. Review measured results, then deploy to the Jetson. Mac timings are not
   Jetson throughput. If test-video failures inform the next model iteration,
   obtain a fresh final test recording for that iteration.

## Reproduction and outputs

```bash
bash training/launch.sh
training/.venv/bin/python training/video.py ~/downloads/IMG_9217.MOV
```

Run long jobs in tmux. `training/uv.lock` pins the isolated environment; the
working SAM and Jetson environments are untouched. The pipeline checks the
frozen dataset before starting and resumes unstripped interrupted checkpoints.

Outputs: `artifacts/training/yolo11n-seg-cv-v1/`:

- `plan.json`, `environment.json`, `pretrained/source.json`: reproducibility.
- `status.json`, `fold*-epochs.jsonl`, `fold*.log`: progress and diagnostics.
- `cv_summary.json`, `fold*-result.json`: CV results and chosen refit duration.
- `runs/final/weights/last.pt`, `final-result.json`: final model and hash.
- `test-result.json`, `test_predictions/`: test metrics and all frame overlays.
- `video/IMG_9217/`: annotated video, per-frame predictions and verified report.

The video overlay uses the source's average frame rate and omits audio; source
timestamps are preserved in JSONL. Predictions on unannotated intervening video
frames provide qualitative evidence, not additional ground-truth accuracy.

## Runtime fixes

Two attempts with Ultralytics 8.3.203 aborted in native tensor memory handling
before completing epoch 1, using PyTorch 2.8.0 then 2.9.1. Upgraded to Ultralytics
8.3.204, which includes the upstream [MPS transfer corruption fix](https://github.com/ultralytics/ultralytics/pull/22181).
The environment pins PyTorch 2.9.1 and torchvision 0.24.1. All attempts restart
from the original pretrained checkpoint; no completed fold results were lost.

At Austin's request, the SAM GPU server was unloaded with launchctl to free
memory. Its files and annotations remain intact. The launch agent is unloaded
for this login session; it may start again on a subsequent login.
