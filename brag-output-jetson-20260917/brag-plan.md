# Brag Plan: Jetson Ball Tracking

**Format:** landscape, 1920×1080, 30 FPS, exactly 20.00 seconds. **Tone:** polished technical sports/engineering. **Voice:** off. Show the working perception system through Austin’s actual footage, then identify the remaining tracking and motor work as planned.

## Nine-question inspection rubric

1. **What is it?** A custom volleyball detection and segmentation project running on Jetson Orin Nano, working toward a pan/tilt camera that follows the ball.
2. **Strongest verified claim:** TensorRT FP16 reduced mean model-call latency from 24.72 to 4.92 ms, a 5.03× speedup against the same checkpoint’s PyTorch CUDA baseline.
3. **Visual hook:** A real volleyball with the model’s existing box/mask overlay in backyard footage. Use the actual navy/mint project palette.
4. **Actual UI/material:** `docs/media/jetson-demo.mp4`: recorded backyard inference, physical hardware, and the live Jetson room feed with boxes, masks, confidence, and box-center markers.
5. **Minimum duration:** The requested 20 seconds: proof → hardware → live result → measured improvement → next step.
6. **Tone:** `polished`; clear technical evidence with the pace of a restrained sports film. Let real motion carry the energy; concise labels and clean transitions.
7. **Audio:** Steady warm instrumental bed, 2–3 soft accents, no narration. Mute the source video’s audio.
8. **Share caption:** Custom volleyball segmentation is running on my Jetson Orin Nano. TensorRT cut model-call latency from 24.72 to 4.92 ms. Next: temporal tracking and pan/tilt.
9. **User flow:** USB global-shutter camera captures a frame → custom YOLO11n-seg predicts independently → browser displays boxes, masks, confidence, and box centers. Temporal association and motor control are future work.

## Visual identity

From `docs/media/system-roadmap.svg`: navy `#111923`, white `#f0f5fb`, working mint `#69d8af`, working-panel green `#142b29`, planned blue `#91baff`, planned-panel blue `#1a2434`, supporting text `#bacadb`. The viewer uses dark `#101418` with system sans. Use available local Geist/Geist Mono for the film’s clean technical labels; this is an explicit font adaptation, not a claim that the repository declares Geist.

Real imagery is the centerpiece. Crop baked-in pillarboxes from portrait footage and present it as a deliberate portrait proof panel. Preserve the actual ball and model annotations. Do not synthesize bounding boxes, tracking trails, hardware motion, or a fabricated interface. Clean cuts/slides and subtle depth are sufficient.

## Storyboard

| Scene | Video time | Duration | Exact principal copy and proof |
|---|---|---|---|
| 1 — See | 0.00–4.00 | 4.00s | **“See the ball.”** Real backyard-inference portrait footage, source 6–10s. Small project label: `Jetson Ball Tracking`. Let the actual segmentation marks establish what works. |
| 2 — Hardware | 4.00–8.00 | 4.00s | **“Runs on Jetson.”** Actual portrait hardware footage, source 30–32s + 35–37s: Jetson enclosure followed by the camera lens, with a hard cut between two two-second excerpts. Supporting label: `YOLO11n-seg · TensorRT FP16`. |
| 3 — Live | 8.00–13.00 | 5.00s | **“Live on the Jetson.”** Full-width source live room feed, 53–58s. Preserve visible boxes, masks, confidence, center markers, and the brief real missed detection. Keep a stable readable title; the real ball movement carries this scene. |
| 4 — Measured | 13.00–17.00 | 4.00s | **“5.03× faster model calls”** with **“24.72 → 4.92 ms”**, labeled `PyTorch CUDA` and `TensorRT FP16`. Small method line: `640×640 · 25 W · batch 1`. Source: matched checkpoint model-only benchmark, not live camera FPS. Reveal the comparison promptly, then hold it. |
| 5 — Next | 17.00–20.00 | 3.00s | **“Next: follow the ball.”** Supporting copy: **“Tracking + pan/tilt · planned”**. Small final identity: `Jetson Ball Tracking`. Use dashed blue treatment adapted from the project roadmap; do not animate a motorized camera as if it exists. |

**Total:** 4 + 4 + 5 + 4 + 3 = **20.00 seconds / 600 frames**.

Portrait preprocessing: crop the 1280×720 source to **408×720 at x=436, y=0** before fitting the proof panels. The selected live excerpt stays full width.

Sequential/interaction: scene 4 has a brief comparison reveal; retain both timings and labels together afterward. Other scenes use real footage rather than simulated interaction. Principal lines settle within roughly 0.4s and hold. Short labels need at least 0.8s settled; sentences need roughly 0.3s per word. Avoid additional feature lists or dense installation commands.

## Audio and timing

- Music: `happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`, source start 0s; steady, clean, approximately 0.26 volume; short fade-in and fade over the final 0.8s.
- Bundled cue metadata read: estimated tempo 109.96 BPM. Optional strong cue near the comparison reveal: 13.11s; a quiet planned-work emphasis may land at 17.47s. Preserve fixed scene boundaries and reading time.
- Sparse accents: soft hardware-panel arrival, restrained metric reveal, quiet outro landing. Exact SFX are chosen after the motion exists using the bundled low/medium high-frequency-risk analysis.
- Audio-reactive treatment: subtle presence of the existing mint panel edge or background depth, derived from music energy. No pulsing labels, waveforms, generic particles, or strobing.

## Accuracy and delivery

Shipped: custom per-frame detection/segmentation, TensorRT deployment, recorded demo and live preview. Planned: temporal tracking, prediction through misses, control and motors. About 15 FPS is current application processing; the browser stream is capped at 10 FPS. Neither the 203.39 model calls/s benchmark nor the film’s 30 FPS export is live camera throughput. Do not display 30 FPS, >99% precision, or ≤33 ms as achieved results.

Deliver `brag.mp4`, an intentionally selected best-frame `brag.jpg`, local share copy, and sources. Bake the poster as frame 0 while preserving 20 seconds. Verify media, typography, sound, scene continuity, and timing before delivery.
