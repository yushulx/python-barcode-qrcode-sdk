# DBR Parameter Playbook

## Goal

Use image symptoms to narrow the next DBR parameter change instead of changing unrelated sections.

When a proven template exists, diff the template structure before editing anything:

```bash
python compare_dbr_template_profiles.py current-template.json proven-template.json
```

## Decision Table

### Few symbols, known format

- Set `ExpectedBarcodesCount` to `1`
- Restrict `BarcodeFormatIds` to the expected format family
- Prefer a focused template file over editing a multi-template export

### Barcode likely exists but is not found

- Change `LocalizationModes` before decode modes
- Add or prioritize `LM_SCAN_DIRECTLY`, `LM_CONNECTED_BLOCKS`, `LM_NEURAL_NETWORK`
- Lower `ConfidenceThreshold` only after narrowing the format and count

### Barcode is found on some variants but decode is unstable

- Leave localization unchanged
- Check whether a proven template is solving this with `DeformationResistingModes` instead of `DeblurModes`
- Prefer migrating `DRM_BROAD_WARP`, `DRM_DEWRINKLE`, or a separate decode image parameter block before adding more deblur modes
- Then try stronger grayscale or binarization variants
- Touch acceptance parameters only after decode-oriented changes are exhausted

### Suspected quiet-zone or crop issue

- Lower `MinQuietZoneWidth`
- Try `MirrorMode = MM_BOTH` when orientation is uncertain
- Test padded variants before making more template edits

### Light-on-dark or unusual foreground/background

- Include both `GTM_ORIGINAL` and `GTM_INVERTED`
- Test normal and inverted binarized variants

### No raw image or basic variant decodes in any engine

- Stop calling it a template problem without qualification
- Report that template-only tuning is likely exhausted for the current pixels
- Recommend preprocessing, re-capture, crop refinement, or a human-verified ground truth path

## Official Template Lessons

- Proven templates may keep `BarcodeFormatSpecificationNameArray` as `null`; do not invent format specs without evidence.
- Proven templates may separate localization and decode image parameters. That split is a real parameter family, not just formatting.
- `IfEraseTextZone` is worth checking when the symbol is damaged or small.
- If a proven template differs from yours mainly in deformation handling, do not keep iterating on localization or quiet-zone settings first.

## AI Guidance

When AI proposes a new template, require it to provide these four items together:

1. The observed symptom from the image or probe report
2. The single parameter family being changed
3. The exact JSON snippet to change
4. The next validation command

Reject proposals that change localization, decoding, and acceptance rules all at once unless there is a strong reason.

## Minimal Template Strategy

- Keep one `CaptureVisionTemplate`
- Keep one `TargetROIDefOptions` entry
- Keep one focused `BarcodeReaderTaskSettingOptions` entry
- Add `ImageParameterOptions` only when preprocessing behavior is part of the hypothesis
- Copy only proven sections from exported templates
