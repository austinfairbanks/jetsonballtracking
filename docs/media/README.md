# README media

These assets are derived from Austin's supplied `Jetson Full Demo POC.mp4`.
The original remains outside Git in Downloads.

| Asset | Source / preparation |
| --- | --- |
| `jetson-overview.mp4` | 20-second project overview, 1920×1080, 30 FPS, H.264 with AAC music and sound effects. Uses real footage from `jetson-demo.mp4`, measured TensorRT results, and an explicitly planned tracking/pan/tilt roadmap. The selected poster is baked into frame 0. |
| `jetson-overview.jpg` | Poster selected from the overview at 2.5 seconds, after the opening title has settled. |
| `jetson-demo.mp4` | Full 1,758-frame edit, 29.97 FPS, about 58.66 seconds. Resized from 1920×1080 to 1280×720, H.264 CRF 26, AAC audio if present, fast-start MP4. Original timing and sequence retained. |
| `live-preview.gif` | Live-feed excerpt at 44–50 seconds, 640×360, sampled at 8 FPS, 64-color palette. Loops at the original elapsed-time scale. GIF playback FPS is independent of measured inference FPS. |
| `system-roadmap.svg` | Repo-native diagram. Solid green stages work today; dashed blue stages are planned. No external fonts or scripts. |

The full edit begins with recorded backyard inference, then shows the physical
hardware and the live Jetson room feed. It is qualitative evidence; model
accuracy and latency come from the separate evaluation reports.

## Overview sources and credits

The overview uses source seconds 6–10 for backyard inference, 30–32 and 35–37
for the Jetson enclosure and camera, and 53–58 for the live room feed. Portrait
segments have their encoded black pillars cropped; footage retains its natural
pace and original detection overlays. The 30 FPS export is a video format,
not a claim about live processing throughput.

The 5.03× speedup and 24.72 → 4.92 ms comparison are mean **model-call**
measurements from [the deployment results](../../DEPLOYMENT_RESULTS.md), with
the same checkpoint, 640×640 input, batch 1, and Jetson Orin Nano in 25 W mode.
Temporal tracking and pan/tilt control are labeled as planned.

Created with [Brag](https://github.com/latent-spaces/brag) and
[Hyperframes](https://github.com/heygen-com/hyperframes). Music: “Happy Beats /
Business Moves” vol. 12 by [ende.app](https://ende.app), bundled with Brag.
Sound effects: [Kenney](https://kenney.nl), CC0.

## Format references

The README uses a demo-first introduction and a compact results table, with
setup details linked separately. Examples reviewed for that structure:
[ByteTrack](https://github.com/FoundationVision/ByteTrack),
[Supervision](https://github.com/roboflow/supervision), and
[jetson-inference](https://github.com/dusty-nv/jetson-inference).
These are documentation references, not additional project dependencies.

Descriptions of the implementation were checked against
[`detection/run.py`](../../detection/run.py) and the saved training/deployment
protocols. For the planned work, the
[Ultralytics tracking documentation](https://docs.ultralytics.com/modes/track/)
describes matching detections across frames, retaining tracks through misses,
and camera-motion compensation. No tracker has been selected or added yet.

The main README uses relative Markdown image and video links, tables, headings
and a fenced Bash block. The overview poster renders inline on GitHub; its link
opens the MP4 file. The full demo remains linked, and `live-preview.gif` is
available as a looping preview.
