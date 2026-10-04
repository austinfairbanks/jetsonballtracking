# Hyperframes Composition Brief: Jetson Ball Tracking

Create the 20.00-second, 1920×1080, 30 FPS film specified in `brag-plan.md`. Subject is the current Jetson Ball Tracking project. The central proof is the real `docs/media/jetson-demo.mp4`; no narration.

## Paths

- Project: `/Users/austinfairbanks/code/jetsonballtracking`.
- Output: `/Users/austinfairbanks/code/jetsonballtracking/brag-output-jetson-20260917`.
- Composition: `/Users/austinfairbanks/code/jetsonballtracking/brag-output-jetson-20260917/composition/`.
- Final video/poster: output-root `brag.mp4` and `brag.jpg`.
- Brag skill: `/Users/austinfairbanks/.codex/skills/brag/SKILL.md`.
- Primary input: `/Users/austinfairbanks/code/jetsonballtracking/docs/media/jetson-demo.mp4`.
- Design input: `/Users/austinfairbanks/code/jetsonballtracking/docs/media/system-roadmap.svg`.
- Product/claim sources: project `README.md`, `DEPLOYMENT_RESULTS.md`, `ROADMAP.md`, `docs/media/README.md`, `deployment/README.md`, `deployment/live.sh`, and `detection/run.py`.

## Required edit

| Time | Copy | Visual |
|---|---|---|
| 0–4s | `See the ball.` | Real backyard inference from source **6–10s**, with actual ball boxes. |
| 4–8s | `Runs on Jetson.` | Real hardware portrait footage from source **30–32s + 35–37s**; `YOLO11n-seg · TensorRT FP16`. |
| 8–13s | `Live on the Jetson.` | Full-width actual room-feed footage from source **53–58s**, preserving model output and the brief missed detection. |
| 13–17s | `5.03× faster model calls` / `24.72 → 4.92 ms` | Clean measured comparison; `PyTorch CUDA` / `TensorRT FP16`; `640×640 · 25 W · batch 1`. |
| 17–20s | `Next: follow the ball.` / `Tracking + pan/tilt · planned` | Dashed planned-work treatment from the actual roadmap; project-name lockup. |

The supplied edit is approximately 58.66s, 1758 frames, 29.97 FPS at 1280×720 according to its media README. Portrait content is pillarboxed through much of the first ~38s; the full-width live room feed begins around 39s according to contact-sheet inspection. For the selected backyard and hardware clips, crop to **408×720 at x=436, y=0**, then fit the portrait proof panel. Preserve the ball, confidence, and hardware. The live 53–58s excerpt stays full width; four of five sampled seconds contain detections, and its brief missed detection remains. Use source footage at its natural elapsed-time pace; the 30 FPS final export is only a delivery format. Mute original audio and avoid private-address/browser-chrome details in public-facing crops. Prefer actual content framing to a full desktop capture.

## Design and motion

Polished sports/engineering film: real motion, dark navy space, mint accents, concise legible labels. Palette from source SVG: `#111923`, `#f0f5fb`, `#69d8af`, `#142b29`, `#91baff`, `#1a2434`, `#bacadb`. Reuse available local Geist/Geist Mono as an explicit font adaptation. Solid mint communicates what works; dashed blue communicates planned work. Do not reuse the orange Brag brand.

Give the footage prominence. Preserve actual annotations; do not draw fabricated detection or tracking overlays. Keep all text inside safe margins and hold the metric comparison long enough to read. No simulated following camera or motor action. Main title establishes a project in development, not a finished autonomous product.

## Audio

- Music: `/Users/austinfairbanks/.codex/skills/brag/assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`.
- Cue preset: `/Users/austinfairbanks/.codex/skills/brag/assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.md` and matching `.json`.
- SFX selection: `/Users/austinfairbanks/.codex/skills/brag/assets/sfx/sfx-analysis.md` and matching `.json`.
- Steady warm bed around 0.26, starting at 0s, final 0.8s fade. Estimated 109.96 BPM. Optional reveal locks at 13.11s and 17.47s; keep scene boundaries fixed and let readability override cues.
- 2–3 soft motion-matched accents; choose exact SFX after animation exists. No source speech or narration. Copy selected music/SFX under composition `assets/` and use relative paths.
- Use Hyperframes audio-reactive guidance for a very subtle mint panel edge or background-depth response. Keep footage and readable text stable; document if extraction is unavailable.

## Implementation and verification

Load the domain skills directly:

- `/private/tmp/brag-hyperframes-skills/hyperframes-core/SKILL.md`
- `/private/tmp/brag-hyperframes-skills/hyperframes-animation/SKILL.md`
- `/private/tmp/brag-hyperframes-skills/hyperframes-creative/SKILL.md`
- `/private/tmp/brag-hyperframes-skills/hyperframes-keyframes/SKILL.md`
- `/private/tmp/brag-hyperframes-skills/hyperframes-cli/SKILL.md`

Brag supplies the creative contract; Hyperframes owns composition mechanics, seek safety, runtime, lint/check and rendering. Use its domain workflow without an entry-point interview. Keep dependencies/media local where practical. Run `hyperframes check`, resolve errors, inspect representative frames, then render and verify exactly 20s at 30 FPS with audio. Select a strong poster and bake it into frame 0. Keep share copy local.

Claim boundary: 5.03× and 4.92 ms are model-call measurements only, for one preprocessed resident image, same checkpoint, batch 1, 640×640, Jetson Orin Nano in 25 W mode. Live processing is about 15 FPS, with browser stream capped at 10 FPS. Temporal tracking, recovery prediction, pan/tilt hardware, 30 FPS, and >99% precision remain planned/targets; do not imply they are achieved.
