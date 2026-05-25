# DBR Template Knowledge Base

> This document is a living knowledge base about Dynamsoft Barcode Reader (DBR) templates.
> It grows with each optimization run and community verification. Contributions from Dynamsoft
> engineers are especially welcome to verify accuracy and fill gaps.
>
> **Last verified against official docs**: 2026-02-18

## Template JSON Architecture (DCV v3.x)

A DBR template is a JSON file conforming to the **Dynamsoft Capture Vision (DCV) parameter structure**. It is not a flat key-value config — it's a hierarchical pipeline definition with named, cross-referenced objects.

### Top-Level Sections

```
{
  "CaptureVisionTemplates": [...]      // Entry points — define the capture pipeline
  "TargetROIDefOptions": [...]          // Region-of-interest definitions
  "BarcodeReaderTaskSettingOptions": [...]  // Barcode-specific task parameters
  "ImageParameterOptions": [...]        // Image preprocessing parameters
  "BarcodeFormatSpecificationOptions": [...]  // Per-format fine-tuning
  "GlobalParameter": {...}              // Thread count, memory limits
}
```

### How They Connect

```
CaptureVisionTemplate
  ├─ Name: "ReadBarcodes_Default"
  ├─ ImageROIProcessingNameArray: ["roi-read-barcodes"]
  ├─ Timeout: 10000
  └─ MaxParallelTasks: 4

TargetROIDefOptions
  ├─ Name: "roi-read-barcodes"
  └─ TaskSettingNameArray: ["task-read-barcodes"]

BarcodeReaderTaskSettingOptions
  ├─ Name: "task-read-barcodes"
  ├─ BarcodeFormatIds: ["BF_DEFAULT"]
  ├─ BarcodeFormatSpecificationNameArray: ["bfs1", "bfs2"]
  └─ SectionArray:
       ├─ ST_REGION_PREDETECTION
       │    └─ SST_PREDETECT_REGIONS → RegionPredetectionModes
       ├─ ST_BARCODE_LOCALIZATION
       │    ├─ SST_LOCALIZE_CANDIDATE_BARCODES → LocalizationModes
       │    └─ SST_LOCALIZE_BARCODES
       └─ ST_BARCODE_DECODING
            ├─ SST_RESIST_DEFORMATION → DeformationResistingModes
            ├─ SST_COMPLEMENT_BARCODE → BarcodeComplementModes
            ├─ SST_SCALE_BARCODE_IMAGE → BarcodeScaleModes
            └─ SST_DECODE_BARCODES → DeblurModes

ImageParameterOptions
  ├─ Name: "ip-read-barcodes"
  └─ ApplicableStages:
       ├─ SST_SCALE_IMAGE → ImageScaleSetting
       ├─ SST_CONVERT_TO_GRAYSCALE → ColourConversionModes
       ├─ SST_TRANSFORM_GRAYSCALE → GrayscaleTransformationModes
       ├─ SST_ENHANCE_GRAYSCALE → GrayscaleEnhancementModes
       ├─ SST_BINARIZE_IMAGE → BinarizationModes
       ├─ SST_DETECT_TEXTURE → TextureDetectionModes
       ├─ SST_REMOVE_TEXTURE_FROM_GRAYSCALE → TextureRemovalStrength
       ├─ SST_BINARIZE_TEXTURE_REMOVED_GRAYSCALE → BinarizationModes (BM_AUTO default)
       ├─ SST_FIND_CONTOURS
       ├─ SST_DETECT_SHORTLINES → ShortlineDetectionMode
       ├─ SST_ASSEMBLE_LINES → LineAssemblyMode
       ├─ SST_DETECT_TEXT_ZONES → TextDetectionMode
       └─ SST_REMOVE_TEXT_ZONES_FROM_BINARY → IfEraseTextZone
```

> **Note on ST_BARCODE_DECODING stage order**: The official docs list SST_COMPLEMENT_BARCODE
> before SST_RESIST_DEFORMATION, but the SDK's own `OutputSettings()` dump (v3.4.1000) outputs
> SST_RESIST_DEFORMATION first. The order shown above matches the actual SDK dump. This
> discrepancy may be a documentation issue — the SDK dump is treated as authoritative.

### Key Insight: Section/Stage Architecture

In DCV v3.x templates, parameters are organized into **Sections** and **Stages** within `BarcodeReaderTaskSettingOptions.SectionArray`. Each stage corresponds to a processing step and has its own mode array. This is different from older DBR v9.x templates where parameters were flat.

When modifying a template, you must place parameters in the correct stage:
- `LocalizationModes` → `ST_BARCODE_LOCALIZATION` / `SST_LOCALIZE_CANDIDATE_BARCODES`
- `DeformationResistingModes` → `ST_BARCODE_DECODING` / `SST_RESIST_DEFORMATION`
- `BarcodeComplementModes` → `ST_BARCODE_DECODING` / `SST_COMPLEMENT_BARCODE`
- `BarcodeScaleModes` → `ST_BARCODE_DECODING` / `SST_SCALE_BARCODE_IMAGE`
- `DeblurModes` → `ST_BARCODE_DECODING` / `SST_DECODE_BARCODES`

Image-level parameters go in `ImageParameterOptions.ApplicableStages`.

Each section in BarcodeReaderTaskSettingOptions references an `ImageParameterName` to link to the appropriate ImageParameter for that section's image preprocessing.

---

## Parameter Deep Dive

### GrayscaleTransformationModes

**Where**: `ImageParameterOptions` → `SST_TRANSFORM_GRAYSCALE`

| Mode | Description |
|------|-------------|
| `GTM_ORIGINAL` | Keep original grayscale polarity (dark bars on light background) |
| `GTM_INVERTED` | Invert grayscale (light bars on dark background) |
| `GTM_AUTO` | Library chooses automatically at runtime |

**Sub-parameters**: Only `Mode` (no numeric sub-parameters).

**Defaults by use case**:
- Barcode reading: `[GTM_ORIGINAL]`
- Label recognizing: `[GTM_ORIGINAL, GTM_INVERTED]`

**Best practice**: Always include both `GTM_ORIGINAL` and `GTM_INVERTED` (or use `GTM_AUTO`). The SDK tries each in order and uses whichever works. Cost is minimal (a simple pixel inversion) but the gain can be enormous — any inverted barcode will be completely invisible without `GTM_INVERTED`.

