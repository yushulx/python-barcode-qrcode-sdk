# Flet Chat App with Google AI and Dynamsoft Barcode Reader
The project demonstrates how to integrate [Dynamsoft Barcode Reader](https://pypi.org/project/dbr/) and [Gemini APIs](https://ai.google.dev/tutorials/python_quickstart) into a Flet chat app.

https://github.com/user-attachments/assets/b0f8efd2-ec66-4b02-95c8-e9df437410a7

## Installation

```bash
pip install -r requirements.txt

```

## Getting Started
1. Get an [API key](https://makersuite.google.com/app/apikey) for Gemini in Google AI Studio and replace the value of `API_KEY` in `chatbot.py`.
    
    ```python
    genai.configure(api_key='API_KEY')
    ```

    ![Gemini API key](https://www.dynamsoft.com/codepool/img/2024/09/gemini-api-key.png)

    
2. Request a [free trial license](https://www.dynamsoft.com/customer/license/trialLicense?product=dbr) for Dynamsoft Barcode Reader and replace the value of `LICENSE-KEY` in `chatbot.py`.

    ```python
    license_key = "LICENSE-KEY"
    ```

    ![Dynamsoft Barcode Reader license key](https://www.dynamsoft.com/codepool/img/2024/09/dynamsoft-barcode-reader-license.png)

3. Run the app:

    ```bash
    flet run chatbot.py
    ```

   ![gemini-chat-app](https://www.dynamsoft.com/codepool/img/2024/01/flet-chat-app-gemini-barcode-api.png)

## Blog
[How to Build Flet Chat App with Barcode and Gemini APIs](https://www.dynamsoft.com/codepool/python-flet-chat-app-barcode-gemini.html)
