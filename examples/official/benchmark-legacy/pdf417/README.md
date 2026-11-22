# PDF417 — Dynamsoft re-run

Article: [PDF417 Barcode Scanner SDK Benchmark](https://www.dynamsoft.com/codepool/pdf417-reading-benchmark-and-comparison.html)

```bash
cd ../../   # examples/official/benchmark-legacy
python common/download_dataset.py --project PDF417 --output datasets/PDF417
python common/benchmark_dynamsoft.py --dataset datasets/PDF417 --project PDF417 \
  --output datasets/PDF417/current_run
```

Dataset: 78 images, 88 PDF417 codes, 116 MB. Decoding is restricted to
`BF_PDF417`. Sources and options are in the [parent README](../README.md).

The article's reading rate counts every returned result; `summary.json` also
reports `accuracy` (overlap + text-correct), `precision` and `averageTime`.

## Result (3.6.5000)

| Tuning | Reading rate (detected / 88) | Avg time |
|---|---:|---:|
| `default` | 93.18% | 176.05 ms |
| `accuracy` (full resolution + full localization, used) | **98.86%** | **194.52 ms** |
