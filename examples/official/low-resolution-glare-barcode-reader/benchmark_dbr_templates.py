import argparse
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

import cv2

from dynamsoft_capture_vision_bundle import (
    CaptureVisionRouter,
    EnumErrorCode,
    EnumPresetTemplate,
    LicenseManager,
)


ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "assets"
IMAGE_DIR = ASSET_DIR / "images"
TEMPLATE_DIR = ROOT / "templates"
REPORT_DIR = ROOT / "reports"

TRIAL_LICENSE = (
    "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIs"
    "InNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
)


def init_license() -> None:
    license_key = os.environ.get("DYNAMSOFT_LICENSE_KEY") or TRIAL_LICENSE
    err, msg = LicenseManager.init_license(license_key)
    if err not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_CACHE_USED):
        raise RuntimeError(f"Dynamsoft license initialization failed: {msg}")


def load_default_template() -> dict:
    router = CaptureVisionRouter()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "preset-settings.json"
        err, msg = router.output_settings_to_file(EnumPresetTemplate.PT_READ_BARCODES.value, str(temp_path))
        if err != 0:
            raise RuntimeError(f"Failed to export default template: {msg}")
        return json.loads(temp_path.read_text(encoding="utf-8"))


def set_stage_modes(template: dict, stage_name: str, key: str, modes: list[dict]) -> None:
    for image_parameter in template.get("ImageParameterOptions", []):
        for stage in image_parameter.get("ApplicableStages", []):
            if stage.get("Stage") == stage_name:
                stage[key] = modes


def build_fast_inverted_template() -> Path:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    template = load_default_template()
    template["CaptureVisionTemplates"][0]["Name"] = "ReadBarcodes_FastInverted"

    task = template["BarcodeReaderTaskSettingOptions"][0]
    task["BarcodeFormatIds"] = ["BF_CODE_128", "BF_QR_CODE"]

    set_stage_modes(
        template,
        "SST_TRANSFORM_GRAYSCALE",
        "GrayscaleTransformationModes",
        [{"Mode": "GTM_ORIGINAL"}, {"Mode": "GTM_INVERTED"}],
    )

    fast_path = TEMPLATE_DIR / "read-barcodes-fast-inverted.json"
    fast_path.write_text(json.dumps(template, indent=2), encoding="utf-8")
    return fast_path


def decode_image(router: CaptureVisionRouter, image_path: Path, template_name: str) -> list[dict]:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Failed to load image: {image_path}")
    result = router.capture(image, template_name)
    if not result:
        return []
    decoded = result.get_decoded_barcodes_result()
    if not decoded:
        return []
    items = []
    for item in decoded.get_items() or []:
        location = item.get_location()
        points = []
        if location and getattr(location, "points", None):
            points = [{"x": point.x, "y": point.y} for point in location.points]
        items.append(
            {
                "text": item.get_text(),
                "format": item.get_format_string(),
                "confidence": getattr(item, "get_confidence", lambda: None)(),
                "points": points,
            }
        )
    return items


def run_profile(name: str, template_path: Path | None, template_name: str, image_paths: list[Path], truth: dict) -> dict:
    router = CaptureVisionRouter()
    if template_path:
        err, msg = router.init_settings_from_file(str(template_path))
        if err != 0:
            raise RuntimeError(f"Failed to load template {template_path}: {msg}")

    per_image = []
    correct = 0
    total_ms = 0.0
    for image_path in image_paths:
        start = time.perf_counter()
        items = decode_image(router, image_path, template_name)
        elapsed_ms = (time.perf_counter() - start) * 1000
        total_ms += elapsed_ms
        expected = set(truth.get(image_path.name, []))
        found = {item["text"] for item in items}
        ok = bool(expected and expected.issubset(found))
        if ok:
            correct += 1
        per_image.append(
            {
                "file": image_path.name,
                "expected": sorted(expected),
                "found": sorted(found),
                "ok": ok,
                "time_ms": round(elapsed_ms, 2),
                "items": items,
            }
        )
    total = len(image_paths)
    return {
        "profile": name,
        "template_name": template_name,
        "decoded": correct,
        "total": total,
        "decode_rate": round(correct / total * 100, 2) if total else 0,
        "avg_time_ms": round(total_ms / total, 2) if total else 0,
        "per_image": per_image,
    }


