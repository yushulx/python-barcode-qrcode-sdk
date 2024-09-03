# Flet Chat App with Google AI and Dynamsoft Barcode Reader
The project demonstrates how to integrate [Dynamsoft Barcode Reader](https://pypi.org/project/dbr/) and [Gemini APIs](https://ai.google.dev/tutorials/python_quickstart) into a Flet chat app.

https://github.com/yushulx/flet-chat-app-gemini-barcode/assets/2202306/ef159de0-cdf9-48e2-91d9-3da3ce9f85a0

## Installation

```bash
pip install -r requirements.txt

```

## Getting Started
1. Get an [API key](https://makersuite.google.com/app/apikey) for Gemini in Google AI Studio and replace the value of `API_KEY` in `chatbot.py`.
    
    ```python
    genai.configure(api_key='API_KEY')
    ```

    ![Gemini API key](https://github.com/yushulx/flet-chat-app-gemini-barcode/assets/2202306/a556a3dc-622f-4de0-b3d5-9067de44a5e5)

    
2. Request a [free trial license](https://www.dynamsoft.com/customer/license/trialLicense?product=dbr) for Dynamsoft Barcode Reader and replace the value of `LICENSE-KEY` in `chatbot.py`.

    ```python
    license_key = "LICENSE-KEY"
    ```

    ![Dynamsoft Barcode Reader license key](https://github.com/yushulx/flet-chat-app-gemini-barcode/assets/2202306/59535e1a-3f8e-4711-adb0-2610476848fd)

3. Run the app:

    ```bash
    flet run chatbot.py
    ```

   ![gemini-chat-app](https://github.com/yushulx/flet-chat-app-gemini-barcode/assets/2202306/9b4da08d-ca94-4a64-95b4-c6e5f1dfd985)
