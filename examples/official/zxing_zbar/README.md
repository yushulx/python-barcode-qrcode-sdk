# ZXing-cpp vs. ZBar vs. Dynamsoft Barcode Reader in Python
This repository compares the barcode recognition performance of three popular libraries: **ZXing-cpp**, **ZBar**, and the [Dynamsoft Capture Vision SDK](https://pypi.org/search/?q=dynamsoft-capture-vision-bundle).

## Prerequisites
- Install required packages:

    ```bash
    pip install -r requirements.txt
    ```

- Dataset
    
    The dataset is sourced from this [GitHub issue](https://github.com/openfoodfacts/openfoodfacts-ai/issues/15). You can download it directly from: https://drive.google.com/uc?id=1uThXXH8HiHAw6KlpdgcimBSbrvi0Mksf&export=download. We have cleaned the images to ensure each image file name matches the barcode content.

## Usage
1. Obtain a [30-day trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) and update the code with the license key in `app.py`.
    
    ```python
    from dynamsoft_capture_vision_bundle import *
    error_code, error_message = LicenseManager.init_license(
        "LICENSE-KEY")
    ```

2. Run the Python script:

    ```bash
    python app.py
    
    Usage:
            python app.py -i <image_file>
            python app.py -d <folder_directory>
    ```
    
    **ZXing**
    
    ![python zxing barcode detection](https://www.dynamsoft.com/codepool/img/2024/08/python-zxing-barcode-detection.png)

    **ZBar**

    ![python zxing barcode detection](https://www.dynamsoft.com/codepool/img/2024/08/python-zbar-barcode-detection.png)

    **Dynamsoft Barcode Reader**
    
    ![python zxing barcode detection](https://www.dynamsoft.com/codepool/img/2024/08/python-dbr-barcode-detection.png)
    

## Blog
[Comparing Barcode Scanning in Python: ZXing vs. ZBar vs. Dynamsoft Barcode Reader](https://www.dynamsoft.com/codepool/python-zxing-zbar-barcode.html)
