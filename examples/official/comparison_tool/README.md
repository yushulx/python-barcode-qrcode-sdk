# Multi-Modal Detection Comparison Tool for Dynamsoft Capture Vision SDK

This comprehensive comparison tool allows you to compare detection performance between different versions of the Dynamsoft Capture Vision SDK across multiple detection modes. The tool provides an intuitive graphical interface with side-by-side visual comparisons, detailed results analysis, and performance metrics for **Barcode**, **MRZ (Machine Readable Zone)**, and **Document** detection.

## Demo Video
- Detect blurred 1D barcodes (Dataset: http://users.soe.ucsc.edu/~orazio/Data/Barcodes200909.zip)
  
   https://github.com/user-attachments/assets/d2f0a75d-6c56-4e7b-802f-6f2317976228

- Localize and recognize MRZ (Dataset: http://l3i-share.univ-lr.fr/)

  https://github.com/user-attachments/assets/7617ae99-4471-4b2c-a73d-b50943bb8ba9



## Features

### 🎯 **Multi-Modal Detection Support**
- **Barcode Detection**: 1D/2D barcodes with format identification and confidence scores
- **MRZ Detection**: Machine Readable Zone text from passports and ID documents  
- **Document Detection**: Document boundary detection with edge visualization


### 🔍 **Dynamic SDK Configuration**
- Configure and compare multiple SDK versions
- Automatic SDK version detection from virtual environments
- Support for custom Python environments

### 📁 **Advanced File Processing**
- **Drag & Drop Support**: Drop individual images or entire folders
- **Batch Processing**: Process multiple images automatically
- **Format Support**: PNG, JPG, JPEG, BMP, TIFF
- **File Filtering**: Automatic validation of image file existence
- **Progress Tracking**: Real-time processing progress indicators
- **Mode-Based Clearing**: Automatic cleanup when switching detection modes

### 🖼️ **Visual Comparison Interface**
- **Side-by-Side Views**: Compare detection results visually
- **Dynamic Overlays**: Different visualization for each detection mode:
  - Barcode: Colored rectangles with text and format labels
  - MRZ: Text line highlighting and boundaries  
  - Document: Edge contour visualization
- **Real-time Updates**: Instant visual feedback as processing completes

### 📊 **Enhanced Results Analysis**
- **Mode-Aware Metrics**: Performance comparison tailored to detection type
- **Result Counting**: Accurate counts for barcodes, MRZ lines, or documents
- **Processing Speed**: Timing comparisons between SDK versions
- **Export Capabilities**: CSV export of comparison results
- **Detailed Text Display**: Comprehensive result information with confidence scores and coordinates

## Installation

### Prerequisites
Install the required dependencies using the provided requirements file:

```bash
pip install -r requirements.txt
```

### Virtual Environment Setup (Recommended)
For comparing different SDK versions, set up separate virtual environments:

```bash
# Create environments for different SDK versions
python -m venv D:/envs/sdk_v1
python -m venv D:/envs/sdk_v2

# Activate and install different SDK versions
# Environment 1 (SDK v3.0.4100)
D:/envs/sdk_v1/Scripts/activate
pip install dynamsoft-capture-vision-bundle==3.0.4100

# Environment 2 (SDK v3.0.6000)  
D:/envs/sdk_v2/Scripts/activate
pip install dynamsoft-capture-vision-bundle==3.0.6000
```

## Quick Start

### Basic Usage
```bash
python sdk_comparison.py
```

### Detection Modes

The tool supports three distinct detection modes, easily selectable via the dropdown menu:

#### 🏷️ **Barcode Mode**
- Detects 1D and 2D barcodes (QR codes, Data Matrix, Code 128, etc.)
- Displays barcode text, format, and confidence scores
- Visual overlay shows detected barcode boundaries with colored rectangles

#### 📄 **MRZ Mode** 
- Detects Machine Readable Zone text from passports and ID documents
- Extracts text lines from MRZ areas
- Visual overlay highlights detected text regions

#### 📋 **Document Mode**
- Detects document boundaries and edges
- Useful for document scanning and preprocessing
- Visual overlay shows detected document contours

### Workflow
1. **Configure SDKs**: Click "🔧 Configure SDKs" to set up different SDK versions
2. **Select Detection Mode**: Choose from Barcode, MRZ, or Document in the dropdown
3. **Add Images**: Use "📁 Add Images" button or drag & drop images/folders
4. **View Results**: Compare detection results side-by-side with visual overlays
5. **Export Data**: Use "📤 Export to CSV" to save comparison results

![version comparison tool](https://www.dynamsoft.com/codepool/img/2025/09/python-sdk-comparison-tool.png)
