# ProMirrorGolf

<div align="center">
  <img src="viewer\assets\logo.svg" alt="ProMirrorGolf Logo" width="200"/>
  
  **Free, Open-Source Golf Swing Analysis with 3D Skeleton Visualization**
  
  [![License: Custom Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-red.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
  [![GPU](https://img.shields.io/badge/GPU-NVIDIA%20RTX-green.svg)](https://www.nvidia.com/)
</div>

---

## Overview

ProMirrorGolf is a free golf swing analysis system that uses AI-powered pose detection to compare your swing with professional golfers. Get instant 3D skeleton visualization, detailed metrics, and personalized improvement recommendations.

**Key Features:**
- Real-time 3D skeleton visualization using MediaPipe (33 keypoints)
- Side-by-side comparison with professional golfers
- 7 key swing metrics with visual feedback
- Personalized drill recommendations
- Multiple export formats (Video, HTML, PDF)
- Sub-second processing on RTX 3070
- 100% free forever - no subscriptions, no paid features

## System Requirements

### Minimum Requirements
- **GPU:** NVIDIA GTX 1060 or better (CUDA compatible)
- **RAM:** 8GB
- **OS:** Windows 10/11, Ubuntu 20.04+, macOS 11+
- **Python:** 3.8 or higher
- **Cameras:** 2x USB webcams (60fps, 720p minimum)

### Recommended Setup
- **GPU:** NVIDIA RTX 3070 or better
- **RAM:** 16GB
- **Cameras:** 2x Logitech C920 or better
- **Launch Monitor:** Rapsodo MLM2PRO (optional)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/alonsom3/ProMirrorGolf.git
cd ProMirrorGolf
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Download Pro Database
The official pro database (70 swings from  pros) will be available as a separate download:
```bash
# Download the pro database (when available)
python scripts/download_pros.py
```

### 4. Set Up Cameras
Position two USB webcams:
- **Camera 1:** Down-the-line (DTL) view - behind and to the side
- **Camera 2:** Face-on view - directly facing the golfer

### 5. Verify Installation
```bash
python main.py --test
```

## Usage

### Basic Usage
```bash
# Start the analysis server
python main.py --serve

# The web interface will open automatically at http://localhost:8080
```

### With Launch Monitor Integration
```bash
# If using Rapsodo MLM2PRO
python main.py --serve --launch-monitor rapsodo
```

### Command Line Options
```bash
python main.py [options]

Options:
  --serve              Start web server and analysis system
  --port PORT         Web server port (default: 8080)
  --gpu-device ID     CUDA device ID (default: 0)
  --launch-monitor    Enable launch monitor integration
  --test              Run system tests
  --add-pro PATH      Add custom pro to database
```

## How It Works

1. **Capture:** When you hit a shot, the system captures the last 5 seconds from both cameras
2. **Process:** MediaPipe extracts 33 skeletal keypoints from each frame
3. **Analyze:** The system calculates 7 key metrics from your swing
4. **Compare:** Your metrics are compared against the selected pro
5. **Recommend:** AI generates personalized improvement drills
6. **Visualize:** 3D skeletons show both swings side-by-side

## Metrics Analyzed

| Metric | Ideal Range | What It Measures |
|--------|------------|------------------|
| Hip Rotation | 40-50° | Power generation from lower body |
| Shoulder Rotation | 85-105° | Upper body coil and flexibility |
| X-Factor | 40-55° | Separation between hips and shoulders |
| Spine Angle | 28-38° | Posture consistency |
| Tempo Ratio | 2.7-3.3:1 | Backswing to downswing timing |
| Weight Shift | 60-85% | Transfer to lead foot at impact |
| Spine Angle Change | -3 to +3° | Maintaining posture through swing |

## Adding Custom Pros

You can add your own professional swings to the database:

```bash
# Process a video file
python scripts/add_custom_pro.py --video path/to/video.mp4 --name "Pro Name" --club "Driver"

# Or capture live from cameras
python scripts/add_custom_pro.py --capture --name "Pro Name" --club "7-Iron"
```

**Important Legal Note:** 
- We do NOT provide video downloading tools
- You must obtain videos at your own risk
- We cannot assist with video acquisition
- Only metrics and pose data are stored, never videos

## Export Options

### Video Export (MP4)
- Side-by-side 3D comparison
- Synchronized playback
- Metrics overlay

### HTML Export
- Interactive 3D viewer
- Shareable with coaches
- Works offline

### PDF Report
- Detailed metrics
- Improvement recommendations
- Practice drills

## Project Structure

```
ProMirrorGolf/
├── main.py                 # Main entry point
├── backend/
│   ├── analyzer.py        # Swing analysis coordinator
│   ├── pose_detector.py   # MediaPipe integration
│   ├── metrics_extractor.py # Metric calculations
│   ├── database.py        # Pro database management
│   └── server.py          # Web server
├── viewer/
│   ├── index.html         # Web interface
│   ├── css/
│   │   └── style.css      # Dark theme styles
│   └── js/
│       ├── skeleton-renderer.js # 3D visualization
│       ├── controls.js    # UI controls
│       ├── metrics-display.js # Metrics UI
│       └── main.js        # App coordinator
├── data/
│   └── official_pros.json # Pro swing database
├── scripts/
│   ├── download_pros.py   # Pro database downloader
│   └── add_custom_pro.py  # Custom pro tool
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── LICENSE               # Non-commercial license
└── README.md            # This file
```

## Performance

On NVIDIA RTX 3070:
- Processing time: 0.8-1.2 seconds per swing
- Frame rate: 60 fps capture, 300 frames analyzed
- Pose detection: >90% accuracy
- File size: ~5MB per swing analysis

## Troubleshooting

### Camera Not Detected
```bash
# List available cameras
python scripts/list_cameras.py

# Test camera capture
python scripts/test_capture.py --camera 0
```

### GPU Not Found
```bash
# Check CUDA installation
python -c "import torch; print(torch.cuda.is_available())"

# Use CPU fallback (slower)
python main.py --serve --cpu-only
```

### Poor Pose Detection
- Ensure good lighting (avoid backlighting)
- Wear contrasting clothing
- Check camera positioning
- Verify 60fps capture rate

## Community

### Discord Server
Join our community Discord for:
- Sharing custom metrics (NOT videos)
- Discussing swing improvements
- Getting help with setup
- Feature requests

**Note:** The Discord is community-run and not officially managed.

### Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key areas for contribution:
- Additional metrics algorithms
- UI/UX improvements
- Language translations
- Performance optimizations

## Legal & Safety

### License
This software is released under a **Non-Commercial License**:
- ✅ Free to use personally
- ✅ Free to modify and share
- ✅ Free to use for coaching (no charge to clients)
- ❌ Cannot be sold or monetized
- ❌ Cannot be used in commercial products
- ❌ Cannot charge for access or features

### Video Rights
- We do NOT provide or assist with video downloads
- Users are responsible for obtaining videos legally
- We only store pose data and metrics, never videos
- Respect copyright and personality rights

### Disclaimer
This software is for educational and training purposes only. Not responsible for injury or equipment damage. Always consult a golf professional for personalized instruction.

## Roadmap

### Phase 1 (Current)
- ✅ Core pose detection
- ✅ 3D visualization
- ✅ Metrics analysis
- ✅ Pro comparison
- ✅ Web interface

### Phase 2 (Planned)
- [ ] GSPro overlay integration
- [ ] Mobile app viewer
- [ ] Cloud backup (metrics only)
- [ ] Multi-language support
- [ ] Advanced biomechanics

### Phase 3 (Future)
- [ ] AI coaching suggestions
- [ ] Social features (metric sharing)
- [ ] Tournament analysis mode
- [ ] VR viewing support

## Credits

Created with passion for golf and technology.

**Technologies Used:**
- MediaPipe by Google
- Three.js for 3D rendering
- PyTorch for GPU acceleration
- OpenCV for video processing

## Support

For issues and questions:
1. Check the [FAQ](docs/FAQ.md)
2. Search [existing issues](https://github.com/yourusername/ProMirrorGolf/issues)
3. Create a new issue with details

## Acknowledgments

Special thanks to:
- The open-source community
- Golf professionals who inspired this project
- MediaPipe team for pose detection technology
- Early testers and contributors

---

**Remember:** This tool is meant to supplement, not replace, professional golf instruction. Have fun improving your game!

*ProMirrorGolf - See Your Swing Like Never Before*
