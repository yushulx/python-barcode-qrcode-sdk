# Data Matrix — Dynamsoft re-run

Article: [Data Matrix SDK Benchmark 2026](https://www.dynamsoft.com/codepool/data-matrix-reading-benchmark-and-comparison.html)

```bash
cd ../../   # examples/official/benchmark-legacy
python common/download_dataset.py --project DataMatrix --output datasets/DataMatrix
python common/benchmark_dynamsoft.py --dataset datasets/DataMatrix --project DataMatrix \
  --output datasets/DataMatrix/current_run
```

Dataset: 57 images, 112 Data Matrix codes, 3.9 MB. Ground truth has both text
and quadrilaterals, so `scoring.py` checks overlap and text. Sources and
options are in the [parent README](../README.md).

The images hold up to five codes each; the SDK default finds about one per
image. `--tuning accuracy` sets `expected_barcodes_count=10`, the full
`localization_modes` list and `scale_down_threshold=99999`.

## Result (3.6.5000)

| Tuning | Correct / 112 | Reading rate | Avg time |
|---|---:|---:|---:|
| `default` | 95 | 84.82% | 11.36 ms |
| `accuracy` (used) | **112** | **100%** | **54.13 ms** |

Precision is 100% in both configurations.
