# PDF417 — Dynamsoft re-run

Article: [PDF417 Barcode Scanner SDK Benchmark](https://www.dynamsoft.com/codepool/pdf417-reading-benchmark-and-comparison.html)

```bash
cd ../../   # examples/official/benchmark-legacy
python common/download_dataset.py --project PDF417 --output datasets/PDF417
python common/benchmark_dynamsoft.py \
  --dataset datasets/PDF417 --project PDF417 \
  --output datasets/PDF417/current_run
```

Dataset: 78 images, 88 PDF417 ground-truth codes, ~116 MB. Decoding is
restricted to `BF_PDF417` on the `ReadBarcodes_Default` preset. Sources and
full instructions are in the [parent README](../README.md).

The article's headline metric is `detected codes / total codes` (the original
harness counted every returned result, not text-exact matches). `summary.json`
reports that as `readingRate`, alongside `accuracy` (overlap + text-correct),
`precision` and `averageTime`.

## Runtime settings

`--tuning accuracy` (the default) keeps the 2688 px originals at full
resolution (`scale_down_threshold` 99999 instead of the SDK's 2300) and enables
the full `localization_modes` list. Measured on all 78 images:

| Settings | Reading rate | Text-correct | Avg time |
|---|---:|---:|---:|
| SDK defaults | 93.18% | 67.05% | 176.05 ms |
| no downscaling | 95.45% | 69.32% | 183.42 ms |
| full localization | 96.59% | 71.59% | 218.71 ms |
| **both (used)** | **98.86%** | **72.73%** | **194.52 ms** |

`GEM_GRAY_SMOOTH` (documented in the article) lowers the rate to 96.59% on this
SDK version, so it is not applied here. `ReadBarcodes_ReadRateFirst` reaches
98.86% too but at ~915 ms/image.

## Current run — Dynamsoft Capture Vision 3.6.5000 (Python, 2026-11-04)

| Metric | Value |
|---|---:|
| Reading rate (detected / 88) | 98.86% |
| Precision | 73.56% |
| Average decode time | 194.52 ms/image |
| Images with a result | 93.59% |

Other SDK columns in the article (ML Kit 61.36% / 304.22 ms, ZXingCPP
52.27% / 127.56 ms, Apple Vision 30.68% / 693.96 ms) are the original 2021
measurements and are unchanged.
