# Jetson YOLO11n-seg deployment results

Measured on Jetson Orin Nano in its existing 25 W mode, with default dynamic
clocks, JetPack 7.2.1 and TensorRT 10.16.2.10. Both backends use the same
checkpoint, batch 1, 640×640 input, confidence 0.25 and NMS IoU 0.7.

PyTorch uses FP32 weights/inputs with its default cuDNN TF32 permission enabled;
matmul TF32 permission is disabled. The exact flags are saved with each profile.

| Measurement | PyTorch CUDA FP32 | TensorRT FP16 |
| --- | ---: | ---: |
| Model call FPS, synchronized host timing | 40.46 | 203.39 |
| Mean model call latency | 24.72 ms | 4.92 ms |
| Mean CUDA-event model span | 24.67 ms | 4.84 ms |
| Offline decode + prediction FPS | 12.72 | 17.66 |
| Offline processing p95 latency | 83.66 ms | 60.04 ms |
| Process RSS at end of profile | 1610.23 MiB | 1738.55 MiB |
| System RAM peak during profile | 2615.00 MiB | 2597.00 MiB |
| GPU temperature peak during profile | 56.94 °C | 57.94 °C |
| Mean board input power during profile | 9.66 W | 8.61 W |

**Model-call speedup: 5.03×. Offline processing speedup: 1.39×.**

Model-call results average three rounds of 200 calls after 30 warmups, on
one preprocessed GPU-resident image. CUDA-event spans can include launch gaps;
host timing includes Python dispatch and synchronization. These are not camera FPS.

Offline results use the same 900 consecutive source frames (0–899) from
IMG_9217.MOV, including decoding, resize/transfer, inference, NMS and full-resolution
mask reconstruction. They exclude annotation, encoding and network streaming.
System memory/power/temperature samples cover both benchmark phases and are
whole-device measurements, not model-exclusive GPU allocation.

The source is HEVC decoded through OpenCV/FFmpeg with no hardware acceleration
requested/reported. Decoder time is a substantial part of the offline pipeline.

## Prediction quality after conversion

| Metric on 123 labeled test images | PyTorch | TensorRT |
| --- | ---: | ---: |
| mAP50(B) | 94.94% | 94.93% |
| mAP50-95(B) | 66.27% | 65.30% |
| mAP50(M) | 85.80% | 85.81% |
| mAP50-95(M) | 34.42% | 34.49% |
| Fixed-threshold precision | 87.80% | 86.40% |
| Fixed-threshold recall | 90.00% | 90.00% |
| TP / FP / FN | 108 / 15 / 12 | 108 / 17 / 12 |

Both evaluations force identical square inputs. Earlier Mac results used
different padding/batching, so this matched Jetson baseline is the appropriate
reference for conversion changes. No model or threshold was tuned on these results.

The two additional FP16 false detections occur in images 605 and 641, with
confidence approximately 0.2517 and 0.2510, just above the fixed 0.25 threshold.

## Deployment and scope

The engine has static input shape 1×3×640×640. Internal FP16 execution is enabled;
input/output tensors remain FP32 and NMS/mask reconstruction use the shared
Ultralytics postprocessor. The engine is specific to this target/runtime.

The installed CUDA PyTorch wheel warns that Orin sm_87 is not explicitly supported.
Real custom segmentation and profiling completed on CUDA; the warning remains an
environment maintenance limitation, not evidence of a YOLO architecture failure.

The profile establishes feasibility on this board at this input size. It does
not establish performance on new camera environments, long-duration thermal
stability, or fast/small-ball accuracy. Camera capture and streaming can impose
separate throughput limits.

[Protocol and commands](deployment/README.md) ·
[Raw comparison](artifacts/deployment/v1/comparison.json) ·
[Engine](artifacts/deployment/v1/model-fp16.engine)

## Live camera check

Processed 894 frames in 60.29 seconds (14.83 FPS), status: completed.

This includes camera waits, inference, drawing, JPEG creation and preview writes.
The inspected live image was nearly black; this verifies processing stability,
not live volleyball recognition in the room. The subsequent
[project demo](docs/media/jetson-demo.mp4) shows visible-ball detections on the
live room feed. That qualitative scene check does not replace the timed profile
or establish accuracy on a labeled live-camera test set.
It is not capture-to-display latency. The browser stream itself is capped at 10 FPS.

Viewer: run `bash deployment/live.sh status` for the private URL.
