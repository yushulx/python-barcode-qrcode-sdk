# Dynamsoft Capture Vision - Multi-Mode Scanner

A comprehensive PySide6-based desktop application for real-time and file-based detection of barcodes, documents, and MRZ (Machine Readable Zone) data using the Dynamsoft Capture Vision SDK.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-green.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-red.svg)
![Dynamsoft](https://img.shields.io/badge/Dynamsoft-SDK-orange.svg)

<img width="1590" height="1024" alt="Dynamsoft Capture Vision for barcode, mrz and document detection" src="https://github.com/user-attachments/assets/eddc931c-8313-4161-8364-e24507fe04c1" />

## 🌟 Features

### 📁 **Picture Mode**
- **Multi-format Support**: JPG, PNG, BMP, TIFF, WEBP, PDF
- **Native PDF Processing**: Built-in PDF page extraction and processing
- **Multi-page Navigation**: Browse through PDF pages with intuitive controls
- **Drag & Drop**: Easy file loading by dragging files into the application
- **Zoom Controls**: Multiple zoom levels (25% to 500%) with fit-to-window option
- **Visual Annotations**: Real-time overlay of detection results on images

### 📷 **Camera Mode**
- **Real-time Detection**: Live scanning with immediate visual feedback
- **Multiple Camera Support**: Automatic detection and selection of available cameras
- **Adjustable Settings**: Detection frequency control and various processing options
- **Live Annotations**: Real-time overlay of detection results on camera feed
- **Frame Capture**: Save current camera frame for further analysis

### 🔍 **Detection Modes**
1. **Barcode Detection**
   - QR Codes, Data Matrix, PDF417, Aztec, MaxiCode
   - Linear barcodes: Code 39, Code 128, EAN, UPC, etc.
   - Consistent color coding for multiple barcodes
   - Confidence scoring and validation

2. **Document Detection**
   - Automatic document boundary detection
   - Image deskewing and normalization
   - Side-by-side original/processed view
   - Document quality assessment

3. **MRZ (Machine Readable Zone)**
   - Passport and ID card reading
   - Complete personal information extraction
   - Document validation and verification
   - Parsed data display with structured formatting

## 🚀 Installation

### Prerequisites
```bash
pip install PySide6 opencv-python numpy
```

### Dynamsoft SDK
Install the Dynamsoft Capture Vision SDK:
```bash
pip install dynamsoft-capture-vision-bundle
```

**📝 Note**: The application includes a default trial license. For extended use, get a free 30-day trial license through **Settings** → **Enter License Key...** → **Get 30-Day Trial License**.

### Additional Dependencies
```bash
pip install psutil  # Optional: for memory monitoring
```

## 🏁 Quick Start

### Running the Application
```bash
python main.py
```

### Basic Usage

#### Picture Mode
1. Click **"📂 Load File"** or drag & drop an image/PDF
2. Select detection mode: **Barcode**, **Document**, or **MRZ**
3. Click **"🔍 Detect"** to process the file
4. View results in the right panel
5. Use zoom controls for detailed inspection
6. Export results in TXT, CSV, or JSON format

#### Camera Mode
1. Switch to **"📷 Camera Mode"** tab
2. Select your camera from the dropdown
3. Choose detection mode (Barcode/Document/MRZ)
4. Click **"📷 Start Camera"**
5. Enable **"Real-time Detection"**
6. Point camera at target objects
7. View live results in the results panel

## 🎛️ Interface Overview

### Main Window
- **Tabbed Interface**: Switch between Picture and Camera modes
- **Resizable Panels**: Adjust layout to your preference
- **Status Bar**: Real-time processing information and memory usage
- **Menu Bar**: Quick access to common functions and settings

### Picture Mode Layout
```
┌─────────────┬──────────────────┬─────────────┐
│   Control   │    Image         │   Results   │
│   Panel     │    Display       │   Panel     │
│             │                  │             │
│ • File Ops  │ • Zoom Controls  │ • Summary   │
│ • Settings  │ • Image View     │ • Details   │
│ • Actions   │ • Annotations    │ • Export    │
└─────────────┴──────────────────┴─────────────┘
```

### Camera Mode Layout
```
┌─────────────┬──────────────────┬─────────────┐
│   Camera    │    Live Feed     │   Live      │
│   Controls  │                  │   Results   │
│             │                  │             │
│ • Settings  │ • Real-time      │ • Recent    │
│ • Detection │   Annotations    │   Detections│
│ • Actions   │ • Controls       │ • History   │
└─────────────┴──────────────────┴─────────────┘
```


## 📝 File Support

### Image Formats
- **JPEG/JPG**: Standard photo format
- **PNG**: Lossless compression with transparency
- **BMP**: Windows bitmap format
- **TIFF/TIF**: High-quality image format
- **WEBP**: Modern web image format

### Document Formats
- **PDF**: Multi-page document support with native processing

### Camera Formats
- **USB Cameras**: Standard UVC-compatible cameras
- **Built-in Cameras**: Laptop/tablet integrated cameras
- **Network Cameras**: IP cameras (with proper drivers)

## 🔧 Configuration

### License Management
The application includes a built-in license management system:

#### Default License
- The application comes with a default trial license
- This license may expire and require renewal

#### Updating License Key
1. Go to **Settings** → **Enter License Key...**
2. **For new users**: Click **"🌐 Get 30-Day Trial License"** to open the Dynamsoft trial page
3. **For existing users**: Enter your valid Dynamsoft license key
4. Click **"Apply License"** to validate and apply
5. The license is tested before activation
6. Success confirmation will be shown

#### Getting a Trial License
- [**Free 30-Day Trial**](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform): Click the trial license button in the license dialog
- **Automatic Browser**: Opens the Dynamsoft trial page automatically
- **Quick Setup**: Fill out the form and receive license via email
- **Instant Activation**: Copy and paste the license key to activate immediately


