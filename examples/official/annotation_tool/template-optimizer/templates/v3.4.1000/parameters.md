# DCV v3.4.1000 Parameter Reference

> Dynamsoft Capture Vision C++ SDK v3.4.1000 (version string: "3.4.10.6925")
> Released: February 5, 2026

## Template Format Version

```json
{ "Version": "5.1" }
```

## Default Template Dump

Use `--dump-default-template` to get the full default template for this version.
The default `PT_READ_BARCODES` preset includes:

### Default Values (v3.4.1000)

| Parameter | Default Value |
|-----------|--------------|
| GrayscaleTransformationModes | `[GTM_ORIGINAL]` |
| GrayscaleEnhancementModes | `[GEM_GENERAL]` |
| DeblurModes | `null` (uses format-specific internal defaults — see KNOWLEDGE.md) |
| BinarizationModes | `[BM_LOCAL_BLOCK]` |
| LocalizationModes | `[LM_CONNECTED_BLOCKS, LM_SCAN_DIRECTLY, LM_STATISTICS, LM_LINES]` |
| BarcodeScaleModes | `[BSM_AUTO]` |
| DeformationResistingModes | `[DRM_SKIP]` |
| BarcodeComplementModes | `[BCM_SKIP]` |
| DPMCodeReadingModes | `[DPMCRM_SKIP]` |
| TextureDetectionModes | `[TDM_GENERAL_WIDTH_CONCENTRATION]` |
| MirrorMode (bfs1 - 2D) | `MM_BOTH` |
| MirrorMode (bfs2 - all) | `MM_NORMAL` |
| MinResultConfidence | `30` |
| Timeout | `10000` |
| ExpectedBarcodesCount | `0` |
| MaxParallelTasks | `4` |
| MinQuietZoneWidth | `4` |
| ReturnPartialBarcodeValue | `1` |

### BarcodeFormatSpecificationOptions Defaults

The default template uses two format specs:

**bfs1** — 2D formats:
```json
{
  "Name": "bfs1",
  "BarcodeFormatIds": ["BF_PDF417", "BF_QR_CODE", "BF_DATAMATRIX", "BF_AZTEC",
                        "BF_MICRO_QR", "BF_MICRO_PDF417", "BF_DOTCODE"],
  "MirrorMode": "MM_BOTH",
  "MinResultConfidence": 30,
  "PartitionModes": ["PM_WHOLE_BARCODE", "PM_ALIGNMENT_PARTITION"]
}
```

**bfs2** — All formats (fallback):
```json
{
  "Name": "bfs2",
  "BarcodeFormatIds": ["BF_ALL"],
  "MirrorMode": "MM_NORMAL",
  "MinResultConfidence": 30
}
```

### ImageParameterOptions Stage Pipeline

The image processing pipeline in v3.4.1000 follows this stage order:

1. `SST_INPUT_COLOR_IMAGE`
2. `SST_SCALE_IMAGE` — ImageScaleSetting (EdgeLengthThreshold: 2300, ScaleType: ST_SCALE_DOWN)
3. `SST_CONVERT_TO_GRAYSCALE` — ColourConversionModes
4. `SST_TRANSFORM_GRAYSCALE` — GrayscaleTransformationModes
5. `SST_ENHANCE_GRAYSCALE` — GrayscaleEnhancementModes
6. `SST_BINARIZE_IMAGE` — BinarizationModes
7. `SST_DETECT_TEXTURE` — TextureDetectionModes
8. `SST_REMOVE_TEXTURE_FROM_GRAYSCALE`
9. `SST_BINARIZE_TEXTURE_REMOVED_GRAYSCALE`
10. `SST_FIND_CONTOURS`
11. `SST_DETECT_SHORTLINES` — ShortlineDetectionMode
12. `SST_ASSEMBLE_LINES` — LineAssemblyMode
13. `SST_DETECT_TEXT_ZONES` — TextDetectionMode
14. `SST_REMOVE_TEXT_ZONES_FROM_BINARY`

### BarcodeReaderTaskSettingOptions Stage Pipeline

