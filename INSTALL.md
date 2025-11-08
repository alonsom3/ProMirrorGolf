# ProMirrorGolf Installation Guide

Complete setup instructions for Windows 10/11

---

## System Requirements

### Minimum
- **OS**: Windows 10/11 (64-bit)
- **CPU**: Intel i5 / AMD Ryzen 5
- **GPU**: NVIDIA RTX 2060 (6GB VRAM)
- **RAM**: 16GB
- **Storage**: 50GB SSD
- **Cameras**: 2x USB webcams (60fps)

### Recommended
- **CPU**: Intel i7 / AMD Ryzen 7
- **GPU**: NVIDIA RTX 3070 (8GB VRAM) ⭐
- **RAM**: 32GB
- **Cameras**: 2x high-speed (120fps)

---

## Step-by-Step Installation

### 1. Install Python

Download Python 3.9+ from [python.org](https://www.python.org/downloads/)

**Important**: Check "Add Python to PATH" during installation

Verify installation:
```bash
python --version
```

### 2. Install CUDA (for GPU Acceleration)

Download CUDA Toolkit 11.8 from [NVIDIA](https://developer.nvidia.com/cuda-downloads)

Verify installation:
```bash
nvidia-smi
```

You should see your GPU listed.

### 3. Clone Repository
```bash
git clone https://github.com/alonsom3/ProMirrorGolf.git
cd ProMirrorGolf
```

Or download ZIP and extract to `D:\ProMirrorGolf\`

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- opencv-python (camera capture)
- mediapipe (pose estimation)
- numpy, matplotlib (data processing)
- aiohttp (async networking)
- yt-dlp (video downloading)

### 5. Setup MLM2PRO Connector

#### Option A: Use Included Connector
The connector is already in `MLM2PRO-OGS-Connector/`

#### Option B: Download Latest
```bash
git clone https://github.com/OpenGolfSim/MLM2PRO-OGS-Connector
```

Update `config.json` with path:
```json
{
  "mlm2pro": {
    "connector_path": "D:\\ProMirrorGolf\\MLM2PRO-OGS-Connector\\connector.exe"
  }
}
```

### 6. Connect Cameras

1. Plug in both USB webcams
2. Run test to find device IDs:
```bash
   python test_cameras.py
```
3. Note which camera is which (DTL vs Face-on)
4. Update `config.json`:
```json
   {
     "cameras": {
       "dtl_id": 2,
       "face_id": 0
     }
   }
```

### 7. Setup Pro Swing Database

#### If you have dual-view videos:
```bash
python split_video.py "data/pro_videos/YourVideo.mp4"
```

#### Import to database:
```bash
python import_pro_swing.py
```

Follow the prompts:
- Golfer name: "Justin Thomas"
- DTL video: (auto-filled from split)
- Face-on video: (auto-filled from split)
- Club: Driver
- Style tags: power, athletic, modern

### 8. Configure GSPro Integration

1. Ensure GSPro is installed
2. Configure MLM2PRO in GSPro settings
3. Test connection by hitting a ball in GSPro

---

## Configuration

### config.json Structure
```json
{
  "cameras": {
    "dtl_id": 2,              // Down-the-line camera ID
    "face_id": 0,             // Face-on camera ID
    "fps": 60,                // Frames per second
    "resolution": [1920, 1080],
    "buffer_seconds": 10.0    // Circular buffer size
  },
  "mlm2pro": {
    "connector_path": "D:\\ProMirrorGolf\\MLM2PRO-OGS-Connector\\connector.exe",
    "connector_type": "opengolfsim",
    "listen_port": 5555
  },
  "ai": {
    "pose_model": "mediapipe",
    "use_gpu": true,
    "min_detection_confidence": 0.5
  },
  "database": {
    "user_swings_path": "./data/swings.db",
    "pro_swings_path": "./data/pro_swings.db"
  },
  "output": {
    "videos_dir": "./output/videos",
    "reports_dir": "./output/reports"
  },
  "overlay": {
    "enabled": true,
    "endpoint": "http://localhost:8765/display",
    "port": 8765,
    "auto_hide_seconds": 10
  },
  "processing": {
    "auto_start": true,
    "min_shot_interval": 3.0
  }
}
```

### Camera Positioning

**DTL Camera (Down-the-line)**:
- Behind golfer
- Looking toward target
- Hip height
- 10-15 feet away
- Center golfer in frame

**Face-on Camera**:
- 90° from target line
- Facing golfer
- Hip height
- 10-15 feet away
- Center golfer in frame

---

## Verification Tests

### Test 1: Camera Detection
```bash
python test_cameras.py
```
Expected: Shows both cameras with preview

### Test 2: Video Split
```bash
python split_video.py "data/pro_videos/test_video.mp4"
```
Expected: Creates `test_video_DTL.mp4` and `test_video_Face.mp4`

### Test 3: Pro Import
```bash
python import_pro_swing.py
```
Expected: Imports swing to database, shows confirmation

### Test 4: Full System
```bash
python main.py
```
Expected: GUI opens, no errors

---

## Troubleshooting

### Issue: "No module named 'cv2'"
**Solution**:
```bash
pip install opencv-python
```

### Issue: "CUDA not available"
**Solution**:
1. Install CUDA Toolkit 11.8
2. Verify: `nvidia-smi`
3. Check GPU compatibility

### Issue: "Camera not found"
**Solution**:
1. Check USB connections
2. Try different USB ports (USB 3.0 preferred)
3. Update camera drivers
4. Run `python test_cameras.py`

### Issue: "MLM2PRO connector not found"
**Solution**:
1. Verify path in config.json
2. Use absolute path with double backslashes
3. Check file exists: `dir "D:\ProMirrorGolf\MLM2PRO-OGS-Connector\connector.exe"`

### Issue: "Slow processing"
**Solution**:
1. Lower resolution to 1280x720
2. Reduce FPS to 30-60
3. Close other applications
4. Verify GPU is being used

### Issue: "Import pro swing fails"
**Solution**:
1. Verify video file exists
2. Check video format (MP4 recommended)
3. Ensure video has clear golfer view
4. Try splitting video first if dual-view

---

## Performance Tuning

### For RTX 3070 (Your Setup)
```json
{
  "cameras": {
    "fps": 60,
    "resolution": [1920, 1080]
  },
  "ai": {
    "use_gpu": true
  }
}
```
Expected processing: **2-3 seconds per swing**

### For Lower-End Systems
```json
{
  "cameras": {
    "fps": 30,
    "resolution": [1280, 720]
  }
}
```
Expected processing: **4-6 seconds per swing**

---

## Next Steps

1. ✅ Test cameras
2. ✅ Import pro swings
3. ✅ Run main application
4. 🎮 Practice in GSPro!

---

## Support

If you encounter issues:

1. Check logs: `promirror.log`
2. Run tests in order
3. Verify configuration
4. Open GitHub issue with:
   - Error message
   - Log file
   - System specs

---

## Updates

To update ProMirrorGolf:
```bash
git pull origin main
pip install --upgrade -r requirements.txt
```

---

**Installation complete! Ready to analyze swings! 🏌️‍♂️**

---

## Version 2.0 Updates

ProMirrorGolf v2.0 includes:
- ✅ Modern CustomTkinter UI with modular components
- ✅ Real-time performance dashboard
- ✅ Video upload support with quality modes
- ✅ Comprehensive performance logging
- ✅ Mobile API for companion apps
- ✅ Enhanced error handling and user feedback

See `UI_MODERNIZATION_SUMMARY.md` and `ENHANCEMENT_SUMMARY.md` for details.