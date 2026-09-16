# Live perception requirements

These are user-approved targets for the image-only volleyball perception model
and its processing pipeline. They are acceptance targets, not claims that the
current model meets them. Camera movement, motion prediction and tracking
behavior are outside this definition.

## Operating conditions

- **Target object:** the specific volleyball used for this project. Recognition
  of arbitrary volleyballs or other sports balls is not an approved requirement.
- **Current operating target:** Austin's backyard, in most lighting conditions
  in which he would normally play volleyball. Evaluate representative brightness,
  shadow and background variations rather than claiming success from one scene.
- **Motion coverage:** ordinary volleyball activity, including setting, serving,
  rolling along the ground and being held. For this stage, coverage means correct
  per-image detection/localization throughout those activities.
- **Ball absent:** expected output is no volleyball detection. Include scenes
  without the ball in evaluation; every emitted detection in those frames counts
  as a false positive. Report false detections and the fraction of no-ball frames
  with a false detection separately. The overall >99% precision target does not
  itself specify a no-ball-frame false-positive rate; no numerical limit for that
  separate rate has been approved.
- **Long-term goal:** generalize to indoor and outdoor conditions with this same
  ball. This is a broader coverage goal, not a demonstrated capability or a claim
  that the model works under every possible visibility condition.
- Exact supported distances, ball sizes in pixels, lighting limits, motion speeds
  and occlusion limits remain unquantified. Record the conditions actually tested
  and avoid extrapolating a pass to conditions absent from the evaluation.

## Throughput and processing latency

- **Throughput target:** nominal 30 FPS live capture and processing of distinct
  incoming frames, without an accumulating backlog.
- **Processing latency:** p95 ≤33 ms, measured from a decoded frame being
  available to the application until predicted ball coordinates and mask are
  ready. Include preprocessing, inference, synchronization and postprocessing.
- **Steady-state evaluation:** apply throughput and latency targets after model
  loading and warmup. Record the warmup procedure and report startup time
  separately. Include both ball-present and no-ball frames in the timed run.
- This latency boundary excludes camera buffering, decoding, drawing, display
  and network streaming. Capture-to-result and capture-to-display targets
  remain undefined until measured.
- A p95 target is not a maximum-latency guarantee, and alone does not guarantee
  sustained throughput. No separate worst-case latency limit is approved.
- Current configuration: YOLO11n-seg, TensorRT FP16, batch 1, 640×640 input.

## Detection quality

- **Precision target:** strictly greater than 99%, calculated as TP / (TP + FP).
- **Recall objective:** maximize recall while satisfying the precision target.
  No numerical recall minimum has been approved. Report recall and consecutive
  missed-frame runs; accepting more misses does not make prolonged gaps harmless.
- Prefer fewer false detections over fewer missed balls.
- A confidence score of 0.99 is not equivalent to 99% measured precision.
  Select a threshold using development data, freeze it, then evaluate on fresh
  held-out recordings representative of the intended scenes, including no-ball
  frames. Report counts and dataset composition alongside percentages.

## Correct-localization criteria

Let B be the predicted bounding box, M the annotated ground-truth ball mask,
and G the tight bounding box derived from M. A prediction must pass **both**:

1. **Bounding-box IoU ≥0.50:** area(B ∩ G) / area(B ∪ G) ≥0.50.
2. **Ground-truth mask coverage ≥0.50:** area(B ∩ M) / area(M) ≥0.50.

Coverage uses the annotated ball mask area as its denominator, not the union
area. A box must therefore contain at least half the annotated ball. The IoU
requirement remains necessary because an excessively large box could otherwise
achieve full mask coverage while localizing the ball poorly.

Use one-to-one matching between predictions and labeled balls. Unmatched or
duplicate predictions count as false positives; unmatched labeled balls count
as false negatives. A prediction failing either localization criterion cannot
count as a true positive. Also report ball-center error as a diagnostic, with
no approved numerical limit yet.

## Predicted mask quality

The coverage rule evaluates the **predicted box against the ground-truth mask**.
It does not assess the model's predicted mask outline. Predicted mask quality
is secondary; retain mask metrics as diagnostics, with no minimum predicted-mask
IoU or mAP target currently required.

## Current evidence

See [DEPLOYMENT_RESULTS.md](DEPLOYMENT_RESULTS.md) for measured performance and
the existing accuracy baseline. That accuracy evaluation used box IoU ≥0.50
alone; it has not yet been recomputed with the additional mask-coverage rule.
The 30 FPS live target and >99% precision target are not yet demonstrated.
