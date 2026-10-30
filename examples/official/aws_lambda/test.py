"""Call the barcode reading Lambda function.

Remote mode posts a base64 image to the API Gateway endpoint:

    python test.py --endpoint https://xxxx.execute-api.us-east-2.amazonaws.com/default/BarcodeReader

Local mode invokes lambda_handler in-process, so the handler can be tested
before anything is deployed:

    python test.py --local
"""

import argparse
import base64
import json
import os
import sys

DEFAULT_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_qr.png")


def get_picture_base64_data(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def build_event(base64_string):
    return {"body": json.dumps({"base64": base64_string}), "isBase64Encoded": False}


def invoke_local(base64_string):
    from lambda_function import lambda_handler

    return lambda_handler(build_event(base64_string), None)


def invoke_remote(endpoint, base64_string):
    import requests

    response = requests.post(
        endpoint,
        data=json.dumps({"base64": base64_string}),
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Read barcodes with the AWS Lambda function.")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Image to send (default: sample_qr.png).")
    parser.add_argument("--endpoint", default=os.environ.get("LAMBDA_ENDPOINT", ""), help="API Gateway endpoint URL.")
    parser.add_argument("--local", action="store_true", help="Invoke lambda_handler in this process instead of an HTTP call.")
    args = parser.parse_args()

    base64_string = get_picture_base64_data(args.image)

    if args.local:
        response = invoke_local(base64_string)
    else:
        endpoint = args.endpoint or input("Please input the endpoint: ").strip()
        if not endpoint:
            print("No endpoint given. Use --local to test the handler without deploying.")
            return 1
        response = invoke_remote(endpoint, base64_string)

    body = response.get("body", response)
    print(json.dumps(json.loads(body) if isinstance(body, str) else body, indent=2))
    return 0 if response.get("statusCode", 200) == 200 else 1


if __name__ == "__main__":
    sys.exit(main())
