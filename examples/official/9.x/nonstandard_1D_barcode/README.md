# Decoding Nonstandard 1D Barcodes in Python with Dynamsoft Barcode SDK
This sample demonstrates how to use the [Dynamsoft Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/overview/) to decode nonstandard 1D barcodes.

## Environment
Python 3.x

## Prerequisites
- Obtain a [Dynamsoft Barcode Reader trial license](ttps://www.dynamsoft.com/customer/license/trialLicense)
- Install the Dynamsoft Barcode Reader SDK for Python:
    
    ```bash
    pip install dbr
    ```

## Getting Started

1. Set the license key in `test.py`:

    ```python
    license_key = "LICENSE-KEY" 
    ```

2. Define the barcode format and specify the start/stop characters. Below is an example configuration for [Code39](https://en.wikipedia.org/wiki/Code_39):

    ```json
    "StandardFormat": "BF_CODE_39",
    "HeadModuleRatio": "131111313",
    "TailModuleRatio": "131111313"
    ```

3. After configuring the template file, use the following code to read the barcode:

    ```python
    reader = BarcodeReader()
    reader.init_license(license_key)
    
    error = reader.init_runtime_settings_with_file(json_file)
    if error[0] != EnumErrorCode.DBR_OK:
        print(error[1])
    
    try:
        text_results = reader.decode_file(filename)
        if text_results != None:
            for text_result in text_results:
                print('Barcode Format:')
                print(text_result.barcode_format_string_2)
                print('')
                print('Barcode Text:')
                print(text_result.barcode_text)
                print('')
                print('Localization Points:')
                print(text_result.localization_result.localization_points)
                print('------------------------------------------------')
                print('')
    except BarcodeReaderError as bre:
        print(bre)
    
    ```

4. Run the script:

    ```bash
    python test.py
    ```

    ![python nonstandard 1D barcode detection](https://www.dynamsoft.com/codepool/img/2020/06/nonstandard-1d-barcode-recognition.png)

## Blog
[How to Read Nonstandard 1D Barcode with Dynamsoft Barcode SDK](https://www.dynamsoft.com/codepool/read-nonstandard-1d-barcode-barcode-sdk.html)
