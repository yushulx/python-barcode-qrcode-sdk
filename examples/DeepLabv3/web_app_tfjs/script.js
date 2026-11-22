// TensorFlow.js Document Detection Web App
// Configuration
const MODEL_PATH = 'tfjs_model/model.json';
const INPUT_SIZE = 384;
const MEAN = [0.485, 0.456, 0.406];
const STD = [0.229, 0.224, 0.225];

// State
let model = null;
let isWebcamActive = false;
let webcamStream = null;
let isProcessing = false;
let frameCount = 0;
let fpsInterval = null;

// DOM Elements
const statusText = document.getElementById('status-text');
const statusDot = document.querySelector('.status-dot');
const webcamBtn = document.getElementById('webcam-btn');
const fileInput = document.getElementById('file-input');
const canvas = document.getElementById('output-canvas');
const ctx = canvas.getContext('2d');
const webcamVideo = document.getElementById('webcam-video');
const sourceImage = document.getElementById('source-image');
const backendSelect = document.getElementById('backend-select');

// Metrics Elements
const preprocessEl = document.getElementById('preprocess-time');
const inferenceEl = document.getElementById('inference-time');
const postprocessEl = document.getElementById('postprocess-time');
const totalEl = document.getElementById('total-time');
const fpsEl = document.getElementById('fps-counter');

// Initialization
async function init(backend = 'webgl') {
    try {
        // Enable production mode for performance
        tf.enableProdMode();

        webcamBtn.disabled = true;
        updateStatus(`Initializing ${backend}...`, 'loading');

        // Set TensorFlow.js backend with fallback
        try {
            await tf.setBackend(backend);
            await tf.ready();
        } catch (backendError) {
            console.warn(`${backend} backend not available, falling back to webgl:`, backendError);
            if (backend !== 'webgl') {
                await tf.setBackend('webgl');
                await tf.ready();
                backendSelect.value = 'webgl';
            } else {
                throw backendError;
            }
        }

        console.log(`TF.js backend: ${tf.getBackend()}`);
        document.getElementById('backend-type').textContent = tf.getBackend();

        updateStatus('Loading Model...', 'loading');

        // Dispose existing model if any
        if (model) {
            model.dispose();
            model = null;
        }

        // Load the TensorFlow.js graph model
        model = await tf.loadGraphModel(MODEL_PATH);
        console.log('Model loaded successfully');

        // Log model info
        console.log('Model inputs:', model.inputs);
        console.log('Model outputs:', model.outputs);

        updateStatus('Ready', 'ready');
        webcamBtn.disabled = false;

        // Warmup
        console.log('Warming up model...');
        const dummyInput = tf.zeros([1, INPUT_SIZE, INPUT_SIZE, 3]);
        const warmupResult = await model.executeAsync(dummyInput);

        // Dispose warmup tensors
        dummyInput.dispose();
        if (Array.isArray(warmupResult)) {
            warmupResult.forEach(t => t.dispose());
        } else {
            warmupResult.dispose();
        }

        console.log('Warmup complete');

    } catch (e) {
        console.error('Initialization error:', e);
        updateStatus(`Error: ${e.message}`, 'error');
    }
}

// Handle Backend Change
backendSelect.addEventListener('change', async (e) => {
    await init(e.target.value);
});

// Start initialization
init(backendSelect.value);

// Helper: Update Status
function updateStatus(text, type) {
    statusText.textContent = text;
    statusDot.className = `status-dot ${type}`;
}

// Helper: Preprocess Image using TensorFlow.js
function preprocess(imageSource) {
    const startTime = performance.now();

    // Use tf.tidy to auto-dispose intermediate tensors
    const tensor = tf.tidy(() => {
        // Convert image to tensor [H, W, 3]
        let imageTensor = tf.browser.fromPixels(imageSource);

        // Resize to INPUT_SIZE x INPUT_SIZE
        imageTensor = tf.image.resizeBilinear(imageTensor, [INPUT_SIZE, INPUT_SIZE]);

        // Normalize to 0-1 range
        imageTensor = imageTensor.toFloat().div(255.0);

        // Apply ImageNet normalization: (x - mean) / std
        const mean = tf.tensor1d(MEAN);
        const std = tf.tensor1d(STD);
        imageTensor = imageTensor.sub(mean).div(std);

        // Add batch dimension: [H, W, C] -> [1, H, W, C]
        // Note: TF.js model expects NHWC format
        imageTensor = imageTensor.expandDims(0);

        return imageTensor;
    });

    return {
        tensor,
        time: performance.now() - startTime
    };
}