**Observed impact**: In our testing, adding GTM_INVERTED contributed to a +7.4% decode rate improvement (part of a combined change).

### GrayscaleEnhancementModes

**Where**: `ImageParameterOptions` → `SST_ENHANCE_GRAYSCALE`

| Mode | Description | Sub-parameters |
|------|-------------|----------------|
| `GEM_GENERAL` | No preprocessing — passes through un-preprocessed grayscale (default) | — |
| `GEM_GRAY_EQUALIZE` | Histogram equalization — improves contrast | `Sensitivity` (1-9, default 5) |
| `GEM_GRAY_SMOOTH` | Gaussian smoothing — reduces noise | `SmoothBlockSizeX/Y` (3-1000, default 3) |
| `GEM_SHARPEN_SMOOTH` | Sharpen then smooth — edges + noise reduction | `SharpenBlockSizeX/Y` (3-1000, default 3), `SmoothBlockSizeX/Y` (3-1000, default 3) |
| `GEM_SKIP` | Skip grayscale enhancement entirely | — |

> **Correction from official docs**: `Sensitivity` only applies to `GEM_GRAY_EQUALIZE` (controls
> likelihood of equalization activation). `SharpenBlockSizeX/Y` only applies to `GEM_SHARPEN_SMOOTH`,
> not to `GEM_GRAY_SMOOTH`. `GEM_GENERAL` has no numeric sub-parameters — it's a pass-through.

**Best practice**: For noisy images (camera captures in poor lighting), use all four active modes. The SDK tries each and picks the best result. `GEM_GRAY_EQUALIZE` is particularly effective for low-contrast images. `GEM_GRAY_SMOOTH` helps with color noise/speckle.

**Observed impact**: Adding GEM_GRAY_EQUALIZE + GEM_SHARPEN_SMOOTH contributed to improved decode rates on noisy camera-captured DataMatrix codes.

### DeblurModes

**Where**: `BarcodeReaderTaskSettingOptions` → `ST_BARCODE_DECODING` / `SST_DECODE_BARCODES`

| Mode | Description | Speed Impact |
|------|-------------|-------------|
| `DM_BASED_ON_LOC_BIN` | Reuse binary image from localization stage | Fast |
| `DM_THRESHOLD_BINARIZATION` | Global threshold binarization | Fast |
| `DM_DIRECT_BINARIZATION` | Direct binarization on grayscale | Fast |
| `DM_GRAY_EQUALIZATION` | Equalize then binarize | Medium |
| `DM_SMOOTHING` | Smooth then binarize | Medium |
| `DM_SHARPENING` | Sharpen then binarize | Medium |
| `DM_SHARPENING_SMOOTHING` | Sharpen → smooth → binarize | Medium |
| `DM_MORPHING` | Morphological operations then binarize | Medium |
| `DM_DEEP_ANALYSIS` | ML-based deep analysis | Slow |
| `DM_NEURAL_NETWORK` | CNN-based deblurring with specialized models | Slow |
| `DM_SKIP` | Skip deblurring | — |

**Sub-parameters**:

| Sub-parameter | Type | Range | Default | Applies To |
|---------------|------|-------|---------|------------|
| `ModelNameArray` | String[] | "OneDDeblur", "EAN13Decoder", "Code128Decoder", "Code39ITFDecoder", "DataMatrixQRCodeDeblur", "PDF417Deblur" | null (= all models) | `DM_NEURAL_NETWORK` |
| `Level` | int | [1, 9] | 4 | `DM_NEURAL_NETWORK` |
| `Methods` | String[] | "OneDGeneral", "TwoDGeneral", "EAN13Enhanced" | null | `DM_DEEP_ANALYSIS` |

> **Important correction from official docs**: When `DeblurModes` is `null` in the template JSON,
> the SDK does **NOT** skip deblurring. Instead, it uses **format-specific internal defaults**:
>
> - **PDF417**: `[DM_BASED_ON_LOC_BIN, DM_THRESHOLD_BINARIZATION, DM_DIRECT_BINARIZATION, DM_SMOOTHING, DM_GRAY_EQUALIZATION, DM_MORPHING, DM_DEEP_ANALYSIS]`
> - **1D formats**: `[DM_BASED_ON_LOC_BIN, DM_THRESHOLD_BINARIZATION, DM_DIRECT_BINARIZATION, DM_NEURAL_NETWORK, DM_DEEP_ANALYSIS, DM_SMOOTHING, DM_GRAY_EQUALIZATION, DM_MORPHING]`
> - **QR, DataMatrix, etc.**: `[DM_BASED_ON_LOC_BIN, DM_THRESHOLD_BINARIZATION, DM_DIRECT_BINARIZATION, DM_DEEP_ANALYSIS, DM_SMOOTHING, DM_GRAY_EQUALIZATION, DM_MORPHING]`
>
> This means `null` is actually a reasonable default that already includes most modes. Setting
> DeblurModes explicitly is useful when you want to control the **order** or **include modes
> not in the defaults** (like DM_SHARPENING, DM_SHARPENING_SMOOTHING, DM_NEURAL_NETWORK for 2D).

**Tip from docs**: For 1D barcodes, adding `DM_THRESHOLD_BINARIZATION` **twice** in the array enables a "second round" of blurry area detection and filling, which can sharply improve read rate for blurry 1D codes at the cost of accuracy.

**Best practice**: For maximum decode rate, explicitly set all modes. Array index = priority (lower index tried first). The SDK tries modes in order and stops when one succeeds.

**Observed impact**: Explicitly setting all 9 modes (excluding DM_NEURAL_NETWORK and DM_SKIP) improved decode rate by +4.0% (from 52.48% to 56.44%) on extremely noisy DataMatrix images, converting 8 additional images.

### LocalizationModes

**Where**: `BarcodeReaderTaskSettingOptions` → `ST_BARCODE_LOCALIZATION` / `SST_LOCALIZE_CANDIDATE_BARCODES`

