# Semi-OCR Example with Dynamsoft Capture Vision SDK

This example demonstrates how to use Dynamsoft Capture Vision SDK to recognize **SEMI (Semiconductor Equipment and Materials International)** font markings on silicon wafers. The custom model provided by Dynamsoft is trained for **single-density dot matrix fonts** and supports only **26 uppercase letters and 10 digits**.

https://github.com/user-attachments/assets/703b35dd-9bee-4652-a687-3b5e1d7d64c9

## Prerequisites

- Python 3.8 or later
- Install required packages:

    ```bash
    pip install -r requirements.txt
    ```

- Obtain a [30-day trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform)

## Usage

1. Set your license key in `read_semi_ocr.py`:

    ```python
    err_code, err_str = LicenseManager.init_license("LICENSE-KEY")
    ```

2. Run the script:

    ```bash
    python read_semi_ocr.py
    ```

    ![SEMI font OCR recognition](https://www.dynamsoft.com/codepool/img/2025/07/semi-font-ocr-recognition.png)

## Support

For model-related issues, please contact [Dynamsoft Support](https://www.dynamsoft.com/company/customer-service/).
