# ProMirrorGolf v2.0 - Sanity Test Plan

**Purpose**: Automated and manual test procedures to verify production readiness  
**Duration**: ~30-60 minutes  
**Frequency**: Before each release

---

## 🎯 Test Objectives

1. Verify all core functionality works correctly
2. Ensure UI components are responsive and thread-safe
3. Validate performance meets targets
4. Confirm error handling is user-friendly
5. Check documentation is complete and accurate

---

## 🤖 Automated Sanity Tests

### Quick Run (Recommended)

```bash
python sanity_test.py
```

**Expected Result**: Exit code 0, all critical tests pass

### What Gets Tested

1. **Dependencies Check**
   - Verifies all required packages installed
   - Checks: customtkinter, cv2, numpy, mediapipe, psutil

2. **Module Imports**
   - Tests all UI and backend modules can be imported
   - Verifies no circular dependencies

3. **Config Validation**
   - Checks `config.json` exists and is valid JSON
   - Verifies required keys present

4. **File Structure**
   - Verifies all required files exist
   - Checks source and UI modules present

5. **UI Modernization Tests**
   - Runs `test_ui_modernization.py`
   - Tests all UI components
   - Verifies thread safety

6. **Stress Tests**
   - Runs `test_stress_ui.py`
   - Tests rapid updates, memory usage, concurrency

7. **E2E Pipeline Tests**
   - Runs `test_e2e_swing_pipeline.py`
   - Tests full swing analysis pipeline

8. **Mobile API Module**
   - Verifies mobile API can be initialized
   - Non-blocking (warns if fails)

9. **Git Status**
   - Checks for uncommitted changes
   - Non-blocking (warns if changes found)

---

## 📋 Manual Test Procedures

### Test 1: Application Startup (2 minutes)

**Objective**: Verify application starts correctly

**Steps**:
1. Open terminal/command prompt
2. Navigate to project directory
3. Run: `python main.py`
4. Observe application window

**Expected Results**:
- ✅ Window opens without errors
- ✅ All UI components visible
- ✅ Status shows "Not Active"
- ✅ No error messages in console
- ✅ App icon displays (if available)

**Pass Criteria**: Application starts successfully, UI loads completely

---

### Test 2: Video Upload & Processing (5 minutes)

**Objective**: Verify video upload and processing workflow

**Prerequisites**: Have test videos ready (30-60 second MP4 files)

**Steps**:
1. Click "Upload Video" button
2. Select DTL video (first dialog)
3. Select Face-on video (second dialog)
4. Observe progress bar
5. Wait for processing to complete
6. Verify results display

**Expected Results**:
- ✅ File dialogs open correctly
- ✅ Videos selected successfully
- ✅ Progress bar updates smoothly
- ✅ Status messages update: "Loading videos..." → "Processing..." → "Complete"
- ✅ Metrics display in sidebar
- ✅ Recommendations show
- ✅ No crashes or freezes

**Pass Criteria**: Videos process successfully, results display correctly

---

### Test 3: Quality Mode Selection (3 minutes)

**Objective**: Verify quality slider affects processing

**Steps**:
1. Upload test video
2. Before processing, change quality mode:
   - Select "Speed" mode
   - Process video, note processing time
3. Repeat with "Balanced" mode
4. Repeat with "Quality" mode

**Expected Results**:
- ✅ Quality dropdown updates
- ✅ Processing time varies by mode:
  - Speed: Fastest (<100ms/frame)
  - Balanced: Medium speed
  - Quality: Slower but higher quality
- ✅ Results still accurate in all modes

**Pass Criteria**: Quality modes affect processing speed appropriately

---

### Test 4: View Switching (2 minutes)

**Objective**: Verify view buttons work correctly

**Steps**:
1. After processing a video, click view buttons:
   - "Side" view
   - "Front" view
   - "Top" view
   - "Overlay" view
2. Observe skeleton display updates

**Expected Results**:
- ✅ View buttons respond immediately
- ✅ Skeleton display updates for each view
- ✅ No errors or crashes
- ✅ View state persists

**Pass Criteria**: All views switch correctly, display updates

---

### Test 5: Performance Dashboard (3 minutes)

**Objective**: Verify performance metrics display correctly

**Steps**:
1. Start video processing
2. Observe performance dashboard during processing
3. Check metrics update:
   - CPU usage
   - Memory usage
   - GPU usage (if available)
   - FPS
   - Frame time
   - ETA

**Expected Results**:
- ✅ All metrics update in real-time
- ✅ CPU/Memory/GPU show reasonable values
- ✅ Frame time displays correctly
- ✅ Warning shown if frame time >100ms
- ✅ ETA calculates and updates

**Pass Criteria**: Dashboard updates correctly, metrics accurate

---