| Mode | Description | Best For |
|------|-------------|----------|
| `LM_CONNECTED_BLOCKS` | Connected component analysis | General purpose — **recommended at highest priority** |
| `LM_SCAN_DIRECTLY` | Scan lines in multiple directions | 1D barcodes, interactive scenarios |
| `LM_STATISTICS` | Statistical analysis of pixel distribution | QR Code, DataMatrix |
| `LM_LINES` | Detect lines then find barcodes | 1D barcodes, PDF417 |
| `LM_STATISTICS_MARKS` | Statistical analysis for marks/dots | DPM codes |
| `LM_STATISTICS_POSTAL_CODE` | Optimized for postal codes | Postal barcodes |
| `LM_CENTRE` | Scan from image center outward | Cropped barcode images |
| `LM_NEURAL_NETWORK` | Neural network-based detection | Complex scenes |
| `LM_ONED_FAST_SCAN` | Very fast scan for 1D barcodes | Speed-critical 1D scenarios |
| `LM_SKIP` | Skip localization | — |

**Sub-parameters**:

| Sub-parameter | Type | Range | Default | Applies To |
|---------------|------|-------|---------|------------|
| `ScanStride` | int | [0, 0x7fffffff] | 0 (auto) | `LM_SCAN_DIRECTLY`, `LM_ONED_FAST_SCAN` |
| `ScanDirection` | int | 0=both, 1=vertical, 2=horizontal | 0 | `LM_SCAN_DIRECTLY`, `LM_ONED_FAST_SCAN` |
| `ConfidenceThreshold` | int | [0, 100] | 60 | `LM_ONED_FAST_SCAN` |
| `IsOneDStacked` | int | [0, 1] | 0 | `LM_SCAN_DIRECTLY` |
| `ModuleSize` | int | [0, 0x7fffffff] | 0 | `LM_CENTRE` |
| `ModelNameArray` | String[] | "OneDLocalization", "DataMatrixQRCodeLocalization", "PDF417Localization" | null | All modes |

> **Correction from official docs**: `ConfidenceThreshold` in the default template dump appears
> on all modes with value 60, but the official docs state it only applies to `LM_ONED_FAST_SCAN`.
> The default dump includes it on all modes for serialization completeness.

**Default**: `[LM_CONNECTED_BLOCKS, LM_SCAN_DIRECTLY, LM_STATISTICS, LM_LINES]`

**Observed impact**: Adding `LM_STATISTICS_MARKS` + `LM_CENTRE` helped decode 4 more DataMatrix images (many of our images are tightly cropped barcode captures where LM_CENTRE is ideal).

### BarcodeScaleModes

**Where**: `BarcodeReaderTaskSettingOptions` → `ST_BARCODE_DECODING` / `SST_SCALE_BARCODE_IMAGE`

> **Note**: This parameter replaces the deprecated `ScaleUpModes` from earlier SDK versions.
> BarcodeScaleModes supports both **scale-up AND scale-down**.

| Mode | Description |
|------|-------------|
| `BSM_AUTO` | Library automatically selects scaling approach (default) |
| `BSM_LINEAR_INTERPOLATION` | Linear interpolation for image scaling |

> **Correction from official docs**: `BSM_NEAREST_NEIGHBOUR_INTERPOLATION` is NOT listed in
> the current official documentation. Only `BSM_AUTO` and `BSM_LINEAR_INTERPOLATION` are
> documented as valid modes.

**Sub-parameters**:

| Sub-parameter | Type | Range | Default | Description |
|---------------|------|-------|---------|-------------|
| `ModuleSizeThreshold` | int | [0, 0x7fffffff] | 0 (auto) | Triggers scaling when module size differs from target |
| `TargetModuleSize` | int | [0, 0x7fffffff] | 0 (auto) | Destination module size |
| `AcuteAngleWithXThreshold` | int | [-1, 90] | -1 (auto) | Min angle with X-axis for scaling |

**Scaling logic** (from official docs):
- When `ModuleSizeThreshold < TargetModuleSize` → **enlarge** by power-of-2 factor
- When `ModuleSizeThreshold > TargetModuleSize` → **shrink** by power-of-2 factor
- When equal → skip scaling

**Best practice**: Add `BSM_LINEAR_INTERPOLATION` before `BSM_AUTO` for small barcodes. Set `ModuleSizeThreshold=4` and `TargetModuleSize=6` as starting values.

### DeformationResistingModes

**Where**: `BarcodeReaderTaskSettingOptions` → `ST_BARCODE_DECODING` / `SST_RESIST_DEFORMATION`

| Mode | Description |
|------|-------------|
| `DRM_SKIP` | No deformation handling (default) |
| `DRM_GENERAL` | General deformation-resisting algorithm |
| `DRM_BROAD_WARP` | Broad warp correction |
| `DRM_LOCAL_REFERENCE` | Local reference-based correction |
| `DRM_DEWRINKLE` | De-wrinkling algorithm |
| `DRM_AUTO` | Automatic mode selection |

**Sub-parameters**:

| Sub-parameter | Type | Range | Default | Applies To |
|---------------|------|-------|---------|------------|
| `Level` | int | [1, 9] | 5 | `DRM_GENERAL` |
| `GrayscaleEnhancementMode` | Object | Inline GEM mode object | — | `DRM_BROAD_WARP`, `DRM_LOCAL_REFERENCE`, `DRM_DEWRINKLE` |
| `BinarizationMode` | Object | Inline BM mode object | — | `DRM_BROAD_WARP`, `DRM_LOCAL_REFERENCE`, `DRM_DEWRINKLE` |

> **Note**: `DRM_BROAD_WARP`, `DRM_LOCAL_REFERENCE`, and `DRM_DEWRINKLE` accept **inline**
> `GrayscaleEnhancementMode` and `BinarizationMode` objects (not by index reference, but as
> full embedded mode objects).

**Best practice**: Enable `DRM_GENERAL` if any barcodes might be on curved surfaces. For more specific deformation types, use the specialized modes. Cost is moderate.

### BarcodeComplementModes

**Where**: `BarcodeReaderTaskSettingOptions` → `ST_BARCODE_DECODING` / `SST_COMPLEMENT_BARCODE`

| Mode | Description |
|------|-------------|
| `BCM_SKIP` | No complement (default) |
| `BCM_GENERAL` | Attempt to reconstruct damaged/incomplete barcodes |
| `BCM_AUTO` | Automatic selection (**not supported yet** per official docs) |

**Sub-parameters**: Only `Mode`.

**Best practice**: Enable `BCM_GENERAL` for images with potentially damaged or partially obscured barcodes. Relatively low cost.

### BinarizationModes

**Where**: `ImageParameterOptions` → `SST_BINARIZE_IMAGE` (also `SST_BINARIZE_TEXTURE_REMOVED_GRAYSCALE`)

