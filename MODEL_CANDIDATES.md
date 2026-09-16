# Image-only Volleyball Localization: Five Architecture Families

Research date: September 15, 2026. Austin subsequently selected the YOLO family
and **YOLO11n-seg as the first custom model**. No custom training has started.
The comparisons below are retained as research background, not an active
architecture sweep. Primary sources are linked alongside claims.

## Task contract

Input: one RGB image, without clicks, a supplied box, text prompts, camera
calibration, or previous video frames. Fixed preprocessing is part of inference.

Output: zero or more volleyball detections in original-image coordinates, each
with a confidence score and box. Retain an instance mask where available; derive
a visible-mask centroid or box center for the overlay. Empty output is valid.
Under occlusion, a visible-mask centroid is not the hidden ball's physical center.
This contract does not provide 3D position, velocity, or temporal tracking.

All five families below can be fine-tuned to operate under this contract. The
semantic model needs connected-component postprocessing to produce detections.
Segmentation heads use the existing annotation work and provide a path to both
masks and boxes; bounding-box-only variants remain possible without relabeling.

An image-only interface is feasible. Reliability on literally any volleyball
image is not established by this small dataset, which covers familiar scenes
and the collected ball appearance. Other ball designs, rooms, backgrounds, and
camera conditions require separate evidence.

## Local constraints and an important measurement

Frozen v1: 427 training images (420 positive), 92 validation images (88 positive),
123 held-out test images. Preserve the split across architecture experiments.

The Jetson has JetPack 7.2.1, CUDA 13.2, TensorRT 10.16, and a working YOLO11n
CUDA detection pipeline using Ultralytics 8.3.203. This proves the detection
path works; it does not yet verify segmentation or TensorRT export. Its observed
~14.8 FPS includes capture and rendering; it is not isolated model latency.
See [camera inventory](camera/BRINGUP.md) and [inference evidence](detection/README.md).

Images are 1080×1920. From native visible-mask areas in the frozen manifest,
compute equivalent circular diameter after aspect-preserving resizing as:

`diameter = 2 * sqrt(mask_area / pi) * 640 / max(image_width, image_height)`

| Subset, positive images only | 10th percentile | Median | 90th percentile | Below 10 pixels |
| --- | --- | --- | --- | --- |
| Train, 420 | 9.1 px | 12.7 px | 18.7 px | 76 |
| Validation, 88 | 7.7 px | 9.7 px | 13.7 px | 49 |

These are area-equivalent visible-mask diameters, not literal ball widths; blur
and occlusion affect them. They expose a small-object challenge. Our inference:
compare 640 and 960 inputs before assuming a larger network is the right fix.
960 has 2.25× as many input pixels as 640, not necessarily 2.25× measured latency.
Do not discard tiny validation examples or reshape the split to improve scores.

## 1. YOLO instance segmentation — recommended first family

Concrete baseline: **YOLO11n-seg**. Newer alternative: **YOLO26n-seg**. These are
two generations of one practical architecture family, not two unrelated designs.

