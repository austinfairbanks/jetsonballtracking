# Jetson Ball Tracking — See the ball.

An original 20-second film using the project's real inference, hardware, and live
camera footage. It presents the measured TensorRT model-call speedup and labels
temporal tracking and pan/tilt control as planned work.

- `brag.mp4`: 1920×1080, 30 fps, H.264 with music and sound effects.
- `brag.jpg`: selected poster, also baked into the video's first frame.
- `share-copy.txt`: accompanying caption.
- `composition/`: editable Hyperframes HTML, local fonts, runtime, and media.
- `brag-plan.md`, `composition-brief.md`, `sources.md`: story and source details.
- `check.json`, `verification.json`: composition checks and final video metadata.

Source clips keep their natural pace. The original footage's detection boxes are
preserved. Cropping removes encoded black pillars from the portrait segments.
The 30 fps export is the video format; live application processing is about 15 fps.

To rerender, with Node 22+, FFmpeg and FFprobe on PATH:

```sh
cd composition
pnpm dlx hyperframes@0.8.41 check
pnpm dlx hyperframes@0.8.41 render --fps 30 --quality delivery --output ../brag.mp4
```

That command renders the animation; the delivered MP4 additionally has the selected
poster baked into its first frame. Music is the Brag-bundled Happy Beats / Business
Moves vol. 12 by ende.app; sound effects are from Kenney.
