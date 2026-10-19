# Document Detection Application

A deep learning-based document boundary detection application using DeepLabV3 semantic segmentation with MobileNetV3-Large backbone. Available as both a desktop GUI (PySide6) and a web application (pure JavaScript with ONNX Runtime).

## Features

### Desktop Application (Python + PySide6)
- 📁 **Image Upload**: Load and process images from your file system
- 📷 **Real-time Webcam**: Live document detection from webcam feed
- 🎯 **Accurate Detection**: DeepLabV3 with MobileNetV3-Large backbone
- 📊 **Performance Metrics**: Real-time display of preprocessing, inference, and post-processing times
- 💾 **Export Results**: Save overlay, mask, and cropped document images
- 🖼️ **Interactive Viewer**: Zoom, pan, and fit-to-window controls

### Web Application (Pure JavaScript)
- 🌐 **Browser-based**: Runs entirely in the browser using ONNX Runtime Web
- ⚡ **No Backend Required**: All inference happens client-side via WebAssembly
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🎨 **Modern UI**: Clean, premium interface with real-time metrics
- 📸 **Webcam Support**: Real-time document detection in the browser

## Model Performance

**MobileNetV3-Large Backbone:**
- **Parameters**: 11,020,594
- **Input Size**: 384×384
- **Inference Time** (CPU): ~180-210ms
- **FPS**: ~4-5 (CPU), ~30+ (GPU)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

```bash
pip install -r requirements.txt
```


## Usage

### Desktop Application

Run the desktop GUI application:

```bash
python main.py
```

**Controls:**
- **Load Image**: Open an image file for processing
- **Start Webcam**: Enable real-time webcam detection
- **Process Image**: Manually process the current image
- **Export Results**: Save processed images to disk
- **Clear**: Reset the application state

### Web Application

1. **Generate ONNX model** (first time only):
    ```bash
    python export_onnx.py
    ```

2. **Start the web server**:
    ```bash
    cd web_app
    python -m http.server
    ```

3. **Open in browser**: Navigate to `http://localhost:8000`

The web app will load the ONNX model and run inference entirely in your browser using WebAssembly.

## Credits

This project is based on the LearnOpenCV article:
[Deep Learning Based Document Segmentation Using Semantic Segmentation DeepLabV3 on Custom Dataset](https://learnopencv.com/deep-learning-based-document-segmentation-using-semantic-segmentation-deeplabv3-on-custom-dataset/) and [sampe code](https://github.com/spmallick/learnopencv/tree/master/Document-Scanner-Custom-Semantic-Segmentation-using-PyTorch-DeepLabV3).