| Mode | Description |
|------|-------------|
| `BM_LOCAL_BLOCK` | Adaptive local threshold (default for SST_BINARIZE_IMAGE, best for uneven lighting) |
| `BM_THRESHOLD` | Single unified threshold for entire image (for uniform lighting) |
| `BM_AUTO` | Automatic selection (default for SST_BINARIZE_TEXTURE_REMOVED_GRAYSCALE) |
| `BM_SKIP` | Skip binarization |

**Sub-parameters**:

| Sub-parameter | Type | Range | Default | Applies To |
|---------------|------|-------|---------|------------|
| `BlockSizeX` | int | [0, 1000] | 0 (auto) | `BM_LOCAL_BLOCK` |
| `BlockSizeY` | int | [0, 1000] | 0 (auto) | `BM_LOCAL_BLOCK` |
| `ThresholdCompensation` | int | [-255, 255] | 10 | `BM_LOCAL_BLOCK` |
| `EnableFillBinaryVacancy` | int | [0, 1] | 1 | `BM_LOCAL_BLOCK` |
| `BinarizationThreshold` | int | [-1, 255] | -1 (auto) | `BM_THRESHOLD` |
| `MorphOperation` | String | "None", "Erode", "Dilate", "Open", "Close", "Auto" | "None" | All modes |
| `MorphOperationKernelSizeX` | int | [0, 1000] | 0 (auto) | All modes |
| `MorphOperationKernelSizeY` | int | [0, 1000] | 0 (auto) | All modes |
| `MorphShape` | String | "Rectangle", "Cross", "Ellipse" | "Rectangle" | All modes |
| `GrayscaleEnhancementModesIndex` | int | [-1, 0x7fffffff] | -1 | All modes |

> **Cross-parameter interaction**: `GrayscaleEnhancementModesIndex` links a binarization
> configuration to a specific GrayscaleEnhancementModes result by array index. Value of -1
> means binarization operates independently.

### Other Important Parameters

| Parameter | Location | Notes |
|-----------|----------|-------|
| `Timeout` | `CaptureVisionTemplates` | Default 10000ms. Increase to 30000-60000 for difficult images. |
| `MinResultConfidence` | `BarcodeFormatSpecificationOptions` | Default 30. Lower to 10 to accept borderline results. |
| `ExpectedBarcodesCount` | `BarcodeReaderTaskSettingOptions` | 0 = find all. Higher values may speed up processing. |
| `MirrorMode` | `BarcodeFormatSpecificationOptions` | MM_NORMAL, MM_MIRROR, MM_BOTH |
| `DPMCodeReadingModes` | `BarcodeReaderTaskSettingOptions` | DPMCRM_SKIP (default), DPMCRM_GENERAL. For tiny single-code DataMatrix crops, test `DPMCRM_GENERAL` before adding rescue ROIs. |
| `TextureDetectionModes` | `ImageParameterOptions` → `SST_DETECT_TEXTURE` | TDM_GENERAL_WIDTH_CONCENTRATION |

### DPM On Tiny DataMatrix Crops

Do not reserve `DPMCRM_GENERAL` only for obviously etched metal marks. In practice it can also rescue tiny, rotated, single-code DataMatrix crops that behave more like direct-part-mark scenes than like large printed labels.

**Validated case**:

- Baseline single-ROI tube-cap template with `GTM_AUTO` plus `LM_CONNECTED_BLOCKS` / `LM_LINES` / `LM_STATISTICS` stalled at `95/96` on `matrix/`, missing only `barcode-025.png`.
- Changing only the scope-level settings to `DPMCodeReadingModes = DPMCRM_GENERAL` and `ExpectedBarcodesCount = 1` lifted the same single-ROI template to `96/96` on `matrix/` while preserving `20/20` on `tubes/cropped_barcodes/barcode_001-020.png`.
- A narrower port of an inverted-only DPM template also reached `96/96` on `matrix/`, but collapsed to `1/20` on the earlier crop slice. That means the DPM mode was the reusable win; the inverted-only preprocessing was dataset-specific overfitting.
- Standard DataMatrix inverted-only variants without `DPMCRM_GENERAL` stayed at `95/96`, so the decisive lever in this case was the DPM read path rather than `ExpectedBarcodesCount` alone.

**Best practice**:

- When the scene is one small DataMatrix per crop and standard tuning stalls on one or two hard images, treat `DPMCodeReadingModes` as a scope-level experiment alongside `ExpectedBarcodesCount` before adding center-only crops or multi-ROI rescue.
- Validate the DPM candidate on both the hard slice and one neighboring broader slice. If an inverted-only DPM port wins on the hard slice but collapses on nearby crops, keep the broader preprocessing and port only the DPM behavior.

---

## Cross-Parameter Interactions

These interactions are documented in the official Dynamsoft docs:

1. **BinarizationModes.GrayscaleEnhancementModesIndex** — Links a specific binarization config to a specific GrayscaleEnhancementModes result by array index.

2. **DeformationResistingModes** (DRM_BROAD_WARP / DRM_LOCAL_REFERENCE / DRM_DEWRINKLE) — Embed their own inline `GrayscaleEnhancementMode` and `BinarizationMode` objects for re-processing the deformed barcode image.

3. **DeblurModes with DM_BASED_ON_LOC_BIN** — Reuses the binary image from the localization stage, tying decoding to localization results.

4. **GrayscaleTransformationModes with GTM_INVERTED** — Affects all downstream stages (enhancement, binarization, localization, decoding).

5. **BarcodeScaleModes** — Replaces the deprecated `ScaleUpModes` and supports both scale-up AND scale-down via `ModuleSizeThreshold` vs `TargetModuleSize` comparison.

---

## Evidence-Driven Triage

Use this workflow before broad optimization when one hard image or one recurring failure case is blocking progress.

### Observe The Image First

Before touching the template, describe only what is visibly true in the image:

- Is the quiet zone missing or very thin?
- Is any edge clipped by the image boundary?
- Is the symbol warped, folded, stretched, or wrinkled?
- Is the image blurry, or mainly low contrast?
- Is the code dark-on-light, light-on-dark, or ambiguous?
- Is there heavy background texture or nearby text?
- Are finder or timing patterns obviously damaged?
- Is the symbol front-facing or perspective-skewed?

### Bundled Evidence Path

