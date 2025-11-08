# ProMirrorGolf - Source Code Documentation

## Overview

The `src/` directory contains the core backend modules for ProMirrorGolf. These modules handle all the AI analysis, data management, and system integration. The main application (`main.py` in the root) imports and uses these modules through the `SwingAIController` class.

**Production-Ready Features:**
- ⚡ **High Performance**: <100ms frame processing with GPU acceleration support
- 📹 **Video Upload**: Offline dual-video processing (DTL + Face)
- 🔌 **MLM2Pro Integration**: Real-time launch monitor data
- 📊 **Analytics**: Frame-level metrics, flaw evolution, similarity tracking
- 🎯 **Optimized Matching**: In-memory caching for instant pro matching

## Data Processing Workflow

The complete swing analysis pipeline follows this workflow:

1. **Video/Camera Input** → `DualCameraManager` captures frames from two cameras
2. **Pose Detection** → `PoseAnalyzer` detects human pose landmarks using MediaPipe
3. **Metrics Extraction** → `MetricsExtractor` calculates biomechanical metrics from pose data
4. **Flaw Detection** → `FlawDetector` compares metrics to ideal ranges and identifies issues
5. **Pro Comparison** → `StyleMatcher` finds best matching professional swing
6. **UI Update** → Results displayed in real-time via thread-safe callbacks

## Core Modules

### 1. swing_ai_core.py

**Main Controller** - Orchestrates all backend components and full analysis pipeline

**Class**: `SwingAIController`

**Key Methods**:
- `__init__(config_path="config.json")` - Initialize controller with config file
- `async initialize()` - Initialize all AI components (cameras, pose analyzer, database, metrics extractor, flaw detector, etc.)
- `async start_session(user_id, session_name)` - Start a practice session
- `async stop_session()` - Stop current session
- `async _monitor_swings()` - Internal method that monitors for swing detection
- `async _analyze_swing(pose_data)` - Full analysis pipeline:
  1. Extract metrics from pose data
  2. Detect flaws
  3. Find pro match
  4. Return complete swing data
- `_get_shot_data(metrics)` - Get shot data from launch monitor or estimate

**Full Analysis Pipeline**:
When a swing is detected, `_analyze_swing()` runs:
1. **Metrics Extraction** → `MetricsExtractor.extract_metrics_from_pose()`
2. **Flaw Detection** → `FlawDetector.detect_flaws()`
3. **Pro Matching** → `StyleMatcher.find_best_match()`
4. **Shot Data** → From launch monitor or estimated (MLM2Pro skipped in video upload mode)
5. **Return Complete Data** → All results combined in swing_data dict

**Video Upload Mode:**
- `start_session(..., use_video_upload=True)` - Starts session without cameras or MLM2Pro
- `process_uploaded_videos(dtl_path, face_path, downsample_factor=1)` - Processes uploaded videos
- **Timeout**: 600 seconds (10 minutes) for long videos
- **Frame alignment**: Automatically handles mismatched frame counts with warnings
- **Session stop**: Safe timeout handling, won't crash if processing is ongoing
- **MLM2Pro**: Automatically disabled in video upload mode (not needed)

**Dependencies**: All other modules in `src/`

**Usage**:
```python
from src.swing_ai_core import SwingAIController

controller = SwingAIController('config.json')
await controller.initialize()
await controller.start_session("user123", "Practice Session 1")
```

**Expected Inputs**:
- `config.json` file with camera, database, and AI settings
- User ID and session name for `start_session()`

**Outputs**:
- Session ID when session is created
- Swing data dictionary via `on_swing_detected` callback

---

### 2. camera_manager.py

**Dual Camera Management** - Handles simultaneous capture from two cameras

**Class**: `DualCameraManager`

**Key Methods**:
- `__init__(config)` - Initialize with camera configuration
- `async start_buffering()` - Start capturing frames from both cameras
- `async stop_buffering()` - Stop camera capture
- `async get_latest_frames()` - Get most recent frames from both cameras

**Dependencies**: `cv2`, `numpy`, `asyncio`, `threading`

**Usage**:
```python
from src.camera_manager import DualCameraManager

manager = DualCameraManager(config)
await manager.start_buffering()
dtl_frame, face_frame = await manager.get_latest_frames()
```

**Expected Inputs**:
- Config dict with `cameras.dtl_id`, `cameras.face_id`, `cameras.fps`, `cameras.resolution`

**Outputs**:
- Tuple of `(dtl_frame, face_frame)` as numpy arrays, or `(None, None)` if no frames available

---

### 3. pose_analyzer.py

**AI Pose Estimation** - Analyzes video frames to detect human pose and swing events

**Class**: `PoseAnalyzer`

