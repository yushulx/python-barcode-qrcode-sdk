import argparse
import json
from pathlib import Path

import cv2

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


def decode(image_path, template_file=None, template_name=None):
    ensure_dbr_license()
    router = CaptureVisionRouter()
    if template_file:
        err, msg = router.init_settings_from_file(str(template_file))
        if err != 0:
            print(f"[DBR] Template load failed ({err}): {msg}")

    cv_img = cv2.imread(str(image_path))
    if cv_img is None:
        raise RuntimeError(f"Failed to load image with OpenCV: {image_path}")

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
    items = decode(image_path, template_file, template_name)

    if args.json:
        print(
            json.dumps(
                {
                    "image": str(image_path),
                    "template_file": str(template_file) if template_file else None,
                    "template_name": template_name,
                    "items": items,
                },
                indent=2,
            )
        )
        return

    print(f"image: {image_path}")
    print(f"template_file: {template_file if template_file else 'builtin'}")
    print(f"template_name: {template_name}")
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