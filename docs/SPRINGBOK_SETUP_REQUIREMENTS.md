# Springbok Integration

## Overview

ProMirrorGolf integrates with the Springbok MLM2PRO-GSPro-Connector to receive launch monitor data simultaneously with GSPro. The bridge intercepts Springbok data and forwards it to both applications.

## ⚠️ Important: Startup Order

**ProMirrorGolf must be started first.** If ProMirrorGolf is not running, the Springbok connector will show connection errors because the bridge (port 922) is not listening.

### Status Indicators

The status bar shows connection status:
- **Springbok: ●** (green) = Connected
- **Springbok: ○** (gray) = Waiting
- **GSPro: ●** (green) = Connected  
- **GSPro: ○** (gray) = Not connected

## Setup

### 1. Configure Springbok

Configure Springbok connector to connect to port **922** (instead of 921).

### 2. Enable Bridge in ProMirrorGolf

1. Open Settings → Springbok tab
2. Enable "Bridge Enabled"
3. Verify ports (default: Bridge 922, GSPro 921, ProMirrorGolf 5556)

### 3. Startup Sequence

**Option 1 (Recommended):** Springbok auto-starts GSPro
```
1. Start ProMirrorGolf (bridge starts automatically)
2. Start Springbok (auto-starts GSPro)
3. Connect MLM and hit shots
```

**Option 2:** Manual GSPro startup
```
1. Start ProMirrorGolf
2. Start GSPro + GSPro API Connect
3. Start Springbok
4. Connect MLM and hit shots
```

## Testing

Test without hitting shots:

```bash
python scripts/test_springbok_bridge_without_shot.py
```

Test video recording:

```bash
python scripts/test_springbok_video_recording.py
```

**Requirements:**
- ProMirrorGolf running with bridge enabled
- Session active (for video test)
- GSPro API Connect running (optional)

## Troubleshooting

**Bridge not starting:**
- Check if port 922 is in use
- Verify bridge is enabled in settings
- Check logs for errors

**Springbok can't connect:**
- Verify Springbok is configured for port 922
- Ensure ProMirrorGolf is running first
- Check status indicator in ProMirrorGolf

**GSPro not receiving data:**
- Verify GSPro API Connect is running
- Check status indicator shows "GSPro: ●"
- Check bridge logs for errors

**ProMirrorGolf not receiving data:**
- Verify session is active
- Check shot listener is running (port 5556)
- Check bridge logs for forwarding errors

