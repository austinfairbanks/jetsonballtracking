# Reading References

## Model Design and GPU Inference Performance

Saved September 10, 2026. Read in this order:

1. [NVIDIA: Getting Started with Deep Learning Performance](https://docs.nvidia.com/deeplearning/performance/dl-performance-getting-started/index.html)
   - Start here for compute versus memory bottlenecks and how model dimensions
     affect GPU efficiency.
2. [NVIDIA: Convolutional Layers User's Guide](https://docs.nvidia.com/deeplearning/performance/dl-performance-convolutional/index.html)
   - Most relevant to the volleyball detector: convolution as matrix
     multiplication, channel counts, tensor layouts, and tiling.
3. [NVIDIA: Optimizing TensorRT Performance](https://docs.nvidia.com/deeplearning/tensorrt/latest/performance/optimization.html)
   - Focus on layer fusion and optimizing layer performance to connect model
     design choices to TensorRT's execution choices.

Use these guides for principles. Their benchmark numbers are not predictions
for the Orin Nano; measure on the project hardware. The TensorRT latest link
can change over time; use documentation matching the installed version when
implementing specific APIs or build settings.

## Original SAM-assisted labeling choice — September 13, 2026 (superseded)

Decision: start with **MobileSAM** for human-guided masks in CVAT, not CAT-SAM
fine-tuning or an automatic volleyball detector. This is an engineering choice
for quick labeling on this CPU-backed Mac Docker instance; not a claim of
volleyball accuracy or low-light robustness.

- [Official MobileSAM implementation](https://github.com/ChaoningZhang/MobileSAM):
  authors report 9.66M total parameters versus 615M for original SAM and retain
  the prompt-guided decoder. Supports points and boxes. Their GPU timing is not
  a prediction for our Docker CPU setup; use local measurements.
- [Official CAT-SAM implementation](https://github.com/weihao1115/cat-sam):
  conditional tuning for few-shot domain adaptation. It needs target examples
  and training, and its reported tasks are not this volleyball dataset. Worth
  reconsidering only if reviewed labels show systematic failures that ordinary
  prompts cannot address.
- [CVAT AI tools](https://docs.cvat.ai/docs/annotation/auto-annotation/ai-tools/):
  interactive positive/negative prompts and mask-to-polygon workflow.
- [CVAT SAM2 tracker availability](https://docs.cvat.ai/docs/annotation/auto-annotation/segment-anything-2-tracker/):
  documented packaged SAM2 tracking is Online/Enterprise, not a drop-in
  Community feature. Our independent extracted frames do not need a tracker.

Local code contract was checked in the installed CVAT checkout:
`cvat/apps/lambda_manager/views.py`, `cvat-core/src/rle-utils.ts`, and
`cvat-ui/src/components/annotation-page/standard-workspace/controls-side-bar/tools-control.tsx`.
This implementation has since been replaced by SAM 2.1 Large below. Always
inspect mask quality on tiny/dim/occluded balls;
successful API calls alone do not establish accuracy.

### Local spot check

Ten authenticated CVAT inference calls succeeded across frames 0, 199, 399,
and 643: shaded grass, small ball against roof, sky, and partial leg occlusion.
Point, point-plus-box, and two ROI requests were exercised. Initial full-frame
clicks took about 1.5–2.0 s; cached follow-up box prompts took 0.3–0.5 s.
The service used about 489 MiB after testing. These are spot measurements,
not a benchmark or accuracy evaluation. No human ground-truth IoU was measured.

Visual review found useful object masks, but the shaded ball's darkest lower
edge was under-segmented. ROI did not eliminate that issue. Manually correct
such edges rather than treating predictions as ground truth. Existing CVAT
annotations were byte-for-byte unchanged before/after both test runs. Browser
interaction itself was not exercised; API behavior and installed UI source
contracts were checked.

## Current helper: SAM 2.1 Large on Apple GPU — September 13, 2026

The user rejected MobileSAM because it required too many corrective clicks.
It has been replaced by Meta SAM 2.1 Hiera Large, using native macOS PyTorch MPS
on the M2 Pro GPU. The original MobileSAM service and implementation were removed.

- [Official SAM 2 implementation and model table](https://github.com/facebookresearch/sam2):
  SAM 2.1 Large has 224.4M parameters and supports image point/box prompts.
  Its published video benchmarks favor Large among the SAM 2.1 sizes, but are
  not a volleyball accuracy evaluation or a direct comparison with MobileSAM.
- [PyTorch MPS backend](https://docs.pytorch.org/docs/stable/notes/mps.html):
  enables native Apple GPU execution. Our isolated native environment passed
  `torch.backends.mps.is_available()` and an actual GPU matrix computation.

Single-center-click staging requests returned masks on the same four test frames.
The CPU trial took about 13 seconds per frame. GPU staging took 5.1 seconds for
the first warm-up request, then 1.0–1.2 seconds per new image including bridge
overhead. Visual review found the shaded-ball outline more complete than the
old MobileSAM preview, though difficult dark boundaries still need human review.
MPS and CPU outputs differed; neither is measured against ground truth.
These are spot checks, not a dataset-wide accuracy claim. See `ops/cvat/README.md`
for operation and `ops/cvat/test_sam2.py` for authenticated API verification.

Final authenticated CVAT verification passed all ten point/box/ROI requests and
all server health checks. Full-image point requests took 1.1–2.2 seconds;
cached box follow-ups took 0.3–1.8 seconds. The shaded-ball ROI request selected
only a panel, so use full-image point prompts by default and treat ROI as an
optional experiment. Annotation JSON was unchanged both across the model switch
and during testing. The native endpoint rejects unauthenticated requests (401);
the bridge reports device `mps` with approximately 1.05 GB allocated GPU memory.
