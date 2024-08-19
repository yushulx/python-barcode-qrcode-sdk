# Online Barcode and QR Code Reader with Python Django
This sample demonstrates how to create an online Barcode and QR Code Reader using Python Django and the [Dynamsoft Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/overview/).

## Prerequisites
- **Django** 
    
    Install Django and verify the installation:

    ```bash
    python -m pip install Django
    python -m django --version
    ```
- **Dynamsoft Barcode Reader SDK v9.x**
    
    Install the Dynamsoft Barcode Reader SDK:

    ```bash
    pip install dbr
    ```

- **SDK License**

    To use the Dynamsoft Barcode Reader SDK, request a [30-day free trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dbr). 

## Usage
1. Set the license key in `scanbarcode/views.py`:

    ```python
    BarcodeReader.init_license("LICENSE-KEY")
    ```

2. Run the project:

    ```bash
    python manage.py makemigrations
    python manage.py migrate --run-syncdb
    python manage.py runserver
    ``` 
    
3. Visit `127.0.0.1:8000` in a web browser to access the online barcode reader.

    ![python django online barcode reader](https://www.dynamsoft.com/codepool/img/2022/02/python-django-online-barcode-reader.png)

## Blog
[Building Online Barcode and QR Code Scanning App with Python Django](https://www.dynamsoft.com/codepool/django-barcode-scanning-app.html)

