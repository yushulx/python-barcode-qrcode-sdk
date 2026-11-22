"""Download a Dynamsoft Barcode Benchmark dataset (images + ground truth).

The benchmark site is a Vue SPA. Images live directly under

    https://www.dynamsoft.com/barcode-dataset/benchmark/dataset/<PROJECT>/<name>

and `project_manifest.json` lists every image name. Ground truth and the
historical per-engine detection results are in `results.zip`.

Note: the site returns HTTP 200 with a 1061-byte HTML page for unknown paths,
so always validate Content-Type instead of trusting the status code.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = "https://www.dynamsoft.com/barcode-dataset/benchmark/dataset"
MIN_IMAGE_BYTES = 128  # a few palette PNGs in the dataset are legitimately tiny


def fetch(url: str, retries: int = 3) -> bytes:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "codepool-benchmark/1.0"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                ctype = resp.headers.get("Content-Type", "")
                data = resp.read()
                if "text/html" in ctype:
                    raise ValueError(f"SPA fallback (HTML) for {url}")
                return data
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"failed after {retries} attempts: {url}: {last}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True, choices=["PDF417", "QRCode", "DataMatrix"])
    ap.add_argument("--output", required=True, help="Dataset root (images/ and ground_truth/ are created)")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    root = Path(args.output)
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "ground_truth").mkdir(parents=True, exist_ok=True)

    manifest = fetch(f"{BASE}/{args.project}/project_manifest.json")
    (root / "project_manifest.json").write_bytes(manifest)
    names = json.loads(manifest)["info"]["images"]
    print(f"{args.project}: {len(names)} images in manifest")

    results = fetch(f"{BASE}/{args.project}/results.zip")
    (root / "results.zip").write_bytes(results)
    with zipfile.ZipFile(root / "results.zip") as z:
        for name in z.namelist():
            if name.lower().endswith(".txt"):
                (root / "ground_truth" / name).parent.mkdir(parents=True, exist_ok=True)
                (root / "ground_truth" / name).write_bytes(z.read(name))
    print("ground truth + historical results saved")

    def one(name: str) -> tuple[str, int]:
        dest = root / "images" / name
        if dest.exists() and dest.stat().st_size >= MIN_IMAGE_BYTES:
            return name, dest.stat().st_size
        data = fetch(f"{BASE}/{args.project}/{name}")
        if len(data) < MIN_IMAGE_BYTES:
            raise ValueError(f"suspiciously small image: {name} ({len(data)} B)")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return name, len(data)

    ok = 0
    total_bytes = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(one, n): n for n in names}
        for fut in as_completed(futures):
            name, size = fut.result()
            ok += 1
            total_bytes += size
            if ok % 50 == 0 or ok == len(names):
                print(f"  {ok}/{len(names)} images", flush=True)
    print(f"done: {ok} images, {total_bytes / 1024 / 1024:.1f} MB -> {root / 'images'}")


if __name__ == "__main__":
    main()
