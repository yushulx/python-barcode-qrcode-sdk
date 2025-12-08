# Document Detection Web App

This is a web-based application for document detection and segmentation using DeepLabV3 (MobileNetV3 backbone) and ONNX Runtime Web. It runs entirely in the browser using WebAssembly (WASM) or WebGPU.

## Online Demo
https://yushulx.me/javascript-barcode-qr-code-scanner/examples/DeepLabv3/

## Features

- **Real-time Document Detection**: Segments documents from the background.
- **Multiple Backends**:
  - **WASM (CPU)**: Uses a quantized INT8 model for efficient CPU inference.
  - **WebGPU (GPU)**: Uses an FP32 model for high-performance GPU acceleration (requires a compatible browser).
- **Input Sources**: Support for both live webcam feed and image file uploads.
- **Visualization**: Displays the segmentation mask and document boundary overlay.
- **Performance Metrics**: Real-time tracking of pre-processing, inference, and post-processing times.
- **Model Caching**: Caches downloaded models locally to speed up subsequent loads.

## Prerequisites

- A modern web browser (Chrome, Edge, Firefox).
- For **WebGPU** support, you need a browser that supports the WebGPU API (e.g., latest Chrome or Edge) and compatible hardware.

## Setup & Usage

1. **Clone the repository** (if you haven't already).
2. **Serve the directory**:
   Because this application uses modern web standards (ES modules, WebGPU, Cache API), it must be served over HTTP/HTTPS. You cannot run it by simply opening `index.html` as a file.

   You can use any static file server. For example, using Python:

   ```bash
   # Python 3
   python -m http.server 8000
   ```

   Or using Node.js `http-server`:

   ```bash
   npx http-server .
   ```

3. **Open in Browser**:
   Navigate to `http://localhost:8000` (or the port shown by your server).


