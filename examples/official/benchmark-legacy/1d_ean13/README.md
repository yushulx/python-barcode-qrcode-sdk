# 1D / EAN-13 — Dynamsoft runner

Article: [1D Barcode Scanner Accuracy Benchmark](https://www.dynamsoft.com/codepool/barcode-scanning-accuracy-benchmark-and-comparison.html)

The article evaluates 3,484 EAN-13 images from **three independent public
datasets**. They are not hosted on the Dynamsoft benchmark site, so there is no
single `download_dataset.py --project` command. Fetch them from their authors:

| Dataset | Images | Source | Direct archive |
|---|---:|---|---|
| Arte-Lab Medium Barcode 1D (in-focus + out-of-focus) | 215 + 215 | [Arte-Lab page](http://artelab.dista.uninsubria.it/downloads/datasets/barcode/medium_barcode_1d/medium_barcode_1d.html) | [`medium_barcode_1d.zip`](http://artelab.dista.uninsubria.it/downloads/datasets/barcode/medium_barcode_1d/medium_barcode_1d.zip) (215 MB) |
| WWU Muenster BarcodeDB | 1,054 in this benchmark | [PRIA research page](https://www.uni-muenster.de/PRIA/en/forschung/index.shtml) | [Sciebo share](https://uni-muenster.sciebo.de/index.php/s/8KC6sVAuL2BzCXS) (see the **Download** link in the Muenster BarcodeDB section) |
| DEAL / KAIST Lab Barcode | 2,000 in this benchmark | [AI2Lab datasets page](https://www.resl.kaist.ac.kr/doc/datasets) | public download link on that page |

Ground truth for all three is the barcode value: for Arte-Lab it is in `.txt`
files next to the images; for Muenster and DEAL it is the first 13 characters
of each image file name (rotated-rectangle coordinates are also provided in
`.txt` / XML files). The article's reading rate counts a correctly decoded
EAN-13 value; UPC-A returned for an EAN-13 ground truth is accepted after
normalisation (see `common/scoring.py`).

## Run

```bash
cd ../../   # examples/official/benchmark-legacy
python -m pip install -r requirements.txt

python common/benchmark_dynamsoft.py \
  --dataset /path/to/one-of-the-three-datasets \
  --project 1D --tuning accuracy \
  --output results/1d_current
```

`--project 1D` restricts decoding to `BF_EAN_13 | BF_UPC_A` on
`dynamsoft-capture-vision-bundle==3.6.5000` (DBR 11.6.5000) and writes one
`-Dynamsoft.json` per image plus `summary.json`. The runner expects the dataset
root to contain `project_manifest.json`, `images/` and `ground_truth/`
(the same layout produced by `common/download_dataset.py`); a small helper for
building that layout from a directory of `<EAN13>.jpg` files is included in
`make_manifest.py`.

```bash
python 1d_ean13/make_manifest.py \
  --images /path/to/arte-lab-or-muenster-images \
  --output datasets/1D_artelab
```

## Version note

The article's Dynamsoft figures (100% / 91.95% / 81.86% / 96.96% reading
rates and 100% precision across the three datasets) are the original 2021
measurements. They are kept as published because the three source archives are
distributed independently and a full re-run requires all of them. This runner
provides the current SDK path for anyone who wants to repeat the measurement.
The Scandit, ZXing-CPP and pyZbar columns are unchanged.