// === Pure JS Geometry Utils ===

// Find convex hull using Monotone Chain algorithm
function convexHull(points) {
    points.sort((a, b) => a.x === b.x ? a.y - b.y : a.x - b.x);

    const cross = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);

    const lower = [];
    for (let p of points) {
        while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
            lower.pop();
        }
        lower.push(p);
    }

    const upper = [];
    for (let i = points.length - 1; i >= 0; i--) {
        const p = points[i];
        while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
            upper.pop();
        }
        upper.push(p);
    }

    upper.pop();
    lower.pop();
    return lower.concat(upper);
}

// Find 4 corners from a set of points
function findCorners(points) {
    if (points.length < 4) return null;

    let cx = 0, cy = 0;
    for (let p of points) {
        cx += p.x;
        cy += p.y;
    }
    cx /= points.length;
    cy /= points.length;

    let tl = points[0], tr = points[0], br = points[0], bl = points[0];
    let maxDistTL = -1, maxDistTR = -1, maxDistBR = -1, maxDistBL = -1;

    for (let p of points) {
        const dx = p.x - cx;
        const dy = p.y - cy;
        const dist = dx * dx + dy * dy;

        if (dx < 0 && dy < 0 && dist > maxDistTL) { tl = p; maxDistTL = dist; }
        if (dx > 0 && dy < 0 && dist > maxDistTR) { tr = p; maxDistTR = dist; }
        if (dx > 0 && dy > 0 && dist > maxDistBR) { br = p; maxDistBR = dist; }
        if (dx < 0 && dy > 0 && dist > maxDistBL) { bl = p; maxDistBL = dist; }
    }

    return [tl, tr, br, bl];
}

// Helper: Postprocess - handles NHWC format [1, H, W, 2]
function postprocess(outputTensor, originalWidth, originalHeight) {
    const startTime = performance.now();

    // Get output shape and data
    const shape = outputTensor.shape;
    console.log('Output shape:', shape);

    // Shape should be [1, 384, 384, 2] for NHWC
    const data = outputTensor.dataSync();
    const height = shape[1];
    const width = shape[2];
    const numClasses = shape[3];

    const size = height * width;
    const mask = new Uint8Array(size);
    const points = [];
    const step = 4;

    // Output is [1, H, W, 2] - channel last (NHWC)
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const i = y * width + x;
            // For NHWC: index = (y * W + x) * numClasses + c
            const bgScore = data[i * numClasses];      // Channel 0: background
            const docScore = data[i * numClasses + 1]; // Channel 1: document

            if (docScore > bgScore) {
                mask[i] = 1;
                if (x % step === 0 && y % step === 0) {
                    points.push({ x, y });
                }
            } else {
                mask[i] = 0;
            }
        }
    }

    let corners = null;
    if (points.length > 20) {
        const hull = convexHull(points);
        const rawCorners = findCorners(hull);

        if (rawCorners) {
            const scaleX = originalWidth / width;
            const scaleY = originalHeight / height;

            corners = rawCorners.map(p => ({
                x: p.x * scaleX,
                y: p.y * scaleY
            }));
        }
    }

    return {
        mask,
        maskWidth: width,
        maskHeight: height,
        corners,
        time: performance.now() - startTime
    };
}

