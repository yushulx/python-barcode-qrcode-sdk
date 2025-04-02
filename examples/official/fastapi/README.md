# Barcode Reader Web Application 
A web application that leverages [FastAPI](https://pypi.org/project/fastapi/) for the backend along with a lightweight **HTML/JavaScript** frontend. The application allows users to upload images for **barcode reading**, decodes the barcodes using the [Dynamsoft Capture Vision Bundle](https://pypi.org/project/dynamsoft-capture-vision-bundle/), and presents the decoded data in a user-friendly interface.

## Features

- Upload images containing barcodes.
- Detect and decode barcodes using the Dynamsoft Capture Vision Bundle.
- Display barcode details, including type, content, and location.
- Visualize barcode locations on the uploaded image.

## Prerequisites

- Python 3.8 or higher
- [Dynamsoft Capture Vision Bundle license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform)

## Getting Started
1. Download the source code from the repository.
2. Install the required dependencies using pip. 

    ```bash
    pip install -r requirements.txt
    ```

3. Set the license key in `backend.py`:

    ```python
    license_key = "LICENSE-KEY"
    ```

4. Run the project:
    
    ```bash
    python backend.py
    ```

5. Open your web browser and navigate to `http://localhost:8000` to access the application.