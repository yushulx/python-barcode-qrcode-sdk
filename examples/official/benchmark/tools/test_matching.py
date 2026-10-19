#!/usr/bin/env python3
"""Unit checks for payload normalization and matching."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark import match_results, normalized_payload, is_unreliable_placeholder


def check(cond, message):
    if not cond:
        raise SystemExit(message)


def main() -> int:
    check(normalized_payload("CODE_39", "*8974589*") == "8974589", "code39 asterisks")
    check(normalized_payload("CODE_128", "{GS}8952180") == "8952180", "code128 gs")
    check(normalized_payload("QR_CODE", "t=1&amp;s=2\n") == "t=1&s=2", "html and newline")
    check(normalized_payload("QR_CODE", "\\000001https://example") == "https://example", "nul escape")
    check(is_unreliable_placeholder("^"), "placeholder")

    matches = match_results(
        [{"format": "CODE_39", "text": "*8974589*", "decode_eligible": True}],
        [{"format": "CODE_39", "text": "8974589"}],
        "zxing-python",
    )
    check(matches[0]["outcome"] == "correct", "zxing code39 match")

    matches = match_results(
        [{"format": "CODE_128", "text": "8952180", "decode_eligible": True}],
        [{"format": "CODE_128", "text": "{GS}8952180"}],
        "dynamsoft-dbr-python",
    )
    check(matches[0]["outcome"] == "correct", "dbr gs match")

    matches = match_results(
        [{"format": "PDF_417", "text": "^", "decode_eligible": True}],
        [{"format": "PDF_417", "text": "M1FORTIN"}],
        "dynamsoft-dbr-python",
    )
    check(matches[0]["outcome"] == "extra_result", "placeholder excluded")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
