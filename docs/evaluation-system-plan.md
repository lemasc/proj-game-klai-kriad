# Punch Detection Evaluation System - Implementation Plan

## Overview

This document outlines the design and implementation plan for a recording and evaluation system to assess punch detection performance using confusion matrices. The system enables post-hoc manual labeling of recorded gameplay sessions.

## Evaluation Approaches Considered

### 1. Manual Labeling with Replay (Selected)
- Record a session (video + sensor data + timestamps)
- Manually label actual punches in the recording
- Compare detections against labels
- Generates: True Positives, False Positives, False Negatives, True Negatives

### 2. Controlled Testing Protocol
- Perform known sequences (e.g., "10 punches, 5 second rest, repeat")
- Expected punches = ground truth
- Compare actual detections vs expected
- Simpler but less realistic

### 3. Dual Detection System
- Use one detector as "ground truth" (e.g., manual button press on phone when actually punching)
- Compare automated detection against manual markers
- Most accurate for real gameplay

**Decision:** Option 1 (Manual Labeling with Replay) selected due to current limitations.

## System Architecture

### Recording System (Game Modifications)
- Capture webcam video as MP4
- Log sensor data (accelerometer readings with timestamps)
- Log detection events (when punches are detected, with scores)
- Save all to a timestamped directory (e.g., `recordings/session_2025-10-02_143022/`)
- Files: `video.mp4`, `sensor_data.jsonl`, `detections.jsonl`, `metadata.json`

### Evaluation Tool (Separate Python Application)
- Video player with timeline
- Overlay detection markers on video
- Controls to add/remove/classify detections as TP/FP/FN
- Export labeled data and generate confusion matrix

### Workflow
1. Start recording in game
2. Perform punch sequences
3. Stop recording → saves session
4. Open evaluation tool → load session
5. Review video frame-by-frame
6. Label each detection + add missed punches
7. Generate confusion matrix report

## Metrics to Calculate

From the confusion matrix:
- **Precision**: TP / (TP + FP) - How many detections were real punches?
- **Recall**: TP / (TP + FN) - How many real punches were detected?
- **F1 Score**: Harmonic mean of precision and recall
- **Accuracy**: (TP + TN) / Total

---

# Detailed Implementation Plan

## Phase 1: Recording System (Game Modifications)

### 1.1 Data Structures & Formats

**Directory structure:**
```
recordings/
└── session_YYYYMMDD_HHMMSS/
    ├── video.mp4              # Webcam footage
    ├── metadata.json          # Session info
    ├── detections.jsonl       # One detection per line (streaming friendly)
    ├── sensor_data.jsonl      # One sensor reading per line
    └── labels.json            # Manual labels (created by eval tool)
```

**Files to create/modify:**
- `evaluation/recording_config.py` - Recording settings
- `evaluation/recording_manager.py` - Core recording logic

**metadata.json structure:**
```json
{
  "session_id": "session_20251002_143022",
  "start_time": "2025-10-02T14:30:22Z",
  "duration_seconds": 120.5,
  "fps": 30,
  "resolution": [640, 480],
  "detection_config": {...},
  "strategies": ["accelerometer", "pose"]
}
```

**detections.jsonl** (line-delimited JSON):
```json
{"timestamp": 5.234, "frame": 157, "type": "punch", "hand": "right", "confidence": 0.85, "strategy_scores": {"accel": 0.9, "pose": 0.7}, "accel_data": {"x": 12.3, "y": 8.1, "z": 2.4}}
{"timestamp": 7.891, "frame": 237, "type": "punch", "hand": "left", "confidence": 0.72, "strategy_scores": {"accel": 0.8, "pose": 0.5}, "accel_data": {"x": -11.2, "y": 9.3, "z": 1.8}}
```

