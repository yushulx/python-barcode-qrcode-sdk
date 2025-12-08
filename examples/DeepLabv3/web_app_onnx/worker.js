// Configuration
const QUANTIZED_MODEL_PATH = 'document_detector_quant.onnx';
const FP32_MODEL_PATH = 'document_detector.onnx';
const INPUT_SIZE = 384;
const MEAN = [0.485, 0.456, 0.406];
const STD = [0.229, 0.224, 0.225];

// Import ONNX Runtime Web
importScripts('https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/ort.all.min.js');

// Configure WASM paths to load from CDN
ort.env.wasm.wasmPaths = 'https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/';

// Suppress ONNX Runtime warnings
ort.env.logLevel = 'error';
ort.env.wasm.logLevel = 'error';

let session = null;

// Helper: Fetch and Cache Model
async function getModelBuffer(path) {
    try {
        const cache = await caches.open('onnx-models-v1');
        let response = await cache.match(path);

        if (!response) {
            console.log(`Downloading ${path}...`);
            response = await fetch(path);
            if (response.ok) {
                cache.put(path, response.clone());
            }
        } else {
            console.log(`Loading ${path} from cache...`);
        }

        if (!response.ok) throw new Error(`Failed to fetch ${path}`);
        return await response.arrayBuffer();
    } catch (e) {
        console.error('Caching failed:', e);
        return path; // Fallback to path string
    }
}

// Helper: Preprocess Image
function preprocess(imageData) {
    const startTime = performance.now();

    // 1. Resize to 384x384
    // Since we are in a worker, we can use OffscreenCanvas if available, 
    // or we expect the main thread to send us an ImageBitmap that we can draw to OffscreenCanvas
    // However, OffscreenCanvas support is good in modern browsers.

    const offscreen = new OffscreenCanvas(INPUT_SIZE, INPUT_SIZE);
    const ctx = offscreen.getContext('2d');
    ctx.drawImage(imageData, 0, 0, INPUT_SIZE, INPUT_SIZE);

    const resizedData = ctx.getImageData(0, 0, INPUT_SIZE, INPUT_SIZE);
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

// Message Handler
self.onmessage = async (e) => {
    const { type, data, id } = e.data;

    if (type === 'init') {
        try {
            const backend = data.backend;

            // Initialize ONNX Runtime
            const option = {
                executionProviders: [backend],
                graphOptimizationLevel: 'all',
                logSeverityLevel: 3
            };

            if (backend === 'wasm') {
                // 'parallel' execution mode often adds overhead for WASM. 
                // 'sequential' is usually faster for single inference.
                option.executionMode = 'sequential';

                // Cap threads to 4. Too many threads can cause synchronization overhead.
                // For MobileNetV3 (lightweight model), 2-4 threads is usually optimal.
                const threads = Math.min(navigator.hardwareConcurrency || 4, 4);
                option.intraOpNumThreads = threads;
                console.log(`Configuring WASM with ${threads} threads`);
            }

            const modelPath = backend === 'wasm' ? QUANTIZED_MODEL_PATH : FP32_MODEL_PATH;

            if (session) {
                session = null;
            }

            const modelData = await getModelBuffer(modelPath);
            session = await ort.InferenceSession.create(modelData, option);

            // Warmup
            const dummyInput = new Float32Array(1 * 3 * INPUT_SIZE * INPUT_SIZE).fill(0);
            const tensor = new ort.Tensor('float32', dummyInput, [1, 3, INPUT_SIZE, INPUT_SIZE]);
            await session.run({ input: tensor });

            self.postMessage({
                type: 'init_complete',
                backend: session.handler.backendName
            });

        } catch (err) {
            self.postMessage({ type: 'error', error: err.message });
        }
    } else if (type === 'detect') {
        if (!session) return;

        try {
            // Preprocess
            const preResult = preprocess(data.image);

            // Inference
            const startTime = performance.now();
            const feeds = { input: preResult.tensor };
            const results = await session.run(feeds);
            const output = results.output;
            const inferTime = performance.now() - startTime;

            // Transfer output data back
            // We copy the data to avoid detachment issues if we want to reuse buffers, 
            // but here we just send the Float32Array.
            self.postMessage({
                type: 'detect_complete',
                id: id,
                output: output.data,
                dims: output.dims,
                timings: {
                    preprocess: preResult.time,
                    inference: inferTime
                }
            }, [output.data.buffer]); // Transferable

        } catch (err) {
            self.postMessage({ type: 'error', error: err.message });
        }
    }
};