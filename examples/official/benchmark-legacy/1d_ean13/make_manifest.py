"""Build the download_dataset.py layout from a directory of EAN-13 images.

The three 1D datasets used by the article are distributed separately. This
helper turns a flat directory of `<EAN13>.jpg` images into

    <output>/project_manifest.json
    <output>/images/<name>
    <output>/ground_truth/<stem>.txt

so `common/benchmark_dynamsoft.py --project 1D` can score them with the same
rules as the Dynamsoft benchmark site. Ground truth is taken from the leading
13 digits of the file name, which is how Muenster BarcodeDB and the DEAL/KAIST
dataset encode it. Arte-Lab archives additionally ship `.txt` files; those are
copied into `ground_truth/` when present and take precedence.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
EAN = re.compile(r"(\d{12,14})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", required=True, help="Directory containing the dataset images")
    ap.add_argument("--output", required=True, help="Dataset root to create")
    ap.add_argument("--copy", action="store_true",
                    help="Copy images instead of hard-linking them (use on a different drive)")
    args = ap.parse_args()

    src = Path(args.images)
    out = Path(args.output)
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "ground_truth").mkdir(parents=True, exist_ok=True)

    names: list[str] = []
    skipped = 0
    for path in sorted(src.rglob("*")):
        if path.suffix.lower() not in SUFFIXES or not path.is_file():
            continue
        match = EAN.search(path.stem)
        if not match:
            skipped += 1
            continue
        value = match.group(1)
        if len(value) == 14:          # some archives append a 14th digit
            value = value[:13]
        dest = out / "images" / path.name
        if not dest.exists():
            if args.copy:
                shutil.copy2(path, dest)
            else:
                try:
                    dest.hardlink_to(path)
                except OSError:
                    shutil.copy2(path, dest)
        # Four corner points covering the whole image: these datasets only
        # provide the barcode value, not a localisation polygon. The scoring
        # rules then match on text, which is what the article measures.
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        gt = [{
            "text": value,
            "attrib": {"Type": "EAN_13"},
            "value_attrib": {},
            "x1": 0, "y1": 0, "x2": w, "y2": 0,
            "x3": w, "y3": h, "x4": 0, "y4": h,
        }]
        gt_path = out / "ground_truth" / (path.stem + ".txt")
        provided = path.with_suffix(".txt")
        if provided.is_file() and provided != gt_path:
            gt_path.write_bytes(provided.read_bytes())
        else:
            gt_path.write_text(json.dumps(gt), encoding="utf-8")
        names.append(path.name)

    (out / "project_manifest.json").write_text(
        json.dumps({"info": {"name": out.name, "images": names}}, indent=2),
        encoding="utf-8")
    print(f"{len(names)} images written to {out} (skipped {skipped} without an EAN-13 file name)")


if __name__ == "__main__":
    main()
