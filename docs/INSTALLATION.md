# Installation Guide - ProMirrorGolf

**Complete beginner-friendly guide to installing and setting up ProMirrorGolf**

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Install Python](#step-1-install-python)
3. [Step 2: Download ProMirrorGolf](#step-2-download-promirrorgolf)
4. [Step 3: Install Dependencies](#step-3-install-dependencies)
5. [Step 4: Run the Application](#step-4-run-the-application)
6. [Step 5: First-Time Setup](#step-5-first-time-setup)
7. [Troubleshooting](#troubleshooting)
8. [Quick Start Checklist](#quick-start-checklist)

---

## Prerequisites

Before installing ProMirrorGolf, make sure you have:

- **Windows 10 or Windows 11** (required for high-resolution timer support)
- **Two USB cameras** (recommended for DTL and Face-on views)
- **Internet connection** (for downloading Python and dependencies)
- **Administrator access** (may be needed for some installations)

**Note**: While the application can run with just one camera, two cameras are recommended for the best experience.

---

## Step 1: Install Python

### Check if Python is Already Installed

1. Press `Windows Key + R` to open the Run dialog
2. Type `cmd` and press Enter
3. In the command prompt, type: `python --version`
4. Press Enter

**If you see something like "Python 3.10.x" or higher:**
- ✅ Python is already installed! Skip to [Step 2](#step-2-download-promirrorgolf)

**If you see "Python is not recognized" or an error:**
- ❌ Python is not installed. Continue with the installation below.

### Installing Python (If Needed)

1. **Download Python**
   - Go to: https://www.python.org/downloads/
   - Click the big yellow "Download Python" button
   - This will download the latest Python version (3.12 or newer)

2. **Run the Installer**
   - Double-click the downloaded file (e.g., `python-3.12.x.exe`)
   - **IMPORTANT**: Check the box that says **"Add Python to PATH"** at the bottom
   - Click "Install Now"
   - Wait for installation to complete (this may take a few minutes)

3. **Verify Installation**
   - Close and reopen the command prompt (or restart your computer)
   - Type: `python --version`
   - You should see: `Python 3.12.x` (or similar)

**Troubleshooting Python Installation:**
- If Python still isn't recognized, you may need to restart your computer
- If you forgot to check "Add Python to PATH", you can reinstall Python and check the box this time

---

## Step 2: Download ProMirrorGolf

### Option A: Download as ZIP (Easiest for Beginners)

1. **Download the Project**
   - If you have a ZIP file, extract it to a folder
   - Recommended location: `C:\Users\YourName\Documents\ProMirrorGolf`
   - Right-click the ZIP file → "Extract All" → Choose location → Extract

2. **Note the Folder Location**
   - Remember where you extracted the files (you'll need this in the next step)

### Option B: Using Git (For Advanced Users)

If you have Git installed:

```bash
git clone <repository-url>
cd ProMirrorGolf
```

---

## Step 3: Install Dependencies

Dependencies are additional software packages that ProMirrorGolf needs to run.

### Method 1: Using Command Prompt (Recommended)

1. **Open Command Prompt**
   - Press `Windows Key + R`
   - Type `cmd` and press Enter

2. **Navigate to ProMirrorGolf Folder**
   - Type: `cd ` (with a space after cd)
   - Drag and drop the ProMirrorGolf folder into the command prompt window
   - Press Enter
   
   **Example:**
   ```
   cd C:\Users\YourName\Documents\ProMirrorGolf
   ```

3. **Install Dependencies**
   - Type: `pip install -r requirements.txt`
   - Press Enter
   - Wait for installation to complete (this may take 5-10 minutes)
   - You'll see lots of text scrolling by - this is normal!

**What you should see:**
```
Collecting PyQt6>=6.7.0
  Downloading PyQt6-6.7.0...
Installing collected packages...
Successfully installed PyQt6-6.7.0 opencv-python-4.10.0 ...
```

**If you see errors:**
- Make sure you're in the correct folder (check with `dir` command)
- Make sure Python is installed correctly
- Try: `python -m pip install -r requirements.txt` instead

### Method 2: Using PowerShell (Alternative)

1. **Open PowerShell**
   - Press `Windows Key + X`
   - Click "Windows PowerShell" or "Terminal"

2. **Navigate to Folder**
   - Type: `cd ` (with a space)
   - Drag and drop the ProMirrorGolf folder
   - Press Enter

3. **Install Dependencies**
   - Type: `pip install -r requirements.txt`
   - Press Enter

---

## Step 4: Run the Application

### Quick Start

1. **Open Command Prompt** (or PowerShell)
2. **Navigate to ProMirrorGolf folder** (same as Step 3)
3. **Run the Application**
   - Type: `python main.py`
   - Press Enter

**What should happen:**
- A window should open with "ProMirrorGolf" title
- You may see some text in the command prompt (this is normal)
- The application window should appear

**If nothing happens:**
- Check the command prompt for error messages
- Make sure all dependencies installed correctly
- See [Troubleshooting](#troubleshooting) section below

### Creating a Desktop Shortcut (Optional)

To make it easier to start the application:

1. **Create a Batch File**
   - Right-click in the ProMirrorGolf folder
   - New → Text Document
   - Name it: `Start ProMirrorGolf.bat`
   - Right-click the file → Edit
   - Add these lines:
     ```batch
     @echo off
     cd /d "%~dp0"
     python main.py
     pause
     ```
   - Save and close

2. **Create Shortcut**
   - Right-click `Start ProMirrorGolf.bat`
   - Send to → Desktop (create shortcut)
   - You can now double-click the desktop shortcut to start the app!

---

## Step 5: First-Time Setup

When you first run ProMirrorGolf:

### 1. Configure Cameras

1. **Open Settings**
   - Click the "Settings" button (or press `Ctrl+,`)
   - Go to the "Cameras" tab

2. **Detect Cameras**
   - The app will try to detect your cameras automatically
   - If you have two cameras, you should see:
     - DTL Camera: Camera 0 (or Camera 1)
     - Face Camera: Camera 1 (or Camera 2)

3. **Test Cameras**
   - Click "Test Cameras" to see live preview
   - If cameras don't work:
     - Try different camera IDs (0, 1, 2, etc.)
     - Make sure cameras aren't being used by other apps
     - Check that cameras are properly connected

### 2. Configure Shot Listener

1. **Go to Settings → Shot Listener**
2. **Default Settings** (usually work fine):
   - Host: `127.0.0.1`
   - Port: `5556`
3. **Click "Save"**

### 3. Create Your First Session

1. **Enter Session Name**
   - Type a name like "Practice Session 1"
   
2. **Select Club** (optional)
   - Choose from dropdown (Driver, 7 Iron, etc.)

3. **Add Notes** (optional)
   - Any notes about this session

4. **Click "Start Session"**
   - Cameras should start showing live preview
   - You're ready to record shots!

---

## Troubleshooting

### Problem: "Python is not recognized"

**Solution:**
- Python is not installed or not in PATH
- Reinstall Python and make sure to check "Add Python to PATH"
- Or add Python manually to PATH (advanced)

### Problem: "pip is not recognized"

**Solution:**
- Try: `python -m pip install -r requirements.txt`
- Or: `py -m pip install -r requirements.txt`
- Make sure Python is installed correctly

### Problem: "No module named 'PyQt6'"

**Solution:**
- Dependencies didn't install correctly
- Try: `pip install --upgrade pip`
- Then: `pip install -r requirements.txt`
- Make sure you're in the correct folder

### Problem: "Cameras not detected"

**Solution:**
- Make sure cameras are connected and turned on
- Close other apps that might be using cameras (Zoom, Teams, etc.)
- Try different camera IDs in Settings
- Check Device Manager to see if cameras are recognized by Windows

### Problem: "Port already in use" error

**Solution:**
- Another instance of ProMirrorGolf might be running
- Close all ProMirrorGolf windows
- Or change the port in Settings → Shot Listener

### Problem: Application won't start

**Solution:**
1. Check command prompt for error messages
2. Make sure all dependencies installed: `pip list`
3. Try running: `python -c "import PyQt6; print('OK')"`
4. Check Windows Event Viewer for detailed errors

### Problem: Videos not saving

**Solution:**
- Check disk space (need at least 1GB free)
- Check write permissions for `data/clips/` folder
- Check logs in `data/logs/` folder

### Getting More Help

- Check `docs/TROUBLESHOOTING.md` for detailed troubleshooting
- Check application logs in `data/logs/` folder
- Look for error messages in the command prompt window

---

## Quick Start Checklist

Use this checklist to make sure everything is set up correctly:

- [ ] Python 3.10+ is installed (`python --version` works)
- [ ] ProMirrorGolf folder is extracted/downloaded
- [ ] Dependencies are installed (`pip install -r requirements.txt` completed)
- [ ] Application starts (`python main.py` opens window)
- [ ] Cameras are detected (Settings → Cameras shows cameras)
- [ ] Can create a session (Start Session button works)
- [ ] Can see live camera preview (cameras show video)

**If all checkboxes are checked, you're ready to use ProMirrorGolf!**

---

## Next Steps

Once installation is complete:

1. **Read the README.md** for usage instructions
2. **Check Keyboard Shortcuts** in `docs/KEYBOARD_SHORTCUTS.md`
3. **Try the Test Shot feature** to verify everything works
4. **Connect your launch monitor** (if you have one)

---

## System Requirements Summary

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Windows 10 or Windows 11 |
| **Python Version** | 3.10 or higher (3.12 recommended) |
| **RAM** | 4GB minimum, 8GB recommended |
| **Storage** | 500MB for application, 1GB+ for video clips |
| **Cameras** | 1-2 USB cameras (webcams work fine) |
| **Internet** | Required for initial installation only |

---

## Installation Time Estimate

- **First-time installation**: 15-30 minutes
  - Python installation: 5-10 minutes
  - Downloading dependencies: 5-15 minutes
  - Configuration: 5 minutes

- **Subsequent runs**: Instant (just double-click or run `python main.py`)

---

## Need Help?

If you're stuck:

1. **Check the Troubleshooting section** above
2. **Read `docs/TROUBLESHOOTING.md`** for detailed help
3. **Check application logs** in `data/logs/` folder
4. **Look for error messages** in the command prompt

Good luck and enjoy using ProMirrorGolf! 🏌️

