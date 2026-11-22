"""Re-run the Dynamsoft column of the PDF417 / QR Code Codepool benchmarks.

Uses the current Dynamsoft Capture Vision Python SDK (3.6.5000, DBR 11.6.5000),
reproducing the original benchmark's input, format restriction and scoring.

Input layout (produced by common/download_dataset.py):

    <dataset>/
      project_manifest.json        # info.images: ordered image names
      images/<name>                # jpg, may contain category sub-directories
      ground_truth/<stem>.txt      # JSON ground-truth quadrilaterals
      results.zip                  # original per-engine results (for comparison)

Output:

    <output>/detection_results/<stem>-Dynamsoft.json   # same shape as the original
    <output>/summary.json                              # reading rate, precision, time

Scoring is identical to the original browser benchmark (see common/scoring.py).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring import engine_statistics  # noqa: E402

import cv2  # noqa: E402
import dynamsoft_capture_vision_bundle as dcv  # noqa: E402

DEFAULT_LICENSE = (
    "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
)
TEMPLATE = "ReadBarcodes_Default"
FORMATS = {
    "PDF417": (dcv.EnumBarcodeFormat.BF_PDF417, "PDF417"),
    "QRCode": (dcv.EnumBarcodeFormat.BF_QR_CODE, "QR_CODE"),
}

# The published tables used tuned runtime settings (the PDF417 article documents
# GrayscaleEnhancementModes and a scan ROI). On DCV 3.6.5000 the two settings
# that actually help are: keep large images at full resolution (the default
# scale_down_threshold of 2300 shrinks 2688px / 4032px originals), and enable
# the full localization mode list. A/B results are in pdf417/README.md.
END = -1
FULL_LOCALIZATION = [2, 8, 4, 16, 512, 32, 128, END]
GRAY_SMOOTH = [8, 2] + [END] * 6
_BASE_ACCURACY = {
    "scale_down_threshold": 99999,
    "localization_modes": FULL_LOCALIZATION,
}
TUNING = {
    "default": {"PDF417": {}, "QRCode": {}},
    "accuracy": {
        # PDF417: full resolution + full localization wins (98.86%).
        "PDF417": dict(_BASE_ACCURACY),
        # QR Code: GEM_GRAY_SMOOTH additionally helps the lots / damaged cases
        # (84.75%, vs 84.05% without it).
        "QRCode": {**_BASE_ACCURACY, "grayscale_enhancement_modes": GRAY_SMOOTH},
    },
}


def make_router(project: str, license_key: str, tuning: str) -> dcv.CaptureVisionRouter:
    code, message = dcv.LicenseManager.init_license(license_key)
    ok = {dcv.EnumErrorCode.EC_OK}
    if hasattr(dcv.EnumErrorCode, "EC_LICENSE_CACHE_USED"):
        ok.add(dcv.EnumErrorCode.EC_LICENSE_CACHE_USED)
    if code not in ok:
        raise RuntimeError(f"license init failed: {code}, {message}")
    router = dcv.CaptureVisionRouter()
    code, message, settings = router.get_simplified_settings(TEMPLATE)
    if code != dcv.EnumErrorCode.EC_OK:
        raise RuntimeError(f"get_simplified_settings failed: {code}, {message}")
    settings.barcode_settings.barcode_format_ids = FORMATS[project][0]
    tuning_settings = TUNING[tuning][project]
    for key, value in tuning_settings.items():
        setattr(settings.barcode_settings, key, value)
    code, message = router.update_settings(TEMPLATE, settings)
    if code != dcv.EnumErrorCode.EC_OK:
        raise RuntimeError(f"update_settings failed: {code}, {message}")
    return router


def decode_one(router: dcv.CaptureVisionRouter, bgr) -> dict:
    results = []
    begin = time.perf_counter_ns()
    captured = router.capture(bgr, TEMPLATE)
    elapsed_ms = (time.perf_counter_ns() - begin) / 1_000_000.0
    if captured.get_error_code() != dcv.EnumErrorCode.EC_OK:
        return {"results": results, "elapsedTime": round(elapsed_ms, 2),
                "error": captured.get_error_string()}
    for item in captured.get_items():
        quad = item.get_location().points
        raw = item.get_bytes() or b""
        # The original tool stored bytes as a UTF-16BE hex string.
        raw_hex = raw.decode("utf-8", errors="replace").encode("utf-16-be").hex()
        row = {
            "barcodeFormat": item.get_format_string(),
            "barcodeText": item.get_text(),
            "barcodeBytes": raw_hex,
            "confidence": item.get_confidence(),
        }
        for i, point in enumerate(quad[:4], 1):
            row[f"x{i}"] = point.x
            row[f"y{i}"] = point.y
        results.append(row)
    return {"results": results, "elapsedTime": round(elapsed_ms, 2)}


def load_ground_truth(root: Path, images: list[str]) -> dict[str, list[dict]]:
    out = {}
    for image in images:
        stem = image.rsplit(".", 1)[0]
        p = root / "ground_truth" / (stem + ".txt")
        try:
            out[stem] = json.loads(p.read_text(encoding="utf-8"))
        except FileNotFoundError:
            out[stem] = []
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", required=True, help="Root produced by download_dataset.py")
    ap.add_argument("--project", required=True, choices=["PDF417", "QRCode"])
    ap.add_argument("--output", default="results", help="Where to write detection results")
    ap.add_argument("--license-key-file", help="Text file containing a Dynamsoft license key")
    ap.add_argument("--tuning", choices=list(TUNING), default="accuracy",
                    help="accuracy = full-resolution input + all localization modes (default)")
    ap.add_argument("--limit", type=int, default=0, help="Only process the first N images (smoke test)")
    args = ap.parse_args()

    root = Path(args.dataset)
    out = Path(args.output)
    det_dir = out / "detection_results"
    det_dir.mkdir(parents=True, exist_ok=True)
    images = json.loads((root / "project_manifest.json").read_text(encoding="utf-8"))["info"]["images"]
    if args.limit:
        images = images[: args.limit]
    license_key = (Path(args.license_key_file).read_text(encoding="utf-8").strip()
                   if args.license_key_file else DEFAULT_LICENSE)
    router = make_router(args.project, license_key, args.tuning)

    detection: dict[str, dict] = {}
    for index, image in enumerate(images, 1):
        stem = image.rsplit(".", 1)[0]
        bgr = cv2.imread(str(root / "images" / image), cv2.IMREAD_COLOR)
        if bgr is None:
            print(f"  [warn] unreadable: {image}", flush=True)
            continue
        record = decode_one(router, bgr)
        detection[stem] = record
        (det_dir / (stem + "-Dynamsoft.json")).parent.mkdir(parents=True, exist_ok=True)
        (det_dir / (stem + "-Dynamsoft.json")).write_text(
            json.dumps(record, ensure_ascii=False), encoding="utf-8")
        if index % 25 == 0 or index == len(images):
            print(f"  {index}/{len(images)}", flush=True)

    gt = load_ground_truth(root, images)
    overall = engine_statistics(images, gt, detection)
    # The article's headline "reading rate" counts every returned result, and
    # the QR article's "total average" is the unweighted mean of 16 categories.
    overall["readingRate"] = round(overall["detected"] / overall["totalBarcodes"] * 100, 2) \
        if overall["totalBarcodes"] else 0.0
    categories = {}
    if args.project == "QRCode":
        for cat in sorted({i.split("/")[0] for i in images}):
            s = engine_statistics(images, gt, detection, cat)
            s["readingRate"] = round(s["detected"] / s["totalBarcodes"] * 100, 2) \
                if s["totalBarcodes"] else 0.0
            categories[cat] = s
        overall["totalAverageReadingRate"] = round(
            statistics.fmean(s["readingRate"] for s in categories.values()), 2)

    summary = {
        "sdk": "Dynamsoft Capture Vision / Barcode Reader",
        "sdk_version": getattr(dcv, "__version__", "unknown"),
        "project": args.project,
        "template": TEMPLATE,
        "tuning": args.tuning,
        "tuning_settings": TUNING[args.tuning][args.project],
        "format": FORMATS[args.project][1],
        "images": len(images),
        "overall": overall,
        "categories": categories,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{args.project} / DCV {summary['sdk_version']}")
    print(f"  images          : {len(images)}")
    print(f"  ground truth    : {overall['totalBarcodes']:,}")
    print(f"  detected        : {overall['detected']:,}")
    print(f"  reading rate    : {overall['readingRate']:.2f}%")
    print(f"  precision       : {overall['precision']:.2f}%")
    print(f"  average time    : {overall['averageTime']:.2f} ms/image")
    if categories:
        print(f"  16-class average: {overall['totalAverageReadingRate']:.2f}%")
    print(f"  wrote {out / 'summary.json'}")


if __name__ == "__main__":
    main()
