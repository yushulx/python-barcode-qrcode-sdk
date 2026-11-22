#!/usr/bin/env python3
"""
DBR template test harness — Python edition.

Interfaces with the Dynamsoft Capture Vision Python SDK to test barcode templates
against image sets. Produces the JSON output schema expected by the optimizer
workflow and `report_template.html`.

Install:
    pip install -r requirements.txt

Usage:
    python main.py --images <dir> --template <file> [--license <key>] [--output <file>]
    python main.py --images <dir> --template <file> --ground-truth <file.json>
    python main.py --images <dir> --template <file> --converted-dir <dir>
    python main.py --dump-default-template <output-file> [--license <key>]

Notes:
    - PDF files are NOT supported by the Python SDK and will be skipped with a warning.
        - avg_time_ms includes Python/SDK call overhead and should be used only for
            relative comparisons inside the same Python session.
    - If the SDK API doesn't match (different version), update the two helper functions
      extract_barcodes() and dump_default_template() — those are the only SDK-specific spots.
    - Use --converted-dir to permanently save HEIC/HEIF images as JPEGs. The results JSON
      will include a "converted_file" field for each converted image, and the HTML report
      will use that path so images display correctly in the browser.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import tempfile
import time

TRIAL_LICENSE = "DLS2eyJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSJ9"
EMBED_SIZE_THRESHOLD = 20 * 1024 * 1024  # 20 MB
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".gif", ".heic", ".heif"}
DEFAULT_TEMPLATE  = "ReadBarcodes_Default"


# ---------------------------------------------------------------------------
# SDK import — provides a clear error if the package isn't installed
# ---------------------------------------------------------------------------

def import_sdk():
    try:
        from dynamsoft_capture_vision_bundle import CaptureVisionRouter, LicenseManager
        return CaptureVisionRouter, LicenseManager
    except ImportError:
        sys.exit(
            "ERROR: dynamsoft-capture-vision-bundle is not installed.\n"
            "Run:   pip install dynamsoft-capture-vision-bundle\n"
            "Or:    pip install -r resources/harness_py/requirements.txt"
        )


# ---------------------------------------------------------------------------
# SDK-specific helpers — update here if your SDK version has different APIs
# ---------------------------------------------------------------------------

def extract_barcodes(captured_result):
    """
    Extract barcode items from a CapturedResult.
    Returns a list of dicts matching the optimizer result schema:
        { format, text, confidence, location: [[x,y], [x,y], [x,y], [x,y]] }
    """
    barcodes = []
    barcode_result = captured_result.get_decoded_barcodes_result()
    if barcode_result is None:
        return barcodes
    for item in barcode_result.get_items():
        loc = item.get_location()
        points = [[p.x, p.y] for p in loc.points] if loc else []
        barcodes.append({
            "format":     item.get_format_string(),
            "text":       item.get_text(),
            "confidence": item.get_confidence(),
            "location":   points,
        })
    return barcodes


def find_bundled_preset_template():
    """
    Locate the DBR-PresetTemplates.json bundled with the installed SDK package.
    Returns the path if found, or None.
    """
    try:
        import dynamsoft_capture_vision_bundle as _pkg
        candidate = os.path.join(os.path.dirname(_pkg.__file__), "Templates", "DBR-PresetTemplates.json")
        if os.path.isfile(candidate):
            return candidate
    except Exception:
        pass
    return None


def dump_default_template(router, output_path):
    """
    Write the SDK's built-in default template JSON to output_path.
    First tries the bundled DBR-PresetTemplates.json (most reliable).
    Falls back to SDK API methods for compatibility.
    Raises RuntimeError if no method works.
    """
    import shutil

    # Preferred: copy the bundled preset file directly (avoids SDK path issues)
    bundled = find_bundled_preset_template()
    if bundled:
        shutil.copy2(bundled, output_path)
        return

    # Fallback: try output_settings_to_string (returns string we write ourselves)
    fn_string = getattr(router, "output_settings_to_string", None)
    if fn_string is not None:
        content = fn_string("")
        if content:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            return

    # Last resort: output_settings_to_file (may silently fail on some platforms)
    fn_file = getattr(router, "output_settings_to_file", None)
    if fn_file is not None:
        fn_file(output_path, "")
        if os.path.isfile(output_path):
            return

    raise RuntimeError(
        "Could not dump default template: bundled DBR-PresetTemplates.json not found "
        "and no working SDK API method available. Check your SDK installation."
    )


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def init_license(LicenseManager, key):
    error_code, error_message = LicenseManager.init_license(key)
    if error_code != 0:
        print(
            f"WARNING: License init returned code {error_code}: {error_message}\n"
            "         Decoding may be limited to a small number of images.",
            file=sys.stderr,
        )


def collect_images(image_dir):
    images = []
    pdf_count = 0
    for root, _, files in os.walk(image_dir):
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext == ".pdf":
                pdf_count += 1
            elif ext in IMAGE_EXTENSIONS:
                images.append(os.path.join(root, f))
    if pdf_count:
        print(
            f"WARNING: {pdf_count} PDF file(s) skipped — PDF is not supported by the "
            "Python SDK.",
            file=sys.stderr,
        )
    return images


def load_ground_truth(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


HEIC_EXTENSIONS = {".heic", ".heif"}


def prepare_image_path(image_path, converted_dir=None):
    """
    If the image is HEIC/HEIF, convert it to a JPEG and return
    (decode_path, converted_basename, cleanup_fn).
    - If converted_dir is given, save permanently as <converted_dir>/<stem>.jpg;
      cleanup_fn is a no-op and the file stays on disk for the report to reference.
    - Otherwise save to a temp file that is deleted after decoding.
    For non-HEIC images returns (image_path, None, no-op).
    Requires pillow + pillow-heif for HEIC support.
    """
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in HEIC_EXTENSIONS:
        return image_path, None, lambda: None

    try:
        from pillow_heif import register_heif_opener
        from PIL import Image
        register_heif_opener()
        img = Image.open(image_path)
        stem = os.path.splitext(os.path.basename(image_path))[0]
        jpg_name = stem + ".jpg"

        if converted_dir:
            os.makedirs(converted_dir, exist_ok=True)
            jpg_path = os.path.join(converted_dir, jpg_name)
            img.save(jpg_path, "JPEG", quality=95)
            return jpg_path, jpg_name, lambda: None
        else:
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.close()
            img.save(tmp.name, "JPEG", quality=95)
            return tmp.name, None, lambda: os.unlink(tmp.name)
    except Exception as exc:
        print(f"WARNING: Could not convert {os.path.basename(image_path)} to JPEG: {exc}",
              file=sys.stderr)
        return image_path, None, lambda: None


def embed_image_data_uri(image_path):
    """Return a base64 data URI string for the given image file."""
    mime, _ = mimetypes.guess_type(image_path)
    if not mime:
        ext = os.path.splitext(image_path)[1].lower()
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".bmp": "image/bmp", ".gif": "image/gif",
                ".tif": "image/tiff", ".tiff": "image/tiff"}.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def run_images(router, images, template_name, ground_truth, converted_dir=None, embed_images=False):
    per_image    = []
    total_decoded = 0

    for image_path in images:
        filename = os.path.basename(image_path)
        decode_path, converted_basename, cleanup = prepare_image_path(image_path, converted_dir)
        t0 = time.perf_counter()
        try:
            captured = router.capture(decode_path, template_name)
            elapsed  = (time.perf_counter() - t0) * 1000
            barcodes = extract_barcodes(captured)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            cleanup()
            per_image.append({
                "file":     filename,
                "time_ms":  round(elapsed, 2),
                "barcodes": [],
                "error":    str(exc),
            })
            continue
        cleanup()

        embed_src = decode_path  # path of the image actually decoded (may be converted JPEG)
        entry = {
            "file":     filename,
            "time_ms":  round(elapsed, 2),
            "barcodes": barcodes,
        }
        if converted_basename:
            entry["converted_file"] = converted_basename
        if embed_images:
            entry["data_uri"] = embed_image_data_uri(embed_src)

        if ground_truth is not None:
            expected = ground_truth.get(filename, [])
            found    = [b["text"] for b in barcodes]
            matched  = all(t in found for t in expected) if expected else bool(barcodes)
            entry["ground_truth_expected"] = expected
            entry["ground_truth_matched"]  = matched

        if barcodes:
            total_decoded += 1
        per_image.append(entry)

    return per_image, total_decoded


def build_result(template_file, image_dir, per_image, total_decoded, ground_truth):
    total   = len(per_image)
    times   = [e["time_ms"] for e in per_image]
    confs   = [b["confidence"] for e in per_image for b in e["barcodes"]]
    n_bars  = sum(len(e["barcodes"]) for e in per_image)

    result = {
        "template_file":       template_file,
        "image_dir":           image_dir,
        "total_images":        total,
        "images_decoded":      total_decoded,
        "total_barcodes_found": n_bars,
        "decode_rate":         round(total_decoded / total, 4) if total else 0,
        "avg_confidence":      round(sum(confs) / len(confs), 2) if confs else 0,
        "avg_time_ms":         round(sum(times) / len(times), 2) if times else 0,
        "total_time_ms":       round(sum(times), 2),
        "per_image":           per_image,
    }

    if ground_truth is not None:
        matched = sum(1 for e in per_image if e.get("ground_truth_matched", False))
        result["ground_truth_match_rate"] = round(matched / total, 4) if total else 0

    return result


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_dump(args, CaptureVisionRouter, LicenseManager):
    init_license(LicenseManager, args.license or TRIAL_LICENSE)
    router = CaptureVisionRouter()
    try:
        dump_default_template(router, args.dump_default_template)
    except RuntimeError as e:
        sys.exit(f"ERROR: {e}")
    print(f"Default template written to: {args.dump_default_template}")


def cmd_run(args, CaptureVisionRouter, LicenseManager):
    # License
    init_license(LicenseManager, args.license or TRIAL_LICENSE)
    router = CaptureVisionRouter()

    # Load template — use provided file, or fall back to bundled preset
    template_path = args.template
    if not template_path:
        template_path = find_bundled_preset_template()
        if template_path:
            print(f"No --template specified; using bundled preset: {template_path}", file=sys.stderr)

    template_label = "(default)"
    if template_path:
        error_code, error_msg = router.init_settings_from_file(template_path)
        if error_code != 0:
            sys.exit(f"ERROR loading template '{template_path}': {error_msg}")
        template_label = template_path

    # Images
    if not os.path.isdir(args.images):
        sys.exit(f"ERROR: Image directory not found: {args.images}")
    images = collect_images(args.images)
    if not images:
        sys.exit(f"ERROR: No supported images found in: {args.images}")

    # Ground truth
    ground_truth = load_ground_truth(args.ground_truth) if args.ground_truth else None

    # Decide whether to embed images as data URIs
    if args.no_embed_images:
        embed_images = False
    elif args.embed_images:
        embed_images = True
    else:
        total_size = sum(os.path.getsize(p) for p in images)
        embed_images = total_size < EMBED_SIZE_THRESHOLD
        if embed_images:
            print(
                f"INFO: Total image size {total_size/1024/1024:.1f} MB < 20 MB — "
                "embedding images in results (use --no-embed-images to disable).",
                file=sys.stderr,
            )

    # Run
    per_image, total_decoded = run_images(
        router, images, DEFAULT_TEMPLATE, ground_truth, args.converted_dir, embed_images
    )
    result = build_result(template_label, args.images, per_image, total_decoded, ground_truth)
    if args.converted_dir:
        result["converted_dir"] = args.converted_dir
    if embed_images:
        result["images_embedded"] = True

    # Output
    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Results written to: {args.output}", file=sys.stderr)
    else:
        print(output_json)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="DBR template test harness — Python edition")
    p.add_argument("--template",     help="Path to template JSON file")
    p.add_argument("--images",       help="Directory of barcode images")
    p.add_argument("--license",      help="Dynamsoft license key (defaults to trial key)")
    p.add_argument("--ground-truth", metavar="FILE",
                   help="JSON mapping filename → expected barcode texts")
    p.add_argument("--output",        help="Write results JSON to this file (default: stdout)")
    p.add_argument("--converted-dir", metavar="DIR",
                   help="Save HEIC/HEIF images as JPEGs in this directory (created if needed). "
                        "Results will include a 'converted_file' field for browser-viewable reports.")
    embed_group = p.add_mutually_exclusive_group()
    embed_group.add_argument("--embed-images", action="store_true",
                   help="Always embed images as base64 data URIs in the results JSON "
                        "(self-contained report, no separate image files needed).")
    embed_group.add_argument("--no-embed-images", action="store_true",
                   help="Never embed images (overrides the automatic <20 MB default).")
    p.add_argument("--dump-default-template", metavar="OUTPUT_FILE",
                   help="Dump the SDK default template JSON and exit")
    args = p.parse_args()

    CaptureVisionRouter, LicenseManager = import_sdk()

    if args.dump_default_template:
        cmd_dump(args, CaptureVisionRouter, LicenseManager)
    elif args.images:
        cmd_run(args, CaptureVisionRouter, LicenseManager)
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
