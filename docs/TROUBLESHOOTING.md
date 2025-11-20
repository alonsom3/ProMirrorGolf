# Troubleshooting Guide

**Having problems? Start here!**

This guide helps you solve common issues with ProMirrorGolf. If you're having installation problems, see [INSTALLATION.md](INSTALLATION.md) first.

## Installation Issues

### "Python is not recognized"
**Problem:** Command prompt says Python is not found.

**Solutions:**
1. Python is not installed - Download from https://www.python.org/downloads/
2. Python not in PATH - Reinstall Python and check "Add Python to PATH"
3. Need to restart - Close and reopen command prompt after installing Python

**Verify:** Type `python --version` in command prompt. Should show Python 3.10 or higher.

### "pip is not recognized"
**Problem:** Can't install dependencies.

**Solutions:**
1. Try: `python -m pip install -r requirements.txt`
2. Or: `py -m pip install -r requirements.txt`
3. Make sure Python is installed correctly (see above)

### "No module named 'PyQt6'"
**Problem:** Application won't start, missing modules.

**Solutions:**
1. Dependencies didn't install - Run: `pip install -r requirements.txt`
2. Wrong folder - Make sure you're in the ProMirrorGolf folder
3. Multiple Python versions - Try: `python -m pip install -r requirements.txt`

### "Port already in use"
**Problem:** Error when starting application.

**Solutions:**
1. Another instance running - Close all ProMirrorGolf windows
2. Change port - Edit Settings → Shot Listener → Change port number
3. Restart computer - Sometimes ports stay locked after crash

### Application Won't Start
**Problem:** Nothing happens when running `python main.py`.

**Solutions:**
1. Check command prompt for error messages (scroll up to see)
2. Verify dependencies: `pip list | findstr PyQt6`
3. Check Python version: `python --version` (needs 3.10+)
4. Check logs: Look in `data/logs/` folder for error files

## Camera Issues

### Camera Not Detected
1. Check camera connections (USB cables)
2. Verify cameras are not being used by another application
3. Open Settings and try different camera IDs
4. Restart the application

### Camera Disconnects During Session
- The application will automatically attempt to reconnect
- Check USB cable connections
- Ensure cameras have sufficient power
- Try different USB ports

### Poor Video Quality
1. Check camera settings in Settings dialog
2. Verify camera resolution and FPS settings
3. Ensure adequate lighting
4. Check USB bandwidth (try different ports)

## Video Recording Issues

### Videos Not Saving
1. Check disk space availability
2. Verify clips directory is writable (check Settings)
3. Check application logs for errors
4. Ensure session is running before shots are detected

### Video Files Corrupted
1. Check disk space during recording
2. Verify USB connection stability
3. Check for antivirus interference
4. Review logs for write errors

### Missing Video Clips
- Videos are only saved if frames are buffered before shot detection
- Wait a few seconds after starting session before triggering shots
- Check circular buffer settings

## Performance Issues

### Slow UI Response
1. Close unnecessary applications
2. Reduce video resolution in Settings
3. Check system resources (CPU, RAM)
4. Review logs for performance warnings

### High CPU Usage
- Reduce FPS in camera settings
- Lower video resolution
- Close other video applications
- Check for background processes

### Memory Issues
- Close and reopen the application periodically
- Reduce buffer size if available
- Check for memory leaks in logs

## Database Issues

### Session Not Saving
1. Check database file permissions
2. Verify disk space
3. Review logs for database errors
4. Check database file integrity

### Data Loss
- Regular backups recommended
- Check logs for database errors
- Verify database file exists and is accessible

## Shot Detection Issues

### Shots Not Detected
1. Verify TCP listener is running (check status bar)
2. Check connector configuration (host/port)
3. Test with "Run Test Shot" button
4. Review logs for connection errors

### Incorrect Shot Data
- Verify connector is sending correct JSON format
- Check data fields match expected format
- Review logs for parsing errors

## UI Issues

### Buttons Not Working
1. Restart the application
2. Check for error messages in status bar
3. Review logs for exceptions
4. Verify window is not minimized/hidden

### Display Issues
1. Check display scaling settings
2. Verify window is not off-screen
3. Try maximizing window
4. Check graphics drivers

## Export Issues

### Export Fails
1. Check file permissions for output directory
2. Verify disk space
3. Check for invalid characters in session names
4. Review logs for export errors

### Missing Data in Exports
- Verify session has shots
- Check data fields are populated
- Review export format requirements

## General Issues

### Application Crashes
1. Check logs for error messages
2. Verify all dependencies are installed
3. Check system requirements
4. Try running with administrator privileges

### Configuration Not Saving
1. Check config file permissions
2. Verify config file location
3. Review logs for config errors

## Getting Help

If issues persist:
1. Check application logs in `data/logs/`
2. Review error messages in status bar
3. Verify system requirements
4. Check for known issues in documentation

