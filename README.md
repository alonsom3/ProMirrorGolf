# ProMirrorGolf

Professional golf swing analysis application with dual camera capture, comprehensive session management, and advanced shot data integration.

## Features

### Core Functionality
- **Dual USB Camera Capture** - Simultaneous DTL (Down the Line) and Face-on camera recording with live preview
- **Session Management** - SQLite database for persistent storage of sessions and shots
- **Shot Data Integration** - TCP JSON listener for launch monitor data via TCP/IP
- **Automatic Video Recording** - Circular buffer captures video clips automatically on shot detection
- **Modern UI with Theme Support** - GitHub-inspired dark theme with light theme option, consistent styling throughout

### Shot Review & Analysis
- **Slow-Motion Playback** - Precise playback at 0.1x, 0.25x, 0.5x, 1x, 2x, 4x speeds
- **Drawing Tools** - Freehand, swing plane, and reference line drawing with customizable colors and widths
- **Timeline Scrubber** - Visual markers at key positions (0%, 25%, 50%, 75%, 100%) for quick navigation
- **Dual Video Display** - Side-by-side DTL and Face-on video playback
- **FPS/Duration Overlay** - Real-time playback statistics displayed on video canvas
- **Shot Data Overlay** - Display shot metrics (club speed, ball speed, distance) directly on video
- **Overlay Customization** - Customize overlay position, metrics, colors, and font size
- **Next/Previous Navigation** - Navigate between shots with automatic skipping of shots without video

### Shot Management
- **Tags** - Add custom tags to shots for organization and filtering
- **Favorites** - Mark important shots as favorites for quick access
- **Notes** - Multi-line notes for detailed shot analysis and observations
- **Batch Operations** - Bulk tag and favorite operations for multiple shots
- **Thumbnail Generation** - Automatic thumbnail generation for quick visual identification

### Session Browser
- **Advanced Filtering** - Filter sessions by date range, club type, and custom search
- **Multi-Select** - Select multiple sessions for batch operations
- **Session Editing** - Edit session name, club, and notes inline
- **Session Deletion** - Delete sessions with confirmation dialogs
- **Export Functionality** - Export sessions to CSV, JSON, or PDF formats
- **Shot Table** - View all shots with thumbnails, tags, and favorite indicators

### Analysis & Comparison
- **Analysis Dashboard** - Comprehensive statistics and trend analysis
  - Speed trends (Club Speed, Ball Speed)
  - Distance trends (Carry, Total)
  - Spin trends (Total Spin)
  - Dispersion plots (Carry vs. Launch Direction) with heat map view
  - Club comparison charts
  - Distribution analysis (histograms, box plots)
  - Advanced analytics (tempo, swing plane, ball flight prediction)
- **Multi-Session Comparison** - Side-by-side comparison of shots from different sessions
- **Period Filtering** - Filter analysis by date ranges (Today, Last 3/7/30/90 days, Custom range)
- **Club Filtering** - Filter analysis by specific club types
- **Chart Customization** - Customize colors, grid, legend, and marker sizes
- **Data Export** - Export charts as PNG/SVG and data as CSV/Excel
- **Report Builder** - Generate custom reports (PDF, HTML, DOCX) with templates

### Data Import & Management
- **CSV/Excel Import** - Import shot data from CSV and Excel files (File → Import Data, Ctrl+I)
- **Data Validation** - Automatic validation of shot metrics to flag anomalies and impossible values
- **Duplicate Detection** - Find and merge duplicate shots based on similarity (File → Find Duplicates)
- **Smart Filters** - Save and reuse filter combinations for quick data access
- **Advanced Search** - Full-text search across all session and shot data
- **Custom Fields** - Define custom data fields for sessions and shots
- **Tag Management** - Organize shots with tags, categories, and autocomplete suggestions

