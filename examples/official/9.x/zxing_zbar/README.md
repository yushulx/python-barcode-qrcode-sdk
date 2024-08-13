# ZXing vs. ZBar vs. Dynamsoft Barcode Reader in Python
This repository provides a comparison of barcode recognition performance between three popular barcode scanning libraries: **ZXing**, **ZBar**, and [Dynamsoft Barcode Reader](https://pypi.org/project/dbr/).

## Dataset Download
Download the full dataset from the following link: https://drive.google.com/uc?id=1uThXXH8HiHAw6KlpdgcimBSbrvi0Mksf&export=download

## Installation

To get started, install the required dependencies:

```bash
pip install -r requirements.txt
```


## Usage
1. Obtain a [Dynamsoft Barcode Reader trial license](ttps://www.dynamsoft.com/customer/license/trialLicense) and update the code with the license key in `app.py`.
    
    ```python
    BarcodeReader.init_license('LICENSE-KEY')
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
    
## Benchmark Results
Below is a visual comparison of the barcode recognition rates among ZXing, ZBar, and Dynamsoft Barcode Reader based on the dataset.

![barcode sdk benchmark](https://www.dynamsoft.com/codepool/img/2024/08/python-barcode-sdk-benchmark.png)

## Blog
[Comparing Barcode Scanning in Python: ZXing vs. ZBar vs. Dynamsoft Barcode Reader](https://www.dynamsoft.com/codepool/python-zxing-zbar-barcode.html)