def write_html_report(results: list[dict], output_path: Path) -> None:
    baseline = {item["file"]: item for item in results[0]["per_image"]} if results else {}
    recovered_by_profile = {}
    for profile in results[1:]:
        recovered_by_profile[profile["profile"]] = [
            item["file"]
            for item in profile["per_image"]
            if item["ok"] and baseline.get(item["file"]) and not baseline[item["file"]]["ok"]
        ]

    rows = []
    for profile in results:
        for item in profile["per_image"]:
            rows.append(
                f"<tr><td>{profile['profile']}</td><td>{item['file']}</td><td class=\"{'pass' if item['ok'] else 'fail'}\">{'PASS' if item['ok'] else 'FAIL'}</td>"
                f"<td>{', '.join(item['expected'])}</td><td>{', '.join(item['found'])}</td><td>{item['time_ms']}</td></tr>"
            )
    max_time = max((r["avg_time_ms"] for r in results), default=1)
    accuracy_bars = "".join(
        f"<div class=\"bar-row\"><span>{r['profile']}</span><div class=\"bar-track\"><div class=\"bar accuracy\" style=\"width: {r['decode_rate']}%\"></div></div><strong>{r['decode_rate']}%</strong></div>"
        for r in results
    )
    time_bars = "".join(
        f"<div class=\"bar-row\"><span>{r['profile']}</span><div class=\"bar-track\"><div class=\"bar time\" style=\"width: {max(4, r['avg_time_ms'] / max_time * 100):.2f}%\"></div></div><strong>{r['avg_time_ms']} ms</strong></div>"
        for r in results
    )
    summary_cards = "".join(
        f"<section class=\"card\"><h2>{r['profile']}</h2><p class=\"metric\">{r['decoded']}/{r['total']}</p><p>{r['decode_rate']}% decoded, avg {r['avg_time_ms']} ms/image</p></section>"
        for r in results
    )
    recovered_html = "".join(
        f"<p><strong>Recovered by {profile}:</strong> {', '.join(files) if files else 'None'}</p>"
        for profile, files in recovered_by_profile.items()
    )
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>DBR custom template benchmark</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; background: #f7f9fb; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 24px 0; }}
    .card, .chart {{ background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 16px; }}
    .metric {{ font-size: 32px; font-weight: 700; margin: 8px 0; }}
    .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin: 24px 0; }}
    .bar-row {{ display: grid; grid-template-columns: 180px 1fr 96px; gap: 12px; align-items: center; margin: 12px 0; }}
    .bar-track {{ height: 18px; background: #e8edf3; border-radius: 4px; overflow: hidden; }}
    .bar {{ height: 100%; }}
    .accuracy {{ background: #1f8a70; }}
    .time {{ background: #c75000; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 24px; }}
    th, td {{ border: 1px solid #d8dee8; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #eef3f8; }}
    .pass {{ color: #087f5b; }}
    .fail {{ color: #b42318; }}
  </style>
</head>
<body>
  <h1>Dynamsoft Barcode Reader custom template benchmark</h1>
  <div class="cards">{summary_cards}</div>
  <div class="charts">
    <section class="chart"><h2>Decode rate</h2>{accuracy_bars}</section>
    <section class="chart"><h2>Average time per image</h2>{time_bars}</section>
  </div>
  {recovered_html}
  <table>
    <thead><tr><th>Profile</th><th>Image</th><th>Status</th><th>Expected</th><th>Found</th><th>Time ms</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>"""
    output_path.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Dynamsoft DBR preset vs a focused custom template.")
    parser.add_argument("--images", default=str(IMAGE_DIR), help="Directory containing generated test images.")
    parser.add_argument("--truth", default=str(ASSET_DIR / "ground_truth.json"), help="Ground-truth JSON file.")
    parser.add_argument("--output", default=str(REPORT_DIR / "benchmark-results.json"), help="JSON output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    init_license()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fast_path = build_fast_inverted_template()

    image_paths = sorted(Path(args.images).glob("*.png"))
    truth = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    if not image_paths:
        raise RuntimeError(f"No PNG files found in {args.images}. Run generate_test_images.py first.")

    results = [
        run_profile("PT_READ_BARCODES preset", None, EnumPresetTemplate.PT_READ_BARCODES.value, image_paths, truth),
        run_profile("Fast custom template", fast_path, "ReadBarcodes_FastInverted", image_paths, truth),
    ]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    write_html_report(results, REPORT_DIR / "benchmark-report.html")
    cover_src = ASSET_DIR / "low-resolution-glare-barcode-reader.png"
    if cover_src.exists():
        shutil.copy2(cover_src, REPORT_DIR / "cover.png")

    for result in results:
        print(
            f"{result['profile']}: {result['decoded']}/{result['total']} "
            f"({result['decode_rate']}%), avg {result['avg_time_ms']} ms/image"
        )
    if len(results) >= 2:
        baseline = {item["file"]: item for item in results[0]["per_image"]}
        for result in results[1:]:
            optimized = {item["file"]: item for item in result["per_image"]}
            recovered = [
                filename
                for filename, base_item in baseline.items()
                if not base_item["ok"] and optimized.get(filename, {}).get("ok")
            ]
            print(f"Recovered by {result['profile']}: {len(recovered)}")
            for filename in recovered:
                print(f"  - {filename}")
    print(f"Wrote {output_path}")
    print(f"Wrote {REPORT_DIR / 'benchmark-report.html'}")
    print(f"Wrote {fast_path}")


if __name__ == "__main__":
    main()
