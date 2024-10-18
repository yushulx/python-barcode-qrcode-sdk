# Python Ctypes for Dynamsoft Barcode Shared Library
This repository demonstrates how to load and utilize Dynamsoft Barcode Reader shared libraries using Python's Ctypes module.

## Why Use Ctypes?
While Dynamsoft Barcode Reader for Python is available on [PyPI](https://pypi.org/project/dbr/) and can be installed with:

```bash
pip install dbr
```

This project explores an alternative approach to invoking C APIs from shared libraries using Ctypes, offering a way to use C/C++ native threads and callbacks in Python.

## How to Use
1. Build the `bridge` CMake project:
    
    **On Windows**:

    ```bash
    cd bridge && mkdir build && cd build
    cmake -DCMAKE_GENERATOR_PLATFORM=x64 ..
    cmake --build .
    ```
    
    **On Linux:**

    ```bash
    cd bridge && mkdir build && cd build
    cmake ..
    cmake --build .
    ```    

2. Get a valid license key from [Dynamsoft](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform). Then, update the license key in the `success.py` file.

    ```python
    license_key = b"LICENSE-KEY"
    ```

3. Execute the `success.py` script.
    
    ```bash
    python success.py
    ```

## Blog
[Python Ctypes for Loading and Calling Shared Libraries](https://www.dynamsoft.com/codepool/python-ctypes-load-call-shared-library.html)
