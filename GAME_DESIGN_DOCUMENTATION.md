# Punch Detection Game - Technical Design Documentation

## 1. Game Overview & Concept

### Core Mechanics
The Punch Detection Game is a real-time interactive system that combines smartphone accelerometer data with computer vision to detect and score punching movements. Players perform physical punches while standing in front of a camera, with their smartphone providing additional motion data for enhanced accuracy.

### Game Objectives
- **Real-time punch detection**: Immediate feedback on punch execution quality
- **Scoring system**: Points awarded based on punch strength and timing
- **Combo mechanics**: Bonus points for consecutive punches within time windows
- **Multi-modal validation**: Dual verification using both visual and motion sensors

### Target Experience
Players engage in a physically active gaming experience that encourages proper punching form while providing immediate quantitative feedback on their performance through a sophisticated detection system.

## 2. Detection System Architecture

### 2.1 Fusion Detection Strategy

The game employs a dual-sensor fusion approach that combines two independent detection methods to achieve high accuracy while minimizing false positives.

#### Weighted Scoring Algorithm
```
Final Score = (Accelerometer Score × 0.7) + (Pose Detection Score × 0.3)
```

**Rationale**: Accelerometer data provides precise motion measurements but lacks spatial context. Computer vision provides spatial awareness but can be affected by lighting conditions. The 70/30 weighting favors the more reliable accelerometer data while incorporating visual validation.

#### Multi-Criteria Validation
A punch is registered when:
1. **High accelerometer activity** (score > 0.3) OR **significant visual movement** (score > 0.3)
2. **Combined weighted score** exceeds minimum threshold (0.2)
3. **Cooldown period** has elapsed (0.5 seconds since last punch)

#### Cooldown Mechanism
A 500-millisecond cooldown prevents false positives from:
- Arm recoil after impact
- Multiple rapid movements during single punch execution
- Sensor noise or processing artifacts

### 2.2 Accelerometer Detection (Smartphone Sensor)

#### Physics Principles
The smartphone accelerometer measures linear acceleration in three axes (X, Y, Z) at high frequency (typically 50-100 Hz).

**3D Acceleration Magnitude Calculation:**
```
magnitude = √(ax² + ay² + az²)
```

**Gravity Compensation:**
```
motion_magnitude = |total_magnitude - 9.81|
```
*Note: 9.81 m/s² represents Earth's gravitational acceleration*

#### Detection Algorithm
1. **Raw Data Processing**: Capture X, Y, Z acceleration values from smartphone
2. **Magnitude Calculation**: Compute 3D acceleration vector magnitude
3. **Gravity Removal**: Subtract gravitational component to isolate motion
4. **Threshold Application**: Compare against 20 m/s² minimum punch threshold
5. **Score Normalization**: Scale linearly with 40 m/s² representing maximum score

#### Scoring Formula
```
if motion_magnitude > 20.0:
    punch_score = min(motion_magnitude / 40.0, 1.0)
else:
    punch_score = 0
```

#### Data Transmission
- **Protocol**: WebSocket over HTTP/HTTPS
- **Frequency**: Real-time streaming (30-60 Hz)
- **Format**: JSON with timestamp, X/Y/Z values
- **Connectivity**: Local network or ngrok HTTPS tunneling for iOS compatibility

### 2.3 Computer Vision Detection (MediaPipe)

#### Pose Landmark Extraction
Google's MediaPipe framework extracts 33 anatomical landmarks from camera feed, creating a real-time skeletal representation of the user.

**Key Landmarks for Punch Detection:**
- Wrists (left/right): Primary movement tracking points
- Shoulders (left/right): Reference points for extension calculation
- Elbows (left/right): Arm angle and extension analysis

#### Multi-Orientation Support

**Front-Facing Detection:**
- **Identification**: Shoulder width > 0.3 (normalized coordinate space)
- **Analysis Focus**: Lateral (X-axis) and vertical (Y-axis) movements
- **Movement Formula**: `max(lateral_movement, vertical_movement)`

