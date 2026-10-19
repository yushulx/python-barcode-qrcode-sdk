import argparse
import json
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

try:
    import zxingcpp
except ImportError:
    zxingcpp = None

try:
    from dynamsoft_capture_vision_bundle import EnumPresetTemplate
except ImportError:
    from dynamsoft_barcode_reader_bundle import EnumPresetTemplate

from validate_dbr_template import decode as dbr_decode


DEFAULT_ANGLES = [-22, -18, -14, -10, -6, 0]
DEFAULT_SCALES = [4, 8]


def parse_int_list(value):
    try:
        return [int(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected a comma-separated integer list, got: {value}") from exc


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Recover hard low-light or tilted QR images by searching auto-generated ROIs, "
            "deskew angles, scales, and preprocessing variants before optionally re-validating "
            "the best candidates with DBR."
        )
    )
    parser.add_argument("image", help="Path to the difficult image to recover")
    parser.add_argument(
        "--output-dir",
        help="Directory to write recovered candidate images and JSON reports. Defaults to <image-stem>_recover.",
    )
    parser.add_argument(
        "--angles",
        type=parse_int_list,
        default=DEFAULT_ANGLES,
        help="Comma-separated deskew angles to try. Default: -22,-18,-14,-10,-6,0",
    )
    parser.add_argument(
        "--scales",
        type=parse_int_list,
        default=DEFAULT_SCALES,
        help="Comma-separated scale factors to try. Default: 4,8",
    )
    parser.add_argument(
        "--stop-after-roi-hits",
        type=int,
        default=3,
        help=(
            "Stop scanning a specific ROI once the same decoded text has been recovered this many times. "
            "Use 0 to disable early stopping. Default: 3"
        ),
    )
    parser.add_argument(
        "--verify-dbr",
        action="store_true",
        help="Run the best recovered candidate images back through DBR for confirmation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full JSON report instead of a concise human-readable summary.",
    )
    return parser.parse_args()