For single-image failures, use the bundled helper tools in this order. If your repo still exposes root-level wrappers, treat them as compatibility aliases for these commands:

1. **Direct validation**

  ```bash
  python template-optimizer/tools/validate_dbr_template.py <image> --template-file <template>
  ```

2. **Broader baseline**

  ```bash
  python template-optimizer/tools/probe_dbr_templates.py <image>
  ```

3. **Template diff against a proven reference**

  ```bash
  python template-optimizer/tools/compare_dbr_template_profiles.py <current-template> <proven-template>
  ```

4. **Basic preprocessing variants**

  ```bash
  python template-optimizer/tools/probe_dbr_templates.py <image> --variant-set basic --report-json tuning-report.json
  ```

Interpret the evidence conservatively:

- **Raw image succeeds with a candidate template** → keep tuning in the template only.
- **Only a preprocessed variant succeeds** → recommend preprocessing plus template tuning; do not claim template-only success.
- **No raw or basic variant succeeds** → template-only tuning is likely exhausted for the current pixels.
- **A proven template mainly differs in deformation handling or separate decode image parameters** → prioritize those before adding more `DeblurModes`.

For hard QR-like scenes with tiny tilted codes, low contrast, and multiple candidate code blocks, switch from template tuning to ROI-and-preprocessing recovery before giving up entirely:

```bash
python template-optimizer/tools/recover_difficult_qr.py <image> --verify-dbr
```

Use that tool when the image still visibly contains QR markers but `validate_dbr_template.py` plus `probe_dbr_templates.py --variant-set basic` remain `NO_RESULT`.

### Symptom To First Parameter Family

| Symptom | First Parameter Family | Notes |
|---------|------------------------|-------|
| Quiet zone missing or crop too tight | `MinQuietZoneWidth`, padding variants | Test padded variants before broad decode changes |
| Warped, folded, or wrinkled symbol | `DeformationResistingModes` | Compare against any proven template using `DRM_BROAD_WARP` / `DRM_DEWRINKLE` |
| Low contrast but still sharp | Grayscale enhancement, binarization | Prefer decode image parameters over localization churn |
| Blur without obvious geometric damage | `DeblurModes`, `BarcodeScaleModes` | Keep localization stable if the symbol is already likely found |
| Nearby dense text or texture | `IfEraseTextZone`, texture removal | Verify text-zone removal is not erasing damaged structure |
| Inverted or ambiguous foreground/background | `GrayscaleTransformationModes` | Include both `GTM_ORIGINAL` and `GTM_INVERTED` |

### Decision Rules Before Editing

- **Few symbols, known format** → set `ExpectedBarcodesCount` to the known count, restrict `BarcodeFormatIds`, and prefer a focused template.
- **Barcode likely exists but is not found** → change `LocalizationModes` before decode modes.
- **Barcode is found on some variants but decode is unstable** → leave localization unchanged, inspect deformation handling and decode image parameters before adding more `DeblurModes`.
- **Suspected quiet-zone or crop issue** → lower `MinQuietZoneWidth`, test padded variants, and use `MirrorMode = MM_BOTH` only when orientation is uncertain.
- **No raw image or basic variant decodes** → stop calling it a template problem without qualification; recommend preprocessing, crop refinement, re-capture, or ground-truth verification.

### Minimal Change Contract

When proposing a template edit, always provide these four items together:

1. The observed symptom from the image or probe report
2. The single parameter family being changed
3. The exact JSON snippet to change
4. The next validation command

Reject proposals that change localization, decoding, and acceptance rules all at once unless there is strong evidence they are coupled.

### Minimal Template Strategy

- Keep one `CaptureVisionTemplate`
- Keep one `TargetROIDefOptions` entry
- Keep one focused `BarcodeReaderTaskSettingOptions` entry
- Add `ImageParameterOptions` only when preprocessing behavior is part of the hypothesis
- Copy only proven sections from exported templates

---

## Optimization Playbook

### Proven Optimization Order (most impact first)

**Step 0 — Ask the customer first.** If the customer knows the barcode format (e.g. CODE_128) and text pattern (e.g. serial number format), start with a focused template:
- Set `BarcodeFormatIds` to the single known format
- Set `BarcodeTextRegExPattern` in `BarcodeFormatSpecificationOptions` to match the expected text
- Set `MinResultConfidence: 0` (the regex acts as quality control)
- Use minimal mode arrays (2-3 modes each) tuned for the image type
- This "focused-first" approach is 10-20x faster and often more accurate than the kitchen-sink below

**If the barcode format/pattern is unknown**, use the kitchen-sink approach below:

Based on empirical testing with 202 noisy DataMatrix images:

1. **GrayscaleTransformationModes** — Add `GTM_INVERTED` (handles inverted barcodes, nearly free)
2. **GrayscaleEnhancementModes** — Add `GEM_GRAY_EQUALIZE`, `GEM_SHARPEN_SMOOTH`, `GEM_GRAY_SMOOTH`
3. **DeblurModes** — Explicitly set all modes (controls order and includes modes not in format-specific defaults)
4. **DeformationResistingModes** — Enable `DRM_GENERAL`
5. **BarcodeComplementModes** — Enable `BCM_GENERAL`
6. **BarcodeScaleModes** — Add `BSM_LINEAR_INTERPOLATION` for small barcodes
7. **LocalizationModes** — Add `LM_STATISTICS_MARKS`, `LM_CENTRE`, `LM_NEURAL_NETWORK`
8. **MinResultConfidence** — Lower from 30 to 10 (accept borderline decodes)
9. **Timeout** — Increase to 30000ms
10. Fine-tune sub-parameters (BlockSizeX/Y, ModuleSizeThreshold, etc.)

### Results From Real-World Testing

**Test run 1 — Noisy DataMatrix images (202 images):**

| Iteration | Changes | Rate | Delta |
|-----------|---------|------|-------|
| Baseline | Default template | 43.07% | — |
| 1 | GTM_INVERTED, GEM_GRAY_EQUALIZE, GEM_SHARPEN_SMOOTH, DRM_GENERAL, BCM_GENERAL, Timeout 30s | 50.50% | +7.43% |
| 2 | + LM_STATISTICS_MARKS, LM_CENTRE, BSM_LINEAR_INTERPOLATION, MinResultConfidence 10 | 52.48% | +1.98% |
| 3 | + Explicit DeblurModes (9 modes), GEM_GRAY_SMOOTH | 56.44% | +3.96% |

