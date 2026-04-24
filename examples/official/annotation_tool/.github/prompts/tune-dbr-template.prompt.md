---
name: "Tune DBR Template"
description: "Tune Dynamsoft Barcode Reader template parameters when the default DBR preset cannot decode a hard barcode image. Use for difficult QR, DataMatrix, PDF417, 1D, blurry, low-contrast, skewed, cropped, mirrored, or repeated NO_RESULT cases."
argument-hint: "image path, current template path, expected format, constraints"
agent: "agent"
model: "GPT-5 (copilot)"
---

Tune a Dynamsoft Barcode Reader template for the user's image and template inputs.
Do not assume the image is a QR code and do not assume any existing example template is the correct first move.

Workflow:

1. Inspect the image itself first using the image tool.
2. Describe the visible symptoms before proposing any parameter changes.
3. Read the current template file if the user provided one.
4. Decide whether any existing example template in the workspace is actually relevant to this image's format and failure mode. If not, say so explicitly and ignore it.
5. Run `python validate_dbr_template.py <image> --template-file <template>` first when a template file is available.
Make sure the script initializes the DBR license before it creates `CaptureVisionRouter`; otherwise ignore `NO_RESULT` from that run.
6. If the user also provided a known-good template, run `python compare_dbr_template_profiles.py <current-template> <known-good-template>` and use that diff to choose the next parameter family.
7. Run `python probe_dbr_templates.py <image>`.
8. If the image still fails, run `python probe_dbr_templates.py <image> --variant-set basic --report-json tuning-report.json`.
9. Classify the failure as one of:
   - scope problem
   - localization problem
   - decode problem
   - acceptance problem
   - pixels likely unrecoverable by template-only tuning
10. Propose the smallest template change that tests the classification.
11. If a known-good template differs mainly in `DeformationResistingModes`, decode `ImageParameterOptions`, or text-zone removal, prioritize migrating those before adding more `DeblurModes`.
12. If a change is needed, create or update a focused template file instead of editing a large exported template unless the user explicitly asked otherwise.
13. Re-run `python validate_dbr_template.py <image> --template-file <candidate-template>` after the edit.

Output format:

- Visual diagnosis
- Diagnosis
- Example-template relevance
- Exact JSON change
- Validation command
- Next fallback step if it still fails

Constraints:

- Do not skip image inspection when the image is available.
- Do not assume the included incomplete-QR template applies unless the image really matches that failure pattern.
- Change one parameter family at a time.
- Do not skip a known-good template diff when one is available.
- Do not keep randomizing parameters after raw plus basic variants all fail.
- Say explicitly when preprocessing or recapturing the image is more justified than more template edits.
- Treat standalone helper output as valid only after DBR license initialization is confirmed.