**Side-Facing Detection:**
- **Identification**: Shoulder width ≤ 0.3 (indicating profile view)
- **Analysis Focus**: Forward/backward (X-axis) and vertical (Y-axis) movements
- **Forward Movement Boost**: 1.2× multiplier for X-axis motion

#### Movement Analysis Algorithms

**Arm Extension Calculation:**
```
extension = |wrist_position - shoulder_position|
max_extension = max(left_arm_extension, right_arm_extension)
```

**Velocity Tracking:**
```
distance = √((x₂-x₁)² + (y₂-y₁)²)
velocity = distance / time_difference
velocity_score = min(velocity / 2.0, 1.0)  // 2.0 m/s threshold
```

**Combined Pose Scoring:**
```
pose_score = (max_extension × 0.8 + movement_score × 0.2) × 2.0
final_pose_score = min(pose_score, 1.0)
```

#### MediaPipe Configuration
- **Model Complexity**: Level 1 (balance of accuracy and performance)
- **Detection Confidence**: 0.5 minimum
- **Tracking Confidence**: 0.5 minimum
- **Processing Mode**: Video stream (optimized for continuous frames)

## 3. Scoring and Game Mechanics

### 3.1 Base Scoring System

#### Punch Strength Evaluation
Each detected punch receives a quality score (0-1) based on:
- **Accelerometer intensity**: Higher acceleration = higher score
- **Movement quality**: Proper arm extension and velocity
- **Detection confidence**: Clear sensor readings and pose visibility

#### Point Conversion
```
base_points = punch_quality_score × 100
```
*Example: A 0.75 quality punch awards 75 base points*

#### Quality Factors
- **Minimum detectable punch**: 20 m/s² acceleration yields ~50 points
- **Maximum intensity punch**: 40+ m/s² acceleration yields 100 points
- **Pose enhancement**: Good visual form can boost accelerometer-only detection
- **Poor form penalty**: Low pose scores can reduce overall point award

### 3.2 Combo System

#### Timing Window Mechanics
```
time_since_last_punch = current_time - last_punch_timestamp
if time_since_last_punch < 2.0 seconds:
    combo_count += 1
else:
    combo_count = 1  // Reset to new combo
```

#### Bonus Point Calculation
```
combo_bonus = combo_count × 10
total_points = base_points + combo_bonus
```

**Combo Examples:**
- 1st punch: 75 base points + 0 bonus = 75 points
- 2nd punch (within 2s): 80 base points + 20 bonus = 100 points
- 3rd punch (within 2s): 70 base points + 30 bonus = 100 points

#### Reset Conditions
- **Timeout**: No punch detected within 2-second window
- **Manual reset**: Player presses 'R' key or game restart
- **Game session end**: Application closure or quit command

### 3.3 Real-time Feedback

#### Visual Effects
- **Screen Flash**: 300ms duration with 30% transparency overlay
- **Color Coding**:
  - Green: Successful punch detection
  - Cyan: Active combo multiplier
  - Red: Sensor disconnection warning
  - Yellow: Instruction text

#### Score Display Elements
- **Current Score**: Live-updating point total
- **Combo Counter**: Current consecutive punch count
- **Punch Count**: Total punches in session
- **Sensor Status**: Real-time connectivity indicator

#### Connection Status Indicators
- **Green dot**: Smartphone sensor connected and transmitting
- **Red dot**: No sensor connection or data timeout
- **Pose skeleton**: MediaPipe landmarks visible when person detected

## 4. Technical Implementation Details

### 4.1 Mathematical Formulas

#### Core Detection Mathematics

**3D Vector Magnitude (Accelerometer):**
```
magnitude = √(ax² + ay² + az²)
where: ax, ay, az = acceleration components in m/s²
```

**Motion Isolation (Gravity Compensation):**
```
motion = |magnitude - 9.81|
where: 9.81 = Earth's gravitational acceleration (m/s²)
```

