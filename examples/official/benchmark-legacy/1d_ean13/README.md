# 1D / EAN-13 — Dynamsoft runner

Article: [1D Barcode Scanner Accuracy Benchmark](https://www.dynamsoft.com/codepool/barcode-scanning-accuracy-benchmark-and-comparison.html)

The three datasets are published independently, not on the Dynamsoft
benchmark site:

| Dataset | Images | Download |
|---|---:|---|
| Arte-Lab Medium Barcode 1D (in-focus + out-of-focus) | 215 + 215 | [`medium_barcode_1d.zip`](http://artelab.dista.uninsubria.it/downloads/datasets/barcode/medium_barcode_1d/medium_barcode_1d.zip) (215 MB) |
| WWU Muenster BarcodeDB | 1,054 | [Sciebo share](https://uni-muenster.sciebo.de/index.php/s/8KC6sVAuL2BzCXS) |
| DEAL / KAIST Lab Barcode | 2,000 | [AI2Lab datasets page](https://www.resl.kaist.ac.kr/doc/datasets) |

Ground truth is the EAN-13 value: Arte-Lab ships `.txt` files, Muenster and
DEAL encode it in the image file name. UPC-A returned for an EAN-13 ground
truth is accepted after normalisation.

## Run

Each archive needs the `project_manifest.json` / `images/` / `ground_truth/`
layout expected by the runner. Build it from a directory of `<EAN13>.jpg`
files, then decode:

```bash
cd ../../   # examples/official/benchmark-legacy
python -m pip install -r requirements.txt

python 1d_ean13/make_manifest.py \
  --images /path/to/dataset-images --output datasets/1D_artelab

python common/benchmark_dynamsoft.py \
  --dataset datasets/1D_artelab --project 1D --tuning accuracy \
  --output results/1d_artelab
```

`--project 1D` restricts decoding to `BF_EAN_13 | BF_UPC_A` on
`dynamsoft-capture-vision-bundle==3.6.5000` and writes one
`-Dynamsoft.json` per image plus `summary.json`. Data sources, options and
metric definitions are in the [parent README](../README.md).