### Performance & Reliability
- **Parallel Processing** - Multi-threaded video writing for improved responsiveness
- **Error Recovery** - Automatic camera reconnection on disconnect
- **High-Resolution Timing** - Precise playback timing using Windows high-resolution timer
- **Optimized Frame Processing** - Efficient BGR to RGB conversion and frame handling
- **Pagination** - Automatic pagination for large datasets (>100 rows) to improve performance
- **Caching** - LRU cache system for frequently accessed data (sessions, shots, thumbnails, stats)
- **Multi-Monitor Support** - Optimal window positioning and layout for dual-monitor setups
- **Database Indexes** - Optimized queries with indexes on common fields (session_id, recorded_at, speeds, distances)

### Advanced Features
- **Advanced Search** - Visual filter builder with saved presets, multiple operators (equals, greater than, between, etc.)
- **Measurement Tools** - Save measurements with shots, Ctrl+S shortcut, auto-save on close
- **Video Export Presets** - Quality presets (High/Medium/Low) with automatic codec and scale selection
- **Chart Export** - Export all web dashboard charts as PNG images
- **Layout Customization** - Save and load window layouts, multi-monitor support
- **Mobile Support** - Progressive Web App (PWA) foundation, responsive design for mobile devices

## Installation

### Quick Start (For Beginners)

**New to Python or command line?** See our [Complete Installation Guide](docs/INSTALLATION.md) for step-by-step instructions with screenshots and troubleshooting.

**Want to get running fast?** See [Quick Start Guide](docs/QUICK_START.md) for a 5-minute setup.

### Quick Installation (For Experienced Users)

**Requirements:**
- Python 3.10 or higher
- Windows 10/11 (for high-resolution timer support)
- USB cameras (2 recommended for DTL and Face-on views)

**Steps:**

1. **Install Python** (if not already installed)
   - Download from https://www.python.org/downloads/
   - **Important**: Check "Add Python to PATH" during installation

2. **Download ProMirrorGolf**
   - Extract ZIP file or clone repository
   - Note the folder location

3. **Install Dependencies**
   ```bash
   # Open Command Prompt in the ProMirrorGolf folder
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python main.py
   ```

**That's it!** The application will start and the web dashboard will be available at http://127.0.0.1:5000

