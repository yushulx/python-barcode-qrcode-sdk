// Configuration
const QUANTIZED_MODEL_PATH = 'document_detector_quant.onnx';
const FP32_MODEL_PATH = 'document_detector.onnx';
const INPUT_SIZE = 384;
const MEAN = [0.485, 0.456, 0.406];
const STD = [0.229, 0.224, 0.225];

// State
let session = null;
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
async function init(backend = 'wasm') {
    try {
        webcamBtn.disabled = true;
        updateStatus(`Initializing ${backend}...`, 'loading');

        // Initialize ONNX Runtime
        const option = {
            executionProviders: [backend],
            graphOptimizationLevel: 'all'
        };

        // Optimization for WASM
        if (backend === 'wasm') {
            option.executionMode = 'parallel';
            option.intraOpNumThreads = navigator.hardwareConcurrency || 4;
        }

        // Select model based on backend
        // WASM -> Quantized (INT8) for CPU speed
        // WebGL/WebGPU -> FP32 for GPU shader compatibility
        const modelPath = backend === 'wasm' ? QUANTIZED_MODEL_PATH : FP32_MODEL_PATH;

        updateStatus(`Loading Model (${backend})...`, 'loading');

        // Release existing session if any
        if (session) {
            session = null;
        }

        session = await ort.InferenceSession.create(modelPath, option);

        // Log the execution provider
        console.log('Inference Session created with provider:', session.handler.backendName);
        document.getElementById('backend-type').textContent = session.handler.backendName;

        updateStatus('Ready', 'ready');
        webcamBtn.disabled = false;

        // Warmup
        console.log('Warming up model...');
        const dummyInput = new Float32Array(1 * 3 * INPUT_SIZE * INPUT_SIZE).fill(0);
        const tensor = new ort.Tensor('float32', dummyInput, [1, 3, INPUT_SIZE, INPUT_SIZE]);
        await session.run({ input: tensor });
        console.log('Warmup complete');

    } catch (e) {
        console.error(e);
        updateStatus(`Error: ${e.message}`, 'error');
    }
}

// Handle Backend Change
backendSelect.addEventListener('change', (e) => {
    init(e.target.value);
});

// Start initialization immediately
init(backendSelect.value);
init();

// Helper: Update Status
function updateStatus(text, type) {
    statusText.textContent = text;
    statusDot.className = `status-dot ${type}`;
}

// Helper: Preprocess Image
function preprocess(imageData) {
    const startTime = performance.now();

    // 1. Resize to 384x384
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = INPUT_SIZE;
    tempCanvas.height = INPUT_SIZE;
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.drawImage(imageData, 0, 0, INPUT_SIZE, INPUT_SIZE);

    const resizedData = tempCtx.getImageData(0, 0, INPUT_SIZE, INPUT_SIZE);
    const { data } = resizedData;

    // 2. Normalize and HWC -> CHW
    const float32Data = new Float32Array(3 * INPUT_SIZE * INPUT_SIZE);

    for (let i = 0; i < INPUT_SIZE * INPUT_SIZE; i++) {
        const r = data[i * 4] / 255.0;
        const g = data[i * 4 + 1] / 255.0;
        const b = data[i * 4 + 2] / 255.0;

        // Normalize: (value - mean) / std
        float32Data[i] = (r - MEAN[0]) / STD[0]; // R
        float32Data[INPUT_SIZE * INPUT_SIZE + i] = (g - MEAN[1]) / STD[1]; // G
        float32Data[2 * INPUT_SIZE * INPUT_SIZE + i] = (b - MEAN[2]) / STD[2]; // B
    }

    const tensor = new ort.Tensor('float32', float32Data, [1, 3, INPUT_SIZE, INPUT_SIZE]);

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

// Find 4 corners from a set of points (simplified approximation)
function findCorners(points) {
    if (points.length < 4) return null;

    // Find center
    let cx = 0, cy = 0;
    for (let p of points) {
        cx += p.x;
        cy += p.y;
    }
    cx /= points.length;
    cy /= points.length;

    // Find top-left, top-right, bottom-right, bottom-left
    // based on quadrants relative to center
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

// Helper: Postprocess
function postprocess(outputTensor, originalWidth, originalHeight) {
    const startTime = performance.now();

    const data = outputTensor.data;
    const size = INPUT_SIZE * INPUT_SIZE;

    // Create mask array (0 or 1)
    const mask = new Uint8Array(size);
    const points = [];

    // Threshold and collect points
    // We downsample points to speed up hull calculation
    const step = 4;

    for (let y = 0; y < INPUT_SIZE; y++) {
        for (let x = 0; x < INPUT_SIZE; x++) {
            const i = y * INPUT_SIZE + x;
            const bgScore = data[i];
            const docScore = data[size + i];

            if (docScore > bgScore) {
                mask[i] = 1;
                // Collect boundary points (simple edge check)
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
        // 1. Get Convex Hull
        const hull = convexHull(points);

        // 2. Find 4 corners
        const rawCorners = findCorners(hull);

        if (rawCorners) {
            // Scale corners to original image size
            const scaleX = originalWidth / INPUT_SIZE;
            const scaleY = originalHeight / INPUT_SIZE;

            corners = rawCorners.map(p => ({
                x: p.x * scaleX,
                y: p.y * scaleY
            }));
        }
    }

    return {
        mask,
        corners,
        time: performance.now() - startTime
    };
}

// Helper: Draw Results
function drawResults(imageSource, mask, corners) {
    const width = canvas.width;
    const height = canvas.height;

    // Draw original image
    ctx.drawImage(imageSource, 0, 0, width, height);

    const showMask = document.getElementById('show-mask').checked;
    const showBoundary = document.getElementById('show-boundary').checked;

    if (showMask && mask) {
        // Create ImageData from mask
        // We need to resize the 384x384 mask to canvas size
        // For speed, we draw to a small canvas then scale up
        const smallCanvas = document.createElement('canvas');
        smallCanvas.width = INPUT_SIZE;
        smallCanvas.height = INPUT_SIZE;
        const smallCtx = smallCanvas.getContext('2d');
        const imgData = smallCtx.createImageData(INPUT_SIZE, INPUT_SIZE);
        const data = imgData.data;

        for (let i = 0; i < INPUT_SIZE * INPUT_SIZE; i++) {
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
    if (isProcessing) return;
    isProcessing = true;

    try {
        // 1. Preprocess
        const preResult = preprocess(imageSource);
        preprocessEl.textContent = `${preResult.time.toFixed(1)} ms`;

        // 2. Inference
        const startTime = performance.now();
        const feeds = { input: preResult.tensor };
        const results = await session.run(feeds);
        const output = results.output; // Assuming output name is 'output'
        const inferTime = performance.now() - startTime;
        inferenceEl.textContent = `${inferTime.toFixed(1)} ms`;

        // 3. Postprocess
        const postResult = postprocess(output, canvas.width, canvas.height);
        postprocessEl.textContent = `${postResult.time.toFixed(1)} ms`;

        // Total Time
        const totalTime = preResult.time + inferTime + postResult.time;
        totalEl.textContent = `${totalTime.toFixed(1)} ms`;

        // Draw
        drawResults(imageSource, postResult.mask, postResult.corners);

    } catch (e) {
        console.error(e);
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