1. `ST_REGION_PREDETECTION` / `SST_PREDETECT_REGIONS` — RegionPredetectionModes
2. `ST_BARCODE_LOCALIZATION` / `SST_LOCALIZE_CANDIDATE_BARCODES` — LocalizationModes
3. `ST_BARCODE_LOCALIZATION` / `SST_LOCALIZE_BARCODES`
4. `ST_BARCODE_DECODING` / `SST_RESIST_DEFORMATION` — DeformationResistingModes
5. `ST_BARCODE_DECODING` / `SST_COMPLEMENT_BARCODE` — BarcodeComplementModes
6. `ST_BARCODE_DECODING` / `SST_SCALE_BARCODE_IMAGE` — BarcodeScaleModes
7. `ST_BARCODE_DECODING` / `SST_DECODE_BARCODES` — DeblurModes

## All Available Mode Values

### DeblurModes

`DM_BASED_ON_LOC_BIN`, `DM_THRESHOLD_BINARIZATION`, `DM_DIRECT_BINARIZATION`,
`DM_GRAY_EQUALIZATION`, `DM_SMOOTHING`, `DM_SHARPENING`, `DM_SHARPENING_SMOOTHING`,
`DM_MORPHING`, `DM_DEEP_ANALYSIS`, `DM_NEURAL_NETWORK`, `DM_SKIP`

When `null`: SDK uses format-specific defaults (7-8 modes per format, includes DM_DEEP_ANALYSIS).

### LocalizationModes

`LM_CONNECTED_BLOCKS`, `LM_SCAN_DIRECTLY`, `LM_STATISTICS`, `LM_LINES`,
`LM_STATISTICS_MARKS`, `LM_STATISTICS_POSTAL_CODE`, `LM_CENTRE`,
`LM_NEURAL_NETWORK`, `LM_ONED_FAST_SCAN`, `LM_SKIP`

### GrayscaleTransformationModes

`GTM_ORIGINAL`, `GTM_INVERTED`, `GTM_AUTO`

### GrayscaleEnhancementModes

`GEM_GENERAL`, `GEM_GRAY_EQUALIZE`, `GEM_GRAY_SMOOTH`, `GEM_SHARPEN_SMOOTH`, `GEM_SKIP`

### BarcodeScaleModes

`BSM_AUTO`, `BSM_LINEAR_INTERPOLATION`

### DeformationResistingModes

`DRM_SKIP`, `DRM_GENERAL`, `DRM_BROAD_WARP`, `DRM_LOCAL_REFERENCE`, `DRM_DEWRINKLE`, `DRM_AUTO`

### BinarizationModes

`BM_LOCAL_BLOCK`, `BM_THRESHOLD`, `BM_AUTO`, `BM_SKIP`

### BarcodeComplementModes

`BCM_SKIP`, `BCM_GENERAL`, `BCM_AUTO` (not supported yet)

### BarcodeFormatIds
```
BF_ALL, BF_DEFAULT, BF_ONED, BF_GS1_DATABAR,
BF_CODE_39, BF_CODE_128, BF_CODE_93, BF_CODABAR, BF_ITF,
BF_EAN_13, BF_EAN_8, BF_UPC_A, BF_UPC_E,
BF_INDUSTRIAL_25, BF_CODE_39_EXTENDED,
BF_GS1_DATABAR_OMNIDIRECTIONAL, BF_GS1_DATABAR_TRUNCATED,
BF_GS1_DATABAR_STACKED, BF_GS1_DATABAR_STACKED_OMNIDIRECTIONAL,
BF_GS1_DATABAR_EXPANDED, BF_GS1_DATABAR_EXPANDED_STACKED,
BF_GS1_DATABAR_LIMITED,
BF_PATCHCODE, BF_PDF417, BF_QR_CODE, BF_DATAMATRIX, BF_AZTEC,
BF_MAXICODE, BF_MICRO_QR, BF_MICRO_PDF417, BF_GS1_COMPOSITE,
BF_MSI_CODE, BF_CODE_11,
BF_PHARMACODE, BF_PHARMACODE_ONE_TRACK, BF_PHARMACODE_TWO_TRACK,
BF_DOTCODE,
BF_POSTALCODE, BF_AUSTRALIANPOST, BF_RM4SCC, BF_KIX, BF_POSTNET,
BF_PLANET, BF_USPS_INTELLIGENT_MAIL
```
