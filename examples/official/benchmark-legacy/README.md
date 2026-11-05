# Legacy Barcode Benchmarks — Dynamsoft Python Runner

Runnable inputs and a `dynamsoft-capture-vision-bundle==3.6.5000` (DBR 11.6.5000)
runner for four Codepool benchmark articles:

| Article | Dataset | Images | Ground truth |
|---|---|---:|---:|
| [PDF417](https://www.dynamsoft.com/codepool/pdf417-reading-benchmark-and-comparison.html) | `PDF417` | 78 | 88 codes |
| [QR Code](https://www.dynamsoft.com/codepool/qr-code-reading-benchmark-and-comparison.html) | `QRCode` | 536 | 1,232 codes, 16 categories |
| [Data Matrix](https://www.dynamsoft.com/codepool/data-matrix-reading-benchmark-and-comparison.html) | `DataMatrix` | 57 | 112 codes |
| [1D EAN-13](https://www.dynamsoft.com/codepool/barcode-scanning-accuracy-benchmark-and-comparison.html) | three public archives | 3,484 | EAN-13 values |

## Data source

For `P` = `PDF417`, `QRCode` or `DataMatrix`:

| What | URL |
|---|---|
| Image list | `https://www.dynamsoft.com/barcode-dataset/benchmark/dataset/P/project_manifest.json` → `info.images` |
| Each image | `https://www.dynamsoft.com/barcode-dataset/benchmark/dataset/P/<name-in-manifest>` |
| Ground truth + archived engine results | `https://www.dynamsoft.com/barcode-dataset/benchmark/dataset/P/results.zip` |

Ground-truth `.txt` files are JSON arrays of quadrilaterals with `text` and
`x1..y4`; QR ground truth has no `text`. The site is a Vue SPA — unknown paths
return HTTP 200 with an HTML page, so `download_dataset.py` checks
`Content-Type`. Sizes: PDF417 116 MB, QRCode 205 MB, DataMatrix 3.9 MB. Images
are not committed; fetch them with the downloader. The 1D article's three
archives are listed in [1d_ean13/README.md](1d_ean13/README.md).

## Run

Requires Python 3.9+.

```bash
cd examples/official/benchmark-legacy
python -m pip install -r requirements.txt

python common/download_dataset.py --project PDF417 --output datasets/PDF417
python common/benchmark_dynamsoft.py --dataset datasets/PDF417 --project PDF417 \
  --output datasets/PDF417/current_run
```

Use `--project QRCode` / `DataMatrix` the same way; for 1D see
[1d_ean13/README.md](1d_ean13/README.md).

| Option | Meaning |
|---|---|
| `--dataset` | Root produced by `download_dataset.py` |
| `--project` | `PDF417`, `QRCode`, `DataMatrix` or `1D` (selects the symbology) |
| `--output` | Destination for `detection_results/` and `summary.json` |
| `--tuning` | `accuracy` (default) or `default` |
| `--license-key-file` | Text file with a [trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) |
| `--limit N` | First N images only |

Each image produces `detection_results/<stem>-Dynamsoft.json` in the archived
`results` / `elapsedTime` / `barcodeText` / `x1..y4` shape; `summary.json` holds
the aggregates and the exact settings used.

## Settings

The runner starts from `ReadBarcodes_Default`, restricts `barcode_format_ids`
to one symbology, and times only `CaptureVisionRouter.capture()`. `--tuning
accuracy` keeps large originals at full resolution (`scale_down_threshold`
99999 instead of 2300), enables the full `localization_modes` list, adds
`GEM_GRAY_SMOOTH` for QR Code, and sets `expected_barcodes_count=10` for Data
Matrix (its images hold up to five codes each). Use `--tuning default` for the
out-of-the-box figures.

## Metrics

`common/scoring.py` ports the original browser harness's rules: a detection is
correct when its axis-aligned overlap with a ground-truth quadrilateral exceeds
`0.20` and the cleaned text matches (or the ground truth has no text).

```
reading rate = detected codes / total ground-truth codes
precision    = (detected − misdetected) / detected
average time = total decode time / images
```

The QR article's "total average" is the unweighted mean of the 16 category
rates (`totalAverageReadingRate` in `summary.json`).

## Results (3.6.5000, `--tuning accuracy`)

| Project | Reading rate | Avg time |
|---|---:|---:|
| PDF417 | 98.86% (87/88) | 194.52 ms |
| QR Code | 84.75% (16-class avg) | 116.20 ms |
| Data Matrix | 100% (112/112) | 54.13 ms |

Per-project details: [pdf417](pdf417/README.md) · [qr_code](qr_code/README.md) ·
[data_matrix](data_matrix/README.md) · [1d_ean13](1d_ean13/README.md).