def rotate_bound(image, angle):
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])

    new_width = int((height * sin) + (width * cos))
    new_height = int((height * cos) + (width * sin))

    matrix[0, 2] += (new_width / 2) - center[0]
    matrix[1, 2] += (new_height / 2) - center[1]
    return cv2.warpAffine(
        image,
        matrix,
        (new_width, new_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def auto_rois(image):
    height, width = image.shape[:2]

    roi_specs = {
        "left_focus": (0, 0, int(width * 0.30), int(height * 0.90)),
        "left_wide": (0, 0, int(width * 0.38), height),
        "right_focus": (int(width * 0.68), 0, width, int(height * 0.85)),
        "right_wide": (int(width * 0.60), 0, width, height),
    }

    rois = {}
    for name, (x1, y1, x2, y2) in roi_specs.items():
        x1 = max(0, min(width, x1))
        y1 = max(0, min(height, y1))
        x2 = max(0, min(width, x2))
        y2 = max(0, min(height, y2))
        if x2 <= x1 or y2 <= y1:
            continue
        rois[name] = {
            "box": [x1, y1, x2, y2],
            "image": image[y1:y2, x1:x2],
        }
    return rois


def build_variants(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8)).apply(gray)
    denoise = cv2.fastNlMeansDenoising(clahe, None, 10, 7, 21)
    blur = cv2.GaussianBlur(denoise, (3, 3), 0)
    sharpen = cv2.addWeighted(denoise, 1.8, blur, -0.8, 0)
    otsu = cv2.threshold(sharpen, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    adaptive = cv2.adaptiveThreshold(
        denoise,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
    )
    return {
        "clahe": clahe,
        "denoise": denoise,
        "sharpen": sharpen,
        "otsu": otsu,
    }


def opencv_hits(qr_detector, candidate):
    hits = []

    try:
        text, points, _ = qr_detector.detectAndDecode(candidate)
        if text:
            hits.append(
                {
                    "engine": "opencv-detectAndDecode",
                    "format": "QR_CODE",
                    "text": text,
                    "points": None if points is None else np.asarray(points).tolist(),
                }
            )
    except Exception:
        pass

    try:
        retval, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(candidate)
        if retval:
            points_list = None if points is None else np.asarray(points).tolist()
            for index, text in enumerate(decoded_info):
                if not text:
                    continue
                hits.append(
                    {
                        "engine": "opencv-detectAndDecodeMulti",
                        "format": "QR_CODE",
                        "text": text,
                        "points": None if points_list is None else points_list[index],
                    }
                )
    except Exception:
        pass

    return hits


def zxing_hits(candidate):
    if zxingcpp is None:
        return []

    hits = []
    try:
        for item in zxingcpp.read_barcodes(candidate):
            if not item.text:
                continue
            position = None
            if hasattr(item, "position"):
                position = {
                    "top_left": [item.position.top_left.x, item.position.top_left.y],
                    "top_right": [item.position.top_right.x, item.position.top_right.y],
                    "bottom_right": [item.position.bottom_right.x, item.position.bottom_right.y],
                    "bottom_left": [item.position.bottom_left.x, item.position.bottom_left.y],
                }
            hits.append(
                {
                    "engine": "zxingcpp",
                    "format": item.format.name,
                    "text": item.text,
                    "points": position,
                }
            )
    except Exception:
        pass

    return hits


def verify_with_dbr(image_paths):
    template_name = EnumPresetTemplate.PT_READ_BARCODES.value
    validations = []
    for image_path in image_paths:
        items, attempt = dbr_decode(image_path, template_name=template_name, fallback_profile="none")
        validations.append(
            {
                "image": str(image_path),
                "attempt": attempt,
                "items": items,
            }
        )
    return validations


def build_summary(hits):
    grouped = defaultdict(
        lambda: {
            "text": None,
            "formats": set(),
            "engines": set(),
            "rois": set(),
            "angles": set(),
            "scales": set(),
            "variants": set(),
            "hit_count": 0,
            "saved_images": [],
        }
    )

    for hit in hits:
        entry = grouped[hit["text"]]
        entry["text"] = hit["text"]
        entry["formats"].add(hit["format"])
        entry["engines"].add(hit["engine"])
        entry["rois"].add(hit["roi"])
        entry["angles"].add(hit["angle"])
        entry["scales"].add(hit["scale"])
        entry["variants"].add(hit["variant"])
        entry["hit_count"] += 1
        if hit["saved_image"] not in entry["saved_images"]:
            entry["saved_images"].append(hit["saved_image"])

    summaries = []
    for text, entry in grouped.items():
        summaries.append(
            {
                "text": text,
                "formats": sorted(entry["formats"]),
                "engines": sorted(entry["engines"]),
                "rois": sorted(entry["rois"]),
                "angles": sorted(entry["angles"]),
                "scales": sorted(entry["scales"]),
                "variants": sorted(entry["variants"]),
                "hit_count": entry["hit_count"],
                "saved_images": entry["saved_images"],
            }
        )

    summaries.sort(key=lambda item: (-item["hit_count"], -len(item["engines"]), item["text"]))
    return summaries


def main():
    args = parse_args()
    image_path = Path(args.image).resolve()
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")

    output_dir = Path(args.output_dir).resolve() if args.output_dir else (Path.cwd() / f"{image_path.stem}_recover")
    hits_dir = output_dir / "hits"
    hits_dir.mkdir(parents=True, exist_ok=True)

    source = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if source is None:
        raise SystemExit(f"Failed to load image with OpenCV: {image_path}")

    qr_detector = cv2.QRCodeDetector()
    hits = []
    candidate_index = 0

    for roi_name, roi_data in auto_rois(source).items():
        roi_image = roi_data["image"]
        roi_text_hits = defaultdict(int)
        roi_complete = False
        for angle in args.angles:
            rotated = rotate_bound(roi_image, angle) if angle else roi_image
            for scale in args.scales:
                enlarged = cv2.resize(rotated, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                for variant_name, variant in build_variants(enlarged).items():
                    candidate_hits = opencv_hits(qr_detector, variant) + zxing_hits(variant)
                    if not candidate_hits:
                        continue

                    save_path = hits_dir / f"{candidate_index:03d}_{roi_name}_a{angle}_s{scale}_{variant_name}.png"
                    cv2.imwrite(str(save_path), variant)
                    candidate_index += 1

                    unique_texts = set()
                    for hit in candidate_hits:
                        unique_texts.add(hit["text"])
                        hits.append(
                            {
                                "text": hit["text"],
                                "format": hit["format"],
                                "engine": hit["engine"],
                                "points": hit["points"],
                                "roi": roi_name,
                                "roi_box": roi_data["box"],
                                "angle": angle,
                                "scale": scale,
                                "variant": variant_name,
                                "saved_image": str(save_path),
                            }
                        )

                    if args.stop_after_roi_hits > 0:
                        for text in unique_texts:
                            roi_text_hits[text] += 1
                            if roi_text_hits[text] >= args.stop_after_roi_hits:
                                roi_complete = True
                                break
                if roi_complete:
                    break
            if roi_complete:
                break

    summaries = build_summary(hits)
    report = {
        "image": str(image_path),
        "output_dir": str(output_dir),
        "zxingcpp_available": zxingcpp is not None,
        "angles": args.angles,
        "scales": args.scales,
        "hits": hits,
        "summaries": summaries,
    }

    if args.verify_dbr:
        for summary in report["summaries"]:
            representative_images = [Path(path) for path in summary["saved_images"][:3]]
            summary["dbr_validation"] = verify_with_dbr(representative_images)

    for summary in report["summaries"]:
        summary["manual_validation_commands"] = [
            f'python template-optimizer/tools/validate_dbr_template.py "{path}" --json'
            for path in summary["saved_images"][:3]
        ]

    report_path = output_dir / "search_results.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"image: {image_path}")
    print(f"report_json: {report_path}")
    print(f"hit_images_dir: {hits_dir}")
    if not report["summaries"]:
        print("NO_RESULT")
        return

    print(f"CANDIDATE_TEXTS: {len(report['summaries'])}")
    for index, summary in enumerate(report["summaries"], start=1):
        print(f"[{index}] text={summary['text']}")
        print(f"    formats={summary['formats']}")
        print(f"    engines={summary['engines']}")
        print(f"    hit_count={summary['hit_count']}")
        print(f"    rois={summary['rois']}")
        print(f"    angles={summary['angles']}")
        print(f"    scales={summary['scales']}")
        print(f"    variants={summary['variants']}")
        if summary.get("dbr_validation"):
            successful = [item for item in summary["dbr_validation"] if item["items"]]
            print(f"    dbr_hits={len(successful)}")
        print(f"    first_candidate={summary['saved_images'][0]}")
        print(f"    manual_validate={summary['manual_validation_commands'][0]}")


if __name__ == "__main__":
    main()