**Having trouble?** Check [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed, beginner-friendly instructions.

### Web Dashboard

The web dashboard automatically starts when you run `main.py`. Access it at:
- **URL**: http://127.0.0.1:5000
- **Features**: Same data and functionality as the desktop app
  - Real-time statistics and charts
  - Session browsing and filtering
  - Period and club filtering
  - Interactive charts (speed, distance, spin, dispersion, club comparison)
  - Responsive design for desktop and mobile

To disable the web dashboard, edit `data/config.json` and set `"web.enabled": false`.

To run the web dashboard separately:
```bash
python web/start_server.py
```

### Dependencies
- PyQt6 >= 6.7.0 - GUI framework
- opencv-python >= 4.10.0 - Video capture and processing
- numpy >= 1.26.0 - Numerical operations
- SQLAlchemy >= 2.0.0 - Database ORM
- matplotlib >= 3.8.0 - Chart generation
- reportlab >= 4.0.0 - PDF report export
- flask >= 3.0.0 - Web dashboard API server
- flask-cors >= 4.0.0 - CORS support for web dashboard
- python-docx >= 1.1.0 - DOCX report export
- pandas >= 2.0.0 - Data analysis and Excel export
- openpyxl >= 3.1.0 - Excel file support
- psutil >= 5.9.0 - System utilities
- python-dotenv >= 1.0.0 - Configuration management

## Quick Start

**New to ProMirrorGolf?** Start here:

1. **📥 Install** - See [Installation Guide](docs/INSTALLATION.md) for step-by-step setup
2. **🚀 Quick Start** - See [Quick Start Guide](docs/QUICK_START.md) to get running in 5 minutes
3. **❓ Troubleshooting** - Having issues? Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
4. **📚 Documentation** - See [Documentation Index](docs/README.md) for guides

## Usage

### Starting a Session

1. **Configure Cameras** (if needed)
   - Open Settings from the main window
   - Select DTL and Face camera IDs
   - Adjust resolution and FPS if needed

2. **Set Session Details**
   - Enter session name (required)
   - Select club type from dropdown (optional)
   - Add session notes (optional)

3. **Start Session**
   - Click "Start Session" button
   - Cameras will begin capturing frames
   - Live preview displays in main window

### Recording Shots

Shots are automatically detected via TCP listener (default: `127.0.0.1:5556`). When a shot is detected:
- Video clips are automatically saved from the circular buffer (5 seconds before shot)
- Shot data is logged to the database with all available metrics
- Shot appears in the table (green time = has video)
- Thumbnails are generated automatically

### Testing Shot Detection

**Method 1: Test Shot Button**
1. Start a session
2. Wait a few seconds for cameras to buffer
3. Click "Run Test Shot" button

**Method 2: Test Script**
```bash
python test_shot_sender.py [host] [port]
```

**Method 3: Manual TCP**
```python
import socket
import json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 5556))
sock.sendall((json.dumps({
    "ClubSpeed": 95.5,
    "BallSpeed": 142.3,
    "TotalSpin": 3200,
    "LaunchAngle": 12.5,
    "CarryDistance": 245.0
}) + "\n").encode("utf-8"))
sock.close()
```

### Reviewing Shots

1. **From Main Window**
   - Double-click any shot in the shot table
   - Shot review window opens with DTL and Face videos

2. **From Session Browser**
   - Open Session Browser
   - Select a session
   - Click on any shot in the shots table
   - Use Previous/Next buttons to navigate between shots

3. **Playback Controls**
   - Use Play/Pause to control playback
   - Adjust speed with speed dropdown (0.1x to 4x)
   - Use timeline scrubber to jump to specific frames
   - Rewind/Forward buttons for 10-frame jumps

4. **Drawing Tools**
   - Select tool (Freehand, Swing Plane, Reference, Select)
   - Choose color and line width
   - Draw on video canvas
   - Right-click lines to change color
   - Clear button removes all drawings

### Managing Shots

**Adding Tags**
- In shot review window, click "Edit Tags"
- Enter comma-separated tags
- Tags are saved automatically

**Marking Favorites**
- Click the star button in shot review window
- Favorites are indicated with ★ in shot tables

**Adding Notes**
- Click "Edit Notes" in shot review window
- Enter multi-line notes
- Notes are saved to database

**Batch Operations**
- In Session Browser, select multiple shots
- Click "Batch Operations"
- Add/remove tags or set/remove favorites for all selected shots

### Session Management

**Viewing Sessions**
- Click "Session Browser" in main window
- All sessions listed in sidebar
- Filter by date, club, or search term
- Click session to view shots

**Editing Sessions**
- Select session in Session Browser
- Click "Edit" button
- Modify name, club, or notes
- Changes saved immediately

**Deleting Sessions**
- Select one or more sessions
- Click "Delete Selected"
- Confirm deletion
- All associated shots are deleted

**Exporting Sessions**
- Select one or more sessions
- Click "Export Selected"
- Choose format (CSV, JSON, PDF)
- Select save location

### Analysis Dashboard

1. Click "Analysis" button in main window
2. Select time period (Last 7 days, 30 days, All time)
3. Optionally filter by club type
4. View:
   - Summary statistics (Total Shots, Avg Speeds, Avg Distances)
   - Speed trend charts
   - Distance trend charts
   - Spin trend charts
   - Dispersion plots
   - Club comparison charts

### Multi-Session Comparison

1. Click "Comparison" button in main window
2. Select sessions from dropdown
3. Click "Add" to add to comparison list
4. Click "Compare" to view side-by-side statistics
5. Click "Side-by-Side Review" to open two shot review windows

### Report Builder

1. Open Analysis Dashboard
2. Click "Build Report" button
3. Select a template:
   - **Session Summary** - Single session report with key metrics
   - **Performance Trends** - Multi-session trend analysis with charts
   - **Club Comparison** - Compare performance across clubs
   - **Custom Report** - Build your own custom report
4. Configure filters (date range, club type)
5. Choose export format (PDF, HTML, DOCX)
6. Generate and save report

### Web Dashboard

Access your data remotely via web browser:

1. **Start Web Server**
   ```bash
   python web/start_server.py
   ```

2. **Access Dashboard**
   - Open browser: `http://127.0.0.1:5000`
   - View sessions and statistics
   - Filter by club and date range
   - Mobile-responsive design

3. **API Endpoints**
   - `GET /api/sessions` - List all sessions
   - `GET /api/sessions/<id>` - Get session details
   - `GET /api/shots` - Get shots with filters
   - `GET /api/stats` - Get summary statistics
   - `GET /api/clubs` - List available clubs

## Project Structure

```
ProMirrorGolf/
├── app/
│   ├── widgets/
│   │   ├── camera_view.py          # Live camera preview widget
│   │   ├── shot_review_window.py   # Shot review with playback and drawing
│   │   ├── session_browser.py      # Session management and browsing
│   │   ├── session_comparison.py   # Multi-session comparison
│   │   ├── analysis_dashboard.py  # Analysis charts and statistics
│   │   ├── video_player.py         # Video playback widget
│   │   ├── marked_slider.py        # Timeline scrubber with markers
│   │   ├── settings_dialog.py     # Application settings
│   │   ├── import_dialog.py        # CSV/Excel import dialog
│   │   ├── enhanced_table.py       # Table with filtering, sorting, pagination
│   │   ├── goals_dialog.py          # Goals management dialog
│   │   ├── recent_shots_dialog.py  # Recent shots viewer
│   │   ├── thumbnail_grid.py       # Thumbnail grid view
│   │   ├── report_builder_dialog.py # Report builder UI
│   │   ├── tag_edit_dialog.py      # Tag editing dialog
│   │   ├── tag_input.py            # Tag input widget with autocomplete
│   │   ├── custom_field_editor.py  # Custom field editor
│   │   ├── custom_fields_form.py   # Custom fields form widget
│   │   ├── shortcut_editor.py     # Shortcut customization dialog
│   │   └── trajectory_3d.py        # 3D trajectory visualization (deprecated)
│   ├── main_window.py              # Main application window
│   └── theme.py                    # UI theme definitions
├── core/
│   ├── buffer.py                   # Circular buffer for video frames
│   ├── camera_service.py           # Camera capture and management
│   ├── config.py                   # Configuration management
│   ├── session_manager.py          # Database operations
│   ├── shot_listener.py            # TCP shot data listener
│   ├── system_timer.py             # High-resolution timer utilities
│   ├── thumbnails.py               # Thumbnail generation
│   ├── video_export.py             # Video export with drawings
│   ├── data_import.py              # CSV/Excel import functionality
│   ├── data_validation.py          # Shot data validation
│   ├── duplicate_detection.py      # Duplicate shot detection and merging
│   ├── cache_manager.py             # LRU cache for performance
│   ├── multi_monitor.py             # Multi-monitor layout support
│   ├── search.py                    # Advanced search functionality
│   ├── filters.py                   # Smart filter management
│   ├── analytics.py                 # Advanced analytics (tempo, swing plane, etc.)
│   ├── goals.py                     # Goal setting and tracking
│   ├── recent_shots.py              # Recent shots tracking
│   ├── backup.py                    # Backup and restore functionality
│   ├── themes.py                    # Custom theme management
│   ├── session_templates.py         # Session template management
│   ├── shortcuts.py                 # Keyboard shortcut management
│   ├── tag_manager.py               # Tag management system
│   ├── custom_fields.py             # Custom fields management
│   ├── column_preferences.py        # Table column preferences
│   ├── report_builder.py            # Report generation (PDF, HTML, DOCX)
│   └── export.py                    # Export functionality (CSV, JSON, PDF)
├── data/
│   ├── clips/                      # Saved video clips
│   ├── thumbnails/                 # Generated thumbnails
│   ├── logs/                       # Application logs
│   └── promirror.db                # SQLite database
├── docs/
│   ├── KEYBOARD_SHORTCUTS.md      # Keyboard shortcuts reference
│   └── TROUBLESHOOTING.md         # Troubleshooting guide
├── scripts/
│   └── profile_performance.py     # Performance profiling script
├── tests/
│   ├── test_core_functionality.py # Core functionality tests
│   ├── test_ui_integration.py    # UI integration tests
│   └── run_tests.py               # Test runner
├── main.py                         # Application entry point
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Design System & Themes

ProMirrorGolf follows a comprehensive design system for consistent, accessible UI components with dynamic theme support.

### Design System
See [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) for complete specifications including:
- **Color Palette**: GitHub-inspired dark theme with WCAG AA compliant contrast ratios
- **Spacing System**: 8px grid system for consistent layouts
- **Typography**: System font stack with defined sizes and weights
- **Component Specifications**: Detailed specs for buttons, inputs, tables, and more
- **Accessibility Standards**: WCAG compliance guidelines and testing checklist

### Theme System
The application supports dynamic theme switching:
- **Dark Theme**: Default GitHub-inspired dark theme
- **Light Theme**: Light theme with proper contrast ratios
- **Theme Switching**: Available in Settings → Appearance tab
- **Automatic Updates**: All UI components update when theme changes

See [docs/THEME_SYSTEM.md](docs/THEME_SYSTEM.md) for complete theme system documentation.

Design constants are available in `app/design_constants.py` for programmatic access to colors, spacing, and typography values. Always use `get_current_colors()` to get theme-aware colors.

## Configuration

Configuration is stored in `config/config.json`. Key settings:

- `cameras.dtl_id` - DTL camera ID (default: 0)
- `cameras.face_id` - Face camera ID (default: 1)
- `cameras.fps` - Frame rate (default: 60)
- `cameras.resolution` - Resolution [width, height] (default: [1280, 720])
- `storage.buffer_seconds` - Pre-shot buffer duration (default: 5)
- `storage.clips_dir` - Video clips directory (default: "data/clips")
- `storage.database` - Database path (default: "data/promirror.db")
- `shot_listener.host` - TCP listener host (default: "127.0.0.1")
- `shot_listener.port` - TCP listener port (default: 5556)

## Keyboard Shortcuts

See [docs/KEYBOARD_SHORTCUTS.md](docs/KEYBOARD_SHORTCUTS.md) for a complete list of keyboard shortcuts.

### Quick Reference
- **Main Window**: `Ctrl+S` (Start), `Ctrl+B` (Browse Sessions), `Ctrl+A` (Analysis)
- **Shot Review**: `Space` (Play/Pause), `1-6` (Speed), `D/P/R/E` (Drawing tools)
- **Shot Table**: `Return` (Review), `Delete` (Delete), `F/T/N` (Metadata)

## Troubleshooting

For detailed troubleshooting information, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

### Common Issues

**Cameras Not Detecting**
- Check camera IDs in Settings
- Ensure cameras are not in use by other applications
- Try different camera IDs (0, 1, 2, etc.)

**Videos Not Saving**
- Check disk space
- Verify write permissions for clips directory
- Check logs in `data/logs/` for errors

**Playback Too Fast/Slow**
- Ensure high-resolution timer is enabled (Windows only)
- Check FPS settings match camera capabilities
- Verify video files are not corrupted

**Database Errors**
- Check database file permissions
- Ensure sufficient disk space
- Database will auto-migrate on schema changes

## Testing

## Testing

### Running Tests
```bash
# Run all tests
python tests/run_tests.py

# Quick verification
python scripts/quick_test.py

# Performance profiling
python scripts/profile_performance.py
```
