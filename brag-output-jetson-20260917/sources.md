# Sources and credits

Subject: [Jetson Ball Tracking](https://github.com/austinfairbanks/jetsonballtracking), Austin Fairbanks’s current project. Repository origin was read locally; no publication or messages are part of this artifact.

- Local project: `/Users/austinfairbanks/code/jetsonballtracking`.
- Inspected commit: `3fef0266a0b9d5492d335d64dda4061d8e3fe897`.
- Inspection date: 2026-09-17.

## Claim provenance

| Local source | Verified material |
|---|---|
| `README.md` | Custom YOLO11n-seg project; Jetson deployment; per-frame predictions; live demo; dataset and benchmark summary; future tracking and pan/tilt. |
| `DEPLOYMENT_RESULTS.md` | Same checkpoint, batch 1, 640×640, 25 W mode; mean model-call latency 24.72 ms PyTorch CUDA and 4.92 ms TensorRT FP16; 5.03× model-call speedup. Includes separate offline and live measurements. |
| `deployment/README.md` | 30 warmups, three rounds of 200 model calls on a preprocessed GPU-resident image; model timing excludes preprocessing/decoding/postprocessing; browser viewer capped at 10 FPS; no temporal tracking. |
| `deployment/live.sh` | Custom `model-fp16.engine` launch with `--task segment`. |
| `detection/run.py:197` | Custom viewer explicitly says image-only predictions with no temporal tracking. |
| `detection/run.py:256` | Per-frame `model.predict`; subsequent drawing adds box-center markers. |
| `ROADMAP.md` | Detection works today; temporal association, prediction through misses, camera control, motors and moving-camera validation remain planned. |
| `docs/media/system-roadmap.svg` | Native navy/mint/blue visual palette; solid working stages and dashed planned stages. |
| `docs/media/README.md` | Demo provenance, approximate duration, format and the documented live excerpt at 44–50s. |

The nine planning answers are in `brag-plan.md`. The benchmark statistic is not camera FPS or capture-to-display latency. Current application processing is about 15 FPS; the browser stream is capped at 10 FPS. Targets of 30 FPS, p95 ≤33 ms and >99% precision are not achieved claims. Held-out box mAP50 is not described as generic accuracy and is not needed on screen.

## Actual footage

`docs/media/jetson-demo.mp4` is derived from Austin’s supplied **Jetson Full Demo POC.mp4**. Per the media README, it retains the full original timing/sequence: 1758 frames, approximately 58.66s, 29.97 FPS, 1280×720. It begins with recorded backyard inference, then hardware, then the live room feed. It is qualitative evidence; benchmark/accuracy claims come from the reports above.

- Live room excerpt documented by media README: **44–50s**. After visual review, the film instead selects **53–58s**: four of five sampled seconds show detections, and a brief actual missed detection is retained.
- Final backyard selection: **6–10s**, with ball boxes visible in all inspected samples.
- Final hardware selection: **30–32s + 35–37s**, showing Jetson enclosure followed by camera-lens closeups.
- The portrait selections are cropped to **408×720 at x=436, y=0**; the live selection remains full width.
- Contact-sheet inspection supplied by the composing agent places portrait/pillarboxed footage in the opening ~38s and full-width room footage from approximately 39s; these are editorial observations, not benchmark timestamps.
- Cropping pillarboxes and fitting video panels are presentation changes. Preserve natural elapsed-time playback and actual model annotations; no synthesized detections or tracking behavior.

## Production credits

- Workflow: installed [Brag skill](https://github.com/latent-spaces/brag), `/Users/austinfairbanks/.codex/skills/brag/SKILL.md`.
- Composition/render tooling: [Hyperframes](https://hyperframes.heygen.com/).
- Music: **Happy Beats / Business Moves, Vol. 12**, by [ende.app](https://ende.app/en), bundled with Brag. Filename: `happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`.
- Cue metadata: matching bundled `.music-cues.md` and `.json`; estimated tempo 109.96 BPM.
- Selected family SFX: [Kenney](https://kenney.nl/), CC0 according to Brag’s audio reference.
- Film typography: locally available Geist/Geist Mono, deliberately adapted from the source’s system-sans direction.

No narration. Source-demo audio is muted for the new music/SFX mix. This document records provenance and supplied attribution for the local deliverable.
