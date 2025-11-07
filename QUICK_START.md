# ProMirrorGolf - Quick Start Guide

## 🎯 Goal
Get your golf swing analysis system running in under 30 minutes.

---

## 📋 Pre-Flight Checklist

Before starting, verify you have:
- [ ] Windows 10/11 PC
- [ ] NVIDIA GPU (RTX 3070 recommended)
- [ ] Python 3.9+ installed
- [ ] Two webcams connected
- [ ] MLM2PRO launch monitor
- [ ] GSPro installed

---

## 🚀 Step-by-Step Setup

### Step 1: Install Python Dependencies (5 minutes)

Open Command Prompt or PowerShell in your project folder:

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
python -c "import cv2, mediapipe; print('✅ Packages installed successfully')"
```

**Common Issues:**
- If `pip` not found: Add Python to PATH or use `python -m pip install -r requirements.txt`
- If MediaPipe fails on Windows: Try `pip install mediapipe-silicon` (Apple Silicon) or reinstall with `--force-reinstall`

---

### Step 2: Configure Your Cameras (5 minutes)

**Find your camera IDs:**

```python
# Save this as test_cameras.py and run it
import cv2

print("Scanning for cameras...")
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            h, w = frame.shape[:2]
            print(f"✅ Camera {i}: {w}x{h}")
        cap.release()
    else:
        print(f"❌ Camera {i}: Not available")
```

Run it:
```bash
python test_cameras.py
```

**Update config.json:**
Open `config.json` and update these lines:
```json
{
  "cameras": {
    "dtl_id": 0,        ← Change to your DTL camera ID
    "face_id": 1,       ← Change to your face-on camera ID
    "fps": 120,         ← Match your camera's capability (60, 120, 240)
    "resolution": [1920, 1080]
  }
}
```

**Tips:**
- Put DTL camera behind you, facing toward target
- Put face-on camera 90° to your right (for right-handed golfers)
- USB 3.0 ports give better performance
- Try to get at least 60fps cameras

---

### Step 3: Setup MLM2PRO Connector (5 minutes)

**Download the connector:**
```bash
# Clone OpenGolfSim connector
git clone https://github.com/OpenGolfSim/MLM2PRO-OGS-Connector
```

Or download from: https://github.com/OpenGolfSim/MLM2PRO-OGS-Connector/releases

**Update config.json:**
```json
{
  "mlm2pro": {
    "connector_path": "C:/MLM2PRO-OGS-Connector/connector.exe",  ← Update this path
    "connector_type": "opengolfsim",
    "listen_port": 5555
  }
}
```

**Test the connector:**
1. Connect MLM2PRO via Bluetooth
2. Run the connector executable
3. Open GSPro
4. Hit a ball - verify data shows in GSPro
5. If working in GSPro, it will work with ProMirrorGolf

---

### Step 4: Build Pro Database (10 minutes)

**CRITICAL:** The system needs at least 1 pro swing to work.

**Option A: Quick Test (Fastest)**
```bash
python build_pro_database.py
# Choose option 1: "Quick test with single video"
# Point it to ANY golf swing video you have
```

**Option B: Use Pre-Recorded Videos**
If you have pro swing videos:
```bash
# Put videos in: ./data/pro_videos/
# Then run:
python build_pro_database.py
# Choose option 2: "Build from local video files"
```

**Option C: Download from YouTube**
```bash
# Edit build_pro_database.py first:
# - Update the SAMPLE_PROS list with real YouTube URLs
# Then run:
python build_pro_database.py
# Choose option 3: "Build from YouTube URLs"
```

**Verify database:**
```bash
python build_pro_database.py
# Choose option 4: "Check database status"
```

You should see at least 1 pro swing listed.

---

### Step 5: First Run (5 minutes)

**Launch the application:**
```bash
python config_and_main.py
```

**Choose interface:**
- Type `1` for GUI (recommended for first run)
- Type `2` for CLI

**In the GUI:**
1. Enter User ID: `test_user`
2. Session name: `First Test`
3. Click **"Start Session"**

**What should happen:**
```
✅ Cameras start buffering
✅ Launch monitor starts listening
✅ Console shows: "SwingAI ready - waiting for shots..."
```

---

### Step 6: Test a Swing (5 minutes)

1. **Open GSPro** (leave ProMirrorGolf running)
2. **Address ball** with cameras recording
3. **Hit a ball**
4. **Wait 2-3 seconds**

**Expected results:**
- GSPro shows shot data
- ProMirrorGolf console shows: "Shot detected! Processing swing..."
- 2-3 seconds later: Analysis complete
- Overlay should appear (if enabled)

**Files created:**
- Video saved in: `./output/videos/`
- Report saved in: `./output/reports/`
- Data saved in database: `./data/swings.db`

---

## ✅ Success Checklist

After your first test swing, verify:
- [ ] Videos captured (check `./output/videos/`)
- [ ] Report generated (check `./output/reports/`)
- [ ] Console shows swing score
- [ ] Pro comparison found
- [ ] Data in database (run: `SELECT COUNT(*) FROM swings` on `swings.db`)

---

## 🐛 Troubleshooting

### "Camera not found"
```bash
# Check if cameras work at all
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"

