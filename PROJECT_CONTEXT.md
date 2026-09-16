# Project Context

This document distills the planning conversation supplied on August 30. It is
background for future design and implementation decisions, not a record of
completed work.

## Goal

Build a real-time volleyball detection and tracking pipeline on NVIDIA Jetson
hardware, then integrate its output with a drone flight controller for ball
following. The project is also intended to build a practical understanding of
NVIDIA's embedded AI stack rather than merely getting a model to run.

The target pipeline is:

```text
camera -> capture -> preprocess -> TensorRT inference -> detections -> tracker
       -> visualization/telemetry -> flight-controller integration
```

## Hardware Direction

The preferred target is a **Jetson Orin Nano 8GB** system, including a carrier
board, cooling, power hardware, and NVMe storage. An Orin Nano 4GB with a carrier
board could also be viable, but the 8GB model is preferred.

Avoid choosing an original Jetson Nano as the final platform. Listings with
names such as "Jetson Nano," "Nano B01," Cortex-A57 CPU specifications, or a
Maxwell GPU refer to the older generation rather than an Orin Nano. The older
Jetson Nano 4GB can support a constrained proof of concept, but it has much
lower performance and is tied to the older JetPack 4.x software ecosystem.

A previously discussed ClawBox listing appeared to be a complete Orin Nano 8GB
computer with a carrier board, 512GB NVMe SSD, enclosure, cooling, and likely
power hardware—not merely an SSD. Its exact module, carrier board, included
power supply, condition, and boot state still need verification before relying
on that assessment.

Prices and product listings mentioned in the original conversation were
time-sensitive and are deliberately not treated here as current purchasing
guidance.

## Technical Mental Model

The important platform hierarchy is:

```text
Jetson Orin Nano
├── Ubuntu / Jetson Linux (L4T)
├── JetPack
│   ├── CUDA
│   ├── cuDNN
│   ├── TensorRT
│   ├── multimedia and camera APIs
│   └── development and profiling tools
├── ARM CPU
├── NVIDIA Ampere GPU and Tensor Cores
└── shared LPDDR5 memory
```

JetPack is NVIDIA's Jetson software distribution and SDK, not an inference
program. CUDA provides GPU computing, cuDNN provides optimized deep-learning
primitives, and TensorRT compiles trained networks into optimized inference
engines for NVIDIA hardware.

The expected model deployment path is:

```text
PyTorch model -> ONNX -> TensorRT builder -> TensorRT engine -> runtime inference
```

TensorRT is a central focus. Relevant concepts include graph optimization,
operator/layer fusion, kernel or tactic selection, FP16 and INT8 execution,
memory planning, and hardware-specific engine building. For example, compatible
convolution, bias, batch-normalization, and activation operations may be fused
to reduce intermediate memory traffic and kernel-launch overhead.

Because this is a real-time perception system, performance work must consider
the entire frame path—not only neural-network compute. Capture latency,
preprocessing, memory copies, CPU/GPU synchronization, postprocessing, and
tracking all consume the frame budget. Shared memory does not automatically
eliminate unnecessary copies.

## Learning Priorities

Study the stack in this order:

1. Jetson Orin hardware: ARM CPU, Ampere GPU, CUDA cores, Tensor Cores, shared
   memory, memory bandwidth, thermals, and power envelope.
2. JetPack and how Jetson Linux, CUDA, cuDNN, TensorRT, multimedia APIs, camera
   support, and profiling tools fit together.
3. CUDA fundamentals: host/device roles, kernels, blocks, warps, threads, and
   why data movement can dominate perception workloads.
4. TensorRT: graph compilation, fusion, tactics, precision selection, memory
   optimization, engine building, and runtime inference.
5. Jetson performance controls: power modes, clocks, thermals, GPU utilization,
   memory bandwidth, and `tegrastats`.
6. Nsight Systems and Nsight Compute after a working pipeline exists, so CPU
   work, CUDA calls, kernels, transfers, streams, and synchronization can be
   examined on a real timeline.

## Initial Bring-up Plan

Before the project camera is available:

1. SSH into the Jetson.
2. Record the installed JetPack, L4T, CUDA, cuDNN, and TensorRT versions.
3. Run `tegrastats` and learn to interpret its output.
4. Run a small detector such as YOLO11n or YOLOv8n on sample video.
5. Export through ONNX and build/run a TensorRT engine where practical.
6. Measure end-to-end latency, inference latency, and achieved FPS separately.

When the camera is available, replace the video-file input with live capture
while keeping the rest of the pipeline stable. Then use the working volleyball
pipeline—not generic demos—as the main vehicle for profiling and optimization.

## Design Principles and Open Questions

- Optimize for a reliable end-to-end frame budget; high detector FPS alone is
  not sufficient for a fast-moving ball.
- Begin with a small YOLO model to validate deployment, then substitute or train
  a volleyball-specific detector.
- Measure before optimizing. Use `tegrastats` first and Nsight once the pipeline
  is functional.
- Track where each frame and tensor lives, when the CPU or GPU owns the work,
  and where copies or synchronization occur.
- Do not assume advertised TOPS translates directly into application FPS.
- Select the camera interface, resolution, target FPS, tracking algorithm,
  flight-controller protocol, and control-loop behavior through later tests and
  design work.
