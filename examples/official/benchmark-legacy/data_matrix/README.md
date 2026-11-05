# Data Matrix — Dynamsoft re-run

Article: [Data Matrix SDK Benchmark 2026](https://www.dynamsoft.com/codepool/data-matrix-reading-benchmark-and-comparison.html)

```bash
cd ../../   # examples/official/benchmark-legacy
python common/download_dataset.py --project DataMatrix --output datasets/DataMatrix
python common/benchmark_dynamsoft.py \
  --dataset datasets/DataMatrix --project DataMatrix \
  --output datasets/DataMatrix/current_run
```

Dataset: 57 images, 112 Data Matrix ground-truth codes, ~3.9 MB. Ground truth
has both text and quadrilaterals, so `scoring.py` checks location overlap and
text. Sources and full instructions are in the [parent README](../README.md).

## The 100% configuration

The 57 images contain up to five codes each. The SDK's default
`expected_barcodes_count` of 0 finds roughly one code per image, which is the
main reason the out-of-the-box rate is only 84.82%. `--tuning accuracy`
(default) applies the settings that decode all 112 codes:

```python
settings.barcode_settings.barcode_format_ids = EnumBarcodeFormat.BF_DATAMATRIX
settings.barcode_settings.expected_barcodes_count = 10
settings.barcode_settings.localization_modes = [
    LM_CONNECTED_BLOCKS, LM_LINES, LM_STATISTICS, LM_SCAN_DIRECTLY,
    LM_NEURAL_NETWORK, LM_STATISTICS_MARKS, LM_CENTRE, -1,
]
settings.barcode_settings.scale_down_threshold = 99999
```

Search results on all 57 images / 112 codes, all measured on
`dynamsoft-capture-vision-bundle` **3.6.5000**:

| Configuration | Correct / 112 | Reading rate | Avg time |
|---|---:|---:|---:|
| SDK defaults | 95 | 84.82% | 11.36 ms |
| `expected_barcodes_count=10` | 107 | 95.54% | 24.45 ms |
| `=10` + full `localization_modes` (**used**) | **112** | **100.00%** | **54.13 ms** |
| `=20` + full localization + no downscaling | 112 | 100.00% | 54.68 ms |

Precision is 100.00% in every configuration. `--tuning default` reproduces the
out-of-the-box figure; `--tuning accuracy` reproduces the article's 100%.

## Version note

The article's earlier 83.04% / 100% figures were measured on 3.6.1000 with a
JSON template using `DPMCodeReadingModes`, `DeformationResistingModes` and
adaptive `BinarizationModes`. On 3.6.5000, `DeformationResistingModes` is
rejected by the template loader (`-10077 Skipped unsupported keys`) and
`BinarizationModes` at the `ImageParameterOptions` level is rejected too. The
article's code snippet now uses `SimplifiedCaptureVisionSettings`, which reaches
the same 100% on the current SDK. The archived `-Dynamsoft.json` results in
`results.zip` score 112/112 with `common/scoring.py`, so the scoring rules are
unchanged.

The libdmtx (72.32%) and zxing-cpp (65.18%) columns in the article are the
original measurements and are unchanged.
