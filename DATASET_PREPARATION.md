# Frozen Dataset: Volleyball v1

Completed September 15, 2026. Roadmap steps 3 and 4 are complete. No custom
model has been selected or trained during this work.

## Artifacts

- [Restorable CVAT task backup](dataset/exports/20260915T140320Z/cvat-task-1-backup.zip)
- [Untouched Ultralytics YOLO Segmentation 1.0 export, including images](dataset/exports/20260915T140320Z/volleyball-segmentation.zip)
- [Working training configuration](dataset/volleyball-v1/data.yaml)
- [Frozen source-to-split manifest](ops/dataset/v1_split_manifest.csv)
- [Audit report](ops/dataset/v1_audit_report.json)
- [Freeze record and checksums](ops/dataset/v1_freeze.json)
- [Visual QA contact sheets](dataset/volleyball-v1/qa/)

The two ZIPs are about 1.86 GB each. They preserve all 644 source images and
630 annotations: 613 masks and 17 polygons. The working YOLO representation
uses polygons. Original annotations and task/data metadata were also saved as
JSON beside the archives. No CVAT annotations were edited; before/after
snapshots matched. CVAT's workflow status remains `annotation`.

## Frozen split

| Subset | Recording groups | Original image ranges | Included images | Ball annotations | No-ball images |
| --- | --- | --- | --- | --- | --- |
| Train | 1, 2, 4, 6, 7 | 1–79; 128–158; 203–521, excluding 209 and 213 | 427 | 420 | 7 |
| Validation | 3, 5 | 80–127; 159–202 | 92 | 88 | 4 |
| Test | 8 | 522–644 | 123 | 120 | 3 |
| Total | All eight | 644 source images; 2 duplicate copies excluded | 642 | 628 | 14 |

Exact pixel duplicates were found at **206/209** and **207/213**, all in training
group 6. Keep the lower-numbered copy by a deterministic rule, independent of
label quality or model results. Images 209 and 213 remain in both archives and
in the 644-row manifest, marked `included=False` with `duplicate_of` provenance;
they are absent from working training folders. No original files were deleted.
The included split is approximately 66.5% / 14.3% / 19.2%.

Austin confirmed that each angle group comes from a separate video recording;
some share environments. Original video filenames remain unknown. The
[image key](IMAGE_KEY.md) defines the eight groups. No recording crosses subsets.

Training retains evening low light, indoor blur, varied sun/shadow, and overcast
footage. Validation uses two evening recordings. Test holds out the complete
close-ball overcast recording. Use validation for model/checkpoint/settings
selection. Test is for final evaluation after those choices are frozen.
Apply augmentation only to training, after splitting.

## Verification and limitations

- All 644 exported images match the original source bytes and CVAT frame order;
  all retain 1080×1920 dimensions. Every exported object maps to the single
  `volleyball` class, with finite normalized polygon coordinates.
- All 14 user-confirmed negatives are retained as empty label files:
  78, 83, 95, 150, 176, 191, 298, 390, 425, 460, 501, 569, 570, 612.
- Both archives passed full ZIP CRC and SHA-256 checks. Every backup image
  matches its source, and all 630 backup shapes match native annotation fields.
  Backup contents were verified without restoring a second task into CVAT.
- No exact image duplicates cross subsets. A heuristic cross-subset similarity
  screen found no candidates: 1024-bit dHash distance <=80 and 32×32 RGB mean
  absolute difference <=12. This does not prove content independence; the
  recordings share backgrounds and collection conditions.
- Rasterized export/native-mask overlap was checked for all 630 objects:
  median IoU **0.9503**, minimum **0.8075**, with 12 below 0.90. This measures
  conversion fidelity, **not model accuracy**. Boundary quantization and polygon
  conversion affect tiny masks most. Native annotations remain authoritative.
- Visual QA covered samples from all eight groups, the 16 lowest-conversion-IoU
  examples, and all negatives. Inspected exported outlines are aligned with
  visible balls. Conversion differences are accepted and documented for this
  baseline. This was export QA, not an exhaustive independent relabeling.
- The test is one held-out recording in a familiar outdoor environment, not a
  test of unseen locations or room-camera performance. Validation is evening-only.
  A separate labeled room-camera session is still needed for that demo's final
  evaluation; footage used to tune the model must remain development footage.

## Layout and verification commands

```text
dataset/volleyball-v1/
  data.yaml
  split_config.json
  split_manifest.csv
  audit_report.json
  freeze.json
  images/{train,val,test}/
  labels/{train,val,test}/
  qa/
```

Large data/artifacts stay git-ignored. The split config, full manifest, audit
summary, freeze record, and scripts are kept under `ops/dataset` for version
control. Original filenames and zero-based CVAT frame indices are recorded
explicitly; excluded images are not renumbered.

From the repository root, verify the frozen data (Python 3.12+, standard library):

```bash
uv run --no-project --python 3.12 ops/dataset/verify.py dataset/volleyball-v1
uv run --no-project --python 3.12 ops/dataset/verify.py dataset/volleyball-v1 --archives
```

Long-running operations should run inside tmux. The completed run used the
existing isolated Python 3.12 environment at `ops/cvat/.local/sam2-venv` with
Pillow 11.3.0 and numpy 2.2.6; no dependencies were installed globally.

To reconstruct a candidate in a **new** directory from the saved export:

```bash
uv run --no-project --python 3.12 --with pillow==11.3.0 --with numpy==2.2.6 \
  ops/dataset/prepare.py dataset/exports/20260915T140320Z dataset/volleyball-v1-rebuild
```

The preparation script verifies the snapshot and reproduces image/label
assignments and QA sheets. It intentionally leaves the candidate unfrozen for
review. For byte-identical reconstruction, compare its manifest hash to the
saved freeze record before reusing that record. Do not overwrite v1 after
training starts; new labels, exclusions, or split changes require a new version.

`ops/cvat/export_dataset.py` creates fresh timestamped backup/export archives
via the installed asynchronous API, using git-ignored local login credentials.
It creates no labels and rejects annotation changes during the export window.

## References

- [CVAT backup](https://docs.cvat.ai/docs/dataset_management/backup/)
- [CVAT Ultralytics YOLO formats](https://docs.cvat.ai/docs/dataset_management/formats/format-yolo-ultralytics/)