**sensor_data.jsonl** (high-frequency samples):
```json
{"timestamp": 5.001, "accel": {"x": 0.2, "y": 0.1, "z": 9.8}, "gyro": {"x": 0, "y": 0, "z": 0}}
{"timestamp": 5.021, "accel": {"x": 0.3, "y": 0.2, "z": 9.7}, "gyro": {"x": 0.1, "y": 0, "z": 0}}
```

### 1.2 RecordingManager Class

**Location:** `evaluation/recording_manager.py`

**Key methods:**
- `start_recording(session_name=None)` - Initialize session directory, start video writer
- `stop_recording()` - Finalize files, write metadata
- `record_frame(frame)` - Write video frame
- `record_detection(detection_data)` - Append to detections.jsonl
- `record_sensor_data(sensor_data)` - Append to sensor_data.jsonl
- `is_recording()` - Check recording state

**Integration points:**
- Event listeners for `PUNCH_DETECTED` events
- Hook into accelerometer data stream
- Capture frames from main game loop

### 1.3 Game Integration

**Modify:** `main.py` - PunchDetectionGame class

**Changes:**
- Add `RecordingManager` instance
- Add keyboard shortcut (e.g., 'R' key) to toggle recording
- Pass frames to recorder in main loop
- Subscribe recorder to detection events
- Display recording indicator in UI

**UI additions in UIManager:**
- Red dot indicator when recording
- Session timer display
- Recordings saved count

---

## Phase 2: Evaluation Tool (Separate Application)

### 2.1 Tool Architecture

**New directory structure:**
```
evaluation/
├── __init__.py
├── recording_config.py      # Shared config
├── recording_manager.py     # Used by game
├── eval_tool.py            # Main evaluation app
├── video_player.py         # Video playback widget
├── timeline_widget.py      # Timeline with markers
├── labeling_panel.py       # Labeling controls
├── session_loader.py       # Load recording sessions
└── metrics_calculator.py   # Confusion matrix & stats
```

### 2.2 Main Evaluation Window

**File:** `evaluation/eval_tool.py`

**Features:**
- Session selector (dropdown/list of recordings)
- Video player (OpenCV + tkinter/PyQt)
- Timeline with scrubbing
- Playback controls (play/pause, speed control, frame-by-frame)
- Labeling panel

**UI Layout:**
```
┌─────────────────────────────────────────┐
│ Session: session_20251002_143022    [▼]│
├─────────────────────────────────────────┤
│                                         │
│          Video Player Area              │
│                                         │
├─────────────────────────────────────────┤
│ Timeline: ▮━━━━━●━━━━━━●━━━━━━━━━━━━━ │
│           ^                             │
│           Current position              │
├─────────────────────────────────────────┤
│ Detections at current time:             │
│ ● 5.234s - Right Punch (conf: 0.85)    │
│   [True Positive] [False Positive]      │
│                                         │
│ [+ Add Missed Punch]                    │
├─────────────────────────────────────────┤
│ Progress: 12 labeled / 47 detections   │
│ [Export Labels] [Generate Report]       │
└─────────────────────────────────────────┘
```

### 2.3 Video Player Component

**File:** `evaluation/video_player.py`

**Features:**
- Load MP4 file
- Seek to specific frame/timestamp
- Overlay detection markers on current frame
- Color-coded markers:
  - 🔴 Red = Unlabeled detection
  - 🟢 Green = True Positive
  - 🟡 Yellow = False Positive
  - 🔵 Blue = Manually added (False Negative)

### 2.4 Timeline Widget

**File:** `evaluation/timeline_widget.py`

**Features:**
- Horizontal timeline bar
- Vertical markers for each detection
- Click to jump to timestamp
- Color-coded based on label status
- Hover tooltips with detection info

### 2.5 Labeling Interface

**File:** `evaluation/labeling_panel.py`

**Workflow:**
1. User navigates to detection (via timeline or auto-advance)
2. Reviews video at that timestamp
3. Classifies detection:
   - **True Positive**: Real punch, correctly detected
   - **False Positive**: No punch, incorrectly detected
