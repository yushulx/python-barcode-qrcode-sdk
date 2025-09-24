# Dynamsoft Barcode SDK Parameter Adjustment Tool 

A GUI application built with PySide6 to help developers find optimal parameters for barcode scanning using the Dynamsoft Barcode Reader SDK. This tool provides an intuitive interface for parameter tuning, real-time barcode detection, and automated parameter optimization.

## 🎯 Purpose

When working with barcode detection in various conditions (poor lighting, low quality images, different barcode types), finding the right parameters can be challenging and time-consuming. This tool simplifies the process by providing:

- **Visual Parameter Tuning**: Interactive controls for all barcode detection parameters
- **Real-time Testing**: Immediate feedback on parameter changes with live barcode detection
- **Auto-adjustment**: Intelligent parameter optimization that automatically tests different combinations
- **Multiple Barcode Format Support**: Comprehensive support for 40+ barcode formats
- **Template Management**: Save and load parameter configurations

## 🛠️ Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yushulx/python-barcode-qrcode-sdk.git
   cd python-barcode-qrcode-sdk/examples/official/template_config
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Dynamsoft License**
   - Obtain a license from [Dynamsoft](https://www.dynamsoft.com/customer/license/trialLicense)
   - Set the license in parameter_adjustment_tool.py:
       
        ```python
        error_code, error_message = LicenseManager.init_license(
                "LICENSE-KEY"
            )
        ```
    

## 🚀 Quick Start

1. **Launch the Application**
   ```bash
   python parameter_adjustment_tool.py
   ```

2. **Load an Image**
   - Drag and drop an image file onto the left panel, or
   - Use the Load Image button to browse for an image

3. **Adjust Parameters**
   - Use the parameter controls in the middle panel
   - Watch real-time results in the left panel
   - Monitor JSON output in the right panel

4. **Try Auto-Adjustment**
   - Click the "Auto Adjust" button
   - The tool will automatically test different parameter combinations
   - Stops when barcodes are successfully detected
