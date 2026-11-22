# Decoding Nonstandard 1D Barcodes in Python with Dynamsoft Barcode SDK
This sample demonstrates how to use the [Dynamsoft Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/overview/) to decode nonstandard 1D barcodes.

## Environment
Python 3.x

## Prerequisites
- Obtain a [Dynamsoft Barcode Reader trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform)
- Install the Dynamsoft Barcode Reader SDK for Python:
    
    ```bash
    pip install dynamsoft-capture-vision-bundle
    ```

## Getting Started

1. Set the license key in `test.py`:

    ```python
    error_code, error_message = LicenseManager.init_license(
        "LICENSE-KEY")
    ```

2. Define the barcode format and specify the start/stop characters. Below is an example configuration for [Code39](https://en.wikipedia.org/wiki/Code_39):

    ```json
    "StandardFormat": "BF_CODE_39",
    "HeadModuleRatio": "131111313",
    "TailModuleRatio": "131111313"
    ```

3. After configuring the template file, use the following code to read the barcode:

    ```python
    error_code, error_message = LicenseManager.init_license("LICENSE-KEY")
    if error_code != EnumErrorCode.EC_OK and error_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print("License initialization failed: ErrorCode:",
              error_code, ", ErrorString:", error_message)
    else:
        cvr_instance = CaptureVisionRouter()
    
        cvr_instance.init_settings_from_file('template_plus.json') # Or template_minus.json 

        result = cvr_instance.capture(
                cv_image, "") # The empty string means using the default template
        if result.get_error_code() != EnumErrorCode.EC_OK:
            print("Error:", result.get_error_code(),
                    result.get_error_string())
        else:
            
            items = result.get_items()
            print('Found {} barcodes.'.format(len(items)))
            for item in items:
                format_type = item.get_format_string()
                text = item.get_text()
                print("Barcode Format:", format_type)
                print("Barcode Text:", text)

                location = item.get_location()
                x1 = location.points[0].x
                y1 = location.points[0].y
                x2 = location.points[1].x
                y2 = location.points[1].y
                x3 = location.points[2].x
                y3 = location.points[2].y
                x4 = location.points[3].x
                y4 = location.points[3].y
                print("Location Points:")
                print("({}, {})".format(x1, y1))
                print("({}, {})".format(x2, y2))
                print("({}, {})".format(x3, y3))
                print("({}, {})".format(x4, y4))
                print("-------------------------------------------------")

                pts = np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], dtype=np.int32).reshape((-1, 1, 2))
                cv2.drawContours(
                    cv_image, [pts], 0, (0, 255, 0), 2)

                cv2.putText(cv_image, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            cv2.imshow(
                "Original Image with Detected Barcodes", cv_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    
    ```

4. Run the script:

    ```bash
    python test.py
    ```

    ![python nonstandard 1D barcode detection](https://www.dynamsoft.com/codepool/img/2020/06/nonstandard-1d-barcode-recognition.png)

## Blog
[How to Read Nonstandard 1D Barcode with Dynamsoft Barcode SDK](https://www.dynamsoft.com/codepool/read-nonstandard-1d-barcode-barcode-sdk.html)
