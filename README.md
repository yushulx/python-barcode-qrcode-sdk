# DBR Python Extension
Version 7.2

The repository aims to help developers build **Python barcode** apps with [Dynamsoft Barcode Reader](https://www.dynamsoft.com/Products/Dynamic-Barcode-Reader.aspx) in Windows, Linux, macOS, and Raspberry Pi.

## License
Get the trial license [here](https://www.dynamsoft.com/CustomerPortal/Portal/Triallicense.aspx). Then replace the old license with the newly generated one in the **config.py** file.

## Contact Us
<support@dynamsoft.com>

## Environment
**Python 2/3**

## Supported Symbologies
- Linear Barcodes (1D)

    - Code 39 (including Code 39 Extended)
    - Code 93
    - Code 128
    - Codabar
    - Interleaved 2 of 5
    - EAN-8
    - EAN-13
    - UPC-A
    - UPC-E
    - Industrial 2 of 5

- 2D Barcodes:
    - QR Code (including Micro QR Code)
    - Data Matrix
    - PDF417 (including Micro PDF417)
    - Aztec Code
    - MaxiCode (mode 2-5)

- Patch Code
- GS1 DataBar (Omnidirectional,
Truncated, Stacked, Stacked
Omnidirectional, Limited,
Expanded, Expanded Stacked)
- GS1 Composite Code

## Installation
* [Dynamsoft Barcode Reader SDK](https://www.dynamsoft.com/Downloads/Dynamic-Barcode-Reader-Download.aspx).
* OpenCV

    ```
    py -2 -m pip install opencv-python
    py -3 -m pip install opencv-python
    ```
    
    For **Raspberry Pi**
    
    ```
    sudo apt-get install libopencv-dev python-opencv
    ```
    
* NumPy
	
    ```
    py -2 -m pip install numpy
    py -3 -m pip install numpy
    ```
    
## HowTo
### Windows
Set **Visual Studio** in **cmd.exe**. For example, **Visual Studio 2015**:

```
SET VS90COMNTOOLS=%VS140COMNTOOLS%
```

Edit `setup.py`. Replace the **dbr_lib_dir** and **dbr_dll** with yours:

```
dbr_lib_dir = r'e:\Program Files (x86)\Dynamsoft\Barcode Reader 7.2\Components\C_C++\Lib'
dbr_dll = r'e:\Program Files (x86)\Dynamsoft\Barcode Reader 7.2\Components\C_C++\Redist\x64'
```

Build and install the Python extension:

```
cd src
py -2 setup.py build install
py -3 setup.py build install
```

### Linux, macOS and Raspberry Pi
Copy **libDynamsoftBarcodeReader.so**/**libDynamsoftBarcodeReader.dylib** to `/usr/lib`. If you don't have access to `/usr/lib`, try to copy the library to `/usr/local/lib` and set the **LD_LIBRARY_PATH** as follows:

```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
```

Build and install the Python extension:

```
cd src
sudo py -2 setup.py build install
sudo py -3 setup.py build install
```

## Examples
- examples/video

    ```
    python rtsp.py
    ```
    
- examples/camera

    ```
    python camera-decodevideo.py
    ```
    
- examples/command-line

    ```
    python test.py
    ```

## Functions
- initLicense(license-key)
- decodeFile(filename, barcodeTypes) 

    ```
    barcodeTypes = dbr.BF_ONED | dbr.BF_PDF417 | dbr.BF_QR_CODE | dbr.BF_DATAMATRIX | dbr.BF_AZTEC 
    ```

    | Barcode Format| Values            |
    | ------------- |-------------------|
    | ALL           | dbr.BF_ALL        |
    | 1D            | dbr.BF_ONED       |
    | PDF417        | dbr.BF_PDF417     |
    | QR Code       | dbr.BF_QR_CODE    |
    | DataMatrix    | dbr.BF_DATAMATRIX |
    | Aztec Code    | dbr.BF_AZTEC      |

- decodeBuffer(frame-by-opencv-capture, barcodeTypes)
- startVideoMode(max_buffer, max_results, video_width, video_height, image_format, barcodeTypes, callback)
- stopVideoMode()
- appendVideoFrame(frame-by-opencv-capture)
- initLicenseFromLicenseContent(license-key, license-content)
- outputLicenseToString()
- initLicenseFromServer(license-key, license-server)
- setFurtherModes(mode, [values])
- setParameters(json-string)

## Online Documentation
https://www.dynamsoft.com/Products/Barcode-Reader-Resources.aspx#documentation

## Related Articles
* [How to Define Python Object Members in C Code](https://www.codepool.biz/python-object-members.html)
* [Python Barcode Decoding on Non-Python Created Thread](https://www.codepool.biz/python-decode-barcode-c-thread.html)
* [Things to Do with DBR 6.0 and Python Barcode Extension](http://www.codepool.biz/dynamsoft-barcode-python-extension-6-0.html)
* [How to Port C/C++ Barcode Extension to Python 3](http://www.codepool.biz/cc-barcode-extension-python-3.html)
* [Building Python Barcode Extension with DBR 5.0 on Windows](http://www.codepool.biz/python-barcode-extension-dbr-windows.html)
* [Building Python Barcode Extension with DBR 5.2 for Linux](http://www.codepool.biz/build-linux-python-barcode-extension.html)
