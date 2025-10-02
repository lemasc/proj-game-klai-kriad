# Evaluation System Guide

## Overview

The evaluation system allows you to assess the accuracy of the automated punch detection by comparing it against ground truth observations from a peer. This dual detection system enables you to measure precision, recall, and identify areas for improvement in the detection algorithms.

## System Architecture

### Components

1. **Recording System** (`evaluation/recording_manager.py`)
   - Records video, sensor data, and detection events
   - Logs ground truth events from peer observations
   - Manages session lifecycle and file I/O

2. **Ground Truth Interface** (`templates/index.html`)
   - Web-based buttons for peer to mark observed punches
   - LEFT and RIGHT punch buttons
   - Appears automatically when connected via WebSocket

3. **Sensor Server** (`detection/accelerometer/sensor_server.py`)
   - Receives ground truth events via WebSocket
   - Captures server-side timestamps for synchronization
   - Forwards events to RecordingManager

4. **Comparison Script** (`evaluation/compare_ground_truth.py`)
   - Analyzes detection accuracy against ground truth
   - Calculates precision, recall, and F1 score
   - Generates detailed markdown reports

### Data Flow

```
Player Punches                    Peer Observes
      ↓                                 ↓
Automated Detection            Ground Truth Button
      ↓                                 ↓
detections.jsonl              ground_truth.jsonl
      ↓                                 ↓
      └─────────────┬───────────────────┘
                    ↓
          Comparison Script
                    ↓
         Accuracy Report (metrics + insights)
```

### Timestamp Synchronization

- **Server-side timestamps**: Both detection and ground truth use `time.time()` on the server
- **Relative time**: All timestamps are stored relative to `session_start_time`
- **Match window**: Configurable tolerance (default ±300ms) for human reaction time
- **Manual offset**: Adjustable parameter to correct systematic delays

## How to Use

### Step 1: Enable Evaluation Mode

In the game, press the evaluation mode toggle key (check `main.py` for the key binding).

```
🔬 Evaluation Mode ENABLED
```

### Step 2: Set Up Peer Observer

1. The peer opens the smartphone web interface (scan QR code or visit URL)
2. Connect to the server by pressing "Start Tracking"
3. Ground truth section appears with LEFT/RIGHT buttons
4. Peer positions themselves to clearly observe the player's punches

### Step 3: Record Session

1. Player starts the game (enters PLAYING mode)
2. Recording automatically starts in evaluation mode
3. Player performs punches
4. Peer presses corresponding button when they observe a punch:
   - Press **LEFT** button when observing a left punch
   - Press **RIGHT** button when observing a right punch
5. Game ends or player returns to menu
6. Recording automatically stops and saves to `recordings/session_YYYYMMDD_HHMMSS/`

**Important**: The peer should press the button AS they observe the punch, not before or after. Reaction time is accounted for in the comparison script.

### Step 4: Analyze Results

Run the comparison script on the recorded session:

```bash
python evaluation/compare_ground_truth.py --session recordings/session_20250102_143022
```

The script outputs a detailed report to the console. Optionally save to a file:

```bash
python evaluation/compare_ground_truth.py \
  --session recordings/session_20250102_143022 \
  --output analysis_report.md
```

## Session File Structure

Each recording session creates a directory with these files:

```
recordings/
└── session_20250102_143022/
    ├── video.mp4              # Recorded gameplay video
    ├── detections.jsonl       # Automated punch detections
    ├── sensor_data.jsonl      # Raw accelerometer data
    ├── ground_truth.jsonl     # Peer observations
    └── metadata.json          # Session metadata
```

### File Formats

#### detections.jsonl
```json
{"timestamp": 2.145, "frame": 64, "type": "punch", "hand": "right", "confidence": 0.85, ...}
{"timestamp": 4.892, "frame": 147, "type": "punch", "hand": "left", "confidence": 0.92, ...}
```

#### ground_truth.jsonl
```json
{"timestamp": 2.180, "hand": "right", "source": "peer"}
{"timestamp": 4.901, "hand": "left", "source": "peer"}
```

#### sensor_data.jsonl
```json
{"timestamp": 2.140, "accel": {"x": 12.5, "y": -8.3, "z": 15.2}, "gyro": {...}}
```

#### metadata.json
```json
{
  "session_id": "session_20250102_143022",
  "start_time": "2025-01-02T14:30:22.123456",
  "duration_seconds": 45.2,
  "fps": 30,
  "resolution": [640, 480],
  "detection_config": {
    "accel_threshold": 20.0,
    "visual_threshold": 0.7,
    "accel_weight": 0.7,
    "visual_weight": 0.3
  },
  "strategies": ["accelerometer", "pose"]
}
```

## Comparison Script Options

### Basic Usage

```bash
python evaluation/compare_ground_truth.py --session <path>
```

### Advanced Options

```bash
--session <path>           # Required: Path to session directory
--match-window <seconds>   # Time tolerance for matching (default: 0.3)
--offset <seconds>         # Time offset for ground truth (default: 0.0)
--output <file>            # Save report to file (default: console)
```

### Examples

**Default analysis:**
```bash
python evaluation/compare_ground_truth.py \
  --session recordings/session_20250102_143022
```

**Wider match window for slower reactions:**
```bash
python evaluation/compare_ground_truth.py \
  --session recordings/session_20250102_143022 \
  --match-window 0.5
```

**Apply systematic time offset:**
```bash
python evaluation/compare_ground_truth.py \
  --session recordings/session_20250102_143022 \
  --offset -0.15
```