# If False, check:
1. USB cables connected
2. Camera drivers installed
3. No other app using cameras (Zoom, Teams, etc.)
4. Try different USB port
```

### "ModuleNotFoundError"
```bash
# Reinstall all dependencies
pip install --force-reinstall -r requirements.txt
```

### "MLM2PRO not connecting"
```bash
1. Verify Bluetooth connection in Windows
2. Test with GSPro first
3. Check connector is running (should see console window)
4. Verify port in config.json matches connector
```

### "No pro match found"
```bash
# Check database
python build_pro_database.py
# Option 4 - should show at least 1 pro

# If empty, import at least one pro swing
```

### "GPU not detected"
```bash
# Check NVIDIA drivers
nvidia-smi

# If error, install CUDA:
# https://developer.nvidia.com/cuda-downloads

# Verify PyTorch sees GPU:
python -c "import torch; print(torch.cuda.is_available())"
```

### "Processing too slow (>5 seconds)"
```bash
# Edit config.json - reduce quality:
{
  "cameras": {
    "fps": 60,              ← Lower from 120
    "resolution": [1280, 720]  ← Lower from 1920x1080
  }
}
```

### "Overlay not showing"
This is normal - overlay integration with GSPro requires additional work.
For now, check the generated reports in `./output/reports/`

---

## 📊 Viewing Your Results

### Via Files
```bash
# Videos
./output/videos/[swing_id]_dtl.mp4
./output/videos/[swing_id]_face.mp4

# Reports
./output/reports/[swing_id]/
  ├── comparison.mp4         ← Side-by-side with pro
  ├── skeleton_overlay.mp4   ← 3D skeleton visualization
  ├── metrics_comparison.png ← Charts
  ├── flaw_analysis.png      ← Detected issues
  └── report.txt             ← Full text report
```

### Via Database
```python
from database import SwingDatabase

db = SwingDatabase('./data/swings.db')
swings = db.get_session_swings('your_session_id')

for swing in swings:
    print(f"Swing {swing['swing_number']}: Score {swing['overall_score']}")
```

---

## 🎓 Next Steps

Once your first swing analysis works:

### Immediate
1. **Build full pro database** (10-15 pros for better matching)
2. **Calibrate cameras** for accurate measurements
3. **Adjust flaw detection** thresholds if needed

### Soon
4. **Test with multiple clubs** (driver, irons, wedges)
5. **Practice session** - hit 10-20 balls, track progress
6. **Review historical data** - compare swings over time

### Advanced
7. **Optimize processing speed** (GPU settings, resolution)
8. **Customize coaching tips** (edit recommendations)
9. **Add more pros** to database (specialty swings)

---

## 📞 Getting Help

If you're stuck:

1. **Check logs:** `swingai.log` in project folder
2. **Console output:** Look for error messages
3. **Test components individually:**
   - `python test_cameras.py` - Camera test
   - `python build_pro_database.py` - Database test
   - Run connector separately and verify it works in GSPro

---

## 🎉 You're Ready!

If you've made it through this guide, you should have:
- ✅ Working cameras
- ✅ MLM2PRO connected
- ✅ Pro database built
- ✅ First successful swing analysis

**Now go practice and let ProMirrorGolf help you improve! ⛳**

---

## 🔄 Daily Workflow

Once set up, daily use is simple:

```bash
1. Connect MLM2PRO (Bluetooth)
2. Run: python config_and_main.py
3. Open GSPro
4. Start hitting balls
5. Analysis appears automatically after each shot
6. Review reports in ./output/reports/
```

That's it! No manual input between shots.
