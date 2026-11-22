# QR Code — Dynamsoft re-run

Article: [QR Code Reading Benchmark](https://www.dynamsoft.com/codepool/qr-code-reading-benchmark-and-comparison.html)

```bash
cd ../../   # examples/official/benchmark-legacy
python common/download_dataset.py --project QRCode --output datasets/QRCode
python common/benchmark_dynamsoft.py --dataset datasets/QRCode --project QRCode \
  --output datasets/QRCode/current_run
```

Dataset: 536 images in 16 categories, 1,232 QR ground-truth quadrilaterals,
205 MB. Decoding is restricted to `BF_QR_CODE`. Ground truth has no text, so
the metric is a detection rate. Sources and options are in the
[parent README](../README.md).

The article's "total average" is the unweighted mean of the 16 category rates
(`totalAverageReadingRate`); `readingRate` is the global `detected / 1,232`.

## Result (3.6.5000, `--tuning accuracy`: full resolution + full localization + `GEM_GRAY_SMOOTH`)

| Metric | Default | Tuned |
|---|---:|---:|
| Total average (16 categories) | 80.61% | **84.75%** |
| Global detection rate | 73.46% | 87.34% |
| Avg decode time | 73.29 ms | 116.20 ms |
