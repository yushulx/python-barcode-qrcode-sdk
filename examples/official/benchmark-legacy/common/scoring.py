"""Python port of the original browser benchmark's scoring rules (src/utils.ts).

Used so a fresh Dynamsoft run can be scored exactly like the published 2021
numbers. No dependency on the Vue app: it reads the same `results.zip` ground
truth / detection result JSON files.

Rules (verbatim from utils.ts):
  calculateEngineStatistics:
    accuracy  = totalBarcodesCorrectlyDetected / totalBarcodes * 100
    precision = (totalBarcodesDetected - totalBarcodesMisDetected) / totalBarcodesDetected * 100
    averageTime = totalElapsedTime / detectedFiles
  calculateDetectionStatistics:
    for each detection, find the first ground truth whose axis-aligned
    bounding-box overlap ratio > 0.20; if GT has text, compare cleaned text
    (correct / misdetected), otherwise count as correct. No overlap -> ignored.
"""
from __future__ import annotations

import json
from typing import Any


def rect_from_points(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def overlapping_percent(a: tuple[float, float, float, float],
                        b: tuple[float, float, float, float]) -> float:
    """intersection area / smaller rect area (utils.ts overlappingPercent)."""
    left, right = (a, b) if a[0] < b[0] else (b, a)
    upper, lower = (a, b) if a[1] < b[1] else (b, a)
    if left[2] <= right[0] or upper[3] <= lower[1]:
        return 0.0
    overlapped_x = min(left[2], right[2]) - right[0]
    overlapped_y = min(upper[3], lower[3]) - lower[1]
    if overlapped_x <= 0 or overlapped_y <= 0:
        return 0.0
    overlapped_area = overlapped_x * overlapped_y
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    smaller = min(area_a, area_b)
    return overlapped_area / smaller if smaller else 0.0


def clean_text(value: str) -> str:
    return (value.replace("\u001d", "").replace("{GS}", "")
            .replace("\r", "").replace("\n", "").replace("\t", ""))


def text_correct(gt: dict[str, Any], result: dict[str, Any]) -> bool:
    if gt.get("value_attrib", {}).get("Mode") == "binary":
        # Not used by these two datasets; kept for completeness.
        from difflib import SequenceMatcher
        a, b = gt.get("text", ""), result.get("barcodeBytes", "")
        return SequenceMatcher(None, a, b).ratio() >= 0.85
    gt_text = clean_text(gt.get("text", ""))
    out = clean_text(result.get("barcodeText", ""))
    fmt = str(result.get("barcodeFormat", "")).lower()
    gt_type = str(gt.get("attrib", {}).get("Type", "")).lower()
    if "upc" in fmt and "ean" in gt_type and out != gt_text:
        out = "0" + out
    if "ean" in fmt and "upc" in gt_type and out != gt_text:
        out = out[1:]
    return gt_text == out


def gt_points(gt: dict[str, Any]) -> list[tuple[float, float]]:
    return [(float(gt[f"x{i}"]), float(gt[f"y{i}"])) for i in range(1, 5)]


def result_points(r: dict[str, Any]) -> list[tuple[float, float]]:
    return [(float(r[f"x{i}"]), float(r[f"y{i}"])) for i in range(1, 5)]


def detection_statistics(results: list[dict[str, Any]],
                         ground_truth: list[dict[str, Any]]) -> dict[str, int]:
    correct = misdetected = 0
    gt_rects = [rect_from_points(gt_points(g)) for g in ground_truth]
    for r in results:
        r_rect = rect_from_points(result_points(r))
        for g, g_rect in zip(ground_truth, gt_rects):
            if g.get("hasLocation") is False:
                percent = 1.0
            else:
                percent = overlapping_percent(r_rect, g_rect)
            if percent > 0.20:
                if g.get("text"):
                    if text_correct(g, r):
                        correct += 1
                    else:
                        misdetected += 1
                else:
                    correct += 1
                break
    return {"groundTruth": len(ground_truth), "detected": len(results),
            "misdetected": misdetected, "correct": correct}


def engine_statistics(manifest_images: list[str],
                      ground_truth_by_image: dict[str, list[dict[str, Any]]],
                      detection_by_image: dict[str, dict[str, Any]],
                      category: str | None = None) -> dict[str, Any]:
    total_barcodes = correct_all = misdetected_all = detected_all = elapsed_all = 0
    files_with_results = detected_files = correct_files = 0
    for image in manifest_images:
        if category and image.split("/")[0] != category:
            continue
        key = image.rsplit(".", 1)[0]
        gt = ground_truth_by_image.get(key, [])
        det = detection_by_image.get(key)
        if det is not None:
            results = det.get("results", [])
            elapsed_all += float(det.get("elapsedTime", 0) or 0)
            detected_files += 1
            if results:
                files_with_results += 1
            st = detection_statistics(results, gt)
            correct_all += st["correct"]
            misdetected_all += st["misdetected"]
            detected_all += len(results)
            if gt:
                if st["correct"] == st["groundTruth"]:
                    correct_files += 1
            elif results:
                correct_files += 1
        total_barcodes += len(gt)
    accuracy = round(correct_all / total_barcodes * 100, 2) if total_barcodes else 0.0
    precision = round((detected_all - misdetected_all) / detected_all * 100, 2) if detected_all else 100.0
    return {
        "accuracy": accuracy,
        "precision": precision,
        "totalBarcodes": total_barcodes,
        "correct": correct_all,
        "misdetected": misdetected_all,
        "detected": detected_all,
        "detectedFilesRate": round(files_with_results / len(manifest_images) * 100, 2),
        "averageTime": round(elapsed_all / detected_files, 2) if detected_files else 0.0,
    }


def load_results_zip(zip_path: str, engine: str = "Dynamsoft"):
    """Return (ground_truth_by_image, detection_by_image) keyed by filename w/o ext."""
    import zipfile
    gt_map: dict[str, list[dict[str, Any]]] = {}
    det_map: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if name.endswith("/"):
                continue
            stem = name.rsplit(".", 1)[0]
            if name.lower().endswith(".txt"):
                try:
                    gt_map[stem] = json.loads(z.read(name))
                except Exception:
                    gt_map[stem] = []
            elif name.lower().endswith(".json") and name.endswith(f"-{engine}.json"):
                det_map[stem[: -(len(engine) + 1)]] = json.loads(z.read(name))
    return gt_map, det_map
