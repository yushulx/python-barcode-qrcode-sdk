---
name: dbr-template-tuner
description: 'Tune Dynamsoft Barcode Reader template JSON when the default DBR preset returns NO_RESULT on a hard barcode image. Use for difficult QR, DataMatrix, PDF417, 1D, blurry, low-contrast, mirrored, skewed, cropped, warped, or cluttered images when you need evidence-driven parameter tuning instead of random template edits.'
argument-hint: 'image path, current template path, expected barcode type if known'
user-invocable: true
---

# DBR Template Tuning

## When to Use

- The default DBR preset fails with `NO_RESULT` on a barcode image.
- You need to tune `dbr_template.json` or create a focused template for one failure case.
- You want evidence before changing `LocalizationModes`, `DeblurModes`, `MinQuietZoneWidth`, or related parameters.
- You want AI to stop random parameter churn and use a repeatable workflow.

## Inputs

- Image path
- The image itself attached to chat when available, so AI can inspect visual symptoms before changing parameters
- Current template path if one already exists
- Expected format if known, such as `QR`, `DataMatrix`, or `Code128`
- Whether preprocessing is allowed or the ask is strictly template-only
- Whether any included example template is actually relevant to this image

## Procedure

1. Observe the image before touching the template.
Use the image tool on the provided barcode image and describe visible symptoms in concrete terms: quiet-zone loss, border clipping, blur, low contrast, warping, wrinkles, inversion, reflection, background texture, finder-pattern damage, or perspective skew.

2. Validate the current template directly through the simplest DBR path.
The validator must initialize the DBR license before creating `CaptureVisionRouter`; otherwise treat `NO_RESULT` as invalid evidence.
Run `python validate_dbr_template.py <image> --template-file <template>`.

3. Establish a broader baseline only after the direct validation result is known.
Run `python probe_dbr_templates.py <image>`.

Do not assume an existing example template is the right first answer. Only reuse one when the symbol type and failure pattern are close enough to justify it.

4. If the user already has a proven template from Dynamsoft or another teammate, compare it before theorizing.
Run `python compare_dbr_template_profiles.py <current-template> <proven-template>`.

5. If everything still returns `NO_RESULT`, test whether simple preprocessing changes the outcome.
Run `python probe_dbr_templates.py <image> --variant-set basic --report-json tuning-report.json`.

6. Use image observation, the direct validation result, the result matrix, and the template diff to classify the failure.
- Raw image succeeds with a candidate template: keep tuning in the template only.
- Only a preprocessed variant succeeds: the image needs preprocessing plus template tuning.
- No raw or basic variant succeeds: treat this as a stop signal for template-only tuning and say so explicitly.
- A proven template differs mainly in `DeformationResistingModes` or separate decode `ImageParameterOptions`: prioritize those before adding more `DeblurModes`.

7. Change one parameter family at a time.
- Scope first: `ExpectedBarcodesCount`, `BarcodeFormatIds`
- Localization second: `LocalizationModes`, `ConfidenceThreshold`
- Decode third: `DeformationResistingModes`, decode `ImageParameterOptions`, `DeblurModes`, `BarcodeScaleModes`, grayscale and binarization choices
- Acceptance last: `MinQuietZoneWidth`, `MirrorMode`, `ReturnPartialBarcodeValue`

8. Keep the edit minimal.
Prefer a new focused template file with one `CaptureVisionTemplate` over editing a large exported default file.

9. Re-run the direct validator after each edit.
Run `python validate_dbr_template.py <image> --template-file <candidate-template>`.

10. Re-run the broader probe only when needed.
Do not make another parameter change before the previous change is tested.

## Lessons From The Official Template Example

- More `DeblurModes` is not automatically better; a proven template may win through `DRM_BROAD_WARP` and `DRM_DEWRINKLE` with `DeblurModes = null`.
- Separate image parameters for localization and decoding can matter.
- Do not assume custom `BarcodeFormatSpecificationOptions` are needed; leaving default format behavior intact may be better.
- `IfEraseTextZone = 0` can preserve damaged structure that an aggressive text-zone removal step might destroy.
- Standalone DBR helper scripts need license initialization too, not just the GUI app.
- Treat any example template in this folder as a reference point, not a default first move.

## Output Requirements

When using this skill, return:

- a short visual diagnosis based on the image itself
- a short diagnosis of the likely failure mode
- the smallest candidate template change that tests the diagnosis
- the exact direct-validation command to run next
- whether any existing example template is relevant or should be ignored
- a stop condition when evidence suggests the pixels are not recoverable by template tuning alone

## References

- Read the image symptom guide in [image-symptoms.md](./references/image-symptoms.md)
- Read the tuning matrix in [parameter-playbook.md](./references/parameter-playbook.md)
