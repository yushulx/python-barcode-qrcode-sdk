# Server-side Barcode Detection over Socket

The sample code aims to carry out Dynamsoft barcode Qr code detection algorithms on the server side when the client-side CPU performance is insufficient. It is suitable for Raspberry Pi, Jetson Nano, and other embedded and IoT devices. 

## Environment

- Python 3.6 or above

## Installation
```
pip install barcode-qr-code-sdk
```

## Usage
1. Run `server.py`

    ```bash
    python server.py
    ```
2. Change the server address in `client.py`:

    ```python
    client.startClient('localhost', 80)
    ```
3. Run `client.py`

    ```bash
    python client.py
    ```