### Test 6: Export Features (5 minutes)

**Objective**: Verify export functions work

**Steps**:
1. After processing a video:
2. Click "Save HTML" button
3. Select save location
4. Verify HTML file created
5. Open HTML file in browser
6. Verify report content

**Expected Results**:
- ✅ Export buttons work
- ✅ File dialogs open
- ✅ Files save correctly
- ✅ HTML report contains:
  - Metrics data
  - Flaw analysis
  - Pro comparison
  - Charts/graphs (if applicable)
- ✅ Report opens in browser

**Pass Criteria**: All export functions work, files created correctly

---

### Test 7: Cancel Processing (2 minutes)

**Objective**: Verify cancel button works safely

**Steps**:
1. Start video processing
2. Click "Cancel" button mid-processing
3. Observe application behavior

**Expected Results**:
- ✅ Cancel button appears during processing
- ✅ Processing stops safely
- ✅ No crashes or errors
- ✅ UI returns to ready state
- ✅ No partial data saved

**Pass Criteria**: Cancel works safely, no crashes

---

### Test 8: Error Handling (3 minutes)

**Objective**: Verify error messages are user-friendly

**Steps**:
1. Try to export video without processing one first
2. Try to upload invalid file format
3. Try to upload corrupted video
4. Observe error messages

**Expected Results**:
- ✅ Error messages clear and helpful
- ✅ No technical jargon
- ✅ Actionable suggestions provided
- ✅ No crashes
- ✅ UI remains stable

**Pass Criteria**: Errors handled gracefully, messages user-friendly

---

### Test 9: Stress Test - Long Video (10 minutes)

**Objective**: Verify application handles long videos

**Prerequisites**: 3-5 minute test video

**Steps**:
1. Upload long video (3-5 minutes)
2. Monitor:
   - Memory usage (Task Manager/Activity Monitor)
   - CPU usage
   - Processing progress
   - Application responsiveness
3. Let processing complete

**Expected Results**:
- ✅ Processing completes without timeout
- ✅ Memory usage stays reasonable (<4GB)
- ✅ No memory leaks
- ✅ UI remains responsive
- ✅ Progress updates continuously
- ✅ No crashes

**Pass Criteria**: Long videos process successfully, no resource issues

---

### Test 10: Batch Processing (5 minutes)

**Objective**: Verify multiple videos process correctly

**Steps**:
1. Upload 3-5 videos sequentially
2. Process each one
3. Monitor memory usage
4. Verify all complete successfully

**Expected Results**:
- ✅ All videos process successfully
- ✅ Memory released between videos
- ✅ No memory leaks
- ✅ All results saved correctly
- ✅ UI remains responsive

**Pass Criteria**: Batch processing works, no memory issues

---

## 📊 Test Results Template

### Automated Tests

```
Date: _______________
Tester: _______________

Test Suite              | Status | Notes
------------------------|--------|------------------
Dependencies Check      | ✅/❌  | 
Module Imports          | ✅/❌  | 
Config Validation       | ✅/❌  | 
UI Modernization Tests  | ✅/❌  | 
Stress Tests            | ✅/❌  | 
E2E Pipeline Tests      | ✅/❌  | 
Mobile API Module       | ✅/❌  | 
Git Status              | ✅/❌  | 

Overall: ✅ PASS / ❌ FAIL
```

### Manual Tests

```
Date: _______________
Tester: _______________

Test                    | Status | Time | Notes
------------------------|--------|------|------------------
Application Startup     | ✅/❌  | __m  | 
Video Upload            | ✅/❌  | __m  | 
Quality Mode            | ✅/❌  | __m  | 
View Switching          | ✅/❌  | __m  | 
Performance Dashboard   | ✅/❌  | __m  | 
Export Features         | ✅/❌  | __m  | 
Cancel Processing       | ✅/❌  | __m  | 
Error Handling          | ✅/❌  | __m  | 
Long Video Stress       | ✅/❌  | __m  | 
Batch Processing        | ✅/❌  | __m  | 

Overall: ✅ PASS / ❌ FAIL
```

---

## 🚨 Failure Criteria

### Critical Failures (Block Release)
- Application crashes on startup
- Video processing fails consistently
- Memory leaks detected
- Data corruption
- Security vulnerabilities

### Non-Critical Failures (Review Before Release)
- Minor UI glitches
- Non-essential features not working
- Documentation typos
- Performance slightly below targets

---

## ✅ Sign-Off

**Automated Tests**: ✅ PASS / ❌ FAIL  
**Manual Tests**: ✅ PASS / ❌ FAIL  
**Ready for Release**: ✅ YES / ❌ NO

**Tester Signature**: _________________  
**Date**: _______________

---

## 📝 Notes

_Use this section to document any issues, observations, or recommendations_

