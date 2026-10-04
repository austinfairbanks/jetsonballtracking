# Hyperframes Composition Brief: /brag

Create a new 20.00-second launch video about the Brag skill itself. Use `brag-plan.md` as the storyboard contract; it contains exact copy, scene boundaries, all nine inspection answers, and audio direction.

## Output and inputs

- Output root: `/Users/austinfairbanks/code/jetsonballtracking/brag-output`.
- Composition: `/Users/austinfairbanks/code/jetsonballtracking/brag-output/composition/`.
- Deliverables: `brag.mp4` and best-frame `brag.jpg`, alongside the plan, brief, `share-copy.txt`, and `sources.md`.
- Format: landscape, 1920×1080, exactly 20.00s; narration disabled.
- Brag source repository: `/private/tmp/brag-source-20260917`.
- Installed Brag skill: `/Users/austinfairbanks/.codex/skills/brag/SKILL.md`.
- Primary project sources: `README.md`, `PRODUCT.md`, `docs/index.html`, `docs/styles.css` in the repository above.

## Story and design

Tone `default`: confident editorial launch with a straight-faced recursive joke. The user flow is coding-agent prompt → rendered video and share copy. Recreate the documented interaction honestly and use real example footage to substantiate the output. Do not invent an editing application, execution logs, adoption figures, or rendering-speed claims.

| Time | Required copy | Required visual |
|---|---|---|
| 0.00–3.70 | `you built it.` / `now brag.` | Actual orange hero typography, italic reverse highlight, real project thumbnail. |
| 3.70–8.44 | `one command.` / `let's /brag` | Simulated coding-agent typing, with the source project present. |
| 8.44–12.65 | `your project, in motion.` | Actual example footage in a result preview; `brag.mp4` and `share-copy.txt` appear beside it. |
| 12.65–16.34 | `music. motion. share copy.` | Actual horse tinder, fish flight school, taxi for taxis example cards. |
| 16.34–20.00 | `now go brag.` / `github.com/latent-spaces/brag` | Orange final lockup with `/brag`; optional Hyperframes credit. |

Brand: Geist 900 display, Geist body, Geist Mono labels. Orange `oklch(64% 0.22 35)`, ink `oklch(16% 0.06 35)`, dark background `oklch(14% 0.03 35)`, cream `oklch(96% 0.02 35)`, dark-scene accent `oklch(72% 0.22 35)`. Prefer local fonts. Avoid abstract filler and generic gradient branding. Let readable copy settle after quick entrances; maintain generous safe margins.

## Real media

Paths below are relative to `/private/tmp/brag-source-20260917`:

- `docs/assets/hero.png` and `docs/assets/hero-poster.jpg`.
- `docs/assets/brag-about-brag.mp4` — an existing reference/example clip, not the final deliverable.
- `docs/examples/horse-tinder/{site.jpg,brag.jpg,brag.mp4}`.
- `docs/examples/fish-flight-school/{site.jpg,brag.jpg,brag.mp4}`.
- `docs/examples/taxi-for-taxis/{site.jpg,brag.jpg,brag.mp4}`.

Copy selected assets into the composition and use relative paths. Mute source example footage so the new music/SFX mix controls the soundtrack. Preserve original branding and use footage as supporting evidence inside the newly authored video.

## Audio

- Music source: `/private/tmp/brag-source-20260917/skills/brag/assets/music/happy-beats-business-moves-vol-9-by-ende-dot-app.mp3`.
- Cue sources: `/private/tmp/brag-source-20260917/skills/brag/assets/music/cues/happy-beats-business-moves-vol-9-by-ende-dot-app.music-cues.md` and the matching `.json`.
- SFX selection guidance: `/private/tmp/brag-source-20260917/skills/brag/assets/sfx/sfx-analysis.md` and matching `.json`.
- Warm music bed around 0.30; start at 0s, brief fade-in, final 0.80s fade-out. Estimated tempo 114.84 BPM; optional major locks at 3.70, 8.44, and 12.65s. Use the plan’s beat windows for sequential motion only when readability permits.
- Sparse typing, output reveal, and card-motion accents. Choose exact SFX after the animation exists; low/medium high-frequency risk is preferred. Put copied music and chosen SFX under composition `assets/`.
- Use Hyperframes’ audio extraction guidance for subtle energy-driven card presence or background depth; keep text stable. If extraction is unavailable, document that omission and continue the render. Do not add narration.

## Hyperframes handoff and verification

Load these exact domain-skill entry files:

- `/private/tmp/brag-hyperframes-skills/hyperframes-core/SKILL.md`
- `/private/tmp/brag-hyperframes-skills/hyperframes-animation/SKILL.md`
- `/private/tmp/brag-hyperframes-skills/hyperframes-creative/SKILL.md`
- `/private/tmp/brag-hyperframes-skills/hyperframes-keyframes/SKILL.md`
- `/private/tmp/brag-hyperframes-skills/hyperframes-cli/SKILL.md`

Brag supplies the creative contract; Hyperframes owns implementation, timing mechanics, seek safety, runtime, and render workflow. Follow this direct domain-skill workflow without an entry-point intent interview. Use local dependencies/assets where practical. Do not author or overwrite unrelated project files.

Before rendering, run `hyperframes check` and resolve errors. Inspect representative frames for clipping, missing media/fonts, legibility, and scene transitions. Verify the final 20.00s duration and audio presence; choose a strong poster and bake it as frame 0. Keep share copy local for user delivery.