**Key Methods**:
- `__init__(config)` - Initialize MediaPipe pose detection with confidence thresholds
- `async analyze(dtl_frame, face_frame)` - Analyze frames and detect swing
- `_detect_swing_events(poses)` - Detect key swing events (address, top, impact)
- `clear_buffer()` - Clear pose buffers after swing processing

**Dependencies**: `mediapipe`, `cv2`, `numpy`, `asyncio`, `collections.deque`

**Usage**:
```python
from src.pose_analyzer import PoseAnalyzer

analyzer = PoseAnalyzer(config)
pose_data = await analyzer.analyze(dtl_frame, face_frame)
```

**Expected Inputs**:
- Two numpy arrays (BGR format) from cameras
- Config dict with `ai.min_detection_confidence`

**Outputs**:
- Dictionary with:
  - `swing_detected`: bool
  - `dtl_poses`: list of pose landmark dictionaries
  - `face_poses`: list of pose landmark dictionaries
  - `events`: dict with 'address', 'top', 'impact', 'finish' frame indices
  - `dtl_landmarks`: current frame landmarks
  - `face_landmarks`: current frame landmarks

**Pose Data Structure**:
- Each pose contains landmarks dictionary with MediaPipe indices (0-32)
- Each landmark has: `x`, `y`, `z`, `visibility`

---

### 4. database.py

**Data Persistence** - Manages SQLite databases for swings and pro swings

**Classes**: 
- `SwingDatabase` - User swing data
- `ProSwingDatabase` - Professional swing reference data

**Key Methods (SwingDatabase)**:
- `create_session(user_id, session_name)` - Create new practice session
- `save_swing(session_id, swing_id, swing_metrics, shot_data, ...)` - Save analyzed swing
- `get_swing(swing_id)` - Retrieve specific swing
- `get_session_swings(session_id)` - Get all swings from a session
- `get_user_sessions(user_id)` - Get all sessions for a user

**Dependencies**: `sqlite3`, `json`

**Usage**:
```python
from src.database import SwingDatabase

db = SwingDatabase("./data/swings.db")
session_id = db.create_session("user123", "Session 1")
db.save_swing(session_id, swing_id, metrics, shot_data, ...)
swing = db.get_swing(swing_id)
```

**Expected Inputs**:
- Database path string
- Session/user IDs, swing data dictionaries

**Outputs**:
- Session ID (string)
- Swing dictionaries with all stored data

---

### 5. style_matcher.py

**Pro Swing Matching** - Finds best matching professional swing for comparison

**Class**: `StyleMatcher`

**Key Methods**:
- `__init__(pro_db_path)` - Initialize with pro swing database
- `find_top_n_matches(swing_metrics, club_type, n=3)` - Find best matches
- `analyze_swing_style(swing_metrics)` - Analyze swing style characteristics

**Dependencies**: `numpy`, `ProSwingDatabase` (from `database.py`)

**Usage**:
```python
from src.style_matcher import StyleMatcher

matcher = StyleMatcher("./data/pro_swings.db")
matches = matcher.find_top_n_matches(metrics, "Driver", n=3)
```

**Expected Inputs**:
- Swing metrics dictionary
- Club type string ("Driver", "7-Iron", etc.)

**Outputs**:
- List of matched pro swings with similarity scores

---

### 6. metrics_extractor.py

**Swing Metrics Extraction** - Calculates biomechanical metrics from pose data

**Class**: `MetricsExtractor`

**Key Methods**:
- `extract_metrics_from_pose(pose_data, fps=60)` - Extract all swing metrics from pose detection results
- `_calc_hip_rotation(pose1, pose2)` - Calculate hip rotation between two poses
- `_calc_shoulder_rotation(pose1, pose2)` - Calculate shoulder rotation between two poses
- `_calc_spine_angle(pose)` - Calculate spine angle (forward tilt)
- `_calc_weight_transfer(pose1, pose2)` - Calculate weight transfer

**Dependencies**: `numpy`

**Usage**:
```python
from src.metrics_extractor import MetricsExtractor

extractor = MetricsExtractor()
metrics = extractor.extract_metrics_from_pose(pose_data, fps=60)
```

**Expected Inputs**:
- `pose_data`: Dictionary with `dtl_poses` (list of pose dicts) and `events` (dict with frame indices)
- `fps`: Frames per second for time calculations

**Outputs**:
- Dictionary with metrics:
  - `hip_rotation_top`: degrees
  - `shoulder_rotation_top`: degrees
  - `x_factor`: degrees (shoulder - hip)
  - `spine_angle_address`: degrees
  - `spine_angle_impact`: degrees
  - `spine_angle_change`: degrees
  - `backswing_time`: seconds
  - `downswing_time`: seconds
  - `tempo_ratio`: backswing:downswing
  - `weight_transfer`: normalized value

