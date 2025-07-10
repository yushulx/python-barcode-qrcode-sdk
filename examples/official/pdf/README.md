# Dynamsoft Barcode Reader - Enhanced GUI Application

A modern, feature-rich GUI application for barcode detection and reading using the Dynamsoft Capture Vision SDK. This application provides a comprehensive graphical interface for processing images and PDF files with professional barcode detection capabilities.

## 🚀 Features

### Core Functionality
- **Multi-format Support**: JPG, PNG, BMP, TIFF, WEBP image files
- **Native PDF Support**: Multi-page PDF processing using Dynamsoft SDK (no external dependencies)
- **Real-time Detection**: Fast barcode detection with visual annotations
- **Multi-page Navigation**: Easy navigation through PDF pages

### User Interface
- **Modern GUI**: Clean, intuitive interface with professional styling
- **Zoom & Pan**: Interactive image viewing with zoom controls (10%-500%)
- **Beautiful Results Display**: Color-coded results with background highlights
- **Drag & Drop**: Enhanced file loading support
- **Professional Layout**: Organized panels with clear visual hierarchy

### Results Management
- **Beautiful Formatting**: Enhanced result display with emojis, colors, and professional styling
- **Detailed Results**: Format, content, location with corner labels (TL, TR, BR, BL)
- **Smart Area Display**: Area calculations with K-unit formatting for large values
- **Export Options**: Export to TXT, CSV, or JSON formats
- **Clipboard Support**: Quick copy results to clipboard
- **Multi-page Results**: Organize results by page for PDF files

### Processing Options
- **Auto-processing**: Automatically detect barcodes when files are loaded
- **Confidence Display**: Optional confidence scores for each detection
- **Progress Tracking**: Real-time processing status and timing
- **Memory Monitoring**: Optional memory usage display

## 📋 Requirements

- Required Dependencies

    ```bash
    pip install dynamsoft-capture-vision-bundle opencv-python Pillow tkinterdnd2 psutil
    ```

- [30-day trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform)

## 🎯 Quick Start

### Run the Enhanced GUI
```bash
python gui_barcode_reader_enhanced.py
```
### Alternative: Command Line Interface
```bash
python command_line.py
```

## 📁 File Structure

```
📂 project/
├── 📄 command_line.py                  # Command-line interface
├── 🖥️ gui_barcode_reader_enhanced.py   # Enhanced GUI application
├──  requirements.txt                # Dependencies list
├── 📖 README.md                       # This documentation
└── 🎯 Sample files (barcode.jpg, barcodes.pdf)
```

## 🔧 Usage Guide

### Loading Files
1. **Click "📂 Load File"** button to browse for files
2. **Drag and drop** files directly onto the image area (enhanced support)
3. Supported formats: JPG, PNG, BMP, TIFF, WEBP, PDF (native support)

### Navigation (PDF Files)
- Use **◀ Prev/Next ▶** buttons for page navigation
- **Go to page** field for direct page jumping
- Page counter shows current position (e.g., "Page: 2/5")

### Image Controls
- **Zoom dropdown**: Select zoom level (10%-500% or Fit)
- **Zoom buttons**: Quick zoom in/out (🔍+ / 🔍-)
- **Reset button**: Return to fit-to-window view (↻)
- **Mouse wheel**: Zoom with Ctrl+scroll

### Processing
- **Auto-process**: Automatically detect barcodes when loading files
- **🔍 Detect Barcodes**: Manual processing trigger
- **Show confidence**: Toggle confidence scores display

### Results Display
- **Beautiful Formatting**: Color-coded results with professional styling
- **Corner Labels**: Location points shown as TL→TR→BR→BL format
- **Smart Units**: Area display with K-units for large values
- **Export**: Save results to TXT, CSV, or JSON files
- **Copy**: Quick copy to clipboard
- **Page Summary**: Shows barcode count per page



