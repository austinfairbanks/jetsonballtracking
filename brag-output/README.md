# Brag — from repo to reel

`brag.mp4` is an original 20-second launch film about the Brag skill, built from
the repository's brand, documented command, and supplied example media.

- 1920 × 1080, 30 fps, H.264 MP4 with music and sparse sound effects.
- `brag.jpg`: selected poster frame, also baked into the MP4's first frame.
- `share-copy.txt`: accompanying caption.
- `composition/`: editable Hyperframes HTML, local fonts, runtime, and media.
- `brag-plan.md` and `composition-brief.md`: creative plan and production brief.
- `sources.md`: source repository, inspected commit, and asset attribution.
- `check.json`: final layout, runtime, and contrast checks.
- `verification.json`: final stream metadata and duration verification.

The personal skill is installed at `/Users/austinfairbanks/.codex/skills/brag`.
It matches `skills/brag` from the inspected repository.

To render the source again, use Node 22+, FFmpeg and FFprobe on PATH, and run:

```sh
cd composition
pnpm dlx hyperframes@0.8.41 check
pnpm dlx hyperframes@0.8.41 render --fps 30 --quality delivery --output ../brag.mp4
```

The renderer above outputs the original animation; the delivered MP4 additionally
has the selected poster baked into its first frame. No narration was requested.
