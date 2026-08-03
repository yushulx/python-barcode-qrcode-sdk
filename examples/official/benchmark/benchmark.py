#!/usr/bin/env python3
"""Auditable Python benchmark for zxing-cpp and Dynamsoft Barcode Reader."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cv2

PROTOCOL = "protocol-v1"
DEFAULT_LICENSE = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="

ZXING_SUPPORTED = {
    "AZTEC", "CODE_128", "GS1_128", "CODE_39", "DATA_MATRIX", "EAN_13",
    "EAN_8", "EAN_2", "ITF", "PDF_417", "QR_CODE", "UPC_A", "UPC_E",
}
DBR_SUPPORTED = {
    "AZTEC", "CODE_128", "GS1_128", "CODE_39", "DATA_MATRIX", "EAN_13",
    "EAN_8", "EAN_2", "ITF", "IATA_2_OF_5", "USPS_INTELLIGENT_MAIL",
    "JAPAN_POST", "KIX", "PDF_417", "POSTNET", "QR_CODE", "ROYAL_MAIL",
    "UPC_A", "UPC_E",
}


def canonical_format(value: str) -> str:
    key = "".join(ch for ch in value.upper() if ch.isalnum())
    mapping = {
        "AZTEC": "AZTEC", "C128": "CODE_128", "CODE128": "CODE_128",
        "UCC128": "GS1_128", "GS1128": "GS1_128",
        "C39": "CODE_39", "CODE39": "CODE_39", "CODE39EXTENDED": "CODE_39",
        "DATAMATRIX": "DATA_MATRIX", "EAN13": "EAN_13", "EAN8": "EAN_8",
        "2DIGIT": "EAN_2", "EAN2": "EAN_2",
        "I2O5": "ITF", "ITF": "ITF", "INTERLEAVED2OF5": "ITF",
        "IATA25": "IATA_2_OF_5", "INTELLIGENTMAIL": "USPS_INTELLIGENT_MAIL",
        "JAPANPOST": "JAPAN_POST", "KIX": "KIX", "PDF417": "PDF_417",
        "POSTNET": "POSTNET", "QR": "QR_CODE", "QRCODE": "QR_CODE",
        "ROYALMAILCODE": "ROYAL_MAIL", "UPCA": "UPC_A", "UPCS": "UPC_A",
        "UPCE": "UPC_E", "1D": "GENERIC_1D", "GENERIC1D": "GENERIC_1D",
        "UNKNOWN": "UNKNOWN", "1": "UNKNOWN",
    }
    return mapping.get(key, key)


def normalized_payload(fmt: str, payload: str) -> str:
    fmt = canonical_format(fmt)
    if fmt == "UPC_A" and len(payload) == 13 and payload.startswith("0"):
        return payload[1:]
    return payload


def valid_gtin(value: str) -> bool:
    if not value.isdigit() or len(value) < 2:
        return False
    total = 0
    weight_three = True
    for ch in reversed(value[:-1]):
        total += int(ch) * (3 if weight_three else 1)
        weight_three = not weight_three
    return (10 - (total % 10)) % 10 == int(value[-1])


def is_payload_valid(fmt: str, payload: str) -> bool:
    fmt = canonical_format(fmt)
    if not payload:
        return False
    if fmt == "EAN_13":
        return len(payload) == 13 and valid_gtin(payload)
    if fmt == "EAN_8":
        return len(payload) == 8 and valid_gtin(payload)
    if fmt == "EAN_2":
        return len(payload) == 2 and payload.isdigit()
    if fmt == "UPC_A":
        value = normalized_payload(fmt, payload)
        return len(value) == 12 and valid_gtin(value)
    return True


def is_specific_barber_format(fmt: str) -> bool:
    fmt = canonical_format(fmt)
    return bool(fmt) and fmt not in {"GENERIC_1D", "UNKNOWN"}


def is_supported(decoder: str, fmt: str) -> bool:
    supported = ZXING_SUPPORTED if decoder == "zxing-python" else DBR_SUPPORTED
    return canonical_format(fmt) in supported


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def probe_image(path: Path) -> tuple[int, int]:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"could not load image: {path}")
    height, width = image.shape[:2]
    return width, height


def audit(args: argparse.Namespace) -> int:
    image_root = args.images.resolve()
    annotation_root = args.annotations.resolve()
    if not image_root.is_dir():
        raise SystemExit(f"image root is not a directory: {image_root}")
    if not annotation_root.is_dir():
        raise SystemExit(f"annotation root is not a directory: {annotation_root}")

    image_index: dict[str, Path] = {}
    source_images = 0
    for path in sorted(p for p in image_root.rglob("*") if p.is_file()):
        rel = path.relative_to(image_root)
        image_index[str(rel).replace("\\", "/").lower()] = rel
        image_index[path.name.lower()] = rel
        source_images += 1

    summary = Counter()
    source_files: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    referenced: set[str] = set()

    json_files = sorted(p for p in annotation_root.rglob("*.json") if p.is_file())
    summary["annotation_files"] = len(json_files)
    for source in json_files:
        print(f"Auditing {source.name}...", file=sys.stderr, flush=True)
        source_relative = str(source.relative_to(annotation_root)).replace("\\", "/")
        source_files.append({
            "relative_path": source_relative,
            "sha256": sha256_file(source),
            "bytes": source.stat().st_size,
        })
        doc = json.loads(source.read_text(encoding="utf-8"))
        metadata = doc.get("_via_img_metadata")
        if not isinstance(metadata, dict):
            raise SystemExit(f"missing _via_img_metadata: {source}")
        for _, item in sorted(metadata.items()):
            filename = item.get("filename", "")
            found = image_index.get(filename.lower())
            record: dict[str, Any] = {
                "relative_path": filename,
                "annotation_file": source_relative,
                "image_sha256": "",
                "width": 0,
                "height": 0,
                "ground_truth": [],
            }
            if found is None:
                summary["missing_images"] += 1
            else:
                record["relative_path"] = str(found).replace("\\", "/")
                referenced.add(record["relative_path"].lower())
                absolute = image_root / found
                record["image_sha256"] = sha256_file(absolute)
                try:
                    record["width"], record["height"] = probe_image(absolute)
                except ValueError:
                    summary["invalid_annotations"] += 1
            record["sample_id"] = "sha256:" + sha256_bytes(
                f"{source_relative}\0{filename}\0{record['image_sha256']}".encode("utf-8")
            )

            for region_index, region in enumerate(item.get("regions", [])):
                attrs = region.get("region_attributes", {})
                shape = region.get("shape_attributes", {})
                fmt = canonical_format(str(attrs.get("Type", "")))
                text = str(attrs.get("String", ""))
                ppe = attrs.get("PPE")
                xs = shape.get("all_points_x", [])
                ys = shape.get("all_points_y", [])
                polygon = [[int(x), int(y)] for x, y in zip(xs, ys)] if len(xs) == len(ys) else []
                gt = {
                    "annotation_id": f"{record['sample_id']}:{region_index}",
                    "format": fmt,
                    "text": text,
                    "polygon": polygon,
                    "ppe": ppe if isinstance(ppe, (int, float)) else None,
                    "decode_eligible": False,
                    "exclusion_reason": "",
                }
                if found is None:
                    gt["exclusion_reason"] = "missing_image"
                elif not is_specific_barber_format(fmt):
                    gt["exclusion_reason"] = "missing_reliable_payload"
                elif not text or text == "-1" or (isinstance(ppe, (int, float)) and ppe < 0):
                    gt["exclusion_reason"] = "missing_reliable_payload"
                elif not is_payload_valid(fmt, text):
                    gt["exclusion_reason"] = "invalid_payload"
                else:
                    gt["decode_eligible"] = True
                summary["annotations"] += 1
                if gt["decode_eligible"]:
                    summary["eligible_annotations"] += 1
                elif gt["exclusion_reason"] == "missing_reliable_payload":
                    summary["missing_payload_or_generic"] += 1
                else:
                    summary["invalid_annotations"] += 1
                record["ground_truth"].append(gt)
            records.append(record)

    records.sort(key=lambda r: (r["relative_path"], r["annotation_file"], r["sample_id"]))
    unique_records: list[dict[str, Any]] = []
    overlaps: list[dict[str, Any]] = []
    for record in records:
        if unique_records and unique_records[-1]["relative_path"] == record["relative_path"]:
            selected = unique_records[-1]
            signature = lambda r: sorted((g["format"], g["text"]) for g in r["ground_truth"])
            overlaps.append({
                "relative_path": record["relative_path"],
                "selected_annotation_file": selected["annotation_file"],
                "discarded_annotation_file": record["annotation_file"],
                "same_format_payload_multiset": signature(selected) == signature(record),
            })
            continue
        unique_records.append(record)
    records = sorted(unique_records, key=lambda r: r["sample_id"])

    audited_image_records = len(records)
    post_overlap = Counter()
    max_barcodes_before_filter = 0
    for record in records:
        max_barcodes_before_filter = max(max_barcodes_before_filter, len(record["ground_truth"]))
        for gt in record["ground_truth"]:
            post_overlap["annotations"] += 1
            if gt["decode_eligible"]:
                post_overlap["eligible_annotations"] += 1
            elif gt["exclusion_reason"] == "missing_reliable_payload":
                post_overlap["missing_payload_or_generic"] += 1
            else:
                post_overlap["invalid_annotations"] += 1
    hash_counts = Counter(r["image_sha256"] for r in records if r["image_sha256"])
    duplicate_image_records = sum(count - 1 for count in hash_counts.values() if count > 1)
    unique_images = {str(p.relative_to(image_root)).replace("\\", "/").lower() for p in image_root.rglob("*") if p.is_file()}

    benchmark_records: list[dict[str, Any]] = []
    benchmark_hashes: set[str] = set()
    excluded_images: list[dict[str, Any]] = []
    duplicate_images: list[dict[str, Any]] = []
    for record in records:
        record["ground_truth"] = [gt for gt in record["ground_truth"] if gt["decode_eligible"]]
        if not record["ground_truth"]:
            excluded_images.append({
                "relative_path": record["relative_path"],
                "annotation_file": record["annotation_file"],
                "reason": "no_reliable_ground_truth",
            })
            continue
        if record["image_sha256"] in benchmark_hashes:
            duplicate_images.append({
                "relative_path": record["relative_path"],
                "annotation_file": record["annotation_file"],
                "image_sha256": record["image_sha256"],
                "reason": "exact_duplicate_image",
            })
            continue
        benchmark_hashes.add(record["image_sha256"])
        benchmark_records.append(record)

    manifest_summary = {
        "annotation_files": summary["annotation_files"],
        "manifest_images": len(benchmark_records),
        "audited_image_records": audited_image_records,
        "source_images": source_images,
        "annotations": post_overlap["annotations"],
        "eligible_annotations": post_overlap["eligible_annotations"],
        "missing_payload_or_generic": post_overlap["missing_payload_or_generic"],
        "invalid_annotations": post_overlap["invalid_annotations"],
        "missing_images": summary["missing_images"],
        "unannotated_images": len(unique_images - referenced),
        "duplicate_image_records": duplicate_image_records,
        "excluded_images_without_ground_truth": len(excluded_images),
        "benchmark_annotations": sum(len(r["ground_truth"]) for r in benchmark_records),
        "dataset_max_barcodes": max((len(r["ground_truth"]) for r in benchmark_records), default=max_barcodes_before_filter),
    }

    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "benchmark_manifest.jsonl", benchmark_records)
    write_jsonl(output / "smoke_manifest.jsonl", choose_smoke(benchmark_records))
    inventory = {
        "dataset": "BarBeR",
        "image_root": str(image_root).replace("\\", "/"),
        "annotation_root": str(annotation_root).replace("\\", "/"),
        "source_annotation_files": source_files,
        "overlapping_annotation_records": overlaps,
        "excluded_images": excluded_images,
        "exact_duplicate_images": duplicate_images,
        "summary": manifest_summary,
    }
    (output / "barber_source_files.json").write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    review = output / "annotation_review.json"
    if not review.exists():
        review.write_text('{\n  "version": 1,\n  "reviews": []\n}\n', encoding="utf-8")
    print(" ".join(f"{key}={value}" for key, value in manifest_summary.items()))
    return 2 if summary["missing_images"] else 0


def choose_smoke(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    selected: set[str] = set()
    ordered = sorted(records, key=lambda r: r["sample_id"])

    def has_2d(record: dict[str, Any]) -> bool:
        return any(canonical_format(gt["format"]) in {"QR_CODE", "DATA_MATRIX", "AZTEC", "PDF_417"} for gt in record["ground_truth"])

    def add(predicate, target: int) -> None:
        for record in ordered:
            if len(output) >= target:
                break
            if record["sample_id"] in selected or not predicate(record):
                continue
            output.append(record)
            selected.add(record["sample_id"])

    add(lambda r: len(r["ground_truth"]) > 1 and not has_2d(r), 1)
    add(lambda r: len(r["ground_truth"]) > 1 and has_2d(r), 2)
    add(lambda r: not has_2d(r) and any(gt["text"].startswith("0") for gt in r["ground_truth"]), 3)
    add(lambda r: any(isinstance(gt.get("ppe"), (int, float)) and gt["ppe"] < 2.0 for gt in r["ground_truth"]), 4)
    add(lambda r: not has_2d(r), 6)
    add(has_2d, 10)
    add(lambda r: True, 10)
    return output


class ZXingPythonReader:
    name = "zxing-python"

    def __init__(self) -> None:
        import zxingcpp

        self.zxingcpp = zxingcpp
        version = getattr(zxingcpp, "__version__", "") or ""
        if not version:
            try:
                from importlib.metadata import version as package_version

                version = package_version("zxing-cpp")
            except Exception:
                version = "unknown"
        self._version = version

    @property
    def version(self) -> str:
        return str(self._version)

    def decode(self, image: Any) -> tuple[list[dict[str, Any]], int, str | None]:
        begin = time.perf_counter_ns()
        try:
            raw = self.zxingcpp.read_barcodes(image)
            decode_ns = time.perf_counter_ns() - begin
            results = []
            for item in raw:
                results.append({
                    "format": canonical_format(getattr(getattr(item, "format", None), "name", "")),
                    "text": str(getattr(item, "text", "")),
                    "raw_bytes_hex": "",
                    "confidence": None,
                })
            return results, decode_ns, None
        except Exception as exc:
            return [], time.perf_counter_ns() - begin, f"decoder_error: {exc}"


class DynamsoftPythonReader:
    name = "dynamsoft-dbr-python"

    def __init__(self, license_key: str, template: str) -> None:
        from dynamsoft_capture_vision_bundle import CaptureVisionRouter, EnumErrorCode, LicenseManager

        error_code, error_message = LicenseManager.init_license(license_key)
        ok_codes = {EnumErrorCode.EC_OK}
        if hasattr(EnumErrorCode, "EC_LICENSE_CACHE_USED"):
            ok_codes.add(EnumErrorCode.EC_LICENSE_CACHE_USED)
        if error_code not in ok_codes:
            raise RuntimeError(f"Dynamsoft license initialization failed: {error_code}, {error_message}")
        self.bundle = sys.modules["dynamsoft_capture_vision_bundle"]
        self.router = CaptureVisionRouter()
        self.template = template
        self._version = getattr(self.bundle, "__version__", "unknown")

    @property
    def version(self) -> str:
        return str(self._version)

    def decode(self, image: Any) -> tuple[list[dict[str, Any]], int, str | None]:
        from dynamsoft_capture_vision_bundle import EnumErrorCode, EnumPresetTemplate

        template = self.template
        if template == "ReadBarcodes_Default":
            template = EnumPresetTemplate.PT_READ_BARCODES.value
        begin = time.perf_counter_ns()
        try:
            captured = self.router.capture(image, template)
            decode_ns = time.perf_counter_ns() - begin
            if captured.get_error_code() != EnumErrorCode.EC_OK:
                return [], decode_ns, f"decoder_error: {captured.get_error_code()}, {captured.get_error_string()}"
            results = []
            for item in captured.get_items():
                text = item.get_text() if hasattr(item, "get_text") else ""
                fmt = item.get_format_string() if hasattr(item, "get_format_string") else ""
                confidence = item.get_confidence() if hasattr(item, "get_confidence") else None
                raw_bytes = item.get_bytes() if hasattr(item, "get_bytes") else b""
                if isinstance(raw_bytes, str):
                    raw_hex = raw_bytes.encode("utf-8").hex()
                else:
                    raw_hex = bytes(raw_bytes or b"").hex()
                results.append({
                    "format": canonical_format(str(fmt)),
                    "text": str(text),
                    "raw_bytes_hex": raw_hex,
                    "confidence": confidence if isinstance(confidence, (int, float)) else None,
                })
            return results, decode_ns, None
        except Exception as exc:
            return [], time.perf_counter_ns() - begin, f"decoder_error: {exc}"


def match_results(truth: list[dict[str, Any]], predictions: list[dict[str, Any]], decoder: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    used = [False] * len(predictions)
    for ti, gt in enumerate(truth):
        if not gt.get("decode_eligible"):
            continue
        if not is_supported(decoder, gt["format"]):
            output.append({"truth_index": ti, "prediction_index": None, "outcome": "unsupported_format"})
            continue
        gt_fmt = canonical_format(gt["format"])
        gt_text = normalized_payload(gt_fmt, gt["text"])
        exact = None
        for pi, prediction in enumerate(predictions):
            if used[pi]:
                continue
            pf = canonical_format(prediction["format"])
            pt = normalized_payload(pf, prediction["text"])
            if (pf == gt_fmt and pt == gt_text) or ({pf, gt_fmt} == {"UPC_A", "EAN_13"} and normalized_payload("UPC_A", prediction["text"]) == normalized_payload("UPC_A", gt["text"])):
                exact = pi
                break
        if exact is not None:
            used[exact] = True
            output.append({"truth_index": ti, "prediction_index": exact, "outcome": "correct"})
            continue
        same_text = None
        same_format = None
        for pi, prediction in enumerate(predictions):
            if used[pi]:
                continue
            pf = canonical_format(prediction["format"])
            if same_text is None and normalized_payload(pf, prediction["text"]) == gt_text:
                same_text = pi
            if same_format is None and pf == gt_fmt:
                same_format = pi
        if same_text is not None:
            used[same_text] = True
            output.append({"truth_index": ti, "prediction_index": same_text, "outcome": "wrong_format"})
        elif same_format is not None:
            used[same_format] = True
            output.append({"truth_index": ti, "prediction_index": same_format, "outcome": "wrong_text"})
        else:
            output.append({"truth_index": ti, "prediction_index": None, "outcome": "not_found"})
    for pi, was_used in enumerate(used):
        if not was_used:
            output.append({"truth_index": None, "prediction_index": pi, "outcome": "extra_result"})
    return output


def load_license(args: argparse.Namespace) -> str:
    if os.getenv("DYNAMSOFT_LICENSE_KEY"):
        return os.environ["DYNAMSOFT_LICENSE_KEY"]
    if args.license_key_file:
        value = args.license_key_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return DEFAULT_LICENSE


def completed_keys(path: Path) -> set[tuple[str, str, int]]:
    return {(row["sample_id"], row["decoder"], row["repetition"]) for row in read_jsonl(path)}


def execute(args: argparse.Namespace, smoke: bool) -> int:
    samples = read_jsonl(args.manifest)
    if smoke and len(samples) != 10:
        raise SystemExit("smoke manifest must contain exactly 10 images")
    if not samples:
        raise SystemExit("manifest contains no benchmark images")
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    jsonl = output / "results.jsonl"
    completed = completed_keys(jsonl)
    zxing = ZXingPythonReader()
    dbr = DynamsoftPythonReader(load_license(args), args.dbr_template)
    decoders = [zxing, dbr]
    manifest_hash = sha256_file(args.manifest)
    zxing_config_hash = "zxing-python:all-supported"
    dbr_config_hash = f"dbr-template:{args.dbr_template}"
    print(f"zxing-python={zxing.version} dynamsoft-dbr-python={dbr.version} images={len(samples)} repetitions={args.repetitions}")

    for repetition in range(args.repetitions):
        for index, sample in enumerate(samples, 1):
            image_path = args.images / sample["relative_path"]
            load_begin = time.perf_counter_ns()
            image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            image_load_ns = time.perf_counter_ns() - load_begin
            load_error = None if image is not None else f"input_pipeline_error: could not load image: {image_path}"
            order = decoders[:]
            seed = int(hashlib.sha256(f"{sample['sample_id']}:{repetition}".encode("utf-8")).hexdigest()[:16], 16)
            random.Random(seed).shuffle(order)
            for decoder in order:
                key = (sample["sample_id"], decoder.name, repetition)
                if key in completed:
                    continue
                if load_error:
                    predictions, decode_ns, error = [], 0, load_error
                    matches = [{"truth_index": i, "prediction_index": None, "outcome": "input_pipeline_error"} for i, _ in enumerate(sample["ground_truth"])]
                else:
                    predictions, decode_ns, error = decoder.decode(image)
                    matches = [{"truth_index": i, "prediction_index": None, "outcome": "decoder_error"} for i, _ in enumerate(sample["ground_truth"])] if error else match_results(sample["ground_truth"], predictions, decoder.name)
                record = {
                    "protocol": PROTOCOL,
                    "manifest_sha256": manifest_hash,
                    "sample_id": sample["sample_id"],
                    "relative_path": sample["relative_path"],
                    "annotation_file": sample["annotation_file"],
                    "image_sha256": sample["image_sha256"],
                    "width": sample["width"],
                    "height": sample["height"],
                    "ground_truth": sample["ground_truth"],
                    "decoder": decoder.name,
                    "decoder_version": decoder.version,
                    "config_sha256": zxing_config_hash if decoder.name == zxing.name else dbr_config_hash,
                    "repetition": repetition,
                    "image_load_ns": image_load_ns,
                    "decode_ns": decode_ns,
                    "error": error,
                    "predictions": predictions,
                    "matches": matches,
                }
                with jsonl.open("a", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                completed.add(key)
            if index % 100 == 0 or index == len(samples):
                print(f"repetition={repetition + 1} progress={index}/{len(samples)}", flush=True)
    generate_summary(jsonl, output / "summary.json")
    generate_results_json(jsonl, output / "summary.json", output / "results.json")
    print(f"wrote {jsonl}, {output / 'summary.json'} and {output / 'results.json'}")
    return 0


def wilson_interval(successes: int, total: int) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    z = 1.96
    phat = successes / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * ((phat * (1 - phat) + z * z / (4 * total)) / total) ** 0.5
    return (centre - margin) / denom, (centre + margin) / denom


def percentile(values: list[int], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[int(q * (len(ordered) - 1))] / 1e6


def generate_summary(jsonl: Path, output: Path) -> None:
    totals: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "records": 0, "eligible": 0, "correct": 0, "unsupported": 0, "errors": 0,
        "common_eligible": 0, "common_correct": 0, "image_all_read": 0,
        "decode_ns": 0, "outcomes": Counter(), "by_format": defaultdict(Counter),
        "by_source": defaultdict(Counter), "timings": [],
    })
    for row in read_jsonl(jsonl):
        c = totals[row["decoder"]]
        c["records"] += 1
        c["decode_ns"] += int(row.get("decode_ns") or 0)
        c["timings"].append(int(row.get("decode_ns") or 0))
        if row.get("error"):
            c["errors"] += 1
        all_read = row.get("error") is None
        for match in row["matches"]:
            outcome = match["outcome"]
            c["outcomes"][outcome] += 1
            if outcome != "extra_result":
                c["eligible"] += 1
            if outcome == "correct":
                c["correct"] += 1
            if outcome == "unsupported_format":
                c["unsupported"] += 1
            if outcome not in {"correct", "extra_result"}:
                all_read = False
            if match["truth_index"] is not None:
                truth = row["ground_truth"][match["truth_index"]]
                fmt = truth.get("format", "")
                c["by_format"][fmt][outcome] += 1
                c["by_source"][row.get("annotation_file", "")][outcome] += 1
                if is_supported("zxing-python", fmt) and is_supported("dynamsoft-dbr-python", fmt):
                    c["common_eligible"] += 1
                    if outcome == "correct":
                        c["common_correct"] += 1
        if all_read:
            c["image_all_read"] += 1

    decoders: dict[str, Any] = {}
    for name, c in totals.items():
        false_predictions = c["outcomes"]["wrong_text"] + c["outcomes"]["wrong_format"] + c["outcomes"]["extra_result"]
        precision = c["correct"] / (c["correct"] + false_predictions) if c["correct"] + false_predictions else 0.0
        recall = c["correct"] / c["eligible"] if c["eligible"] else 0.0
        interval = wilson_interval(c["correct"], c["eligible"])
        common_interval = wilson_interval(c["common_correct"], c["common_eligible"])
        supported_denominator = c["eligible"] - c["unsupported"]
        decoders[name] = {
            "records": c["records"],
            "eligible_instances": c["eligible"],
            "correct": c["correct"],
            "unsupported": c["unsupported"],
            "errors": c["errors"],
            "outcomes": dict(c["outcomes"]),
            "coverage_adjusted_recall": recall,
            "coverage_adjusted_recall_ci95": list(interval),
            "common_format_eligible": c["common_eligible"],
            "common_format_correct": c["common_correct"],
            "common_format_recall": c["common_correct"] / c["common_eligible"] if c["common_eligible"] else 0.0,
            "common_format_recall_ci95": list(common_interval),
            "supported_format_recall": c["correct"] / supported_denominator if supported_denominator else 0.0,
            "precision": precision,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "image_all_read_rate": c["image_all_read"] / c["records"] if c["records"] else 0.0,
            "by_format": {k: dict(v) for k, v in c["by_format"].items()},
            "by_source": {k: dict(v) for k, v in c["by_source"].items()},
            "mean_decode_ms": c["decode_ns"] / c["records"] / 1e6 if c["records"] else 0.0,
            "median_decode_ms": statistics.median(c["timings"]) / 1e6 if c["timings"] else 0.0,
            "p90_decode_ms": percentile(c["timings"], 0.90),
            "p95_decode_ms": percentile(c["timings"], 0.95),
            "p99_decode_ms": percentile(c["timings"], 0.99),
            "total_decode_ms": c["decode_ns"] / 1e6,
        }
    summary = {
        "title": "ZXing Python vs. Dynamsoft Barcode Reader Python",
        "dataset": "BarBeR public dataset",
        "disclosure": "This benchmark compares Python barcode reader packages on the public third-party BarBeR dataset. To make the comparison auditable, the protocol, decoder configurations, environment details, dataset manifest, HTML report, and per-image raw results are provided. BarBeR's standardized annotations were generated with assistance from proprietary Datalogic software. Difficult undecodable barcode regions are excluded from decoding accuracy when no reliable payload is available.",
        "decoders": decoders,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def generate_results_json(jsonl: Path, summary: Path, output: Path) -> None:
    value = {
        "summary": json.loads(summary.read_text(encoding="utf-8")),
        "records": read_jsonl(jsonl),
    }
    output.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_environment(args: argparse.Namespace) -> int:
    env = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "operating_system": platform.platform(),
        "processor": platform.processor(),
        "physical_cores": None,
        "logical_processors": os.cpu_count(),
        "memory_gb": None,
        "python": platform.python_version(),
        "architecture": platform.machine(),
        "configuration": "Python wheels",
        "benchmark_processes": 1,
        "threads_per_decoder_task": 1,
        "repetitions": args.repetitions,
        "zxing_python_package": "zxing-cpp",
        "dynamsoft_python_package": "dynamsoft-capture-vision-bundle",
        "dynamsoft_barcode_reader_template": args.dbr_template,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(env, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("audit")
    p.add_argument("--images", type=Path, required=True)
    p.add_argument("--annotations", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("manifests"))
    p = sub.add_parser("smoke")
    add_run_args(p)
    p = sub.add_parser("run")
    add_run_args(p)
    p = sub.add_parser("summarize")
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("write-environment")
    p.add_argument("--output", type=Path, default=Path("configs/benchmark_environment.json"))
    p.add_argument("--repetitions", type=int, default=1)
    p.add_argument("--dbr-template", default="ReadBarcodes_Default")
    return parser


def add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--license-key-file", type=Path)
    parser.add_argument("--dbr-template", default="ReadBarcodes_Default")
    parser.add_argument("--repetitions", type=int, default=1)


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "audit":
        return audit(args)
    if args.command == "smoke":
        return execute(args, smoke=True)
    if args.command == "run":
        return execute(args, smoke=False)
    if args.command == "summarize":
        generate_summary(args.results, args.output)
        return 0
    if args.command == "write-environment":
        return write_environment(args)
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
