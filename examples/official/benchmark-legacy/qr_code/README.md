# QR Code — Dynamsoft re-run

Article: [QR Code Reading Benchmark](https://www.dynamsoft.com/codepool/qr-code-reading-benchmark-and-comparison.html)

```bash
cd ../../   # examples/official/benchmark-legacy
python common/download_dataset.py --project QRCode --output datasets/QRCode
python common/benchmark_dynamsoft.py \
  --dataset datasets/QRCode --project QRCode \
  --output datasets/QRCode/current_run
```

Dataset: 536 images in 16 categories, 1,232 QR ground-truth quadrilaterals,
~205 MB. Decoding is restricted to `BF_QR_CODE`. Ground truth has no text, so
the metric is a detection rate. Sources and full instructions are in the
[parent README](../README.md).

The article's "total average" is the **unweighted mean of the 16 category
reading rates**, not the global `detected / 1,232` figure; `summary.json`
reports both as `totalAverageReadingRate` and `readingRate`.

## Runtime settings

`--tuning accuracy` (the default) keeps 4032 px originals at full resolution
(`scale_down_threshold` 99999), enables the full `localization_modes` list, and
adds `GEM_GRAY_SMOOTH`. Measured on all 536 images:

| Settings | 16-class average | Global | Avg time |
|---|---:|---:|---:|
| SDK defaults | 80.61% | 73.46% | 73.29 ms |
| no downscaling | 83.57% | 86.77% | 116.18 ms |
| full localization | 81.34% | 74.11% | 84.93 ms |
| no downscaling + full localization | 84.05% | 87.01% | 121.45 ms |
| **+ GEM_GRAY_SMOOTH (used)** | **84.75%** | **87.34%** | **116.20 ms** |

The biggest gains are on `lots` (62.86% → 100.00%) and `perspective`
(62.86% → 68.57%).

## Current run — Dynamsoft Capture Vision 3.6.5000 (Python, 2026-11-04)

| Metric | Value |
|---|---:|
| Total average (16 categories) | 84.75% |
| Global detection rate (detected / 1,232) | 87.34% |
| Precision | 100.00% |
| Average decode time | 116.20 ms/image |

| Category | New Dynamsoft rate |
|---|---:|
| blurred | 67.69% |
| brightness | 81.18% |
| bright_spots | 41.24% |
| close | 95.00% |
| curved | 75.00% |
| damaged | 60.47% |
| glare | 84.91% |
| high_version | 97.30% |
| lots | 100.00% |
| monitor | 100.00% |
| nominal | 93.59% |
| noncompliant | 96.15% |
| pathological | 95.65% |
| perspective | 68.57% |
| rotations | 99.25% |
| shadows | 100.00% |

The other six engine columns in the article are the original 2021
measurements and are unchanged.