Total improvement: **43.07% → 56.44% (+13.37 percentage points, +27 images)**

**Test run 2 — GS1-128 pharmacy/logistics labels, 10 camera images (2026-03-30):**

Images: Chinese pharmaceutical product labels photographed by mobile phone; each label has 3 barcodes:
1. Large GS1-128 `(00)` shipping container serial (wide, easier to read)
2. Shorter GS1-128 `(11)(10)` production date + lot number (narrower, near dense text)
3. Small 2D code (DataMatrix/QR) at bottom-left corner (not decoded in any run)

| Iteration | Changes | Images Decoded | Total Barcodes | Delta |
|-----------|---------|----------------|----------------|-------|
| Baseline | Default template | 8/10 (80%) | 10 | — |
| 1 | All LocalizationModes + GTM_INVERTED + all GEM modes + all DeblurModes + DRM_GENERAL + BCM_GENERAL + Timeout 30s + MinResultConfidence 10 + TextDetection Sensitivity 1 | 10/10 (100%) | 15 | +20% images, +5 barcodes |
| 2 | + IfEraseTextZone=0 + BSM_LINEAR_INTERPOLATION(4→8) | 10/10 (100%) | 17 | +2 barcodes, +3 confidence |
| 3 | + BM_THRESHOLD, LM_STATISTICS_MARKS, DM_THRESHOLD_BINARIZATION×2 | 10/10 (same) | 17 | no change |
| 4 | + BSM_LINEAR_INTERPOLATION(2→4), GEM_GRAY_EQUALIZE Sensitivity 9, DM_NEURAL_NETWORK Code128Decoder | 10/10 (same) | 17 | slightly worse confidence |
| 5 | **ExpectedBarcodesCount=2** (minimal change on top of iter_4) | 10/10 (100%) | **20** | **+3 barcodes**, avg_conf 33.1, avg_time 320ms |

**Key findings for this label type:**
- **IfEraseTextZone=1 was the main culprit for 90°-rotated image failures.** The aggressive text zone removal erased barcode regions in rotated images. Setting `IfEraseTextZone=0` and reducing `TextDetectionMode.Sensitivity` from 3 to 1 was critical.
- **Adding full LocalizationModes array** (LM_CONNECTED_BLOCKS, LM_SCAN_DIRECTLY, LM_STATISTICS, LM_LINES, LM_NEURAL_NETWORK, LM_CENTRE) fixed images rotated 90°.
- **BSM_LINEAR_INTERPOLATION** with `ModuleSizeThreshold=4, TargetModuleSize=8` helped decode the shorter `(11)(10)` barcode in additional images.
- **ExpectedBarcodesCount=2 was the key fix for the final 3 hard cases.** Setting this to match the known label layout (always 2 barcodes) pushed the engine to keep searching until both are found. This single change on top of iter_4 raised total barcodes from 17→20 with minimal speed cost (~320ms/image). The 3 previously-missed barcodes decoded at confidence 15, 23, 24 — above the MinResultConfidence=10 threshold, so the issue was localization effort, not confidence filtering.
- **MinResultConfidence=5 alone**: No improvement. The missed barcodes were not being found at all (localization failure), not rejected for low confidence.
- **Explicit BinarizationModes (multiple block sizes)**: No improvement on this image type.
- **DRM_BROAD_WARP, DRM_LOCAL_REFERENCE, DRM_DEWRINKLE, DRM_GENERAL Level 9**: No improvement beyond ExpectedBarcodesCount=2 and significantly slower (1234ms vs 320ms).
- **DM_THRESHOLD_BINARIZATION twice, LM_STATISTICS_MARKS, BM_THRESHOLD**: No improvement on this image type.
- **Higher GEM_GRAY_EQUALIZE Sensitivity (9 vs 5)**: No improvement on these images.

**Test run 3 — Warehouse inventory photos, 12 images of stacked phone boxes (2026-04-16):**

Images: Mobile phone boxes (Samsung, iPhone, Oppo, Honor) stacked on warehouse shelves, photographed by mobile phone. Each image contains 15-30+ boxes with Code 128 barcodes on white labels. Low resolution (721×1280), high JPEG compression. Mix of dark boxes (Samsung, Honor) and white boxes (iPhone). Primary format: CODE_128, with some DATAMATRIX and EAN_13.

**Critical finding: SDK version matters enormously.** The Python SDK `dynamsoft-capture-vision-bundle` v3.0.6000 could not decode 4 of 12 images at all, and `LM_NEURAL_NETWORK` / `DM_NEURAL_NETWORK` modes caused the SDK to silently return 0 results. Upgrading to v3.4.2000 solved all failures with the default template alone.

| Iteration | SDK | Changes | Images | Barcodes | Delta |
|-----------|-----|---------|--------|----------|-------|
| Baseline (v3.0) | 3.0.6000 | Default template | 8/12 (67%) | 58 | — |
| Iter 1 | 3.0.6000 | ReadRateFirst pipeline, ExpectedBarcodes=50, IfEraseTextZone=0, Timeout 60s | 8/12 | 72 | +14 barcodes |
| Iter 2 | 3.0.6000 | + All GEM, DRM, explicit DeblurModes (9), LM_STATS_MARKS, BSM, MinConf=10 | 8/12 | 94 | +22 barcodes |
| Iter 4 | 3.0.6000 | + Multiple BinarizationModes, aggressive BSM (2→8) | 9/12 | 103 | +1 image, +9 barcodes |
| **Baseline (v3.4)** | **3.4.2000** | **Default template (no customization)** | **12/12 (100%)** | **118** | **+4 images, +15 barcodes** |
| Iter 6 | 3.4.2000 | Full optimization (all modes incl. NN) | 12/12 | 174 | +56 barcodes |
| **Iter 7 (best)** | **3.4.2000** | **+ Timeout 120s, aggressive BSM, multiple BM** | **12/12** | **198** | **+24 barcodes** |
| Iter 8 | 3.4.2000 | Format restriction (CODE_128+DM+EAN13+QR+EAN8) | 12/12 | 187 | -11 (reverted) |

Total improvement: **8/12 (67%) → 12/12 (100%), 58 → 198 barcodes (+241%)**

