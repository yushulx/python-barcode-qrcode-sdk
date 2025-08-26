# USB Camera to IP Camera with Barcode Scanning

A complete solution for transforming your USB camera into an IP camera with both web access and a professional desktop client! This system includes a Python server that streams video from any USB camera over your local network, plus a modern GUI client for viewing and managing camera streams.

Real-time barcode scanning powered by **Dynamsoft Barcode Reader**! The GUI client also supports live barcode detection with visual overlays showing detected codes directly on the video stream.

https://github.com/user-attachments/assets/b244a25a-f463-4130-b3aa-b25c2ccdeea1


## 📋 Requirements

- **Python**: 3.7 or higher
- **Hardware**: USB camera connected to your PC
- [30-day Trial License Key](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) for Dynamsoft Barcode Reader

## 🛠️ Installation

1. **Clone or download** this repository
2. **Install server dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Install GUI client dependencies**:
   ```bash
   cd gui_client
   pip install -r requirements.txt
   ```

4. Update the license key in `gui_client/barcode_scanner.py` for barcode scanning.
    
    ```python
    license_key = "LICENSE-KEY"
    ```
    

## 🎯 Quick Start

### 1. Start the IP Camera Server

```bash
python ip_camera_server.py
```

The server will:
- Detect your USB camera automatically
- Start streaming on port 5000
- Create a web interface at `http://localhost:5000`

### 2. Access Your Camera

#### Option A: Web Browser
- **Local**: `http://localhost:5000`
- **Network**: `http://YOUR_IP_ADDRESS:5000`

#### Option B: GUI Client
```bash
cd gui_client
python main.py
```

Then:
1. Click "Connect to Camera"
2. Enter connection details:
   - **IP Address**: `localhost` (or your PC's IP)
   - **Port**: `5000`
   - **Stream Path**: `/video_feed`
3. Click "Connect" to start streaming
4. **Enable Barcode Scanning** (optional):
   - Check "Enable Barcode Scanning" in the control panel
   - Point camera at barcodes/QR codes to see real-time detection
   - Detected codes appear as green overlays with yellow text
   - Results are displayed in the "Detected Barcodes" text area

   ![IP camera viewer with barcode scanning](https://www.dynamsoft.com/codepool/img/2025/08/ip-camera-viewer.png)


