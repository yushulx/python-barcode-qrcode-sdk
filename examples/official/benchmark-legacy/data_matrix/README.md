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

## Version note

The article's published Dynamsoft figures (83.04% default, 100% with scenario
templates) were measured with `dynamsoft-capture-vision-bundle` **3.6.1000**.
The runner in this directory uses **3.6.5000**.

On 3.6.5000 the article's template JSON no longer loads cleanly:
`init_settings()` accepts `DeformationResistingModes`, but `capture()` then
returns `-10077 Skipped unsupported keys ... DeformationResistingModes` for
every image. `BinarizationModes` at the `ImageParameterOptions` level is also
rejected. The corrected 3.x template keeps `DPMCodeReadingModes` only:

```python
template = {
  "CaptureVisionTemplates": [{"Name": "read_dm", "ImageROIProcessingNameArray": ["roi_dm"]}],
  "TargetROIDefOptions": [{"Name": "roi_dm", "TaskSettingNameArray": ["bra_dm"]}],
  "BarcodeReaderTaskSettingOptions": [{
    "Name": "bra_dm",
    "BarcodeFormatIds": ["BF_DATAMATRIX"],
    "DPMCodeReadingModes": [{"Mode": "DPMCRM_GENERAL"}],
  }],
}
```

## Measured on 3.6.5000 (Python, 2026-11-04)

| Configuration | Correct / 112 | Reading rate | Avg time | Precision |
|---|---:|---:|---:|---:|
| `ReadBarcodes_Default`, SDK defaults | 95 | 84.82% | 10.34 ms | 100.00% |
| `--tuning accuracy` (full resolution + full localization) | 95 | 84.82% | 12.55 ms | 100.00% |
| Corrected DPM template above | 95 | 84.82% | 11.13 ms | 100.00% |

The archived `-Dynamsoft.json` results shipped in `results.zip` score 112/112
(100%) with the original 3.6.1000 template. `common/scoring.py` reproduces that
value from the archived file, so the scoring rules are unchanged; the
difference is the SDK's template behaviour. Treat the article's 100% as a
3.6.1000 measurement and do not copy it into a 3.6.5000 table.

The libdmtx (72.32%) and zxing-cpp (65.18%) columns in the article are the
original measurements and are unchanged.