**Calculation Methods**:
- Uses MediaPipe landmark indices (11=left_shoulder, 12=right_shoulder, 23=left_hip, 24=right_hip)
- Calculates rotations using arctan2 on x/z coordinates
- Detects swing events (address, top, impact) from pose sequence

---

### 7. flaw_detector.py

**Swing Flaw Detection** - Identifies biomechanical issues and provides recommendations

**Class**: `FlawDetector`

**Key Methods**:
- `__init__()` - Initialize with ideal ranges for each metric
- `detect_flaws(user_metrics, pro_reference=None)` - Analyze metrics and detect flaws
- `_calculate_severity(value, threshold, direction)` - Calculate flaw severity (0-1)
- `_get_recommendation(metric, issue, value, threshold)` - Get coaching recommendation
- `_calculate_overall_score(flaws)` - Calculate overall swing score (0-100)

**Dependencies**: None (pure Python)

**Usage**:
```python
from src.flaw_detector import FlawDetector

detector = FlawDetector()
flaw_analysis = detector.detect_flaws(user_metrics)
```

**Expected Inputs**:
- `user_metrics`: Dictionary with metric names and values
- `pro_reference`: Optional pro metrics for comparison

**Outputs**:
- Dictionary with:
  - `flaws`: List of flaw dictionaries (sorted by severity)
  - `overall_score`: Overall swing score (0-100)
  - `flaw_count`: Number of flaws detected

**Flaw Structure**:
Each flaw contains:
- `metric`: Metric name
- `value`: User's actual value
- `ideal_min`: Minimum ideal value
- `ideal_max`: Maximum ideal value
- `issue`: "too_low" or "too_high"
- `severity`: Severity score (0-1)
- `recommendation`: Coaching recommendation text

**Ideal Ranges**:
- `hip_rotation_top`: 35-50 degrees
- `shoulder_rotation_top`: 80-110 degrees
- `x_factor`: 35-55 degrees
- `spine_angle_address`: 25-40 degrees
- `tempo_ratio`: 2.5-3.5:1
- `weight_transfer`: 0.05-0.15

---

### 8. report_generator.py

**Report Creation** - Generates comprehensive analysis reports

**Class**: `ReportGenerator`

**Key Methods**:
- `__init__(output_dir)` - Initialize with output directory
- `async create_report(swing_id, user_videos, pro_match, ...)` - Generate full report
- `_create_comparison_video(...)` - Create side-by-side comparison video
- `_create_overlay_video(...)` - Create skeleton overlay video
- `_create_metrics_chart(...)` - Generate metrics visualization

**Dependencies**: `cv2`, `matplotlib`, `numpy`

**Usage**:
```python
from src.report_generator import ReportGenerator

generator = ReportGenerator("./data/reports")
report = await generator.create_report(swing_id, videos, pro_match, ...)
```

**Expected Inputs**:
- Swing ID, video paths, metrics, flaw analysis dictionaries

**Outputs**:
- Report dictionary with paths to generated files (videos, images, JSON)

---

### 7. mlm2pro_listener.py

**Launch Monitor Integration** - Listens for shot data from MLM2PRO connector

**Classes**:
- `LaunchMonitorListener` - Real-time UDP listener
- `FileBasedLaunchMonitorListener` - File-based listener for testing

**Key Methods**:
- `start_listening()` - Start listening for shot data
- `async wait_for_shot(timeout)` - Wait for next shot detection
- `stop_listening()` - Stop monitoring

**Dependencies**: `asyncio`, `socket`, `json`

**Usage**:
```python
from src.mlm2pro_listener import LaunchMonitorListener

listener = LaunchMonitorListener(connector_path, "opengolfsim")
listener.start_listening()
shot_data = await listener.wait_for_shot(timeout=60)
```

**Expected Inputs**:
- Connector path, connector type, listen port

**Outputs**:
- Shot data dictionary with ball speed, club speed, carry distance, etc.

---

### 8. youtube_downloader.py

**Video Downloader** - Downloads videos from YouTube for pro swing database

**Class**: `YouTubeDownloader`

**Key Methods**:
- `__init__(output_dir)` - Initialize with download directory
- `async download_video(url, output_filename)` - Download video from URL

**Dependencies**: `yt_dlp`, `asyncio`

**Usage**:
```python
from src.youtube_downloader import YouTubeDownloader

downloader = YouTubeDownloader("./data/pro_videos_raw")
video_path = await downloader.download_video("https://youtube.com/...")
```

**Expected Inputs**:
- YouTube URL string
- Optional output filename

**Outputs**:
- Path to downloaded video file, or `None` if download failed

---

## Import Patterns

### Relative Imports

All modules in `src/` use relative imports when importing from each other:

```python
# In swing_ai_core.py
from .camera_manager import DualCameraManager
from .database import SwingDatabase
```

### Absolute Imports from Root

