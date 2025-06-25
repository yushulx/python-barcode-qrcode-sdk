# Online Barcode and QR Code Reader with Python Django
This sample demonstrates how to create an online Barcode and QR Code Reader using Python Django and the [Dynamsoft Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/overview/).

## Prerequisites
- **Dependency Installation**

    ```bash
    pip install dynamsoft-capture-vision-bundle Django
    ```

- **SDK License**

    Request a [30-day free trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform). 

## Usage
1. Set the license key in `scanbarcode/views.py`:

    ```python
    LicenseManager.init_license("LICENSE-KEY")
    ```

2. Run the project:

    ```bash
    python manage.py runserver
    ``` 
    
3. Open your browser and navigate to `127.0.0.1:8000`.

    ![python django barcode reader](https://www.dynamsoft.com/codepool/img/2022/02/python-django-online-barcode-reader.png)

## Blog
[Building Online Barcode and QR Code Scanning App with Python Django](https://www.dynamsoft.com/codepool/django-barcode-scanning-app.html)

