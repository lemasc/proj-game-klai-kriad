# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a punch detection game that combines smartphone accelerometer data with computer vision using MediaPipe to detect and score punches. The game uses the smartphone as a sensor controller and the computer's webcam for pose tracking.

## Development Setup

### Dependencies and Environment

- Python 3.12+ (specified in .python-version)
- Uses `uv` as package manager with virtual environment
- Key dependencies: Flask, MediaPipe, OpenCV, NumPy

### Commands

**Install dependencies:**

```bash
uv sync
```

**Run the application:**

```bash
uv run main.py
```

**Check Python version:**

```bash
python --version  # Should be 3.12+
```

## Architecture

### Core Components

**main.py** - Single-file application containing:

- `PunchDetectionGame` class - Main game logic and coordination
- Flask web server for smartphone sensor communication
- MediaPipe pose detection pipeline
- OpenCV camera capture and display
- Real-time punch detection algorithm combining accelerometer + pose data

**templates/index.html** - Smartphone interface:

- Web-based accelerometer sensor controller
- Connects to Flask server on port 5000
- Sends motion data via HTTP POST requests
- Provides real-time status and metrics display

### Key Systems

**Sensor Communication:**

- Flask server runs on port 5000 (`/sensor` POST endpoint, `/status` GET endpoint)
- Smartphone connects via local WiFi (IP address) or HTTPS tunnel (for iOS)
- Data format: JSON with x,y,z acceleration, gyroscope, and timestamp

**Punch Detection Algorithm:**

- Combines accelerometer magnitude (70% weight) with pose analysis (30% weight)
- Accelerometer threshold: 20.0 m/s² (configurable in `accel_punch_threshold`)
- Pose analysis: arm extension and forward movement detection
- Punch cooldown: 0.5 seconds between detections
- Combo system: consecutive punches within 2 seconds for bonus points

**Game Mechanics:**

- Score: 0-100 points per punch based on force/speed
- Combo bonuses: +10 points per consecutive hit
- Visual effects: screen flash and "PUNCH!" text overlay
- Real-time pose skeleton overlay using MediaPipe

### Configuration Points

**Detection Sensitivity (in main.py:37-40):**

```python
self.accel_punch_threshold = 20.0    # Lower = more sensitive
self.visual_punch_threshold = 0.3    # Lower = more sensitive
self.punch_cooldown = 0.5           # Seconds between punches
```

**Scoring Weights (in main.py:196):**

```python
combined_score = (accel_score * 0.7 + visual_score * 0.3)
```

## Network Setup

The application requires network connectivity between smartphone and computer:

1. **Same WiFi Network**: Computer IP address method (doesn't work on iOS due to HTTPS requirement)
2. **HTTPS Tunnel**: Use ngrok or similar for iOS compatibility and cross-network access

## Controls

- **Space Bar**: Manual punch trigger for testing
- **R Key**: Reset score
- **Q Key**: Quit game

## Troubleshooting

**Camera Issues**: Ensure no other applications are using the camera; check lighting conditions
**Connection Issues**: Verify firewall settings for port 5000, confirm WiFi connectivity
**Detection Issues**: Adjust thresholds in code or improve lighting/positioning