YOLO11 combines multi-scale image features with box/class predictions and a
segmentation head. Its released configuration produces masks from shared mask
features and per-instance coefficients. It supplies pretrained weights and
training/export support. [YOLO11 docs](https://docs.ultralytics.com/models/yolo11/),
[segmentation architecture](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/models/11/yolo11-seg.yaml)

YOLO26 adds an optional one-to-one NMS-free inference path, small-target-aware
label assignment, and a revised mask head. These are reasons to test it, not
proof it will win on volleyballs. Specify the selected inference head explicitly.
[YOLO26 docs](https://docs.ultralytics.com/models/yolo26/)

Project judgment: lowest integration effort because our prepared YOLO polygons
and existing Jetson code already fit this ecosystem. Start with YOLO11n-seg to
establish the custom baseline, then compare YOLO26 in a separate compatible
environment. Do not assume the installed 8.3.203 build supports YOLO26. Tiny
objects and coarse mask detail remain possible weaknesses. This is the best
first deployment candidate, not a measured accuracy winner.

## 2. RF-DETR-Seg Nano — transformer comparison

Uses a pretrained DINOv2 vision-transformer backbone with detection queries and
a mask head. The official Nano segmentation model has about 33.6M parameters;
its published benchmark uses 312×312 input. ONNX/TensorRT export is documented,
with resolution divisibility constraints. Current dataset documentation supports
YOLO segmentation labels and COCO polygons. [Architecture paper](https://arxiv.org/abs/2511.09554),
[benchmarks](https://rfdetr.roboflow.com/latest/learn/benchmarks/),
[export](https://rfdetr.roboflow.com/latest/learn/export/),
[dataset formats](https://rfdetr.roboflow.com/latest/learn/train/dataset-formats/)

Project judgment: strongest alternative for a meaningful CNN-versus-transformer
comparison. Its pretrained visual representation makes adaptation worth testing;
we have no evidence it generalizes better on this dataset. Nano is a family size,
not evidence of a smaller memory footprint than YOLO Nano. Test a supported
resolution that preserves small balls; published 312-pixel latency is not a
prediction at our chosen resolution. A new training/export stack needs validation.

## 3. RTMDet-Ins Tiny — alternative real-time CNN

Uses a CSPNeXt convolutional backbone, multi-scale feature aggregation, and an
instance-segmentation head. Official pretrained Tiny has about 5.6M parameters.
OpenMMLab documents ONNX Runtime and TensorRT deployment for RTMDet-Ins through
MMDeploy. [Implementation, weights, and deployment instructions](https://github.com/open-mmlab/mmdetection/tree/main/configs/rtmdet),
[paper](https://arxiv.org/abs/2212.07784)

Project judgment: useful compact CNN challenger with a different design from
YOLO. It would need a COCO-style adapter preserving our exact split. MMDetection,
MMCV, and MMDeploy add build/operator compatibility work on this newer ARM64
JetPack stack. The official deployment support is not proof that this exact
board/software combination works. Rank below YOLO for time to first demo.

## 4. Mask R-CNN, ResNet-50-FPN v2 — two-stage reference

First proposes candidate regions, then classifies/refines them and predicts
per-region masks using aligned region features. Torchvision supplies a pretrained
ResNet-50-FPN v2 implementation with about 46.4M parameters.
[Mask R-CNN paper](https://arxiv.org/abs/1703.06870),
[Torchvision model](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.detection.maskrcnn_resnet50_fpn_v2.html)

Project judgment: a useful offline reference for whether a richer region-based
model changes localization or boundary quality. It is not an assumed accuracy
upper bound. Proposal generation, region operations, and mask postprocessing
make it a less attractive first edge implementation. Use native masks and
derived boxes through a Torchvision dataset adapter; TensorRT deployment of
this exact implementation needs separate validation.

## 5. DeepLabV3 with MobileNetV3-Large — binary semantic segmentation

Labels each pixel as background or volleyball, using a mobile convolutional
backbone and atrous multi-scale context. Torchvision provides the model and
pretrained weights; its stock 21-class configuration has about 11.0M parameters.
Replace the output head for the two-class task. [DeepLabV3 paper](https://arxiv.org/abs/1706.05587),
[Torchvision model](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.segmentation.deeplabv3_mobilenet_v3_large.html)

Project judgment: clean for studying pixel classification, losses, and native
mask supervision. It needs background/ball raster targets, component extraction,
and a defined component confidence rule. Pixel scores are not automatically
calibrated object confidence. Heavy foreground/background imbalance and tiny
objects need attention. Touching balls are not inherently separated into
instances. Export/backend behavior is unverified on our Jetson. This is an
educational alternative, with more custom pipeline work than YOLO.

## How to decide without over-expanding the project

Selected initial implementation: **YOLO11n-seg**. Train and inspect this baseline
before reconsidering architecture. YOLO26, RF-DETR, RTMDet, Mask R-CNN, and
DeepLab remain background alternatives; there is no planned comparison sweep.

Before a long training run, exercise each candidate's intended operators and
export path in an isolated environment. Use pretrained weights for all candidates;
427 training images do not justify starting a large model from random weights.

For the shortlist, use the frozen train/validation sets with documented training
budgets. Compare initial 640/960 YOLO inputs; transformer resolutions must follow
its own supported geometry. Report preprocessing differences rather than treating
different resize/crop policies as identical. No inference crop may depend on
ground-truth ball coordinates or previous frames.

Evaluate the user's actual question using localization recall/precision and
center error on matched detections, alongside mask overlap. Derive reference
centers consistently from the visible annotation, report missed detections
separately, and include no-ball false positives. There are only four validation
negatives and three test negatives, so false-positive estimates will be weak.
Whole-image pixel accuracy is unsuitable as the headline because background
dominates. Choose confidence thresholds on validation only.

Then measure batch-1 inference and full-pipeline latency on the same Jetson,
with preprocessing, mask reconstruction, transfers, and precision documented.
Compare memory and accuracy after TensorRT export. Select the smallest/fastest
candidate that meets the agreed localization quality target. Use the frozen
test set only after model/settings selection; a room-camera test remains later.

## Reading benchmark claims correctly

RF-DETR's comparison uses NVIDIA T4, TensorRT 10.4, FP16, batch 1, and a thermal
buffer between timed passes; it measures latency rather than sustained camera
throughput. RTMDet-Ins reports RTX 3090 results with TensorRT 8.4.3. Torchvision's
DeepLab metric is semantic mIoU on COCO's VOC-label subset, not instance mask AP.
These numbers cannot be pasted together into a fair Orin Nano ranking.
[RF-DETR methodology](https://rfdetr.roboflow.com/latest/learn/benchmarks/),
[RTMDet methodology](https://github.com/open-mmlab/mmdetection/tree/main/configs/rtmdet),
[DeepLab metric definition](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.segmentation.deeplabv3_mobilenet_v3_large.html)

No volleyball accuracy, Jetson segmentation speed, or comparative training
result has been measured for these candidates. Recommendations above are
engineering judgments based on the inspected project, data, and primary sources.
