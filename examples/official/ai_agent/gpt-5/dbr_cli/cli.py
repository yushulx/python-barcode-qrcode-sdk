import argparse
import sys
from pathlib import Path
from typing import List

from .scanner import DynamsoftScanner, iter_image_files, results_to_text, results_to_json


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Command-line Dynamsoft Barcode Scanner")
    p.add_argument("paths", nargs="*", help="Image files or directories to scan")
    p.add_argument("-r", "--recursive", action="store_true", help="Recurse into directories")
    p.add_argument("-l", "--license", help="License key (or set DBR_LICENSE env var)")
    p.add_argument("-f", "--format", choices=["text", "json"], default="text", help="Output format")
    p.add_argument("--fail-on-empty", action="store_true", help="Exit with code 2 if no barcodes found")
    p.add_argument("--version", action="version", version="dbr-cli 0.1.0")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    ns = parse_args(argv or sys.argv[1:])

    if not ns.paths:
        print("No input paths provided. Use --help for usage.", file=sys.stderr)
        return 1

    try:
        scanner = DynamsoftScanner(ns.license)
    except Exception as e:
        print(f"Failed to initialize scanner: {e}", file=sys.stderr)
        return 1

    all_results = []
    for img_path in iter_image_files(ns.paths, ns.recursive):
        try:
            res = scanner.scan_file(img_path)
            all_results.extend(res)
        except Exception as e:
            print(f"Error scanning {img_path}: {e}", file=sys.stderr)

    if ns.format == "json":
        print(results_to_json(all_results))
    else:
        print(results_to_text(all_results))

    if ns.fail_on_empty and not all_results:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