When importing from `src/` in root-level scripts:

```python
# In main.py (root)
from src.swing_ai_core import SwingAIController
```

### Path Setup

Root scripts should add the project root to `sys.path`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

---

## Data Flow

1. **Session Start**: `SwingAIController.start_session()` → Creates DB session, starts cameras
2. **Frame Capture**: `DualCameraManager` continuously buffers frames
3. **Swing Detection**: `PoseAnalyzer.analyze()` detects swing motion
4. **Analysis**: `_analyze_swing()` processes pose data → generates metrics
5. **Matching**: `StyleMatcher.find_top_n_matches()` finds best pro comparison
6. **Storage**: `SwingDatabase.save_swing()` saves all data
7. **Callback**: `on_swing_detected()` callback updates UI
8. **Reporting**: `ReportGenerator.create_report()` generates reports on demand

---

## Configuration

All modules read from `config.json`:

```json
{
  "cameras": {
    "dtl_id": 2,
    "face_id": 0,
    "fps": 60,
    "resolution": [1920, 1080]
  },
  "database": {
    "swing_db_path": "./data/swings.db",
    "pro_db_path": "./data/pro_swings.db"
  },
  "reports": {
    "output_dir": "./data/reports"
  }
}
```

---

## Error Handling

All modules use Python's `logging` module for error reporting:

```python
import logging
logger = logging.getLogger(__name__)
logger.error("Error message", exc_info=True)
```

Check `promirror.log` for detailed error logs.

---

## Async/Await Pattern

Most backend operations are asynchronous:

- Use `await` when calling async methods
- Use `asyncio.run_coroutine_threadsafe()` to call from non-async contexts (like UI)
- All camera, database, and analysis operations are async for performance

---

## Entry Point

**The main application entry point is `main.py` in the project root directory**, not any file in this `src/` directory.

## Testing

The project includes a comprehensive end-to-end test suite (`test_e2e_swing_pipeline.py` in the root directory) that validates:
- Pose detection from video frames
- Metrics extraction from pose data
- Flaw detection and recommendations
- Pro swing matching
- Full pipeline integration
- Session management
- Export functionality
- Edge case handling (empty data, missing frames, invalid metrics)

Run tests with:
```bash
python test_e2e_swing_pipeline.py
```

See `TEST_DOCUMENTATION.md` in the root directory for detailed test documentation.

---

## New Production Modules

### 11. video_processor.py

**Video Upload & Processing** - Handles offline video upload and processing

**Class**: `VideoProcessor`

**Key Methods**:
- `load_videos(dtl_path, face_path)` - Load and validate two video files
- `get_frame(frame_number)` - Get synchronized frames at specified index
- `get_all_frames()` - Extract all frames for batch processing
- `validate_video_format(video_path)` - Validate video file format and properties
- `release()` - Release video resources

**Dependencies**: `cv2`, `numpy`, `pathlib`

**Usage**:
```python
from src.video_processor import VideoProcessor

processor = VideoProcessor()
result = processor.load_videos("dtl_video.mp4", "face_video.mp4")
if result['success']:
    frames = processor.get_all_frames()
```

**Supported Formats**: MP4, AVI, MOV, MKV, WEBM

**Frame Alignment:**
- Automatically checks if DTL and Face videos have matching frame counts
- Logs warnings if frame counts differ
- Uses shorter video length for processing
- Returns alignment warnings in result dictionary

**Downsampling:**
- Optional `downsample_factor` parameter for faster processing
- `downsample_factor=1`: Process all frames (default)
- `downsample_factor=2`: Process every other frame (2x faster)
- Useful for long videos or pro swing analysis

---

### 12. analytics.py

**Analytics & Logging** - Tracks and exports swing analysis data

**Class**: `SwingAnalytics`

**Key Methods**:
- `log_frame(frame_number, processing_time_ms, swing_detected, pose_quality)` - Log frame-level metrics
- `log_swing(swing_id, metrics, flaw_analysis, pro_match, shot_data)` - Log complete swing analysis
- `export_csv(filename)` - Export swing history to CSV
- `export_html_dashboard(filename)` - Export interactive HTML dashboard
- `get_summary_stats()` - Get summary statistics for current session

**Features**:
- Frame-level performance tracking
- Flaw evolution tracking (deltas)
- Similarity evolution tracking
- Interactive charts (Chart.js)
- CSV export for spreadsheet analysis

**Usage**:
```python
from src.analytics import SwingAnalytics

analytics = SwingAnalytics("./data/analytics")
analytics.log_swing(swing_id, metrics, flaw_analysis, pro_match, shot_data)
csv_path = analytics.export_csv()
html_path = analytics.export_html_dashboard()
```

**Export Formats**:
- CSV: All swing data in spreadsheet format
- HTML: Interactive dashboard with charts and statistics