// Helper: Draw Results
function drawResults(imageSource, mask, maskWidth, maskHeight, corners) {
    const width = canvas.width;
    const height = canvas.height;

    // Draw original image
    ctx.drawImage(imageSource, 0, 0, width, height);

    const showMask = document.getElementById('show-mask').checked;
    const showBoundary = document.getElementById('show-boundary').checked;

    if (showMask && mask) {
        // Create ImageData from mask
        const smallCanvas = document.createElement('canvas');
        smallCanvas.width = maskWidth;
        smallCanvas.height = maskHeight;
        const smallCtx = smallCanvas.getContext('2d');
        const imgData = smallCtx.createImageData(maskWidth, maskHeight);
        const data = imgData.data;

        for (let i = 0; i < maskWidth * maskHeight; i++) {
            if (mask[i] === 1) {
                const idx = i * 4;
                data[idx] = 0;     // R
                data[idx + 1] = 255; // G
                data[idx + 2] = 0;   // B
                data[idx + 3] = 100; // Alpha
            }
        }
        smallCtx.putImageData(imgData, 0, 0);

        // Draw scaled up
        ctx.drawImage(smallCanvas, 0, 0, width, height);
    }

    if (showBoundary && corners) {
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(corners[0].x, corners[0].y);
        for (let i = 1; i < 4; i++) {
            ctx.lineTo(corners[i].x, corners[i].y);
        }
        ctx.closePath();
        ctx.stroke();

        // Draw corners
        ctx.fillStyle = 'blue';
        corners.forEach((p, i) => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 5, 0, 2 * Math.PI);
            ctx.fill();
        });
    }
}

// Main Processing Loop
async function processFrame(imageSource) {
    if (isProcessing || !model) return;
    isProcessing = true;

    try {
        // 1. Preprocess
        const preResult = preprocess(imageSource);
        preprocessEl.textContent = `${preResult.time.toFixed(1)} ms`;

        // 2. Inference
        const startTime = performance.now();

        // Execute model - use executeAsync for graph models
        const output = await model.executeAsync(preResult.tensor);

        const inferTime = performance.now() - startTime;
        inferenceEl.textContent = `${inferTime.toFixed(1)} ms`;

        // Handle output (could be single tensor or array)
        const outputTensor = Array.isArray(output) ? output[0] : output;

        // 3. Postprocess
        const postResult = postprocess(outputTensor, canvas.width, canvas.height);
        postprocessEl.textContent = `${postResult.time.toFixed(1)} ms`;

        // Total Time
        const totalTime = preResult.time + inferTime + postResult.time;
        totalEl.textContent = `${totalTime.toFixed(1)} ms`;

        // Draw
        drawResults(imageSource, postResult.mask, postResult.maskWidth, postResult.maskHeight, postResult.corners);

        // Dispose tensors to prevent memory leaks
        preResult.tensor.dispose();
        if (Array.isArray(output)) {
            output.forEach(t => t.dispose());
        } else {
            output.dispose();
        }

    } catch (e) {
        console.error('Processing error:', e);
    } finally {
        isProcessing = false;
        frameCount++;
    }
}

// Event Listeners
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            sourceImage.src = e.target.result;
            sourceImage.onload = () => {
                // Stop webcam if active
                if (isWebcamActive) stopWebcam();

                // Resize canvas to match image aspect ratio
                const aspect = sourceImage.width / sourceImage.height;
                const maxWidth = 800;
                canvas.width = Math.min(sourceImage.width, maxWidth);
                canvas.height = canvas.width / aspect;

                processFrame(sourceImage);
            };
        };
        reader.readAsDataURL(file);
    }
});

webcamBtn.addEventListener('click', () => {
    if (isWebcamActive) {
        stopWebcam();
    } else {
        startWebcam();
    }
});

async function startWebcam() {
    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        });
        webcamVideo.srcObject = webcamStream;
        webcamVideo.play();

        webcamVideo.onloadedmetadata = () => {
            canvas.width = webcamVideo.videoWidth;
            canvas.height = webcamVideo.videoHeight;
            isWebcamActive = true;
            webcamBtn.textContent = 'Stop Webcam';
            webcamBtn.classList.replace('primary', 'secondary');

            // Start loop
            requestAnimationFrame(webcamLoop);

            // Start FPS counter
            frameCount = 0;
            fpsInterval = setInterval(() => {
                fpsEl.textContent = frameCount;
                frameCount = 0;
            }, 1000);
        };
    } catch (e) {
        console.error(e);
        alert('Failed to access webcam');
    }
}

function stopWebcam() {
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
    isWebcamActive = false;
    webcamBtn.textContent = 'Start Webcam';
    webcamBtn.classList.replace('secondary', 'primary');
    if (fpsInterval) clearInterval(fpsInterval);
}

function webcamLoop() {
    if (!isWebcamActive) return;

    processFrame(webcamVideo).then(() => {
        requestAnimationFrame(webcamLoop);
    });
}
