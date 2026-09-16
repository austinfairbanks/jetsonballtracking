# Volleyball Dataset Image Key

Recorded September 14, 2026 from Austin's completed-labeling update.

## Dataset and annotation status

- **Labeling complete**, as reported by Austin. Annotation export and dataset-wide
  quality checks have not been performed as part of recording this key.
- 644 PNG images in `dataset/keyframes`, named `video1-00001.png` through
  `video1-00644.png`, imported into CVAT task 1 / job 1.
- The ranges below are inclusive and interpreted as the 1-based image numbers
  in those filenames. CVAT API frame indices are 0-based: image 1 corresponds
  to API frame 0.
- One label: `volleyball`. The established annotation convention is polygons
  around the visible ball, excluding hands/background; images without a visible
  ball remain empty.
- Austin reports that most masks were made with **SAM 2.1 Large**. The linked
  task and local configuration confirm the helper was **SAM 2.1 Hiera Large**,
  running on the Mac's Apple GPU with mask-to-polygon conversion in CVAT.
  MobileSAM was used earlier and then replaced. Per-image helper provenance
  and the amount of manual correction are not recorded.

## Image groups

Lighting and scene descriptions are Austin's qualitative observations.

| Group | Images (inclusive) | Scene / angle | Lighting and background | Motion, distance, and sampling notes |
| --- | --- | --- | --- | --- |
| 1 | 1–31 | Evening, angle 1 | Medium light, tentative (reported as “middle level light?”). | — |
| 2 | 32–79 | Evening, angle 2 | Low light; bright blue background. | — |
| 3 | 80–127 | Evening, angle 3 | Medium-high, even light; mixed background. | “Even” is an interpretation of the original “een light.” |
| 4 | 128–158 | Indoors, angle 1 | Lighting/background not specified. | Kicking the ball around along the floor; strong motion blur; ball much closer. |
| 5 | 159–202 | Evening, angle 4 | Medium light; mixed background. | — |
| 6 | 203–332 | Evening, angle 5 | Varying light, bright sunlit spots, and varying shadows. | More images sampled deliberately to capture the lighting variation. |
| 7 | 333–521 | Overcast, angle 1 | Uniform light; white-like background; a little brighter than the other day. | — |
| 8 | 522–644 | Overcast, angle 2 | Backgrounds of varying darkness. | Ball much closer. |

## Confirmed boundary and next decisions

Austin confirmed that **image 521 belongs to overcast angle 1 and image 522
starts overcast angle 2**. The eight ranges cover all 644 images exactly once,
with no gaps or overlaps.

Austin confirmed on September 15 that all eight groups are separate video
recordings, with shared environments as described above. Original video
filenames are not recorded; the `video1-` image prefix does not distinguish the
eight recordings. See [DATASET_PREPARATION.md](DATASET_PREPARATION.md) for the
frozen split and verified exports. The archives retain all 644 images; the
working split has 642 after excluding exact training duplicates 209 and 213
(copies of 206 and 207). Original image numbers are unchanged.

The carried-forward immediate project target is a live volleyball mask overlay
with measured FPS and latency, initially using a phone and a close, stationary
or slowly moving ball. Tracking and drone integration follow later. SAM is the
labeling helper; the deployable segmentation model has not been selected or
trained in this step.

## Context sources

- [Prior task: Locate prior project decisions](codex://threads/01a09d10-deb8-76c3-a9e9-3999d66f4e61),
  including its final MobileSAM-to-SAM-2.1-Large upgrade.
- Austin's September 14, 2026 completion report and eight image ranges in the
  current task.
- [CVAT setup and labeling convention](ops/cvat/README.md).
- [SAM helper decision and test evidence](REFERENCES.md).
