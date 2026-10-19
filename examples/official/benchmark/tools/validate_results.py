#!/usr/bin/env python3
"""Validate benchmark JSONL structure, uniqueness, and summary counts."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--expected-images", type=int)
    parser.add_argument("--expected-ground-truth", type=int)
    parser.add_argument("--expected-repetitions", type=int)
    args = parser.parse_args()
    with args.results.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    required = {"sample_id", "relative_path", "decoder", "decoder_version", "repetition", "ground_truth", "predictions", "matches", "decode_ns", "image_load_ns", "error"}
    for index, row in enumerate(rows, 1):
        missing = required - row.keys()
        if missing:
            raise SystemExit(f"record {index} missing fields: {sorted(missing)}")
    keys = [(r["sample_id"], r["decoder"], r["repetition"]) for r in rows]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        raise SystemExit(f"duplicate result keys: {duplicates[:5]}")
    by_decoder = defaultdict(list)
    for row in rows:
        by_decoder[row["decoder"]].append(row)
    if args.expected_images is not None:
        for decoder, group in by_decoder.items():
            actual = len({r["sample_id"] for r in group})
            if actual != args.expected_images:
                raise SystemExit(f"{decoder}: expected {args.expected_images} images, got {actual}")
    sample_truth = {}
    for row in rows:
        if not row["ground_truth"]:
            raise SystemExit(f'{row["relative_path"]}: ground truth is empty')
        if any(not item.get("decode_eligible") for item in row["ground_truth"]):
            raise SystemExit(f'{row["relative_path"]}: ground truth contains an excluded item')
        serialized = json.dumps(row["ground_truth"], sort_keys=True, ensure_ascii=False)
        previous = sample_truth.setdefault(row["sample_id"], serialized)
        if previous != serialized:
            raise SystemExit(f'{row["relative_path"]}: ground truth differs between decoder records')
    if args.expected_ground_truth is not None:
        actual = sum(len(json.loads(value)) for value in sample_truth.values())
        if actual != args.expected_ground_truth:
            raise SystemExit(f"expected {args.expected_ground_truth} ground truth items, got {actual}")
    if args.expected_repetitions is not None:
        expected = set(range(args.expected_repetitions))
        grouped = defaultdict(set)
        for row in rows:
            grouped[(row["sample_id"], row["decoder"])].add(row["repetition"])
        incomplete = [key for key, repetitions in grouped.items() if repetitions != expected]
        if incomplete:
            raise SystemExit(f"incomplete repetitions: {incomplete[:5]}")
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    for decoder, group in by_decoder.items():
        expected = summary["decoders"][decoder]["records"]
        if expected != len(group):
            raise SystemExit(f"{decoder}: summary records={expected}, JSONL records={len(group)}")
    errors = [(r["decoder"], r["relative_path"], r["error"]) for r in rows if r["error"]]
    print(json.dumps({"records": len(rows), "unique_keys": len(set(keys)), "decoders": {k: len(v) for k, v in by_decoder.items()}, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