**Save detailed report:**
```bash
python evaluation/compare_ground_truth.py \
  --session recordings/session_20250102_143022 \
  --match-window 0.3 \
  --offset 0.0 \
  --output reports/analysis_$(date +%Y%m%d).md
```

## Understanding the Report

### Summary Metrics

- **Precision**: Percentage of detections that were correct (TP / (TP + FP))
  - High precision = few false alarms
  - Low precision = too many false detections

- **Recall**: Percentage of ground truth events that were detected (TP / (TP + FN))
  - High recall = catches most real punches
  - Low recall = misses many punches

- **F1 Score**: Harmonic mean of precision and recall (2 × P × R / (P + R))
  - Balanced measure of overall accuracy
  - Range: 0.0 (worst) to 1.0 (perfect)

### Event Categories

- **True Positive (TP)**: Detection matched with ground truth ✓
- **False Positive (FP)**: Detection with no matching ground truth (false alarm)
- **False Negative (FN)**: Ground truth with no matching detection (missed punch)

### Matched Events Table

Shows successfully matched punch pairs:

| Ground Truth Time | Detection Time | Time Diff | Hand |
|-------------------|----------------|-----------|------|
| 2.180s | 2.145s | -0.035s | right |
| 4.901s | 4.892s | -0.009s | left |

**Time Diff interpretation:**
- Negative value: Detection came BEFORE ground truth (system is fast)
- Positive value: Detection came AFTER ground truth (system is slow)
- Average time diff suggests systematic offset

### Tuning Suggestions

The report automatically provides tuning suggestions based on results:

**High FN, Low FP:**
- Detection threshold too strict
- **Action**: Lower `ACCEL_PUNCH_THRESHOLD` or `VISUAL_PUNCH_THRESHOLD`

**High FP, Low FN:**
- Detection too sensitive
- **Action**: Raise thresholds

**Systematic Time Offset:**
- Consistent delay in detection or ground truth
- **Action**: Use `--offset` parameter to compensate

**Hand-Specific Issues:**
- Performance differs between left/right
- **Action**: Review hand detection logic or sensor orientation

## Best Practices

### For Peer Observers

1. **Position yourself** where you can clearly see both hands
2. **Press immediately** when you observe the punch motion
3. **Press the correct button** (LEFT/RIGHT) matching the hand used
4. **Avoid anticipation** - press when you SEE it, not when you expect it
5. **Stay consistent** - use the same reaction pattern throughout the session

### For Data Collection

1. **Multiple sessions**: Run 3-5 sessions to get reliable statistics
2. **Varied conditions**: Test different punch speeds, angles, and styles
3. **Different peers**: Use multiple observers to reduce individual bias
4. **Document context**: Note any unusual conditions (lighting, distance, etc.)

### For Analysis

1. **Start with defaults**: Use default match window (0.3s) first
2. **Check time diffs**: Look at average time difference in matched events
3. **Apply offset if needed**: If average diff > 50ms, use `--offset`
4. **Iterate**: Adjust parameters based on report suggestions
5. **Compare across sessions**: Track metrics over time to measure improvements

## Troubleshooting

### No ground_truth.jsonl file

**Problem**: Peer didn't press any buttons during recording

**Solution**:
- Ensure peer's device is connected (check "Sensor: Connected" status)
- Verify ground truth section is visible (appears after connection)
- Make sure recording is active (evaluation mode + PLAYING state)

### All events are False Positives

**Problem**: Ground truth timestamps don't align with detections

**Solutions**:
- Check if recording started/stopped at correct times
- Verify peer pressed buttons during the actual game session
- Try larger `--match-window` (e.g., 0.5s)

### All events are False Negatives

**Problem**: Detections exist but don't match ground truth

**Solutions**:
- Verify hand labels match (LEFT/RIGHT)
- Try larger `--match-window`
- Check for systematic time offset in matched events
- Apply `--offset` to compensate for reaction time

### Inconsistent Results

**Problem**: Metrics vary widely between sessions

**Solutions**:
- Use same peer observer for consistency
- Ensure consistent observation position and conditions
- Collect more sessions for statistical significance
- Review video to identify discrepancies

## Configuration Files

### Detection Configuration
Modify thresholds in `detection/detection_config.py`:

```python
ACCEL_PUNCH_THRESHOLD = 20.0    # Accelerometer threshold
VISUAL_PUNCH_THRESHOLD = 0.7     # Pose detection threshold
ACCEL_WEIGHT = 0.7               # Accelerometer weight in fusion
VISUAL_WEIGHT = 0.3              # Pose weight in fusion
```

### Recording Configuration
Modify buffer and file settings in `evaluation/recording_config.py`:

```python
BUFFER_SIZE = 100                # Number of events before flush
VIDEO_CODEC = 'mp4v'             # Video codec
RECORDINGS_DIR = Path('recordings')  # Output directory
```

## Next Steps

After collecting and analyzing evaluation data:

1. **Identify patterns** in false positives and false negatives
2. **Adjust thresholds** based on precision/recall tradeoff
3. **Tune fusion weights** if one strategy performs better
4. **Re-evaluate** to confirm improvements
5. **Document findings** for future reference

## See Also

- [Evaluation System Plan](evaluation-system-plan.md) - Original system design
- [Ground Truth System Plan](ground-truth-system-plan.md) - Implementation details
- `evaluation/recording_manager.py` - Recording implementation
- `evaluation/compare_ground_truth.py` - Analysis script
