import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from dynamsoft_barcode_reader_bundle import CaptureVisionRouter, EnumPresetTemplate

from dbr_license import ensure_dbr_license

def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate one DBR template against one image using CaptureVisionRouter.capture()."
    )
    parser.add_argument("image", help="Path to the image to decode")
    parser.add_argument(
        "--template-file",
        "--template-fie",
        "--template",
        dest="template_file",
        help="Path to a DBR JSON template file. Omit to use the built-in PT_READ_BARCODES preset.",
    )
    parser.add_argument(
        "--template-name",
        help="Template name inside the JSON file. If omitted, the first CaptureVisionTemplate name is used.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the decode result as JSON.",
    )
    parser.add_argument(
        "--fallback-profile",
        choices=["none", "context-retry"],
        default="none",
        help=(
            "Retry a small prioritized set of app-level image variants when the first decode fails. "
            "'context-retry' favors context expansion and simple resampling/binarization retries."
        ),
    )
    return parser.parse_args()


def resolve_template_name(template_file, cli_template_name):
    if cli_template_name:
        return cli_template_name

    if not template_file:
        return EnumPresetTemplate.PT_READ_BARCODES.value

    with Path(template_file).open("r", encoding="utf-8") as stream:
        data = json.load(stream)

    templates = data.get("CaptureVisionTemplates") or []
    if not templates:
        return EnumPresetTemplate.PT_READ_BARCODES.value
    return templates[0]["Name"]


def preprocess_image(cv_img, pad):
    return cv2.copyMakeBorder(
        cv_img,
        pad,
        pad,
        pad,
        pad,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )


def build_fallback_attempts(cv_img, fallback_profile="none"):
    attempts = [("original", cv_img)]
    if fallback_profile == "none":
        return attempts

    def add_attempt(name, image):
        for existing_name, _ in attempts:
            if existing_name == name:
                return
        attempts.append((name, image))

    for extra_pad in (16, 24, 40):
        add_attempt(f"padded_{extra_pad}", preprocess_image(cv_img, extra_pad))

    base = preprocess_image(cv_img, 16)
    nearest_2x = cv2.resize(base, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    add_attempt("nearest_2x", nearest_2x)

    nearest_4x = cv2.resize(base, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    add_attempt("nearest_4x", nearest_4x)

    gray4 = cv2.cvtColor(nearest_4x, cv2.COLOR_BGR2GRAY)
    otsu = cv2.threshold(gray4, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    add_attempt("nearest_4x_otsu", otsu)
    add_attempt("nearest_4x_otsu_inverted", cv2.bitwise_not(otsu))

    adaptive = cv2.adaptiveThreshold(
        gray4,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
    )
    add_attempt("nearest_4x_adaptive", adaptive)
    add_attempt("nearest_4x_adaptive_inverted", cv2.bitwise_not(adaptive))

    return attempts


def decode_with_router(router, cv_img, template_name):
    result = router.capture(cv_img, template_name)

    items = []
    if result:
        barcode_result = result.get_decoded_barcodes_result()
        if barcode_result:
            for item in barcode_result.get_items() or []:
                location = item.get_location()
                points = []
                if location and getattr(location, "points", None):
                    points = [(point.x, point.y) for point in location.points]
                items.append(
                    {
                        "text": item.get_text(),
                        "format": item.get_format_string(),
                        "points": points,
                    }
                )
    return items


def decode(image_path, template_file=None, template_name=None, fallback_profile="none"):
    ensure_dbr_license()
    router = CaptureVisionRouter()
    if template_file:
        err, msg = router.init_settings_from_file(str(template_file))
        if err != 0:
            print(f"[DBR] Template load failed ({err}): {msg}")

    cv_img = cv2.imread(str(image_path))
    if cv_img is None:
        raise RuntimeError(f"Failed to load image with OpenCV: {image_path}")

    attempts = build_fallback_attempts(cv_img, fallback_profile)
    best_items = []
    best_attempt = attempts[0][0]

    for attempt_name, attempt_image in attempts:
        if isinstance(attempt_image, np.ndarray) and attempt_image.ndim == 2:
            attempt_image = cv2.cvtColor(attempt_image, cv2.COLOR_GRAY2BGR)

        items = decode_with_router(router, attempt_image, template_name)
        if items:
            return items, attempt_name

        if not best_items:
            best_attempt = attempt_name

    return best_items, best_attempt


def main():
    args = parse_args()
    image_path = Path(args.image).resolve()
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")

    template_file = None
    if args.template_file:
        template_file = Path(args.template_file).resolve()
        if not template_file.exists():
            raise SystemExit(f"Template not found: {template_file}")

    template_name = resolve_template_name(template_file, args.template_name)
    items, attempt_name = decode(
        image_path,
        template_file,
        template_name,
        args.fallback_profile,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "image": str(image_path),
                    "template_file": str(template_file) if template_file else None,
                    "template_name": template_name,
                    "fallback_profile": args.fallback_profile,
                    "attempt": attempt_name,
                    "items": items,
                },
                indent=2,
            )
        )
        return

    print(f"image: {image_path}")
    print(f"template_file: {template_file if template_file else 'builtin'}")
    print(f"template_name: {template_name}")
    print(f"fallback_profile: {args.fallback_profile}")
    print(f"attempt: {attempt_name}")
    if not items:
        print("NO_RESULT")
        return

    print(f"HITS: {len(items)}")
    for index, item in enumerate(items, start=1):
        print(f"[{index}] {item['format']} :: {item['text']}")
        if item["points"]:
            print(f"    points={item['points']}")


if __name__ == "__main__":
    main()