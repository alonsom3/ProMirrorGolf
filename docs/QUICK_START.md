# Quick Start Guide - ProMirrorGolf

**Get up and running in 5 minutes!**

## Prerequisites Check

Before starting, make sure you have:
- ✅ Windows 10 or 11
- ✅ Python 3.10+ installed
- ✅ Two USB cameras connected
- ✅ ProMirrorGolf downloaded/extracted

**Not sure?** See [INSTALLATION.md](INSTALLATION.md) for detailed setup.

## Step 1: Start the Application

1. Open Command Prompt
2. Navigate to ProMirrorGolf folder:
   ```
   cd C:\path\to\ProMirrorGolf
   ```
3. Run the application:
   ```
   python main.py
   ```

**Expected:** Application window opens with camera preview areas.

## Step 2: Configure Cameras

1. Click **Settings** button (or press `Ctrl+,`)
2. Go to **Cameras** tab
3. Select camera IDs:
   - DTL Camera: Usually Camera 0 or 1
   - Face Camera: Usually Camera 1 or 2
4. Click **Test Cameras** to verify
5. Click **Save**

**Troubleshooting:**
- No cameras showing? Try different IDs (0, 1, 2, etc.)
- Cameras used by other apps? Close Zoom, Teams, etc.
- Still not working? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Step 3: Create Your First Session

1. **Enter Session Name**
   - Type: "My First Session"

2. **Select Club** (optional)
   - Choose from dropdown (e.g., "Driver")

3. **Add Notes** (optional)
   - Any notes about this session

4. **Click "Start Session"**
   - Cameras should show live preview
   - Status should say "Session Active"

## Step 4: Test Shot Detection

### Option A: Test Shot Button (Easiest)

1. Wait 5 seconds after starting session (for buffer)
2. Click **"Run Test Shot"** button
3. Shot should appear in the table below
4. Double-click the shot to review

### Option B: Connect Launch Monitor

**Standard TCP Connection:**
1. Configure your launch monitor to send data to:
   - Host: `127.0.0.1`
   - Port: `5556`
2. Take a shot
3. Shot should automatically appear in table

**Springbok MLM2PRO Integration:**
1. See [Springbok Setup Guide](SPRINGBOK_SETUP_REQUIREMENTS.md) for integration with Springbok connector and GSPro
2. Enable bridge in Settings → Springbok tab
3. Configure Springbok to connect to port 922

## Step 5: Review Your Shot

1. **Double-click** any shot in the table
2. Shot review window opens with:
   - DTL video (left)
   - Face video (right)
   - Playback controls (bottom)

3. **Try these controls:**
   - **Space** - Play/Pause
   - **1-6** - Change speed (0.1x to 4x)
   - **Left/Right arrows** - Skip 10 frames
   - **Click timeline** - Jump to specific frame

4. **Try drawing tools:**
   - Click **Freehand** tool
   - Draw on video
   - Change color with color picker
   - Change width with dropdown

## Common Tasks

### View All Sessions
- Click **"Session Browser"** button (or `Ctrl+B`)
- All sessions listed in sidebar
- Click session to see shots

### View Statistics
- Click **"Analysis"** button (or `Ctrl+A`)
- See trends, charts, and statistics
- Filter by date range or club

### Export Data
- In Session Browser, select sessions
- Click **"Export Selected"**
- Choose format (CSV, JSON, PDF)

### Change Theme
- Click **Settings** → **Appearance** tab
- Select Dark or Light theme
- Click **Save**

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Start Session | `Ctrl+S` |
| Session Browser | `Ctrl+B` |
| Analysis | `Ctrl+A` |
| Settings | `Ctrl+,` |
| Play/Pause | `Space` (in shot review) |
| Change Speed | `1-6` (in shot review) |

**Full list:** See [KEYBOARD_SHORTCUTS.md](KEYBOARD_SHORTCUTS.md)

## Next Steps

Now that you're up and running:

1. **Record some shots** - Start a session and take some test shots
2. **Review shots** - Double-click shots to review and analyze
3. **Add tags** - Organize shots with tags (click "Edit Tags" in review)
4. **Mark favorites** - Click star button for important shots
5. **View analysis** - Check trends and statistics in Analysis dashboard

## Getting Help

- **Installation problems?** → [INSTALLATION.md](INSTALLATION.md)
- **Something not working?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Want to learn more?** → [README.md](../README.md)
- **Check logs** → `data/logs/` folder

## Tips for Best Results

1. **Wait 5 seconds** after starting session before taking shots (for video buffer)
2. **Use two cameras** for best analysis (DTL + Face-on)
3. **Add tags** to organize shots (e.g., "good", "slice", "hook")
4. **Mark favorites** for shots you want to review later
5. **Check analysis** regularly to track progress

Enjoy using ProMirrorGolf! 🏌️

