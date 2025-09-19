# Dynamsoft SDK Version Comparison Tool

This comparison tool allows you to compare 1D/2D barcode detection performance between different versions of the Dynamsoft Capture Vision SDK. The tool provides a comprehensive graphical interface with side-by-side visual comparisons, detailed results analysis, and performance metrics.

## Features

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

### 🖼️ **Visual Comparison Interface**
- **Side-by-Side Views**: Compare detection results visually

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

## Usage

```bash
python sdk_comparison.py
```

![version comparison tool](https://www.dynamsoft.com/codepool/img/2025/09/python-sdk-comparison-tool.png)