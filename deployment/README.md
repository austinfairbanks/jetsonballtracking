# Jetson deployment and FP16 proof of concept

This deploys the frozen YOLO11n-seg checkpoint from the three-fold experiment.
No retraining or threshold tuning is part of this comparison. Results belong
to the installed Jetson Orin Nano, JetPack 7.2.1 and TensorRT 10.16 environment.

## Fixed comparison protocol

- PyTorch CUDA baseline: FP32 weights and inputs, normal framework defaults.
- TensorRT: FP16-enabled engine, built on this Jetson, 2 GiB tactic workspace.
  Input/output tensors remain FP32; eligible internal layers use FP16.
- Both: batch 1, fixed 640×640 letterboxing, confidence 0.25, NMS IoU 0.7,
  full-resolution mask reconstruction, identical Ultralytics 8.3.204 postprocessing.
- Warm up 30 complete predictions. Then three rounds of 200 network calls on
  the same preprocessed GPU-resident image, using CUDA events and synchronized
  host-call timings. These exclude preprocessing, decoding and postprocessing.
- Process the same first 900 consecutive frames (indices 0–899) of IMG_9217.MOV
  with automatic metadata rotation explicitly enabled (decoded shape 1920×1080×3),
  without pacing or skipping. Measure decode, prediction and total processing
  times, plus the framework's preprocessing/inference/postprocessing breakdown.
  Per-frame timing excludes drawing/encoding/streaming. Four saved previews
  are included only in the separately reported total loop wall time.
- Evaluate all 123 frozen labeled test frames with both backends at the same
  square shape and batch size. Report mask/box mAP and fixed-threshold TP/FP/FN.
  This compares deployment parity; it does not select new model settings.
- Sample system RAM, temperature and power with tegrastats every second.
  PyTorch allocator memory excludes direct TensorRT allocations and must not
  be presented as total GPU memory. Jetson CPU and GPU share physical memory.
- Retain existing 25 W power mode and default dynamic clocks. Stop other
  detector workloads before profiling. This is a quick practical profile,
  not a locked-clock maximum-throughput or multi-hour thermal benchmark.

## Environment and reproduction

Run on the Jetson from `~/code/jetsonballtracking`:

```bash
bash deployment/setup.sh
tmux new -s volleyball-profile '.venv-deploy/bin/python -u deployment/benchmark.py > artifacts/deployment/v1/pipeline.log 2>&1'
```

`setup.sh` creates `.venv-deploy`, reuses the existing `.venv-detect` CUDA
PyTorch/torchvision wheels, and exposes the native JetPack TensorRT Python
bindings. Only Ultralytics 8.3.204, ONNX 1.17.0 and protobuf 5.29.5 are installed
in the new environment. It does not replace CUDA, TensorRT, system Python or
the existing detector environment. Exact imported versions are recorded.

The older Ultralytics exporter expects the legacy Torch ONNX exporter;
`benchmark.py` explicitly sets `dynamo=False` for its export call. ONNX opset 17
is validated before building the engine with the native TensorRT API.

The input bundle must contain the checkpoint, original video, copied test
images/labels and their manifest at `artifacts/deployment/v1/`. The script
verifies source/checkpoint hashes, runs real segmentation on CUDA, builds the
engine, and runs sequential isolated profiling/evaluation processes in tmux.
Successful stages are retained on restart. A failed stage stops the pipeline.

## Live custom model

These commands work from the Mac or Jetson:

For Mac-to-Jetson SSH settings, see [local configuration](../ops/README.md).

```bash
bash deployment/live.sh test --seconds 60
bash deployment/live.sh start
bash deployment/live.sh status
bash deployment/live.sh stop
```

Run `bash deployment/live.sh status` for the private viewer URL. It shows masks,
confidence, box centers and processing FPS, with an explicit no-detection state.
The browser stream is capped at 10 FPS; processing FPS is reported separately.
No temporal tracking, public hosting or boot service is added.

## Evidence

`artifacts/deployment/v1/` contains environment and build reports, engine
inspection, per-stage logs and tegrastats, three-round network timings,
900-frame predictions for both backends, and paired 123-image accuracy results.
`model-fp16.engine` is built for this Jetson/runtime; rebuild on a different
target or incompatible runtime. Keep the original `model.pt` as the portable
trained artifact.

The initial video speed pass was found to decode sideways because this OpenCV
build defaults to disabled metadata rotation. Those speed reports are archived
under `orientation-initial/`; the accepted profile reruns both backends with
upright video and asserts the decoded frame dimensions. The labeled-image
accuracy evaluation already used upright PNGs and is unchanged.

References: [Ultralytics Jetson deployment](https://docs.ultralytics.com/guides/nvidia-jetson/),
[NVIDIA TensorRT performance guidance](https://docs.nvidia.com/deeplearning/tensorrt/10.x.x/performance/best-practices.html).
