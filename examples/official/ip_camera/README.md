# USB Camera to IP Camera 

A complete solution for transforming your USB camera into an IP camera with both web access and a professional desktop client! This system includes a Python server that streams video from any USB camera over your local network, plus a modern GUI client for viewing and managing camera streams.

## 📋 Requirements

- **Python**: 3.7 or higher
- **Hardware**: USB camera connected to your PC

## 🛠️ Installation

1. **Clone or download** this repository
2. **Install server dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Install GUI client dependencies**:
   ```bash
   cd gui_client
   pip install -r requirements.txt
   ```

## 🎯 Quick Start

### 1. Start the IP Camera Server

```bash
python ip_camera_server.py
```

The server will:
- Detect your USB camera automatically
- Start streaming on port 5000
- Display access URLs in console
- Create a web interface at `http://localhost:5000`

### 2. Access Your Camera

#### Option A: Web Browser
- **Local**: `http://localhost:5000`
- **Network**: `http://YOUR_IP_ADDRESS:5000`

#### Option B: GUI Client
```bash
cd gui_client
python main.py
```

Then:
1. Click "Connect to Camera" or press Ctrl+O
2. Enter connection details:
   - **IP Address**: `localhost` (or your PC's IP)
   - **Port**: `5000`
   - **Stream Path**: `/video_feed`
3. Click "Connect" to start streaming


