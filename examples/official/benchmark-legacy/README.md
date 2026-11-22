# Legacy Barcode Benchmarks — Reconstructible Dynamsoft Runs

Location: `yushulx/python-barcode-qrcode-sdk/examples/official/benchmark-legacy/`

Reproducible inputs and a current-SDK Python runner for two Codepool comparison
articles. Only the Dynamsoft column is re-measured; the other SDK columns in
the articles remain the original published measurements.

| Article | Dataset | Images | Ground truth |
|---|---|---:|---:|
| [PDF417 Barcode Scanner SDK Benchmark](https://www.dynamsoft.com/codepool/pdf417-reading-benchmark-and-comparison.html) | `PDF417` | 78 | 88 PDF417 codes |
| [QR Code Reading Benchmark](https://www.dynamsoft.com/codepool/qr-code-reading-benchmark-and-comparison.html) | `QRCode` | 536 | 1,232 QR codes, 16 categories |

## Directory layout

```
benchmark-legacy/
├── README.md                     # this file
├── requirements.txt              # pinned SDK + OpenCV
├── common/
│   ├── download_dataset.py       # fetch images + ground truth
│   ├── benchmark_dynamsoft.py    # run DCV 3.6.5000 and score
│   └── scoring.py                # Python port of the original scoring rules
├── pdf417/README.md              # command + result for the PDF417 article
└── qr_code/README.md             # command + result for the QR Code article
```

## Data source

Everything comes from the public Dynamsoft Barcode Benchmark site. For a
project `P` (`PDF417` or `QRCode`):

| What | URL |
|---|---|
| Image list | `https://www.dynamsoft.com/barcode-dataset/benchmark/dataset/P/project_manifest.json` → `info.images` |
| Each image | `https://www.dynamsoft.com/barcode-dataset/benchmark/dataset/P/<name-in-manifest>` |
| Ground truth + historical per-engine results | `https://www.dynamsoft.com/barcode-dataset/benchmark/dataset/P/results.zip` |

Ground-truth `.txt` files are JSON arrays of quadrilaterals
(`{"attrib":{"Type":"PDF417"|"QR"},"text":...,"x1":...,"y1":..., ... }`).
The QR ground truth has empty `text` — only the location is annotated — so
the QR metric is a detection rate.

The results page for each project is
`https://www.dynamsoft.com/barcode-dataset/benchmark/project/PDF417` (or
`/QRCode`).

> The site is a Vue SPA. **Unknown paths return HTTP 200 with a 1 KB HTML
> page**, so `download_dataset.py` validates `Content-Type` instead of the
> status code. A few palette PNGs are legitimately under 1 KB.

Downloaded sizes: PDF417 ≈ 116 MB, QRCode ≈ 205 MB. The images are **not**
committed to git; use the downloader to fetch them from the source.

## How to run

Requires Python 3.9+ on Windows, Linux or macOS.

```bash
cd examples/official/benchmark-legacy
python -m pip install -r requirements.txt

# 1. Download images, ground truth and the archived results
python common/download_dataset.py --project PDF417 --output datasets/PDF417
python common/download_dataset.py --project QRCode --output datasets/QRCode

# 2. Run Dynamsoft Barcode Reader over the full dataset
python common/benchmark_dynamsoft.py \
  --dataset datasets/PDF417 --project PDF417 \
  --output datasets/PDF417/current_run

python common/benchmark_dynamsoft.py \
  --dataset datasets/QRCode --project QRCode \
  --output datasets/QRCode/current_run

# quick sanity check
python common/benchmark_dynamsoft.py \
  --dataset datasets/PDF417 --project PDF417 --output /tmp/smoke --limit 5

# compare against SDK defaults (no tuning)
python common/benchmark_dynamsoft.py \
  --dataset datasets/PDF417 --project PDF417 \
  --output /tmp/untuned --tuning default
```

Useful options:

| Option | Meaning |
|---|---|
| `--dataset` | Root produced by `download_dataset.py` |
| `--project` | `PDF417` or `QRCode` (also selects the symbology) |
| `--output` | Destination for `detection_results/` and `summary.json` |
| `--tuning` | `accuracy` (default, see below) or `default` |
| `--license-key-file` | Text file with a [30-day trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) |
| `--limit N` | Process only the first N images |

Output per image is `detection_results/<stem>-Dynamsoft.json` in the same shape
as the archived results (`results`, `elapsedTime`, `barcodeFormat`,
`barcodeText`, `x1..y4`). `summary.json` contains the aggregate metrics and
the exact settings used. Re-running the downloader skips existing files.

## Runtime settings

`requirements.txt` pins `dynamsoft-capture-vision-bundle==3.6.5000`
(DBR 11.6.5000). The runner starts from `ReadBarcodes_Default`, restricts
`barcode_format_ids` to the one symbology, and times only
`CaptureVisionRouter.capture()`.

Two settings matter on these large images. The default
`scale_down_threshold` of 2300 shrinks 2688 px and 4032 px originals; raising
it keeps full resolution. Enabling the full `localization_modes` list adds
neural-network / statistics / centre localization. `GEM_GRAY_SMOOTH` is added
for QR Code only, where it helps the `lots` and `damaged` categories.

A/B results on all images (article metric = detected codes / ground truth):

| Setting | PDF417 reading rate | PDF417 ms/image | QR 16-class average | QR ms/image |
|---|---:|---:|---:|---:|
| SDK defaults | 93.18% | 176.05 | 80.61% | 73.29 |
| no downscaling | 95.45% | 183.42 | 83.57% | 116.18 |
| full localization | 96.59% | 218.71 | 81.34% | 84.93 |
| both | 98.86% | 217.57 | 84.05% | 121.45 |
| both + GEM_GRAY_SMOOTH | 96.59% | 175.12 | **84.75%** | 124.46 |

`--tuning accuracy` applies the best combination for each project:
PDF417 = full resolution + full localization; QR Code = the same plus
`GEM_GRAY_SMOOTH`. `ReadBarcodes_ReadRateFirst` was also tested but reached
the same PDF417 rate at ~915 ms/image, so it is not used.

## Metrics

`common/scoring.py` is a Python port of the original harness's `src/utils.ts`.
For each detection it finds the first ground-truth quadrilateral whose
axis-aligned bounding-box overlap ratio exceeds `0.20`, then compares the
cleaned text (or counts it as correct when the ground truth has no text).

```
reading rate = detected codes / total ground-truth codes
precision    = (detected − misdetected) / detected
average time = total decode time / number of processed images
```

The QR article reports the **unweighted mean of the 16 category reading
rates** as its "total average"; the runner emits that as
`totalAverageReadingRate`. The port was validated by replaying the archived
`-Dynamsoft.json` results: PDF417 95.45% / 586.64 ms and QR Code 83.29% /
195.01 ms, matching the published tables.
