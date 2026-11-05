# Python Barcode Reader Benchmark

This project measures barcode decoding accuracy and speed for the ZXing Python package and Dynamsoft Barcode Reader Python on the public [BarBeR dataset](https://ditto.ing.unimore.it/barber/). Both readers are evaluated with the same image set, ground truth manifest, matching rules, and raw JSONL result protocol.

https://github.com/user-attachments/assets/2fb0a810-b7b8-4f3b-9d32-2abe334d28f2

## Dependencies

- Python 3.9 or later
- OpenCV Python
- `zxing-cpp` Python package
- `dynamsoft-capture-vision-bundle`
- A valid [Dynamsoft Barcode Reader license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform)

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Prepare the BarBeR Dataset

The expected dataset layout is:

```text
BarBeR - Dataset/
  Annotations/VIA/
  dataset/images/
```

Generate the benchmark manifest from the same image collection:

```powershell
python benchmark.py audit `
  --images "D:/images/public-barcode-dataset/BarBeR - Dataset/dataset/images" `
  --annotations "D:/images/public-barcode-dataset/BarBeR - Dataset/Annotations/VIA" `
  --output manifests
```

The audit validates image availability, payload structure, overlapping annotations, and exact duplicate image bytes. It writes `manifests/benchmark_manifest.jsonl`, `manifests/smoke_manifest.jsonl`, and `manifests/barber_source_files.json`.

## Run a Smoke Test

Store the Dynamsoft license in a local text file or set `DYNAMSOFT_LICENSE_KEY`.

```powershell
python benchmark.py smoke `
  --images "D:/images/public-barcode-dataset/BarBeR - Dataset/dataset/images" `
  --manifest manifests/smoke_manifest.jsonl `
  --output results/smoke `
  --license-key-file "license-key.txt" `
  --repetitions 1
```

## Run the Full Benchmark

```powershell
python benchmark.py run `
  --images "D:/images/public-barcode-dataset/BarBeR - Dataset/dataset/images" `
  --manifest manifests/benchmark_manifest.jsonl `
  --output results/full `
  --license-key-file "license-key.txt" `
  --dbr-template ReadBarcodes_Default `
  --repetitions 1
```

The command is resumable. It skips existing `(sample_id, decoder, repetition)` records in `results.jsonl`, then writes `summary.json` and `results.json`.

## Validate Results

```powershell
python tools/validate_results.py `
  --results results/full/results.jsonl `
  --summary results/full/summary.json `
  --expected-images 7894 `
  --expected-ground-truth 8615 `
  --expected-repetitions 1
```

`--expected-ground-truth 8615` is the audited annotation count stored in each record. Scoring excludes 204 `^` placeholders, so recall uses 8,411.

## Benchmark Results

The current full run uses one repetition on 7,894 unique BarBeR images with zxing-cpp 3.1.1 and the Dynamsoft Capture Vision 3.6.5000 bundle (DBR 11.6.5000). Recall is calculated as correct ground truth matches divided by 8,411 scored ground truth instances. The audit still records 8,615 original eligible annotations; 204 of those payloads are the unreliable placeholder `^` and are now excluded from scoring. Precision is calculated as correct predictions divided by evaluated predictions, where evaluated predictions are `correct + wrong_text + wrong_format + extra_result`.

| Decoder | Correct | Recall | Precision | Wrong reads | No read | Mean decode time | Median decode time | P95 decode time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dynamsoft Barcode Reader 3.6.5000 | **7,834 / 8,411** | **93.14%** | **95.96%** | 83 (0.99%) | 494 (5.87%) | **63.71 ms** | 44.61 ms | **171.66 ms** |
| ZXing-C++ 3.1.1 | 5,974 / 8,411 | 71.03% | 94.98% | 155 (1.84%) | 2,282 (27.13%) | 70.55 ms | 45.01 ms | 233.79 ms |

Failures are split into **wrong reads** (`wrong_text + wrong_format`) and **no read** (`not_found + unsupported_format + decoder_error`), so correct + wrong reads + no read equals the 8,411 scored ground-truth instances. Extra results beyond the ground truth affect precision, not this split.


DBR read 1,860 more ground truth barcodes in this run, a lead of 22.11 percentage points in recall and 0.98 points in precision. Its mean decoder call was 63.71 ms versus 70.55 ms for ZXing-C++, about 9.7% lower in this run.

### Python vs C++ on the Same BarBeR Images

The [C++ benchmark](https://www.dynamsoft.com/codepool/benchmark-barcode-reading-cpp-zxing-dynamsoft-barcode-reader.html) and the [JavaScript benchmark](https://www.dynamsoft.com/codepool/benchmark-barcode-reading-javascript-zxing-wasm-dynamsoft-barcode-reader.html) run the identical 7,894-image manifest. All three now use DBR 11.6.5000 and ZXing-C++ 3.1.x, so the series isolates the language/runtime binding on unchanged input and one SDK release.

| Decoder | Run | Correct | Recall | Mean decode time |
|---|---|---:|---:|---:|
| Dynamsoft Barcode Reader | C++ 11.6.50.9329 | 7,806 / 8,411 | 92.81% | 57.09 ms |
| Dynamsoft Barcode Reader | Python 11.6.5000 | 7,834 / 8,411 | 93.14% | 63.71 ms |
| Dynamsoft Barcode Reader | JavaScript 11.6.5000 | 7,638 / 8,411 | 90.81% | 121.05 ms |
| ZXing-C++ | C++ 3.1.1 | 6,031 / 8,411 | 71.70% | 69.90 ms |
| ZXing-C++ | Python 3.1.1 | 5,974 / 8,411 | 71.03% | 70.55 ms |
| zxing-wasm | JavaScript 3.1.2 | 5,958 / 8,411 | 70.84% | 116.22 ms |

On the same BarBeR images and one SDK release, the native C++ and Python bindings land within a few tenths of a percentage point of each other, while the browser/WASM binding gives up roughly two points to its JPEG → `ImageBitmap` → RGBA canvas image path. Decode times are not directly comparable across runtimes: the browser adds canvas and WASM boundary overhead that the native and OpenCV paths do not have.

## Generate the HTML Report

Record the Python runtime environment:

```powershell
python benchmark.py write-environment `
  --output configs/benchmark_environment.json `
  --repetitions 1 `
  --dbr-template ReadBarcodes_Default
```

Generate the report:

```powershell
python tools/generate_html_report.py `
  --inventory manifests/barber_source_files.json `
  --environment configs/benchmark_environment.json `
  --results results/full/results.jsonl `
  --results-json results/full/results.json `
  --summary results/full/summary.json `
  --output report/index.html
```

Regenerate the cover image, poster, and slide video:

```powershell
python tools/generate_benchmark_media.py `
  --inventory manifests/barber_source_files.json `
  --summary results/full/summary.json `
  --output report/media
```

## Matching Rules

- Ground truth and predictions are matched one to one as multisets.
- The key is canonical barcode format plus exact normalized payload.
- UPC-A and the equivalent zero-prefixed EAN-13 value are treated as equal.
- CODE_39 start/stop asterisks are stripped before scoring.
- CODE_128 / GS1-128 leading `{GS}`, `{FNC1}`, and ASCII GS markers are stripped before scoring.
- HTML entities, trailing newlines, and a leading `\000001` escape are normalized before scoring.
- Ground truth payload `^` is treated as an unreliable placeholder and excluded from scoring.
- DBR `CODE39EXTENDED` output is treated as `CODE_39` when the payload matches.
- Barcode location is not part of the score.
- Unsupported formats remain visible in coverage-adjusted metrics.
- Decoder and input pipeline errors are explicit outcomes, not no-read results.

To re-score an existing `results.jsonl` after a matching-rule change, without re-running the decoders:

```powershell
python benchmark.py rematch `
  --results results/full/results.jsonl `
  --output results/full
```

## Blog

[How to Benchmark Barcode Reading in Python with ZXing-C++ and Dynamsoft Barcode Reader](https://www.dynamsoft.com/codepool/benchmark-barcode-reading-python-zxing-dynamsoft-barcode-reader.html)