**Euclidean Distance (Pose Tracking):**
```
distance = √((x₂-x₁)² + (y₂-y₁)²)
where: (x₁,y₁), (x₂,y₂) = landmark positions at different frames
```

**Velocity Calculation:**
```
velocity = distance / Δt
where: Δt = time_difference between frames (seconds)
```

**Weighted Fusion Algorithm:**
```
final_score = (accelerometer_score × 0.7) + (pose_score × 0.3)
combined_threshold = 0.2
is_punch = final_score > combined_threshold
```

#### Scoring Transformations

**Accelerometer Score Normalization:**
```
if motion_magnitude > 20.0:
    score = min(motion_magnitude / 40.0, 1.0)
else:
    score = 0
```

**Pose Score Calculation:**
```
extension_component = max_arm_extension × 0.8
movement_component = movement_score × 0.2
pose_score = (extension_component + movement_component) × 2.0
final_pose_score = min(pose_score, 1.0)
```

**Game Point Conversion:**
```
base_points = int(quality_score × 100)
combo_bonus = combo_level × 10
total_points = base_points + combo_bonus
```

### 4.2 Detection Thresholds & Configuration

#### Accelerometer Parameters
- **Detection Threshold**: 20.0 m/s² (minimum punch intensity)
- **Scoring Maximum**: 40.0 m/s² (100% score normalization point)
- **Trigger Weight**: 0.7 (70% contribution to final score)
- **Minimum Trigger**: 0.3 (30% of max score to register punch)

#### Pose Detection Parameters
- **Visual Threshold**: 0.3 (minimum pose score for detection)
- **Trigger Weight**: 0.3 (30% contribution to final score)
- **Velocity Threshold**: 2.0 m/s (minimum wrist movement speed)
- **Extension Weight**: 0.8 (80% emphasis on arm extension)
- **Movement Weight**: 0.2 (20% emphasis on overall movement)

#### Timing Parameters
- **Punch Cooldown**: 0.5 seconds (prevents duplicate detection)
- **Combo Window**: 2.0 seconds (maximum time between combo punches)
- **Effect Duration**: 0.3 seconds (visual feedback display time)

#### MediaPipe Configuration
- **Model Complexity**: 1 (optimized for real-time performance)
- **Detection Confidence**: 0.5 (minimum pose detection threshold)
- **Tracking Confidence**: 0.5 (minimum landmark tracking threshold)
- **Buffer Sizes**: 10 frames each for sensor and pose data

#### Orientation Detection
- **Front-Facing Threshold**: 0.3 (shoulder width in normalized coordinates)
- **Side Confidence**: 0.7 (minimum confidence for side-stance detection)
- **Front Velocity Multiplier**: 1.0 (standard movement sensitivity)
- **Side Forward Multiplier**: 1.2 (enhanced forward movement detection)

### 4.3 Libraries and Technologies

#### Computer Vision Stack
- **MediaPipe**: Google's pose estimation framework
  - Real-time pose landmark detection
  - 33-point skeletal model
  - Optimized for mobile and desktop deployment

- **OpenCV**: Computer vision and camera processing
  - Camera capture and frame processing
  - Image format conversion (BGR ↔ RGB)
  - Display rendering and overlay graphics

#### Sensor Communication
- **Flask**: Python web framework for HTTP server
- **WebSocket**: Real-time bidirectional communication
- **ngrok**: HTTPS tunneling service for iOS compatibility
- **JSON**: Data serialization for sensor readings

#### Mathematical Processing
- **Python Math**: Built-in mathematical functions
  - Square root calculations for vector magnitudes
  - Trigonometric functions for angle analysis
  - Min/max operations for threshold applications

#### Development Tools
- **uv**: Python package management and virtual environment
- **dotenv**: Environment variable management for configuration
- **Threading**: Background server execution for sensor data

## 5. Performance Characteristics

### 5.1 Real-time Processing Capabilities

