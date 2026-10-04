# Jetson volleyball restart context

Read README.md, ROADMAP.md, DATASET_PREPARATION.md, TRAINING_RESULTS.md and deployment/README.md. Detection/segmentation, grouped training/evaluation, TensorRT optimization and a live demo are implemented. Temporal tracking, pan/tilt and camera-motion compensation remain future work.

Preserve the distinction between model latency (4.92 ms FP16 historical mean), decoded video throughput (17.66 FPS) and live camera throughput (about 15 FPS). 30 FPS and >99% precision are targets. Current documented held-out precision is 86.4%, with only three negative test images; avoid overstating robustness.

Git has source, protocol, results and public demo media. Restore the exact dataset, labels, checkpoint and private connection settings separately. TensorRT engines depend on target hardware/runtime; follow the export/build instructions on the Jetson. Use `bash deployment/live.sh start`, `status`, and `stop` only on the configured device. SAM 2.1 Large supersedes the early MobileSAM helper.

The seven cards capture labeling, architecture discussion, roadmap, camera work, training/deployment and media. Private addresses, service credentials and machine paths from the chats are excluded. Historical tests and device status are not new validation runs.
