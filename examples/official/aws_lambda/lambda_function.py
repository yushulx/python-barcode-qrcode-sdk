"""AWS Lambda handler that reads barcodes from a base64-encoded image.

The function is packaged with the Dynamsoft Barcode Reader Python bundle
(``dynamsoft-barcode-reader-bundle==11.6.5000``, Capture Vision 3.6.5000).
See README.md for the layer build steps.
"""

import base64
import binascii
import json
import os
import tempfile

from dynamsoft_barcode_reader_bundle import (
    CaptureVisionRouter,
    EnumErrorCode,
    EnumPresetTemplate,
    LicenseManager,
)

# One-day public trial key. Replace it with your own key through the
# DYNAMSOFT_LICENSE_KEY environment variable when deploying.
TRIAL_LICENSE_KEY = (
    "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6"
    "IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
)
LICENSE_KEY = os.environ.get("DYNAMSOFT_LICENSE_KEY", TRIAL_LICENSE_KEY)
TEMPLATE_NAME = os.environ.get("DBR_TEMPLATE", EnumPresetTemplate.PT_READ_BARCODES.value)

_LICENSE_OK_CODES = (
    EnumErrorCode.EC_OK,
    EnumErrorCode.EC_LICENSE_WARNING,
    EnumErrorCode.EC_LICENSE_CACHE_USED,
)


def _init_license():
    """Point the license cache at a writable directory, then initialize.

    Lambda only allows writes under /tmp; tempfile.gettempdir() resolves to
    /tmp there and to the platform temp directory when the function runs
    locally.
    """
    cache_dir = os.path.join(tempfile.gettempdir(), "dynamsoft")
    os.makedirs(cache_dir, exist_ok=True)
    LicenseManager.set_license_cache_path(cache_dir)
    return LicenseManager.init_license(LICENSE_KEY)


LICENSE_CODE, LICENSE_MESSAGE = _init_license()

_router = None


def _get_router():
    """Reuse one CaptureVisionRouter across warm invocations."""
    global _router
    if _router is None:
        _router = CaptureVisionRouter()
    return _router


def _response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _request_payload(event):
    """Return the parsed JSON request body.

    Works for an API Gateway proxy event, for a base64-encoded binary body,
    and for a plain dict when the handler is invoked locally.
    """
    body = event.get("body") if isinstance(event, dict) else None
    if body is None:
        body = event
    if isinstance(body, str):
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        body = json.loads(body)
    if not isinstance(body, dict):
        raise ValueError("The request body must be a JSON object.")
    return body


def _decode_image(payload):
    """Turn the base64 field into image bytes, accepting data URLs."""
    if "base64" not in payload:
        raise ValueError('The request body must contain a "base64" field.')
    data = payload["base64"]
    if not isinstance(data, str) or not data:
        raise ValueError('The "base64" field must be a non-empty string.')
    if data.startswith("data:"):
        _, _, data = data.partition(",")
    return base64.b64decode(data, validate=True)


def _barcode_to_dict(item):
    points = item.get_location().points
    result = {
        "barcodeFormat": item.get_format_string(),
        "barcodeText": item.get_text(),
        "barcodeBytes": base64.b64encode(item.get_bytes()).decode("ascii"),
        "confidence": item.get_confidence(),
    }
    for index, point in enumerate(points[:4], start=1):
        result[f"x{index}"] = point.x
        result[f"y{index}"] = point.y
    return result


def lambda_handler(event, context):
    if LICENSE_CODE not in _LICENSE_OK_CODES:
        return _response(500, {"error": f"License error: {LICENSE_MESSAGE}", "code": LICENSE_CODE})

    try:
        image_bytes = _decode_image(_request_payload(event))
    except (ValueError, binascii.Error, json.JSONDecodeError) as error:
        return _response(400, {"error": str(error)})

    result = _get_router().capture(image_bytes, TEMPLATE_NAME)
    error_code = result.get_error_code()
    if error_code != EnumErrorCode.EC_OK:
        return _response(422, {"error": result.get_error_string(), "code": error_code})

    barcode_result = result.get_decoded_barcodes_result()
    items = barcode_result.get_items() if barcode_result is not None else []
    return _response(200, {"results": [_barcode_to_dict(item) for item in items]})
