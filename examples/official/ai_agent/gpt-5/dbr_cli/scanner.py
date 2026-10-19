import os
import json
from typing import List, Dict, Any, Iterable

try:
    from dbr import BarcodeReader, EnumImagePixelFormat
except ImportError:  # dbr not installed yet
    BarcodeReader = None  # type: ignore
    EnumImagePixelFormat = None  # type: ignore


class DynamsoftScanner:
    def __init__(self, license_key: str | None = None):
        if BarcodeReader is None:
            raise RuntimeError("Dynamsoft Barcode Reader SDK (dbr) not installed. Run: pip install dbr")
        self.license = license_key or os.getenv("DBR_LICENSE")
        if not self.license:
            raise ValueError("No license key provided. Set DBR_LICENSE env var or pass --license.")
        BarcodeReader.init_license(self.license)
        self.reader = BarcodeReader()

    def scan_file(self, path: str) -> List[Dict[str, Any]]:
        results = self.reader.decode_file(path) or []
        return [self._result_to_dict(r, source=path) for r in results]

    def scan_buffer(self, buffer: bytes, width: int, height: int, stride: int, pixel_format) -> List[Dict[str, Any]]:
        raise NotImplementedError("Camera buffer decoding unavailable due to SDK signature mismatch in this environment. Use file-based scanning.")

    @staticmethod
    def _result_to_dict(result, source: str) -> Dict[str, Any]:
        return {
            "text": result.barcode_text,
            "format": result.barcode_format_string,
            "source": source,
            "confidence": getattr(result, "confidence", None),
            "x1": result.localization_result.x1 if result.localization_result else None,
            "y1": result.localization_result.y1 if result.localization_result else None,
            "x2": result.localization_result.x2 if result.localization_result else None,
            "y2": result.localization_result.y2 if result.localization_result else None,
            "x3": result.localization_result.x3 if result.localization_result else None,
            "y3": result.localization_result.y3 if result.localization_result else None,
            "x4": result.localization_result.x4 if result.localization_result else None,
            "y4": result.localization_result.y4 if result.localization_result else None,
        }


def iter_image_files(paths: Iterable[str], recursive: bool) -> Iterable[str]:
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".gif", ".webp"}
    for p in paths:
        if os.path.isdir(p):
            if recursive:
                for root, _, files in os.walk(p):
                    for f in files:
                        if os.path.splitext(f)[1].lower() in exts:
                            yield os.path.join(root, f)
            else:
                for f in os.listdir(p):
                    fp = os.path.join(p, f)
                    if os.path.isfile(fp) and os.path.splitext(f)[1].lower() in exts:
                        yield fp
        else:
            if os.path.splitext(p)[1].lower() in exts:
                yield p


def results_to_text(results: List[Dict[str, Any]]) -> str:
    lines = []
    for r in results:
        lines.append(f"{r['source']}: {r['format']} -> {r['text']}")
    return "\n".join(lines)


def results_to_json(results: List[Dict[str, Any]]) -> str:
    return json.dumps(results, indent=2, ensure_ascii=False)
