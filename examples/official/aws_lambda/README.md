# Barcode Reader on AWS Lambda (Python)

Run Dynamsoft Barcode Reader on AWS Lambda and expose it as a serverless barcode
reading API. The handler uses `dynamsoft-barcode-reader-bundle==11.6.5000`
(Capture Vision 3.6.5000), which ships manylinux wheels for Python 3.10-3.14, so
the same package runs locally and inside the Lambda runtime.

## Files

| File | Purpose |
| --- | --- |
| `lambda_function.py` | Lambda handler: base64 image in, barcode JSON out |
| `test.py` | Calls the deployed endpoint, or invokes the handler locally with `--local` |
| `sample_qr.png` | Test image |
| `requirements.txt` | Local dependencies |

## API Specification

Request:

```json
{
  "base64": "<base64-encoded-image>"
}
```

Response:

```json
{"results":
  [
    {
      "barcodeFormat": "QR_CODE",
      "barcodeText": "https://www.dynamsoft.com",
      "barcodeBytes": "aHR0cHM6Ly93d3cuZHluYW1zb2Z0LmNvbQ==",
      "confidence": 82,
      "x1": 7,
      "y1": 7,
      "x2": 93,
      "y2": 6,
      "x3": 94,
      "y3": 94,
      "x4": 6,
      "y4": 93
    }
  ]
}
```

Error responses carry the same JSON envelope with a non-200 status code:
`400` for a malformed request body, `422` when the SDK cannot decode the image,
`500` when the license is not usable.

## Run Locally

```bash
pip install -r requirements.txt
python test.py --local
```

`--local` calls `lambda_handler` in-process, so no AWS resources are needed.

## Deploy

1. Create a Lambda function with the Python 3.10-3.14 runtime.
2. Build the SDK layer. Run the commands on Linux (or in a `manylinux` container)
   so pip picks the manylinux wheel that matches the Lambda runtime:

   ```bash
   python -m pip install --target python dynamsoft-barcode-reader-bundle==11.6.5000
   zip -r dynamsoft-dbr-layer.zip python
   ```

   Upload `dynamsoft-dbr-layer.zip` as a layer and attach it to the function.
   Use the `manylinux2014_x86_64` wheel for x86 functions and the
   `manylinux_2_27_aarch64` wheel for arm64 functions.
3. Copy `lambda_function.py` into the function (handler:
   `lambda_function.lambda_handler`).
4. Set `DYNAMSOFT_LICENSE_KEY` in the function's environment variables. The
   placeholder key in the handler is a one-day public trial.
5. Add an API Gateway trigger and call it from `test.py`:

   ```bash
   python test.py --endpoint https://xxxx.execute-api.us-east-2.amazonaws.com/default/BarcodeReader
   ```

## Notes

- Lambda only allows writes under `/tmp`. The handler calls
  `LicenseManager.set_license_cache_path()` with `tempfile.gettempdir()`, which
  resolves to `/tmp` on Lambda, so the license cache survives warm invocations.
- `DBR_TEMPLATE` overrides the template; it defaults to
  `EnumPresetTemplate.PT_READ_BARCODES`.
- The layers have a 250 MB unzipped limit. The bundle for one platform is well
  below it, but a layer holding every platform wheel is not - build one layer per
  target architecture.

## License Application

A license is required to use Dynamsoft Barcode Reader. You can apply for one
[here](https://www.dynamsoft.com/customer/license/trialLicense/?product=dbr).

## Blog

[Build a Serverless Barcode Reading API with Python and AWS Lambda](https://www.dynamsoft.com/codepool/read-barcodes-aws-lambda-python.html)

## Reference

<https://github.com/aws-samples/barcode-qr-decoder-lambda/>