**Key findings for this image type:**
- **SDK upgrade was the single most impactful change.** v3.0→v3.4 alone went from 8/12 to 12/12 and 58→118 barcodes with the default template.
- **LM_NEURAL_NETWORK and DM_NEURAL_NETWORK break SDK v3.0.6000** — the SDK silently returns 0 results for all images (0ms processing time). These modes work correctly in v3.4.2000.
- **BCM_GENERAL (BarcodeComplementModes) was harmful** for this image type on v3.0 — reduced from 8/12 to 7/12 images and 58 to 21 barcodes.
- **Format restriction (BarcodeFormatIds) was slightly harmful** — reduced from 198 to 187 barcodes, likely because some borderline detections were format-ambiguous.
- **ReadRateFirst pipeline + ExpectedBarcodesCount=50** was effective on v3.0, finding +14 more barcodes on already-decoded images.
- **Multiple BinarizationModes (different BlockSizeX/Y + BM_THRESHOLD)** helped decode 1 more image on v3.0 and +24 more barcodes on v3.4.
- **Aggressive BSM upscaling (ModuleSizeThreshold=2, TargetModuleSize=8)** helped with the small barcodes at 721×1280 resolution.

**Test run 3b — Engineer's optimized template for same warehouse images (2026-04-17/21):**

Same 12 warehouse images as Test run 3. A Dynamsoft engineer created a purpose-built template (U22212-0417.json) targeting only the customer's specific barcodes. Comparison against our iter_8 best (v3.4.2000):

| Template | Target Barcodes (unique) | Target Hits | Avg Confidence | Avg Time/Image |
|----------|:---:|:---:|:---:|:---:|
| iter_8 (kitchen-sink) | 30 | 126 | 65.47 | 46,415ms |
| **Engineer U22212-0417** | **31** | **137** | **71.18** | **2,288ms** |

**The engineer's focused template won on every metric**, finding +1 unique barcode, +11 hits, +5.71 confidence, and running 20x faster. The extra unique barcode (`307018810N`) was one that iter_8 garbled as `30{01N81-N`.

**Critical techniques from the engineer's template:**

1. **`BarcodeTextRegExPattern`** — The single most impactful technique for known-format use cases. Setting `"BarcodeTextRegExPattern": "^3[0-9]{8}N$"` in `BarcodeFormatSpecificationOptions`:
   - Eliminates false decodes at engine level (the garbled `30{01N81-N` becomes a retry instead of a final result)
   - Effectively raises quality without sacrificing decode rate
   - Allows `MinResultConfidence: 0` since the regex itself acts as quality control
   - **Use whenever the customer knows the barcode text format** (serial numbers, part codes, etc.)

2. **Focused `BarcodeFormatIds`** — Restricting to `BF_CODE_128` only (vs 5 formats in iter_8) yielded a 20x speed improvement. The iter_8 finding that format restriction was "slightly harmful" (198→187) was because it still searched broadly. When combined with regex filtering, single-format is strictly better.

3. **Minimal mode arrays beat kitchen-sink** — The engineer used only:
   - 2 LocalizationModes (LM_CONNECTED_BLOCKS + LM_LINES) vs 7
   - 3 DeblurModes (DM_THRESHOLD_BINARIZATION + DM_DIRECT_BINARIZATION + DM_NEURAL_NETWORK) vs 11
   - 3 GrayscaleEnhancementModes (GEM_GENERAL + GEM_GRAY_SMOOTH + GEM_SHARPEN_SMOOTH) vs 4
   - This proves that for a known image type, fewer well-chosen modes outperform exhaustive mode lists.

4. **BinarizationModes with specific BlockSize** — `BM_LOCAL_BLOCK` with `BlockSizeX: 9, BlockSizeY: 9, ThresholdCompensation: 10, EnableFillBinaryVacancy: 0`. This is a tuned binarization (vs default 0/auto), useful for consistent label sizes.

5. **`GlobalParameter.IntraOpNumThreads: 4`** — Explicit thread count for intra-operation parallelism.

6. **`IfEraseTextZone: 1`** — The engineer enabled text zone erasure (we found this harmful in Test run 2's rotated images, but it's fine for consistently-oriented warehouse labels where text near barcodes causes false localizations).

7. **Template schema Version 5.1** — The engineer used the v5.1 template schema which specifies all image processing stages explicitly in `ImageParameterOptions.ApplicableStages`, including SST_INPUT_COLOR_IMAGE, SST_SCALE_IMAGE, SST_CONVERT_TO_GRAYSCALE, SST_TRANSFORM_GRAYSCALE, SST_ENHANCE_GRAYSCALE, SST_BINARIZE_IMAGE, SST_DETECT_TEXTURE, SST_REMOVE_TEXTURE_FROM_GRAYSCALE, SST_BINARIZE_TEXTURE_REMOVED_GRAYSCALE, SST_FIND_CONTOURS, SST_DETECT_SHORTLINES, SST_ASSEMBLE_LINES, SST_DETECT_TEXT_ZONES, SST_REMOVE_TEXT_ZONES_FROM_BINARY. This gives complete control over the entire image processing pipeline.

**Updated optimization strategy: When the customer knows what barcode format and text pattern they need, start with a focused template (single format + regex) rather than a kitchen-sink approach. Reserve the kitchen-sink approach for exploratory/unknown cases.**

### Common Failure Patterns

| Visual Pattern | Root Cause | Fix |
|----------------|-----------|-----|
| Extreme color noise/grain | Low-quality camera sensor, poor lighting | GEM_GRAY_SMOOTH, GEM_GRAY_EQUALIZE, DeblurModes |
| Very small barcode (<30px) | Distance from camera too far | BSM_LINEAR_INTERPOLATION (ModuleSizeThreshold=2-4) |
| Barcode barely visible | Very low contrast | GEM_GRAY_EQUALIZE, BinarizationModes tuning |
| Light bars on dark bg | Inverted polarity | GTM_INVERTED |
| Barcode on curved surface | Geometric distortion | DRM_GENERAL, DRM_BROAD_WARP, DRM_DEWRINKLE |
| Barcode partially cut off | Incomplete data | BCM_GENERAL |
| Dense texture behind barcode | False positive localization | TDM_GENERAL_WIDTH_CONCENTRATION |
| Barcode region near dense text (label with many characters) | TextZoneRemoval erasing barcode area | Set IfEraseTextZone=0, lower TextDetectionMode Sensitivity to 1 |
| Image rotated 90° (phone held sideways) | Default LocalizationModes + text zone removal fail on rotated content | Add full LocalizationModes array, set IfEraseTextZone=0 |
| Etched/stamped on metal | DPM marking | DPMCRM_GENERAL, LM_STATISTICS_MARKS |
| Blurry 1D barcodes | Motion blur, out of focus | DM_THRESHOLD_BINARIZATION (twice in array for 2nd round), DM_NEURAL_NETWORK |

