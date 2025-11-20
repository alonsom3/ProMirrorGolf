# ProMirrorGolf Testing Checklist

## Core Functionality

### Camera Capture
- [ ] DTL camera initializes and displays live feed
- [ ] Face camera initializes and displays live feed
- [ ] Camera status indicators show active (green dot) when capturing
- [ ] Camera reconnects automatically on disconnect
- [ ] Camera settings can be changed in Settings dialog
- [ ] Camera resolution and FPS settings are applied correctly

### Session Management
- [ ] Can start a new session with name, club, and notes
- [ ] Session name is required (validation works)
- [ ] Session is saved to database on start
- [ ] Can stop session and it saves correctly
- [ ] Session browser shows all sessions
- [ ] Can edit session name, club, and notes
- [ ] Can delete single session with confirmation
- [ ] Can delete multiple sessions with confirmation
- [ ] Session deletion removes associated shots

### Shot Detection & Recording
- [ ] Test shot button generates random shot data
- [ ] Shot is detected via TCP listener
- [ ] Video clips are saved automatically (DTL and Face)
- [ ] Shot appears in table with green time indicator if video exists
- [ ] Shot data is logged to database correctly
- [ ] Thumbnails are generated automatically
- [ ] Shots without video still appear in table (gray time)

## Shot Review

### Playback Controls
- [ ] Video loads correctly (DTL and Face)
- [ ] Play/Pause button works
- [ ] Stop button resets to first frame
- [ ] Rewind button moves back 10 frames
- [ ] Forward button moves forward 10 frames
- [ ] Speed control works (0.1x, 0.25x, 0.5x, 1x, 2x, 4x)
- [ ] Timeline scrubber allows seeking to any frame
- [ ] Timeline markers appear at 0%, 25%, 50%, 75%, 100%
- [ ] Frame counter updates correctly
- [ ] FPS/duration overlay displays on video

### Drawing Tools
- [ ] Freehand tool draws lines correctly
- [ ] Swing plane tool draws lines correctly
- [ ] Reference line tool draws lines correctly
- [ ] Select tool allows selecting lines
- [ ] Right-click on line changes color
- [ ] Color picker works
- [ ] Line width selector works
- [ ] Clear button removes all drawings
- [ ] Drawings persist during playback

### Shot Metadata
- [ ] Favorite button toggles correctly
- [ ] Favorite status saves to database
- [ ] Tags can be edited
- [ ] Tags save to database
- [ ] Tags display correctly in shot table
- [ ] Notes can be edited
- [ ] Notes save to database
- [ ] Favorite indicator (★) appears in shot table

## Session Browser

### Navigation
- [ ] Sessions list displays all sessions
- [ ] Clicking session loads shots
- [ ] Shots table displays correctly
- [ ] Thumbnails appear in Time column
- [ ] Tags column displays correctly
- [ ] Favorite column displays correctly
- [ ] Can click shot to review (if video exists)
- [ ] Previous/Next buttons navigate between shots
- [ ] Navigation skips shots without video

### Filtering
- [ ] Search bar filters sessions by name
- [ ] Quick filter buttons work (Today, This Week, This Month, All)
- [ ] Club filter works
- [ ] Multiple filters combine correctly

### Operations
- [ ] Can edit session inline
- [ ] Can delete selected sessions
- [ ] Can export sessions (CSV, JSON, PDF)
- [ ] Batch operations dialog opens
- [ ] Can add tags to multiple shots
- [ ] Can remove tags from multiple shots
- [ ] Can set favorite for multiple shots
- [ ] Can remove favorite from multiple shots

## Analysis Dashboard

### Statistics
- [ ] Summary statistics display correctly
- [ ] Total Shots count is accurate
- [ ] Average speeds calculate correctly
- [ ] Average distances calculate correctly

### Charts
- [ ] Speed trends chart displays
- [ ] Distance trends chart displays
- [ ] Spin trends chart displays
- [ ] Dispersion plot displays
- [ ] Club comparison charts display
- [ ] Charts update when filters change

### Filtering
- [ ] Period filter works (Last 7 days, 30 days, All time)
- [ ] Club filter works
- [ ] Filters update charts correctly

## Session Comparison

### Selection
- [ ] Can add sessions to comparison
- [ ] Can remove sessions from comparison
- [ ] Can clear all selections
- [ ] Comparison table displays correctly

### Comparison
- [ ] Compare button generates comparison
- [ ] Side-by-side review opens two windows
- [ ] Both windows display videos correctly

## Error Handling

### Video Operations
- [ ] Handles missing video files gracefully
- [ ] Handles corrupted video files gracefully
- [ ] Handles disk full errors gracefully
- [ ] Handles invalid frame data gracefully
- [ ] Partial video files are cleaned up on error

### Database Operations
- [ ] Handles database connection errors
- [ ] Handles missing shot/session errors
- [ ] Handles invalid data gracefully

### Camera Operations
- [ ] Handles camera disconnect gracefully
- [ ] Handles camera initialization failures
- [ ] Handles invalid camera IDs

## Performance

### Video Writing
- [ ] Multiple clips write concurrently
- [ ] Video writing doesn't block UI
- [ ] Thumbnail generation doesn't block UI
- [ ] Large video files write correctly

### UI Responsiveness
- [ ] UI remains responsive during video saving
- [ ] UI remains responsive during thumbnail generation
- [ ] UI remains responsive during database queries
- [ ] Large shot tables scroll smoothly

## UI Consistency

### Styling
- [ ] All windows use consistent dark theme
- [ ] All buttons have consistent styling
- [ ] All tables have consistent styling
- [ ] All dialogs have consistent styling
- [ ] Colors match theme.py definitions
- [ ] No blue accent colors (should be red)

### Window Sizing
- [ ] All windows can be maximized
- [ ] All windows can be resized
- [ ] Content auto-sizes on window resize
- [ ] Size grips appear on dialogs

## Edge Cases

### Empty States
- [ ] Empty shot table shows message
- [ ] Empty session list shows message
- [ ] No shots in session shows message

### Invalid Data
- [ ] Handles missing shot data gracefully
- [ ] Handles invalid JSON in tags gracefully
- [ ] Handles null/None values gracefully

### File System
- [ ] Handles missing directories
- [ ] Handles permission errors
- [ ] Handles long file paths

