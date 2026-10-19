#!/usr/bin/env python3
"""
USB Camera to IP Camera Server
Converts a USB camera into an IP camera accessible over the local network.
"""

import cv2
import threading
import time
import socket
from flask import Flask, Response, render_template_string, jsonify, request
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ip_camera.log'),
        logging.StreamHandler()
    ]
)

class IPCameraServer:
    def __init__(self, camera_index=0, host='0.0.0.0', port=5000, resolution=(640, 480), fps=30):
        """
        Initialize IP Camera Server
        
        Args:
            camera_index (int): USB camera index (0 for first camera)
            host (str): Host IP to bind server to
            port (int): Port number for the web server
            resolution (tuple): Camera resolution (width, height)
            fps (int): Frames per second
        """
        self.camera_index = camera_index
        self.host = host
        self.port = port
        self.resolution = resolution
        self.fps = fps
        
        self.app = Flask(__name__)
        self.camera = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        
        # Statistics
        self.frame_count = 0
        self.start_time = time.time()
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page with video stream"""
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>USB IP Camera</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f0f0f0;
                        text-align: center;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }
                    h1 {
                        color: #333;
                        margin-bottom: 20px;
                    }
                    .video-container {
                        margin: 20px 0;
                        border: 2px solid #ddd;
                        border-radius: 8px;
                        overflow: hidden;
                        display: inline-block;
                    }
                    img {
                        display: block;
                        max-width: 100%;
                        height: auto;
                    }
                    .controls {
                        margin: 20px 0;
                    }
                    .controls button {
                        background-color: #007bff;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        margin: 5px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                    }
                    .controls button:hover {
                        background-color: #0056b3;
                    }
                    .info {
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                        text-align: left;
                    }
                    .status {
                        display: inline-block;
                        padding: 5px 10px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    .status.online {
                        background-color: #d4edda;
                        color: #155724;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>USB IP Camera Stream</h1>
                    <div class="status online">🟢 Camera Online</div>
                    
                    <div class="video-container">
                        <img src="{{ url_for('video_feed') }}" alt="Camera Stream">
                    </div>
                    
                    <div class="controls">
                        <button onclick="refreshStream()">🔄 Refresh Stream</button>
                        <button onclick="toggleFullscreen()">🔍 Fullscreen</button>
                        <button onclick="showInfo()">ℹ️ Info</button>
                    </div>
                    
                    <div class="info">
                        <h3>Camera Information</h3>
                        <p><strong>Resolution:</strong> {{ resolution[0] }} x {{ resolution[1] }}</p>
                        <p><strong>Server:</strong> {{ host }}:{{ port }}</p>
                        <p><strong>Access URL:</strong> http://{{ local_ip }}:{{ port }}</p>
                        <p><strong>Stream URL:</strong> http://{{ local_ip }}:{{ port }}/video_feed</p>
                        <p><strong>Status:</strong> <span id="status">Loading...</span></p>
                    </div>
                </div>
                
                <script>
                    function refreshStream() {
                        const img = document.querySelector('.video-container img');
                        img.src = img.src.split('?')[0] + '?t=' + new Date().getTime();
                    }
                    
                    function toggleFullscreen() {
                        const img = document.querySelector('.video-container img');
                        if (img.requestFullscreen) {
                            img.requestFullscreen();
                        }
                    }
                    
                    function showInfo() {
                        fetch('/status')
                            .then(response => response.json())
                            .then(data => {
                                alert(`Camera Status:\\n\\nFPS: ${data.fps}\\nFrames: ${data.frames}\\nUptime: ${data.uptime}s\\nResolution: ${data.resolution}`);
                            });
                    }
                    
                    function updateStatus() {
                        fetch('/status')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('status').innerHTML = 
                                    `FPS: ${data.fps} | Frames: ${data.frames} | Uptime: ${data.uptime}s`;
                            })
                            .catch(() => {
                                document.getElementById('status').innerHTML = 'Connection Error';
                            });
                    }
                    
                    // Update status every 5 seconds
                    setInterval(updateStatus, 5000);
                    updateStatus();
                </script>
            </body>
            </html>
            """
            return render_template_string(
                html_template,
                resolution=self.resolution,
                host=self.host,
                port=self.port,
                local_ip=self.get_local_ip()
            )
            
        @self.app.route('/video_feed')
        def video_feed():
            """Video streaming route"""
            return Response(
                self.generate_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
            
        @self.app.route('/status')
        def status():
            """API endpoint for camera status"""
            current_time = time.time()
            uptime = int(current_time - self.start_time)
            current_fps = self.frame_count / max(1, uptime)
            
            return jsonify({
                'status': 'online' if self.running else 'offline',
                'fps': f"{current_fps:.1f}",
                'frames': self.frame_count,
                'uptime': uptime,
                'resolution': f"{self.resolution[0]}x{self.resolution[1]}",
                'timestamp': datetime.now().isoformat()
            })
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def initialize_camera(self):
        """Initialize the USB camera"""
        try:
            logging.info(f"Initializing camera {self.camera_index}...")
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                logging.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Test capture
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logging.error("Failed to capture test frame")
                return False
            
            logging.info(f"Camera initialized successfully: {self.resolution[0]}x{self.resolution[1]} @ {self.fps}fps")
            return True
            
        except Exception as e:
            logging.error(f"Camera initialization error: {e}")
            return False
    
    def capture_frames(self):
        """Capture frames from camera in a separate thread"""
        logging.info("Starting frame capture thread...")
        
        while self.running:
            try:
                if self.camera is None or not self.camera.isOpened():
                    logging.warning("Camera not available, attempting to reconnect...")
                    if not self.initialize_camera():
                        time.sleep(5)
                        continue
                
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    logging.warning("Failed to capture frame, retrying...")
                    time.sleep(0.1)
                    continue
                
                # Add timestamp overlay
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Thread-safe frame update
                with self.lock:
                    self.frame = frame.copy()
                    self.frame_count += 1
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                logging.error(f"Frame capture error: {e}")
                time.sleep(1)
    
    def generate_frames(self):
        """Generate frames for HTTP streaming"""
        while self.running:
            try:
                with self.lock:
                    if self.frame is not None:
                        frame = self.frame.copy()
                    else:
                        continue
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if not ret:
                    continue
                
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
            except Exception as e:
                logging.error(f"Frame generation error: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start the IP camera server"""
        try:
            logging.info("Starting USB IP Camera Server...")
            
            # Initialize camera
            if not self.initialize_camera():
                logging.error("Failed to initialize camera. Please check your USB camera connection.")
                return False
            
            self.running = True
            self.start_time = time.time()
            
            # Start frame capture thread
            capture_thread = threading.Thread(target=self.capture_frames, daemon=True)
            capture_thread.start()
            
            # Get local IP for display
            local_ip = self.get_local_ip()
            
            logging.info(f"Camera server starting on {self.host}:{self.port}")
            logging.info(f"Access your IP camera at: http://{local_ip}:{self.port}")
            logging.info(f"Direct stream URL: http://{local_ip}:{self.port}/video_feed")
            
            # Start Flask server
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                threaded=True,
                use_reloader=False
            )
            
        except KeyboardInterrupt:
            logging.info("Received shutdown signal...")
            self.stop()
        except Exception as e:
            logging.error(f"Server error: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop the IP camera server"""
        logging.info("Stopping IP camera server...")
        self.running = False
        
        if self.camera is not None:
            self.camera.release()
        
        cv2.destroyAllWindows()
        logging.info("IP camera server stopped.")


def main():
    """Main function to run the IP camera server"""
    # Load configuration
    config = {
        'camera_index': 0,      # USB camera index
        'host': '0.0.0.0',      # Bind to all interfaces
        'port': 5000,           # Web server port
        'resolution': (640, 480), # Camera resolution
        'fps': 30               # Frames per second
    }
    
    # Try to load config from file
    try:
        with open('camera_config.json', 'r') as f:
            file_config = json.load(f)
            # Only use supported parameters
            supported_params = ['camera_index', 'host', 'port', 'resolution', 'fps']
            for param in supported_params:
                if param in file_config:
                    if param == 'resolution' and isinstance(file_config[param], list):
                        config[param] = tuple(file_config[param])
                    else:
                        config[param] = file_config[param]
            logging.info("Loaded configuration from camera_config.json")
    except FileNotFoundError:
        logging.info("No config file found, using default settings")
    except Exception as e:
        logging.warning(f"Error loading config: {e}, using defaults")
    
    # Create and start server
    server = IPCameraServer(**config)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    except Exception as e:
        logging.error(f"Startup error: {e}")
    finally:
        server.stop()


if __name__ == '__main__':
    main()