### What Cannot Be Fixed By Template Tuning

Some images are fundamentally undecodable through template changes alone:
- **Severe physical damage** (>40% of barcode modules destroyed)
- **Extreme motion blur** where modules merge completely
- **Resolution too low** (less than ~2px per module after upscaling)
- **Complete occlusion** of critical barcode regions (finder patterns, timing patterns)

For these cases, recommend image pre-processing (super-resolution, denoising) before DBR.

---

## Version Compatibility Notes

| SDK Version | Template Format | Key Differences |
|------------|----------------|-----------------|
| DCV v3.4.x (current) | SectionArray/StageArray architecture | Full stage-based pipeline control |
| DCV v3.0-3.3 | SectionArray/StageArray | Minor parameter additions per version |
| DBR v9.x (legacy) | Flat parameter structure | No SectionArray, parameters at top level of task settings |
| DBR v8.x (legacy) | Flat parameter structure | Different mode names, fewer options |

Version-specific parameter details are stored in the `templates/` directory.

---

## Contributing

This knowledge base should grow over time. To contribute:

1. **After optimization runs**: Document new parameter combinations that worked (or didn't)
2. **From Dynamsoft documentation**: Verify parameter descriptions and add missing details
3. **From Dynamsoft engineers**: Correct any inaccuracies, add internal best practices
4. **Version updates**: When new SDK versions ship, add parameter diffs to `templates/`

### Verification Status

Items verified against official docs (2026-02-18):
- [x] GrayscaleTransformationModes — modes, sub-params, defaults
- [x] GrayscaleEnhancementModes — modes, sub-params, applicability
- [x] DeblurModes — modes, sub-params, null behavior (format-specific defaults)
- [x] LocalizationModes — modes, sub-params, ConfidenceThreshold applicability
- [x] BarcodeScaleModes — modes (BSM_NEAREST_NEIGHBOUR_INTERPOLATION removed), scale-down support
- [x] BinarizationModes — modes, sub-params, GrayscaleEnhancementModesIndex interaction
- [x] DeformationResistingModes — modes (added DRM_BROAD_WARP, DRM_LOCAL_REFERENCE, DRM_DEWRINKLE, DRM_AUTO)
- [x] BarcodeComplementModes — modes (BCM_AUTO noted as not supported yet)
- [x] Template JSON architecture — section/stage hierarchy, cross-references

### Remaining Items for Dynamsoft Verification

- [ ] Exact runtime behavior when DeblurModes is null vs explicitly set to the same modes
- [ ] Whether DM_NEURAL_NETWORK + DM_DEEP_ANALYSIS together is redundant or complementary
- [ ] Optimal DeblurModes ordering for different image types
- [ ] Impact of `RegionPredetectionModes` sensitivity on decode rate
- [ ] Whether `ImageScaleSetting.EdgeLengthThreshold` should be tuned for small images
- [ ] Best practices for `ColourConversionModes` channel weights with colored barcodes
- [ ] Recommended `BinarizationModes.BlockSizeX/Y` values for different module sizes
- [ ] ST_BARCODE_DECODING stage ordering discrepancy (docs vs SDK dump)

---

## Report Generation — Embedding Images

When the report HTML will be opened via `file://` (the common case), images **must** be embedded as base64 data URIs. Chromium blocks all `file://` resource loading from JavaScript-inserted DOM nodes, producing "Unsafe attempt to load URL" errors.

Use this pattern when generating the report:

```python
import json, base64, os, mimetypes

def embed_images(results, image_dir):
    for img in results['per_image']:
        fname = img.get('converted_file') or img['file']
        path = os.path.join(image_dir, fname)
        if os.path.exists(path):
            mime = mimetypes.guess_type(path)[0] or 'image/jpeg'
            with open(path, 'rb') as f:
                img['data_uri'] = f'data:{mime};base64,{base64.b64encode(f.read()).decode()}'

results = json.load(open('results.json'))
baseline = json.load(open('baseline_results.json'))
embed_images(results, 'barcodemiss')
embed_images(baseline, 'barcodemiss')

tpl = open('SKILL_DIR/resources/report/report_template.html').read()
html = (tpl
    .replace('__RESULTS_JSON__', json.dumps(results))
    .replace('__BASELINE_JSON__', json.dumps(baseline))
    .replace('__IMAGE_DIR__', '"barcodemiss"'))
open('optimization_report.html', 'w').write(html)
```

The template checks `img.data_uri` first; if absent it falls back to `IMAGE_DIR/filename` (works fine when served via HTTP). Embedded reports are self-contained (~700 KB per image) but eliminate all security restrictions.

---

## Python Harness Notes

The Python harness (`resources/harness_py/main.py`) is the canonical validator for this skill. It produces the JSON output schema used by `SKILL.md` workflows and `report_template.html`.

### Practical Constraints

- **PDF support** — PDF files are skipped with a warning because the Python SDK does not expose a PDF decoder.
- **`avg_time_ms`** — includes Python call overhead, so use it for relative comparisons within the same Python session rather than absolute benchmarking.
- **`--dump-default-template`** — uses `output_settings_to_file` / `output_settings_to_string`; the content is equivalent to the SDK preset dump even if field ordering differs.
- **Performance** — expect moderate interpreter overhead; optimize for decode quality first, not raw timing.

### SDK Version Compatibility

The Python harness targets `dynamsoft-capture-vision-bundle` (the all-in-one pip package). Two functions in `main.py` contain all SDK-specific calls — if the API changes between versions, only those need updating:

- **`extract_barcodes(captured_result)`** — extracts barcode items from a `CapturedResult`
- **`dump_default_template(router, output_path)`** — tries `output_settings_to_file` then `output_settings_to_string`

### Optimization Results Comparability

Decode rates measured with the Python harness should be stable for the same template and images because the harness calls the same SDK logic on each run. Treat `avg_time_ms` as environment-sensitive and compare timing only within the same Python-based validation setup.
