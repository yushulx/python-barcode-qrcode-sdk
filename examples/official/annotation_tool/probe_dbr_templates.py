import argparse
import json
from pathlib import Path

import cv2

from dynamsoft_barcode_reader_bundle import CaptureVisionRouter, EnumPresetTemplate

from dbr_license import ensure_dbr_license


DEFAULT_TEMPLATE_FILES = [
    "dbr_template.json",
    "dbr_incomplete_qr_template.json",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Try multiple Dynamsoft templates against a single image."
    )
    parser.add_argument("image", help="Path to the image to decode")
    parser.add_argument(
        "--template-file",
        action="append",
        dest="template_files",
        help=(
            "Template JSON file to load. Can be repeated. "
            "Defaults to local dbr_template.json and dbr_incomplete_qr_template.json if present."
        ),
    )
    parser.add_argument(
        "--template-name",
        action="append",
        dest="template_names",
        help="Only run the specified template names from loaded JSON files.",
    )
    parser.add_argument(
        "--skip-preset",
        action="store_true",
        help="Do not try the built-in PT_READ_BARCODES preset first.",
    )
    parser.add_argument(
        "--variant-set",
        choices=["none", "basic"],
        default="none",
        help=(
            "Generate additional image variants before probing templates. "
            "Use 'basic' to try padded, scaled, sharpened, and binarized variants."
        ),
    )
    parser.add_argument(
        "--report-json",
        help="Optional path to write a JSON report of every attempt.",
    )
    parser.add_argument(
        "--stop-on-first-hit",
        action="store_true",
        help="Stop after the first successful decode.",
    )
    return parser.parse_args()


def resolve_template_files(cli_template_files):
    if cli_template_files:
        return [Path(path).resolve() for path in cli_template_files]

    base_dir = Path(__file__).resolve().parent
    paths = []
    for name in DEFAULT_TEMPLATE_FILES:
        candidate = (base_dir / name).resolve()
        if candidate.exists():
            paths.append(candidate)
    return paths


def load_template_names(template_path, selected_names=None):
    with template_path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)

    template_names = [
        item["Name"]
        for item in data.get("CaptureVisionTemplates", [])
        if isinstance(item, dict) and item.get("Name")
    ]

    if not selected_names:
        return template_names

    selected = []
    selected_lookup = set(selected_names)
    for name in template_names:
        if name in selected_lookup:
            selected.append(name)
    return selected


def decode_image(image_path, template_name, template_path=None):
    ensure_dbr_license()
    router = CaptureVisionRouter()

    if template_path is not None:
        err, msg = router.init_settings_from_file(str(template_path))
        if err != 0:
            return [], f"init_settings_from_file failed [{err}]: {msg}"

    try:
        result = router.capture(str(image_path), template_name)
    except Exception as exc:
        return [], str(exc)

    items = []
    if result:
        barcode_result = result.get_decoded_barcodes_result()
        if barcode_result:
            for item in barcode_result.get_items() or []:
                points = []
                location = item.get_location()
                if location and getattr(location, "points", None):
                    points = [(point.x, point.y) for point in location.points]
                items.append(
                    {
                        "text": item.get_text(),
                        "format": item.get_format_string(),
                        "points": points,
                    }
                )

    return items, None


def build_variants(image_path, variant_set):
    variants = [("original", image_path)]
    if variant_set == "none":
        return variants

    source = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if source is None:
        return variants

    variant_dir = Path(__file__).resolve().parent / "_probe_variants" / image_path.stem
    variant_dir.mkdir(parents=True, exist_ok=True)

    def save_variant(name, image):
        path = variant_dir / f"{name}.png"
        cv2.imwrite(str(path), image)
        variants.append((name, path))

    padded = cv2.copyMakeBorder(
        source,
        40,
        40,
        40,
        40,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )
    save_variant("padded_40", padded)

    for scale in (2, 4):
        resized = cv2.resize(source, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        save_variant(f"nearest_{scale}x", resized)

    scale4 = cv2.resize(source, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    blurred = cv2.GaussianBlur(scale4, (3, 3), 0)
    sharpened = cv2.addWeighted(scale4, 1.6, blurred, -0.6, 0)
    save_variant("nearest_4x_sharpen", sharpened)

    gray4 = cv2.cvtColor(scale4, cv2.COLOR_BGR2GRAY)
    _, otsu = cv2.threshold(gray4, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    save_variant("nearest_4x_otsu", otsu)
    save_variant("nearest_4x_otsu_inverted", cv2.bitwise_not(otsu))

    adaptive = cv2.adaptiveThreshold(
        gray4,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
    )
    save_variant("nearest_4x_adaptive", adaptive)
    save_variant("nearest_4x_adaptive_inverted", cv2.bitwise_not(adaptive))

    padded_gray = cv2.cvtColor(padded, cv2.COLOR_BGR2GRAY)
    padded_otsu = cv2.threshold(padded_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    save_variant("padded_40_otsu", padded_otsu)

    return variants


def print_result(label, items, error):
    print(f"=== {label} ===")
    if error:
        print(f"ERROR: {error}")
        return

    if not items:
        print("NO_RESULT")
        return

    print(f"HITS: {len(items)}")
    for index, item in enumerate(items, start=1):
        print(f"[{index}] {item['format']} :: {item['text']}")
        if item["points"]:
            print(f"    points={item['points']}")


def append_report(report, variant_name, template_label, template_name, template_path, items, error):
    report.append(
        {
            "variant": variant_name,
            "template_label": template_label,
            "template_name": template_name,
            "template_path": str(template_path) if template_path else None,
            "error": error,
            "items": items,
        }
    )


def main():
    args = parse_args()
    image_path = Path(args.image).resolve()
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")

    template_files = resolve_template_files(args.template_files)
    variants = build_variants(image_path, args.variant_set)
    report = []

    for variant_name, variant_path in variants:
        if not args.skip_preset:
            items, error = decode_image(
                variant_path,
                EnumPresetTemplate.PT_READ_BARCODES.value,
            )
            label = f"{variant_name} :: preset: PT_READ_BARCODES"
            print_result(label, items, error)
            append_report(
                report,
                variant_name,
                label,
                EnumPresetTemplate.PT_READ_BARCODES.value,
                None,
                items,
                error,
            )
            if args.stop_on_first_hit and items:
                break

        if args.stop_on_first_hit and report and report[-1]["items"]:
            break

        for template_file in template_files:
            names = load_template_names(template_file, args.template_names)
            if not names:
                print(f"=== {variant_name} :: file: {template_file.name} ===")
                print("NO_TEMPLATE_NAMES")
                continue

            for template_name in names:
                items, error = decode_image(variant_path, template_name, template_file)
                label = f"{variant_name} :: {template_file.name} :: {template_name}"
                print_result(label, items, error)
                append_report(
                    report,
                    variant_name,
                    label,
                    template_name,
                    template_file,
                    items,
                    error,
                )
                if args.stop_on_first_hit and items:
                    break

            if args.stop_on_first_hit and report and report[-1]["items"]:
                break

        if args.stop_on_first_hit and report and report[-1]["items"]:
            break

    if args.report_json:
        report_path = Path(args.report_json).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as stream:
            json.dump(
                {
                    "image": str(image_path),
                    "variant_set": args.variant_set,
                    "attempts": report,
                },
                stream,
                indent=2,
            )
        print(f"REPORT_JSON: {report_path}")


if __name__ == "__main__":
    main()