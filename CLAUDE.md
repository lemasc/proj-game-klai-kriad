# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a punch detection game that combines smartphone accelerometer data with computer vision to detect and score punches. The game uses MediaPipe for pose detection through the webcam and receives real-time accelerometer data from a smartphone via a Flask web server.

## Commands

### Development
- **Run the game**: `uv run main.py`
- **Install dependencies**: `uv sync`

### Testing
No formal test framework is configured. Manual testing involves:
1. Running the game with `uv run main.py`
2. Connecting smartphone to the web interface at `http://localhost:5000`
3. Testing punch detection with physical movements

## Architecture

### Core Game Components
- **Main Loop**: `main.py` - Contains `PunchDetectionGame` class that orchestrates all components
- **Event System**: `game/event_manager.py` - Central event-driven architecture for component communication
- **Game State**: `game/game_state.py` - Manages scoring, combos, and game statistics
- **UI Manager**: `game/ui_manager.py` - Handles all visual rendering and effects

### Detection System
The detection system uses a strategy pattern with fusion:

- **FusionDetector**: `detection/fusion_detector.py` - Combines results from multiple detection strategies
- **AccelerometerStrategy**: `detection/accelerometer/accelerometer_strategy.py` - Processes smartphone sensor data
- **PoseStrategy**: `detection/pose/pose_strategy.py` - Analyzes MediaPipe pose landmarks
- **Base Strategy**: `detection/base_strategy.py` - Abstract base class for all detection strategies

### Data Flow
1. Smartphone sends accelerometer data to Flask server (`detection/accelerometer/sensor_server.py`)
2. OpenCV captures webcam frames
3. Both data sources are processed by their respective strategies
4. FusionDetector combines strategy results using weighted scoring (70% accelerometer, 30% pose)
5. Events are triggered for punch detection, UI updates, and game state changes

### Configuration
- **Detection Config**: `detection/detection_config.py` - Thresholds and weights for detection algorithms
- **Game Config**: `game/game_config.py` - UI colors, timing, scoring, and camera settings

### Key Patterns
- **Event-Driven Architecture**: All components communicate through the EventManager
- **Strategy Pattern**: Detection strategies can be added/removed dynamically
- **Separation of Concerns**: Clear boundaries between detection, game logic, and UI

## Development Notes

### Adding New Detection Strategies
1. Inherit from `BaseDetectionStrategy` in `detection/base_strategy.py`
2. Implement required methods: `setup()`, `cleanup()`, `get_current_results()`
3. Register event handlers in the constructor
4. Add to FusionDetector in `main.py`

### Modifying Detection Sensitivity
Adjust values in `detection/detection_config.py`:
- `ACCEL_PUNCH_THRESHOLD`: Minimum acceleration to trigger detection
- `VISUAL_PUNCH_THRESHOLD`: Minimum pose score for detection
- `ACCEL_WEIGHT`/`VISUAL_WEIGHT`: Fusion weights (must sum to 1.0)

### Network Setup
The smartphone interface requires network connectivity:
- Local network: Use computer's IP address with port 5000
- HTTPS requirement: iOS requires HTTPS; use ngrok for tunneling
- Server runs on `0.0.0.0:5000` by default (configurable in `game/game_config.py`)