# Python Barcode Reader Benchmark

This project measures barcode decoding accuracy and speed for the ZXing Python package and Dynamsoft Barcode Reader Python on the public [BarBeR dataset](https://ditto.ing.unimore.it/barber/). Both readers are evaluated with the same image set, ground truth manifest, matching rules, and raw JSONL result protocol.

https://github.com/user-attachments/assets/af83a174-ff7f-4d3d-9f66-162c46e070f2

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

## Benchmark Results

The current full run uses one repetition on 7,894 unique BarBeR images with zxing-cpp 3.1.1 and the Dynamsoft Capture Vision 3.6.1000 bundle. Recall is calculated as correct ground truth matches divided by 8,615 eligible ground truth instances. Precision is calculated as correct predictions divided by evaluated predictions, where evaluated predictions are `correct + wrong_text + wrong_format + extra_result`.

| Decoder | Correct | Recall | Precision | Image all-read rate | Mean decode time | Median decode time | P95 decode time |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dynamsoft Barcode Reader 3.6.1000 | **7,476 / 8,615** | **86.78%** | 91.49% | **86.91%** | **63.84 ms** | 44.87 ms | **173.80 ms** |
| ZXing-C++ 3.1.1 | 5,809 / 8,615 | 67.43% | 92.35% | 67.24% | 70.22 ms | 42.49 ms | 233.48 ms |

DBR read 1,667 more ground truth barcodes in this run and improved recall by 19.35 percentage points. ZXing-C++ had 0.86 percentage points higher precision. DBR's mean decoder call was 63.84 ms versus 70.22 ms for ZXing-C++, about 9.1% lower in this run.

### Python vs C++ on the Same BarBeR Images

The [C++ benchmark](https://www.dynamsoft.com/codepool/benchmark-barcode-reading-cpp-zxing-dynamsoft-barcode-reader.html) ran the identical 7,894-image manifest with ZXing-C++ 3.1.0 and Dynamsoft Barcode Reader 11.4.20.7177. This Python run uses ZXing-C++ 3.1.1 and the Dynamsoft Capture Vision 3.6.1000 bundle, whose bundled engine is Dynamsoft Barcode Reader 11.6.10.8373.

| Decoder | Run | Correct | Recall | Mean decode time |
|---|---|---:|---:|---:|
| Dynamsoft Barcode Reader | C++ 11.4.20.7177 | 7,444 / 8,615 | 86.41% | 70.08 ms |
| Dynamsoft Barcode Reader | Python 11.6.10.8373 | 7,476 / 8,615 | 86.78% | 63.84 ms |
| ZXing-C++ | C++ 3.1.0 | 5,855 / 8,615 | 67.96% | 74.09 ms |
| ZXing-C++ | Python 3.1.1 | 5,809 / 8,615 | 67.43% | 70.22 ms |

On the same BarBeR images, the newer DBR engine in the Python bundle improved recall by 0.37 percentage points and cut mean decode time by about 8.9% compared with the C++ release used in the earlier article. ZXing-C++ 3.1.1 in Python read fewer barcodes than ZXing-C++ 3.1.0 in C++ on this dataset, while the Python binding and newer revision delivered a faster mean decode time in this run.

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

## Matching Rules

- Ground truth and predictions are matched one to one as multisets.
- The key is canonical barcode format plus exact normalized payload.
- UPC-A and the equivalent zero-prefixed EAN-13 value are treated as equal.
- DBR `CODE39EXTENDED` output is treated as `CODE_39` when the payload matches.
- Barcode location is not part of the score.
- Unsupported formats remain visible in coverage-adjusted metrics.
- Decoder and input pipeline errors are explicit outcomes, not no-read results.

## Blog
[How to Benchmark Barcode Reading in Python with ZXing-C++ and Dynamsoft Barcode Reader](https://www.dynamsoft.com/codepool/benchmark-barcode-reading-python-zxing-dynamsoft-barcode-reader.html)