4. Can add missed punches:
   - Pause at timestamp where punch occurred
   - Click "Add Missed Punch"
   - Specify hand (left/right)
   - Creates False Negative entry

**labels.json format:**
```json
{
  "session_id": "session_20251002_143022",
  "labeled_by": "user",
  "labeled_at": "2025-10-02T15:45:00Z",
  "labels": [
    {
      "timestamp": 5.234,
      "frame": 157,
      "detection_id": 0,
      "label": "TP",
      "hand": "right",
      "notes": ""
    },
    {
      "timestamp": 7.891,
      "frame": 237,
      "detection_id": 1,
      "label": "FP",
      "notes": "Just moving hand, not punching"
    },
    {
      "timestamp": 12.5,
      "frame": 375,
      "detection_id": null,
      "label": "FN",
      "hand": "left",
      "notes": "Missed left punch"
    }
  ]
}
```

### 2.6 Metrics Calculator

**File:** `evaluation/metrics_calculator.py`

**Functions:**
- `calculate_confusion_matrix(labels)` → Returns TP, FP, FN, TN counts
- `calculate_metrics(confusion_matrix)` → Precision, Recall, F1, Accuracy
- `generate_report(session_id, metrics)` → Markdown/HTML report
- `export_dataset(session_ids)` → Combined CSV for analysis

**Report format:**
```markdown
# Punch Detection Evaluation Report

**Session:** session_20251002_143022
**Duration:** 120.5 seconds
**Total Detections:** 47
**Manual Labels:** 47

## Confusion Matrix
|              | Predicted Positive | Predicted Negative |
|--------------|-------------------:|-------------------:|
| Actual Positive |         38 (TP)    |          5 (FN)    |
| Actual Negative |         4 (FP)     |         N/A (TN)   |

## Metrics
- **Precision:** 38 / (38 + 4) = 0.905 (90.5%)
- **Recall:** 38 / (38 + 5) = 0.884 (88.4%)
- **F1 Score:** 0.894

## Strategy Breakdown
- Accelerometer alone: Precision 0.92, Recall 0.85
- Pose alone: Precision 0.78, Recall 0.91
- Fusion: Precision 0.905, Recall 0.884

## Per-Hand Analysis
- Right hand: 22 TP, 1 FP, 2 FN
- Left hand: 16 TP, 3 FP, 3 FN
```

---

## Phase 3: Implementation Order

1. **Recording system foundation** (`evaluation/recording_manager.py`)
2. **Game integration** (`main.py`, `ui_manager.py` modifications)
3. **Test recording** - Verify data capture works correctly
4. **Session loader** (`evaluation/session_loader.py`)
5. **Basic video player** (`evaluation/video_player.py`)
6. **Timeline widget** (`evaluation/timeline_widget.py`)
7. **Labeling interface** (`evaluation/labeling_panel.py`)
8. **Main eval tool** (`evaluation/eval_tool.py`) - Tie everything together
9. **Metrics calculator** (`evaluation/metrics_calculator.py`)
10. **Testing & refinement**

---

## Phase 4: Dependencies & Requirements

**New Python packages needed:**
```
# For evaluation tool GUI
tkinter (built-in) or PyQt5
opencv-python (already have)
matplotlib (for visualizations in reports)
scikit-learn (optional, for advanced metrics)
```

**Add to pyproject.toml:**
```toml
[project.optional-dependencies]
evaluation = [
    "matplotlib>=3.7.0",
    "scikit-learn>=1.3.0",
]
```

---

## Phase 5: Usage Workflow

### Recording a session:
```bash
uv run main.py
# Press 'R' to start recording
# Perform punches
# Press 'R' to stop recording
# Session saved to recordings/session_YYYYMMDD_HHMMSS/
```

### Evaluating a session:
```bash
uv run evaluation/eval_tool.py
# Select session from dropdown
# Review each detection
# Label as TP/FP, add FN as needed
# Export labels and generate report
```