#### Frame Rate Performance
- **Target FPS**: 30+ frames per second for smooth visual feedback
- **Camera Resolution**: 640×480 pixels (optimized for pose detection)
- **Processing Latency**: Sub-100ms from movement to detection
- **Sensor Frequency**: 30-60 Hz accelerometer data sampling

#### Memory and CPU Optimization
- **Buffer Management**: Fixed-size deques prevent memory leaks
- **Efficient Processing**: MediaPipe GPU acceleration when available
- **Minimal Overhead**: Event-driven architecture reduces unnecessary computations
- **Resource Cleanup**: Proper initialization and teardown of camera/sensor resources

### 5.2 Network Performance

#### Connectivity Options
- **Local Network**: Direct IP connection for lowest latency
- **HTTPS Tunneling**: ngrok integration for iOS device compatibility
- **Fallback Modes**: Game functional with camera-only or sensor-only input

#### Data Transmission
- **Payload Size**: Minimal JSON packets (~50 bytes per sensor reading)
- **Connection Stability**: WebSocket reconnection handling
- **Cross-Platform**: iOS and Android smartphone compatibility

### 5.3 Environmental Adaptability

#### Lighting Conditions
- **Indoor Lighting**: Optimized for typical room lighting conditions
- **Pose Confidence**: Automatic adjustment based on detection quality
- **Fallback Detection**: Accelerometer maintains function in poor lighting

#### User Positioning
- **Distance Tolerance**: 1-3 meters from camera optimal range
- **Angle Flexibility**: Front-facing and side-facing stance support
- **Height Adaptation**: Automatic scaling based on detected pose proportions

## 6. Calibration and Tuning

### 6.1 Sensitivity Adjustment

#### User-Specific Tuning
Thresholds can be adjusted in configuration files for different user types:

**Light Users (Casual Players):**
- Accelerometer threshold: 15 m/s² (easier detection)
- Pose threshold: 0.25 (more forgiving movement requirements)
- Combo timeout: 2.5 seconds (longer window for consecutive punches)

**Heavy Users (Athletic/Training):**
- Accelerometer threshold: 25 m/s² (requires more force)
- Pose threshold: 0.35 (stricter form requirements)
- Combo timeout: 1.5 seconds (faster-paced gameplay)

#### Environmental Adaptation
- **Camera Distance**: Pose threshold adjustment based on user size in frame
- **Lighting Compensation**: Automatic confidence threshold modification
- **Device Sensitivity**: Smartphone-specific accelerometer calibration

### 6.2 Fusion Weight Distribution

#### Adjustable Detection Balance
The 70/30 accelerometer/pose weight distribution can be modified based on:

**High-Accuracy Mode (Equal Weighting):**
```
ACCEL_WEIGHT = 0.5
VISUAL_WEIGHT = 0.5
```

**Motion-Primary Mode (Sensor Focus):**
```
ACCEL_WEIGHT = 0.85
VISUAL_WEIGHT = 0.15
```

**Form-Primary Mode (Visual Focus):**
```
ACCEL_WEIGHT = 0.5
VISUAL_WEIGHT = 0.5
```

### 6.3 Performance Optimization

#### Threshold Fine-Tuning
- **False Positive Reduction**: Increase minimum combined score threshold
- **Sensitivity Enhancement**: Lower individual detection thresholds
- **Latency Optimization**: Adjust buffer sizes and processing intervals
- **Accuracy Improvement**: Modify fusion weights based on user feedback

#### Real-time Adaptation
The system can potentially incorporate machine learning for:
- **User-specific calibration**: Learning individual movement patterns
- **Environmental adjustment**: Automatic threshold adaptation
- **Performance optimization**: Dynamic resource allocation based on system capabilities

---

*This documentation provides a comprehensive technical overview of the punch detection game's design principles, algorithms, and implementation details. The system combines proven computer vision techniques with smartphone sensor technology to create an engaging and accurate motion detection gaming experience.*