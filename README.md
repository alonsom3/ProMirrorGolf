# ⛳ ProMirrorGolf

**AI-Powered Golf Swing Analysis System**

Automated, real-time swing analysis that integrates with GSPro and your launch monitor. Hit a ball, get instant feedback with pro comparisons, 3D skeleton analysis, and personalized coaching recommendations.

![ProMirrorGolf](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-Active-success.svg)

---

## 🎯 Features

- ✅ **Zero-Input Automation** - Hit balls, get instant analysis (2-3 seconds)
- ✅ **Dual Camera Capture** - DTL + Face-on views with circular buffering
- ✅ **Launch Monitor Integration** - Rapsodo MLM2PRO via OpenGolfSim connector
- ✅ **AI Pose Analysis** - MediaPipe-based 3D skeletal tracking
- ✅ **Pro Comparison** - Automatic matching to professional swings
- ✅ **Flaw Detection** - ML-based swing diagnostics with recommendations
- ✅ **Side-by-Side Videos** - Compare your swing to matched pros
- ✅ **Historical Tracking** - Database of all swings for progress monitoring
- ✅ **Enhanced UI** - Modern red-themed interface

---

## 📋 Requirements

### Hardware
- **PC**: Windows 10/11, Intel i5/AMD Ryzen 5 or better
- **GPU**: NVIDIA RTX 3070 (8GB VRAM) - *Recommended for RTX 3070*
- **RAM**: 16GB minimum, 32GB recommended
- **Cameras**: 2x USB webcams, 60fps minimum (120fps recommended)
- **Launch Monitor**: Rapsodo MLM2PRO

### Software
- Python 3.9+
- CUDA 11.8+ (for GPU acceleration)
- GSPro golf simulator
- MLM2PRO-OGS-Connector

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure System

Edit `config.json` with your settings:
- Camera IDs (DTL and Face-on)
- MLM2PRO connector path
- GPU settings

### 3. Setup Pro Swings

Split dual-view videos:
```bash
python split_video.py "data/pro_videos/Justin_Thomas_DTLandFFO.mp4"
```

Import to database:
```bash
python import_pro_swing.py
```

### 4. Test Cameras
```bash
python test_cameras.py
```

### 5. Run Application
```bash
python main.py
```

---

## 📁 Project Structure
```
ProMirrorGolf/
│
├── main.py                 # Main application with enhanced UI
├── config.json             # System configuration
├── split_video.py          # Video splitter for dual-view videos
├── import_pro_swing.py     # Pro swing importer
├── test_cameras.py         # Camera testing utility
├── requirements.txt        # Python dependencies
│
├── src/                    # Core source code
│   ├── swing_ai_core.py          # Main controller
│   ├── camera_manager.py         # Dual camera management
│   ├── mlm2pro_listener.py       # Launch monitor integration
│   ├── pose_analyzer.py          # AI pose estimation
│   ├── style_matcher.py          # Pro swing matching
│   ├── report_generator.py       # Report creation
│   ├── database.py               # Data persistence
│   └── youtube_downloader.py     # Video downloader
│
├── data/                   # Data storage
│   ├── pro_videos/               # Professional swing videos
│   ├── pro_swings.db             # Pro swing database
│   └── swings.db                 # User swing database
│
├── output/                 # Generated outputs
│   ├── videos/                   # Captured swing videos
│   └── reports/                  # Analysis reports
│
└── docs/                   # Documentation
    ├── README.md
    ├── INSTALL.md
    └── USAGE.md
```

---

## 🎮 Usage

### Starting a Session

1. Launch ProMirrorGolf
2. Enter your User ID
3. (Optional) Name your session
4. Click **START SESSION**
5. Open GSPro and start hitting balls

### During Practice

- System automatically detects shots via MLM2PRO
- Cameras capture last 5 seconds when ball is struck
- AI analyzes swing in 2-3 seconds
- Results appear automatically:
  - Overall score (0-100)
  - Side-by-side comparison with matched pro
  - Top 3 flaws with recommendations
  - Launch monitor data

### After Session

- All swings saved to database
- Review any swing from history
- Track progress over time
- Compare swings side-by-side

---

## ⚙️ Configuration

### config.json
```json
{
  "cameras": {
    "dtl_id": 2,
    "face_id": 0,
    "fps": 60,
    "resolution": [1920, 1080]
  },
  "mlm2pro": {
    "connector_path": "D:\\ProMirrorGolf\\MLM2PRO-OGS-Connector\\connector.exe"
  },
  "ai": {
    "use_gpu": true
  }
}
```

### Camera Setup

- **DTL Camera (Down-the-line)**: Behind golfer, looking at target
- **Face Camera (Face-on)**: In front of golfer, 90° from target line
- Both should be at hip height, 10-15 feet away

---

## 🔧 Utilities

### split_video.py
Automatically detects and splits dual-view videos:
```bash
python split_video.py "path/to/video.mp4"
```

### import_pro_swing.py
Import professional swings to database:
```bash
python import_pro_swing.py
# Follow interactive prompts
```

### test_cameras.py
Test and preview cameras:
```bash
python test_cameras.py
# Shows all available cameras with live preview
```

---

## 📊 Swing Metrics

The system analyzes:

- **Hip Rotation** (35-50° ideal)
- **Shoulder Rotation** (80-110° ideal)
- **X-Factor** (shoulder-hip separation, 35-55° ideal)
- **Spine Angle** (maintenance through impact)
- **Weight Transfer** (lateral shift)
- **Tempo Ratio** (backswing:downswing, 2.5-3.5 ideal)
- **Club Speed** (from launch monitor)
- **Ball Speed** (from launch monitor)
- **Launch Angle** (from launch monitor)
- **Spin Rate** (from launch monitor)

---

## 🐛 Troubleshooting

### Cameras Not Detected
```bash
python test_cameras.py
# Check device IDs and update config.json
```

### MLM2PRO Connection Issues
1. Verify Bluetooth connection
2. Check connector path in config.json
3. Test with GSPro first

### Slow Processing
- Lower camera resolution in config.json
- Reduce FPS to 60
- Close other GPU applications
- Verify CUDA installation: `nvidia-smi`

### Import Errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

---

## 📈 Roadmap

### Current Version (1.0)
- ✅ Dual camera capture
- ✅ MLM2PRO integration
- ✅ AI pose analysis
- ✅ Pro matching
- ✅ Flaw detection
- ✅ Enhanced UI

### Planned (2.0)
- 🔲 Real-time 3D avatar
- 🔲 Mobile companion app
- 🔲 Cloud sync
- 🔲 Drill recommendations
- 🔲 Progress charts

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/alonsom3/ProMirrorGolf/issues)
- **Discussions**: [GitHub Discussions](https://github.com/alonsom3/ProMirrorGolf/discussions)

---

## 🙏 Acknowledgments

- MediaPipe (Google) for pose estimation
- OpenGolfSim community for MLM2PRO connector
- All professional golfers whose swings we study

---

**Made with ⛳ by golfers, for golfers**

*For best results, practice with purpose. ProMirrorGolf shows you what to work on, but you still have to do the work!*