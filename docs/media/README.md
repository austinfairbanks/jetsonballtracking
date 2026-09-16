# README media

These assets are derived from Austin's supplied `Jetson Full Demo POC.mp4`.
The original remains outside Git in Downloads.

| Asset | Source / preparation |
| --- | --- |
| `jetson-demo.mp4` | Full 1,758-frame edit, 29.97 FPS, about 58.66 seconds. Resized from 1920×1080 to 1280×720, H.264 CRF 26, AAC audio if present, fast-start MP4. Original timing and sequence retained. |
| `live-preview.gif` | Live-feed excerpt at 44–50 seconds, 640×360, sampled at 8 FPS, 64-color palette. Loops at the original elapsed-time scale. GIF playback FPS is independent of measured inference FPS. |
| `system-roadmap.svg` | Repo-native diagram. Solid green stages work today; dashed blue stages are planned. No external fonts or scripts. |

The full edit begins with recorded backyard inference, then shows the physical
hardware and the live Jetson room feed. It is qualitative evidence; model
accuracy and latency come from the separate evaluation reports.

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
and a fenced Bash block. The GIF renders inline on GitHub; the full-video link
opens the MP4 file rather than relying on an unsupported HTML video embed.
